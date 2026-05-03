
from flask import request, jsonify, render_template, send_from_directory
import os
from app.utils import save_uploaded_file, delete_uploaded_file
from pathlib import Path
from src.report_and_list_handler import ReportAndListHandler

# from app.report_old import generate_pdf_report
from app.utils import save_uploaded_file, delete_uploaded_file, save_report_to_server
from app.report import generate_pdf_report

import tempfile
from datetime import datetime
from app.utils import send_report_file, is_report_valid, clean_old_reports

def home():
    """Контроллер главной страницы."""
    return render_template('index.html')

def get_list_rules():
    """Контроллер возвращает список правил проверки."""
    #  rule_id: str 
    # section: str  - название секции, где проходила проверка
    # description: str - пояснение к названии секции 
    # severity: str  # CRITICAL | RECOMMENDATION - тип требований при проверке
    # status: str = "SKIP"  # SKIP | OK | FAIL - результат проверки
    # message: str | None = None - сообщение об ошибке, если был FAIL
    # gost_ref: str = "0" - номер документа на который ссылаемся
    # implemented: bool = False

    

    data=ReportAndListHandler(encoding=False).getList()

    return jsonify({
    'statusCode': 200,
    'message': "Data check successfully 😀",
    'data': data
    })


def download_report(filename):
    # Очищаем старые файлы (можно делать при каждом запросе, это недорого)
    clean_old_reports(max_age_minutes=1)
    # clean_old_reports()
    
    # Проверяем, валиден ли запрошенный файл
    if not is_report_valid(filename):
        return jsonify({'error': 'Ссылка устарела или файл не найден'}), 410
    
    return send_report_file(filename)

def handle_check():
    """Контроллер для загрузки текстового файла через drag-and-drop."""
    if 'attachment' not in request.files:
        return jsonify({
        'statusCode': 400,
		'message': "Файл не загружен на сервер 😀"
        })
    
    file = request.files['attachment']    
    original_filename = file.filename

    try:
        # загружаем файл
        # unique_name, original_name = save_uploaded_file(file)
        unique_name= save_uploaded_file(file)
        

        PathDir = Path(__file__).resolve().parents[1]
        PathFile = str( PathDir / "uploads" / unique_name)


        # ----------------------------------------
        # Тут подключаем функции обработки файла 
        # который мы сохранили unique_name
        # где он хранится file_url
        # Результатом станет объект data
        
        data=ReportAndListHandler(encoding=True).validate(PathFile)


        # 2. Анализ файла (заглушка — здесь будет реальная логика)
        # Пока генерируем тестовый массив структур
        

        test_results=data["list"]

         # 3. Генерация PDF-отчёта
        upload_time = datetime.now()
        pdf_buffer = generate_pdf_report(test_results, original_filename, upload_time)


        # После получения pdf_buffer
        upload_time = datetime.now()
        pdf_buffer = generate_pdf_report(test_results, original_filename, upload_time)
        report_filename = save_report_to_server(pdf_buffer, int(upload_time.timestamp()))
        report_url = f'/reports/{report_filename}'

        # После мы удаляем загруженный файл
        delete_uploaded_file(unique_name)

        

        return jsonify({
        'statusCode': 200,
		'message': "Data check successfully 😀",
		'data': data,
        'report_url': f'/reports/{report_filename}'
        })
    
    except ValueError as e:
        return jsonify({
        'statusCode': 400,
		'message': "При проверке файла возникли критические ошибки 😀"
        })
    except Exception as e:
        return jsonify({'statusCode': 500, 'message': f'Внутренняя ошибка: {str(e)}', 'data': {}})
