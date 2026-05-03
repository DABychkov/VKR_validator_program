import os
from io import BytesIO
import uuid
import time
import hashlib
from werkzeug.utils import secure_filename
from flask import send_from_directory, abort

# Разрешённые расширения для текстовых файлов
ALLOWED_EXTENSIONS = {'docx', 'doc', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# сохранение загруженного файла на аннализ
def save_uploaded_file(file):
    if not file or not allowed_file(file.filename):
        raise ValueError('Недопустимый тип файла. Разрешены: ' + ', '.join(ALLOWED_EXTENSIONS))
    
    original_filename = file.filename
    # Вычисляем MD5 от оригинального имени (в байтах)
    md5_hash = hashlib.md5(original_filename.encode('utf-8')).hexdigest()
    # Получаем расширение
    _, ext = os.path.splitext(original_filename)
    timestamp = int(time.time())
    
    base_name = f"{md5_hash}_{timestamp}"
    candidate_name = base_name + ext
    
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Обработка коллизии (если вдруг два одинаковых файла в одну секунду)
    counter = 1
    while os.path.exists(os.path.join(upload_dir, candidate_name)):
        candidate_name = f"{base_name}_{counter}{ext}"
        counter += 1
    
    file_path = os.path.join(upload_dir, candidate_name)
    file.save(file_path)
    
    return candidate_name

# удаление загруженного файла
def delete_uploaded_file(filename):
    """
    Удаляет файл из папки uploads, если он существует.
    filename — имя файла (без пути).
    Возвращает True, если файл удалён, False — если не найден.
    """
    upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    file_path = os.path.abspath(os.path.join(upload_dir, filename))
    
    # Защита: файл должен быть внутри папки uploads
    if not file_path.startswith(upload_dir):
        raise ValueError("Некорректное имя файла")
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

# Сохраняет PDF-отчёт на сервер и возвращает имя файла
def save_report_to_server(pdf_buffer: BytesIO, timestamp: int) -> str:
    """Сохраняет PDF-отчёт на сервер и возвращает имя файла."""
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    report_filename = f"report_{timestamp}.pdf"
    report_path = os.path.join(reports_dir, report_filename)
    with open(report_path, 'wb') as f:
        f.write(pdf_buffer.getbuffer())
    return report_filename

def get_report_path(filename):
    """Возвращает полный путь к файлу отчёта, если он существует, иначе None."""
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    file_path = os.path.join(reports_dir, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return file_path
    return None

# Отправляет файл отчёта клиенту
def send_report_file(filename):
    """Отправляет файл отчёта клиенту (inline, для просмотра в браузере)."""
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    # Защита от подстановки путей
    if '/' in filename or '\\' in filename:
        abort(400, description="Некорректное имя файла")
    # Проверяем, что файл существует (send_from_directory сам выбросит 404, но можно явно)
    if not os.path.exists(os.path.join(reports_dir, filename)):
        abort(404, description="Файл не найден")
    return send_from_directory(reports_dir, filename, as_attachment=True, download_name=filename)

# ф-я удаляется файлы созданные более определенного времени назад
def clean_old_reports(max_age_minutes: int = 15):
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    if not os.path.exists(reports_dir):
        return
    now = time.time()
    for filename in os.listdir(reports_dir):
        file_path = os.path.join(reports_dir, filename)
        if os.path.isfile(file_path):
            try:
                file_age = now - os.path.getmtime(file_path)
                print("file_age =", file_age, file_age > max_age_minutes * 60)
                if file_age > max_age_minutes * 60:
                # if file_age < max_age_minutes * 60:
                    os.remove(file_path)
            except (PermissionError, OSError):
                print("Файл занят – пропускаем, ничего страшного")
                # Файл занят – пропускаем, ничего страшного
                continue

# проверяю существование и свежесть файла
def is_report_valid(filename: str, max_age_minutes: int = 15) -> bool:
    """Проверяет существование и свежесть файла отчёта."""
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    file_path = os.path.join(reports_dir, filename)
    if not os.path.exists(file_path):
        return False
    file_age = time.time() - os.path.getmtime(file_path)
    return file_age <= max_age_minutes * 60