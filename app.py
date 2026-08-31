import os
import secrets
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

ADMIN_PASSWORD = "MY_SUPER_SECRET_PASSWORD"
DB_FILE = "keys_db.txt"
LOG_FILE = "ip_logs.txt"  # Файл для хранения логов подключений пользователей
VERSION = "2.3.0"
FREE_PUBLIC_KEY = "whyen_free_unlimited"

def load_keys_with_roles():
    keys_dict = {
        FREE_PUBLIC_KEY: "free",
        "whyen_master_owner_key": "owner"
    }
    if not os.path.exists(DB_FILE):
        return keys_dict
        
    with open(DB_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                key, role = line.strip().split("|", 1)
                keys_dict[key] = role
    return keys_dict

def save_key_with_role(key, role):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"{key}|{role}\n")

def log_user_session(key, role, user_ip):
    """Записывает лог использования ключа пользователем"""
    if not user_ip or user_ip == "unknown":
        return
    # Формат: ключ|роль|ip
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{key}|{role}|{user_ip}\n")

def get_session_logs():
    """Читает все уникальные сессии пользователей"""
    if not os.path.exists(LOG_FILE):
        return []
    logs = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    logs.append({"key": parts[0], "role": parts[1], "ip": parts[2]})
    # Возвращаем в обратном порядке (последние подключения сверху)
    return logs[::-1]

