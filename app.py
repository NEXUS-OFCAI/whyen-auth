import os
import secrets
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

ADMIN_PASSWORD = "MY_SUPER_SECRET_PASSWORD"
DB_FILE = "keys_db.txt"
VERSION = "2.1.0"

# Единственный вечный ключ для бесплатного режима
FREE_PUBLIC_KEY = "whyen_free_unlimited"

def load_keys_with_roles():
    """Загружает ключи и их роли. Возвращает словарь {ключ: роль}"""
    # Базовые ключи, которые есть всегда
    keys_dict = {
        FREE_PUBLIC_KEY: "free",
        "whyen_master_owner_key": "owner"
    }
    if not os.path.exists(DB_FILE):
        return keys_dict
        
    with open(DB_FILE, "r") as f:
        for line in f:
            if "|" in line:
                key, role = line.strip().split("|", 1)
                keys_dict[key] = role
    return keys_dict

def save_key_with_role(key, role):
    with open(DB_FILE, "a") as f:
        f.write(f"{key}|{role}\n")

# --- 1. ОБНОВЛЕННАЯ АДМИН-ПАНЕЛЬ С ВЫБОРОМ РОЛЕЙ ---
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    password = request.args.get("pass") or request.form.get("pass")
    if password != ADMIN_PASSWORD:
        return "<h3>Ошибка: Доступ запрещен.</h3>", 403

    generated_key = None
    assigned_role = None
    if request.method == "POST" and request.form.get("action") == "generate":
        assigned_role = request.form.get("role", "premium")
        generated_key = f"whyen_{secrets.token_hex(8)}"
        save_key_with_role(generated_key, assigned_role)

    all_keys = load_keys_with_roles()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>WHYEN Роли v2.1</title></head>
    <body style="font-family:sans-serif; background:#121214; color:#fff; padding:40px; max-width:550px; margin:0 auto;">
        <h2 style="color:#a855f7;">Управление доступом WHYEN v{{ version }}</h2>
        
        <form method="post" style="background:#1e1e24; padding:20px; border-radius:8px; margin-bottom:20px;">
            <input type="hidden" name="pass" value="{{ password }}">
            <input type="hidden" name="action" value="generate">
            <label style="display:block; margin-bottom:10px; color:#a1a1aa;">Выберите уровень нового ключа:</label>
            <select name="role" style="background:#27272a; color:#fff; border:1px solid #3f3f46; padding:10px; width:100%; border-radius:5px; margin-bottom:15px; font-size:14px;">
                <option value="premium">💎 Premium (Обычные возможности)</option>
                <option value="owner">👑 Owner (Максимальный доступ)</option>
            </select>
            <button type="submit" style="background:#a855f7; color:#fff; border:none; padding:12px; border-radius:5px; cursor:pointer; font-weight:bold; width:100%;">⚡ СГЕНЕРИРОВАТЬ КЛЮЧ</button>
        </form>

        {% if generated_key %}
            <div style="background:#1e1e24; padding:15px; border-radius:5px; border:1px solid #60a5fa; margin-bottom:20px;">
                <span style="color:#a1a1aa; display:block; margin-bottom:5px;">Создан ключ [{{ assigned_role.upper() }}]:</span>
                <code style="color:#60a5fa; font-size:16px;">{{ generated_key }}</code>
            </div>
        {% endif %}

        <h3>Публичный бесплатный ключ (Вечный):</h3>
        <p><code style="color:#34d399; font-size:15px;">{{ free_key }}</code></p>

        <h3>База выпущенных ключей ({{ all_keys|length }}):</h3>
        <ul style="list-style:none; padding:0;">
            {% for key, role in all_keys.items() %}
                {% if key != free_key %}
                <li style="background:#1e1e24; padding:10px; margin-bottom:8px; border-radius:5px; display:flex; justify-content:between; align-items:center;">
                    <code>{{ key }}</code>
                    <span style="background:{% if role=='owner' %}#ef4444{% else %}#3b82f6{% endif %}; padding:2px 8px; border-radius:4px; font-size:12px; font-weight:bold; margin-left:auto;">{{ role.upper() }}</span>
                </li>
                {% endif %}
            {% endfor %}
        </ul>
    </body>
    </html>
    """
    return render_template_string(html, all_keys=all_keys, generated_key=generated_key, assigned_role=assigned_role, password=password, free_key=FREE_PUBLIC_KEY, version=VERSION)

# --- 2. ОБНОВЛЕННЫЙ ЭНДПОИНТ ПРОВЕРКИ ДЛЯ НЕЙРОСЕТИ ---
@app.route("/check", methods=["GET"])
def check_key():
    user_key = request.args.get("key")
    if not user_key:
        return jsonify({"valid": False, "error": "Ключ отсутствует"}), 400
        
    db = load_keys_with_roles()
    if user_key in db:
        return jsonify({
            "valid": True, 
            "status": "active", 
            "role": db[user_key] # Передаем нейросети роль: free, premium или owner
        })
    return jsonify({"valid": False, "status": "not_found", "role": "none"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
