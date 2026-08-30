import os
import secrets
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Секретный пароль для доступа к вашей админке
ADMIN_PASSWORD = "MY_SUPER_SECRET_PASSWORD"
DB_FILE = "keys_db.txt"

def load_keys():
    if not os.path.exists(DB_FILE):
        return ["whyen_master_key"]
    with open(DB_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_key_to_file(key):
    with open(DB_FILE, "a") as f:
        f.write(f"{key}\n")

# --- 1. КРАСИВАЯ АДМИН-ПАНЕЛЬ (ТОЛЬКО ДЛЯ ВАС) ---
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    password = request.args.get("pass") or request.form.get("pass")
    if password != ADMIN_PASSWORD:
        return "<h3>Ошибка: Доступ запрещен. Укажите верный пароль в ссылке ?pass=ВАШ_ПАРОЛЬ</h3>", 403

    generated_key = None
    if request.method == "POST" and request.form.get("action") == "generate":
        generated_key = f"whyen_{secrets.token_hex(8)}"
        save_key_to_file(generated_key)

    current_keys = load_keys()
    
    # Простой HTML-шаблон для браузера
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>WHYEN Панель</title></head>
    <body style="font-family:sans-serif; background:#121214; color:#fff; padding:40px; max-width:500px; margin:0 auto;">
        <h2 style="color:#a855f7;">Панель Создателя WHYEN</h2>
        <form method="post" style="margin-bottom:20px;">
            <input type="hidden" name="pass" value="{{ password }}">
            <input type="hidden" name="action" value="generate">
            <button type="submit" style="background:#a855f7; color:#fff; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold; width:100%;">⚡ СГЕНЕРИРОВАТЬ НОВЫЙ КЛЮЧ</button>
        </form>
        {% if generated_key %}
            <div style="background:#1e1e24; padding:15px; border-radius:5px; border:1px solid #a855f7; margin-bottom:20px;">
                <span style="color:#a1a1aa; display:block; margin-bottom:5px;">Новый ключ создан:</span>
                <code style="color:#60a5fa; font-size:16px;">{{ generated_key }}</code>
            </div>
        {% endif %}
        <h3>Все активные ключи в базе ({{ current_keys|length }}):</h3>
        <ul>
            {% for key in current_keys %}
                <li style="margin-bottom:8px;"><code>{{ key }}</code></li>
            {% endfor %}
        </ul>
    </body>
    </html>
    """
    return render_template_string(html, current_keys=current_keys, generated_key=generated_key, password=password)

# --- 2. ЭНДПОИНТ ПРОВЕРКИ ДЛЯ НЕЙРОСЕТИ ---
@app.route("/check", methods=["GET"])
def check_key():
    user_key = request.args.get("key")
    if not user_key:
        return jsonify({"valid": False, "error": "Ключ не указан"}), 400
        
    active_keys = load_keys()
    if user_key in active_keys:
        return jsonify({"valid": True, "status": "active"})
    return jsonify({"valid": False, "status": "not_found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