# --- НЕОНОВЫЙ ВЕБ-ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    password = request.args.get("pass") or request.form.get("pass")
    if password != ADMIN_PASSWORD:
        return "<h1 style='color:#ef4444; text-align:center; font-family:sans-serif; margin-top:50px;'>🛑 ДОСТУП ЗАПРЕЩЕН</h1>", 403

    generated_key = None
    assigned_role = None
    if request.method == "POST" and request.form.get("action") == "generate":
        assigned_role = request.form.get("role", "premium")
        generated_key = f"whyen_{secrets.token_hex(8)}"
        save_key_with_role(generated_key, assigned_role)

    all_keys = load_keys_with_roles()
    session_logs = get_session_logs()
    
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WHYEN Core OS v{{ version }}</title>
        <link rel="preconnect" href="https://googleapis.com">
        <link rel="preconnect" href="https://gstatic.com" crossorigin>
        <link href="https://googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cloudflare.com">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
            body { background: linear-gradient(135deg, #0f0c1b 0%, #151124 50%, #060409 100%); color: #e2e8f0; min-height: 100vh; padding: 40px 20px; display: flex; justify-content: center; align-items: center; flex-direction: column; gap: 30px; }
            .container { width: 100%; max-width: 650px; background: rgba(26, 21, 44, 0.45); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 24px; padding: 40px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5); }
            .header { text-align: center; margin-bottom: 35px; }
            .logo-panel { font-size: 32px; font-weight: 800; letter-spacing: -1px; background: linear-gradient(45deg, #a855f7 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; }
            .subtitle { color: #71717a; font-size: 14px; font-weight: 500; }
            .form-box { background: rgba(15, 12, 27, 0.6); border: 1px solid rgba(255, 255, 255, 0.05); padding: 24px; border-radius: 16px; margin-bottom: 30px; }
            label { display: block; font-size: 13px; font-weight: 700; color: #94a3b8; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
            select { width: 100%; background: #141125; color: #fff; border: 1px solid rgba(168, 85, 247, 0.4); padding: 14px; border-radius: 12px; font-size: 15px; font-weight: 500; outline: none; cursor: pointer; margin-bottom: 20px; }
            button { width: 100%; background: linear-gradient(90deg, #a855f7 0%, #6366f1 100%); color: #fff; border: none; padding: 16px; border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4); }
            button:hover { transform: translateY(-2px); box-shadow: 0 6px 25px rgba(168, 85, 247, 0.6); }
            .result-box { background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); padding: 18px; border-radius: 14px; margin-bottom: 30px; text-align: center; }
            .result-key { color: #fff; font-family: monospace; font-size: 18px; font-weight: 700; background: #000; padding: 8px 14px; border-radius: 8px; display: inline-block; }
            .section-title { font-size: 16px; font-weight: 700; margin-top: 25px; margin-bottom: 15px; color: #f1f5f9; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; }
            .key-list { list-style: none; max-height: 200px; overflow-y: auto; }
            .key-list::-webkit-scrollbar { width: 6px; }
            .key-list::-webkit-scrollbar-thumb { background: rgba(168, 85, 247, 0.3); border-radius: 4px; }
            .key-item { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px 18px; border-radius: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
            .key-text { font-family: monospace; font-size: 14px; color: #cbd5e1; }
            .badge { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; text-transform: uppercase; }
            .badge-free { background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
            .badge-premium { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }
            .badge-owner { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
            .log-ip { font-family: monospace; color: #f43f5e; font-weight: bold; background: rgba(244, 63, 94, 0.1); padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo-panel"><i class="fa-solid fa-terminal"></i> WHYEN MAINFRAME</div>
                <div class="subtitle">Управление лицензиями и трекинг сессий v{{ version }}</div>
            </div>

            {% if generated_key %}
                <div class="result-box">
                    <div style="font-size:12px; font-weight:700; color:#4ade80; text-transform:uppercase; margin-bottom:6px;"><i class="fa-solid fa-circle-check"></i> Токен [{{ assigned_role.upper() }}] инициализирован</div>
                    <div class="result-key">{{ generated_key }}</div>
                </div>
            {% endif %}

            <form method="post" class="form-box">
                <input type="hidden" name="pass" value="{{ password }}">
                <input type="hidden" name="action" value="generate">
                <label><i class="fa-solid fa-layer-group"></i> Приоритет (Уровень доступа)</label>
                <select name="role">
                    <option value="premium">💎 Premium (Стандартный ИИ)</option>
                    <option value="owner">👑 Owner (Режим Создателя)</option>
                </select>
                <button type="submit"><i class="fa-solid fa-bolt"></i> Сгенерировать токен</button>
            </form>

            <div class="section-title"><i class="fa-solid fa-list-check"></i> Реестр активных ключей</div>
            <ul class="key-list">
                <li class="key-item">
                    <span class="key-text">{{ free_key }}</span>
                    <span class="badge badge-free">FREE БЕЗЛИМИТ</span>
                </li>
                {% for key, role in all_keys.items() %}
                    {% if key != free_key %}
                    <li class="key-item">
                        <span class="key-text">{{ key }}</span>
                        <span class="badge badge-{{ role }}">{{ role }}</span>
                    </li>
                    {% endif %}
                {% endfor %}
            </ul>

            <div class="section-title"><i class="fa-solid fa-fingerprint"></i> USER CHECK: Логи сессий по IP (Топ 20)</div>
            <ul class="key-list" style="max-height: 250px;">
                {% if not session_logs %}
                    <li style="color:#71717a; text-align:center; padding:15px; font-size:14px;">Логи подключений пусты. Ожидание запросов от ИИ...</li>
                {% else %}
                    {% for log in session_logs[:20] %}
                    <li class="key-item" style="border-left: 3px solid #a855f7;">
                        <span class="key-text" style="font-size:12px; color:#94a3b8;">{{ log.key[:15] }}...</span>
                        <span class="badge badge-{{ log.role }}" style="font-size:10px;">{{ log.role }}</span>
                        <span class="log-ip">{{ log.ip }}</span>
                    </li>
                    {% endfor %}
                {% endif %}
            </ul>
        </div>
    </body>
    </html>
    """
return render_template_string(html, all_keys=all_keys, generated_key=generated_key, assigned_role=assigned_role, password=password, free_key=FREE_PUBLIC_KEY, session_logs=session_logs, version=VERSION)
