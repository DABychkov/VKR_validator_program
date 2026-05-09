from flask import Flask
# Импортируем расширение для работы с сессиями
from flask_session import Session
from app.routes import register_routes

app = Flask(__name__)
# соль-секретный ключ
app.secret_key = 'your-secret-key-here'  # ваш секретный ключ

# --- НАСТРОЙКИ ДЛЯ SERVER-SIDE СЕССИЙ ---
# Указываем, что сессии будут храниться на сервере
app.config['SESSION_TYPE'] = 'filesystem' 
# (Опционально) Указываем, где хранить файлы сессий. По умолчанию папка 'flask_session' в корне проекта.
# app.config['SESSION_FILE_DIR'] = './my_sessions' 
# --- КОНЕЦ НАСТРОЕК ---

# Инициализируем расширение Flask-Session
Session(app)
register_routes(app)

if __name__ == '__main__':
    app.run(debug=True)