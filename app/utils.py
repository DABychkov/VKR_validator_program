import os
from io import BytesIO
import uuid
import time
import hashlib
from werkzeug.utils import secure_filename
from flask import send_from_directory, abort, session
from pathlib import Path
from typing import List, Dict, Any

# from app.validators import get_section_for_user_rules, get_function_for_user_rules


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

"""Удаляет файлы сессий старше max_age_секунд."""
def clean_old_sessions(max_age_seconds: int = 86400):
    """Удаляет файлы сессий старше max_age_секунд."""
    # Путь к папке, где хранятся файлы сессий.
    # Убедитесь, что путь совпадает с вашим app.config['SESSION_FILE_DIR']
    # Если вы не задавали SESSION_FILE_DIR, то папка называется 'flask_session'
    session_dir = Path('./flask_session')
    if not session_dir.exists():
        return

    now = time.time()
    for file_path in session_dir.iterdir():
        if file_path.is_file():
            file_age = now - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()  # Удаляем файл
                    print(f"Удален старый файл сессии: {file_path.name}")
                except Exception as e:
                    print(f"Не удалось удалить {file_path.name}: {e}")

"""Ф-я возвращает список аргументов."""
def get_args_by_id_func(ld, target_id):
    """Ф-я возвращает список аргументов."""
    data = get_all_vars_for_rule()
    item = next((x for x in data[ld] if x['id_func'] == target_id), None)
    return item['agr'] if item else None


'''Поиск по vars возвращает строку словаря в которой поключу содержится нужное значение'''
def find_in_vars(ld:str, key: str, value:str):
    data = get_all_vars_for_rule()
    item = next((x for x in data[ld] if x[key] == value), None)
    return item if item else None

'''Поиск по правилам в сессии и возвращаем нужное правило'''
def find_rule_inSession_by_id( id_value:str):
    user_rules=session.get('user_rules', [])
    str_id = str(id_value)
    item = next((x for x in user_rules if str(x['rule_id']) == str_id), None)
    return item if item else None

""" Ф-я удаляет из списка пользовательское правило по его id """
def delete_by_id(lst: List[Dict[str, Any]], key:str, id_value: Any) -> bool:
    """ Ф-я удаляет из списка пользовательское правило по его id """
    """
    Удаляет первый словарь из списка, у которого ключ 'field_name' равен id_value.
    
    Args:
        lst: Список словарей.
        id_value: Значение идентификатора, которое нужно удалить.
    
    Returns:
        True, если элемент был удалён, иначе False.
    """
    str_id = str(id_value)
    for index, item in enumerate(lst):
        # if str(item.get('rule_id')) == str_id:
        if str(item.get(key)) == str_id:
            lst.pop(index)
            return True
    return False

""" Ф-я обновляет из списка пользовательское правило по его id """
def update_by_id(lst: List[Dict[str, Any]], id_value: Any, updates: Dict[str, Any]) -> bool:
    """ Ф-я обновляет из списка пользовательское правило по его id """
    str_id = str(id_value)
    for item in lst:
        if str(item.get('rule_id')) == str_id:
            item.update(updates)
            return True
    return False


'''Ф-я Возвращает все правила созданные пользователем, а если нет, то пустой список'''
def get_all_user_rules_from_session():
    '''Ф-я Возвращает все правила созданные пользователем, а если нет, то пустой список'''
    return session.get('user_rules', [])

'''Ф-я Возвращает все переменные необходимые для создания своих правил'''
def get_all_vars_for_rule():
    '''Ф-я Возвращает все переменные необходимые для создания своих правил'''
    # nd={}
    # nd['section']=get_section_for_user_rules()
    # nd['func_check']=get_function_for_user_rules()

    # ------------------
    nd={
        'section':[
            {'id_section':'titulnik', 'name':'Титульник'},
            {'id_section':'list_link', 'name':'Список ссылок'},
            {'id_section':'referat', 'name':'Реферат'}
                    ],
        'func_check':[
            {'id_func':'font', 'name':'шрифт',  'agr':[
                {'name':'a', 'type':'str', 'desc':'введите название шрифта','um':''}
            ]},
            {'id_func':'font_size', 'name':'размер шрифта', 'agr':[
                {'name':'a', 'type':'float', 'desc':'введите размер шрифта min','um':'pt'},
                {'name':'b', 'type':'float', 'desc':'введите размер шрифта max','um':'pt'}
            ]},
            {'id_func':'interval_font', 'name':'интервал шрифта', 'agr':[
                {'name':'a', 'type':'float', 'desc':'введите интервал шрифта','um':'%'}
            ]}
        ]
    }
    # ----------------------
    
    return nd



