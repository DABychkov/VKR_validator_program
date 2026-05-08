
from flask import request, jsonify, render_template, send_from_directory, session
import os
from app.utils import save_uploaded_file, delete_uploaded_file
from pathlib import Path
from src.report_and_list_handler import ReportAndListHandler

# from app.report_old import generate_pdf_report
from app.utils import save_uploaded_file, delete_uploaded_file, save_report_to_server
from app.report import generate_pdf_report

import tempfile
from datetime import datetime
from app.utils import send_report_file, is_report_valid, clean_old_reports, delete_by_id
from app.utils import get_all_vars_for_rule, get_args_by_id_func, find_in_vars, find_rule_inSession_by_id
from app.utils import update_by_id
import uuid
from app.validators import validate_str,validate_int, validate_float

"""Контроллер главной страницы."""
def home():
    """Контроллер главной страницы."""
    return render_template('index.html')

"""Контроллер возвращает список правил проверки."""
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

"""Возвращает отчет после проверки."""
def download_report(filename):
    """Возвращает отчет после проверки."""
    # Очищаем старые файлы 
    clean_old_reports(max_age_minutes=1)
    # clean_old_reports()
    
    # Проверяем, валиден ли запрошенный файл
    if not is_report_valid(filename):
        return jsonify({'error': 'Ссылка устарела или файл не найден'}), 410
    
    return send_report_file(filename)

"""Контроллер для загрузки текстового файла через drag-and-drop. Проверки на соответствие правилам"""
def handle_check():
    """Контроллер для загрузки текстового файла через drag-and-drop. Проверки на соответствие правилам"""
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

def set_session():
    """Записывает данные в сессию."""
    # Можно принимать данные из запроса (GET или POST)
    # Для примера возьмём из аргументов запроса
    key = request.args.get('key', 'test_key')
    value = request.args.get('value', 'test_value')
    session[key] = value
    return jsonify({'message': f'Сессия установлена: {key}={value}'})

def get_session():
    """Читает данные из сессии."""
    key = request.args.get('key', 'test_key')
    value = session.get(key, 'не найдено')
    return jsonify({key: value})

"""Возвращает переменные вопроса."""
def get_vars_options():
    """Возвращает переменные вопроса."""
    return jsonify(get_all_vars_for_rule())

'''Добавляем новое правило пользователя'''
def add_rulle():
    '''Добавляем новое правило пользователя'''
    #  -------------------------------------------------- 
    # создаем словарь нижеследующей структуры
    # rule_id: str 
    # section: str  - название секции, где проходила проверка
    # description: str - пояснение к названии секции 
    # gost_ref: str = "0" - номер документа на который ссылаемся
    # func: str - название функции проверки
    # args: список аргументов

    # формируем новое правило проверки
    new_rule={}
    new_rule['rule_id']=uuid.uuid4()
    new_rule['rule_id']=str(uuid.uuid4())

    # Данные из формы
    select_section = request.form.get('select_section')         
    select_function = request.form.get('select_function')            
    rule_desc = request.form.get('rule_desc')            
    gost_ref = request.form.get('gost_ref')            


    # Валилируем данные из формы
    is_valid, nrs, name_err = validate_str(select_section)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    
    new_rule['section']=find_in_vars('section', 'id_section', nrs)['name']
    # print('select_section',select_section, new_rule['section'])

    is_valid, new_rule['description'], name_err = validate_str(rule_desc)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    # print('rule_desc',rule_desc, new_rule['description'])

    is_valid, new_rule['gost_ref'], name_err = validate_str(gost_ref,True)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    # print('gost_ref',gost_ref, new_rule['gost_ref'])

    is_valid, new_rule['func'], name_err = validate_str(select_function)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    # print('select_function',select_function, new_rule['func'])

    # По функции получаем аргументы
    args = get_args_by_id_func('func_check', select_function)
    # args = get_args_by_id_func(nd_rule['func_check'], select_function)

    # Перебираем аргументы полученные из post, валидируем и записываем в словарь
    for i in range(len(args)):
        arg = args[i]
        # Получаем аргумент из POST
        arg_val=request.form.get(arg['name'])
        # args[i]['val']=arg_val
        # По типу аргумента делаем валидацию
        choice = arg['type']
        if choice == "str":
            is_valid, cleaned_val, name_err = validate_str(arg_val)
        elif choice == "float":
            is_valid, cleaned_val, name_err = validate_float(arg_val)
        elif choice == "int":
            is_valid, cleaned_val, name_err = validate_int(arg_val)
        else:
            print("Invalid state abbreviation entered in valid")

        # если не прошли проверку
        if not is_valid:
            return jsonify({'statusCode': 400, 'message': name_err })
        
        # записываем проверенное значение
        args[i]['val']=arg_val


    new_rule['args']=args;
    # print(new_rule);
    # session['user_rules'].clear()
    user_rules=session.get('user_rules', [])
    user_rules.append(new_rule)
    session['user_rules']=user_rules

    # print("session[user_rules]",session.get('user_rules', []))

    return jsonify({
    'statusCode': 200,
    'message': "Новое правило создано 😀",
    'data': user_rules
    })

'''Отправляем все правила пользователя'''
def get_user_rulles():
    '''Отправляем все правила пользователя'''
    user_rules=session.get('user_rules', [])
    return jsonify({
    'statusCode': 200,
    'message': "Получен список правил пользователя",
    'data': user_rules
    })

'''Удаляем одно правило пользователя'''
def del_user_rulle():
    '''Удаляем одно правило пользователя'''

    # получаем id правила
    rule_id_raw = request.form.get('rule_id') 
    # Проверка id
    is_valid, rule_id, name_err = validate_str(rule_id_raw)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': "Не удалось определить какое правило запрашивается" })
    
    # получаем все правила из сессии
    user_rules=session.get('user_rules', [])
    # удаляем выбранное правило
    deleted = delete_by_id(user_rules,'rule_id', rule_id)

    if deleted:
        # помещаем список правил пользователя обратно в сессиию
        session['user_rules']=user_rules
        return jsonify({
            'statusCode': 200,
            'message': "Правило удалено успешно",
            'data': user_rules
            })
    else:
        return jsonify({
            'statusCode': 400,
            'message': "Удалить не удалось",
            'data': user_rules
            })

'''Отправляем одно правило пользователя'''    
def get_one_user_rulle():
    '''Отправляем одно правило пользователя'''
    # получаем id правила
    rule_id_raw = request.form.get('rule_id')
    # Проверка id
    is_valid, rule_id, name_err = validate_str(rule_id_raw)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': "Не удалось определить какое правило запрашивается" })

    # print('rule_id',rule_id)

    rule=find_rule_inSession_by_id(rule_id)
    # print('rule',rule)
    # var=find_in_vars('section', 'name', rule['section'])
    # print('var',var)

    # rule['id_section']=var['id_section']
    # print('rule_from_session', rule)
    return jsonify({
            'statusCode': 200,
            # 'message': "",
            'data': rule
            })

'''обновить одно правило пользователя'''
def update_user_rulle():
    '''обновить одно правило пользователя'''
    # получаем id правила
    rule_id_raw = request.form.get('rule_id') 
    # Проверка id
    is_valid, rule_id, name_err = validate_str(rule_id_raw)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': "Не удалось определить какое правило обновляется" })
    
    # формируем новое правило проверки
    new_rule={}
    new_rule['rule_id']=rule_id

    # Данные из формы
    select_section = request.form.get('select_section')         
    select_function = request.form.get('select_function')            
    rule_desc = request.form.get('rule_desc')            
    gost_ref = request.form.get('gost_ref')            


    # Валилируем данные из формы
    is_valid, nrs, name_err = validate_str(select_section)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    
    new_rule['section']=find_in_vars('section', 'id_section', nrs)['name']
    # print('select_section',select_section, new_rule['section'])

    is_valid, new_rule['description'], name_err = validate_str(rule_desc)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    # print('rule_desc',rule_desc, new_rule['description'])

    is_valid, new_rule['gost_ref'], name_err = validate_str(gost_ref,True)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    # print('gost_ref',gost_ref, new_rule['gost_ref'])

    is_valid, new_rule['func'], name_err = validate_str(select_function)
    if not is_valid:
        return jsonify({'statusCode': 400, 'message': name_err })
    # print('select_function',select_function, new_rule['func'])

    # По функции получаем аргументы
    args = get_args_by_id_func('func_check', select_function)

    # Перебираем аргументы полученные из post, валидируем и записываем в словарь
    for i in range(len(args)):
        arg = args[i]
        # Получаем аргумент из POST
        arg_val=request.form.get(arg['name'])
        # args[i]['val']=arg_val
        # По типу аргумента делаем валидацию
        choice = arg['type']
        if choice == "str":
            is_valid, cleaned_val, name_err = validate_str(arg_val)
        elif choice == "float":
            is_valid, cleaned_val, name_err = validate_float(arg_val)
        elif choice == "int":
            is_valid, cleaned_val, name_err = validate_int(arg_val)
        else:
            print("Invalid state abbreviation entered in valid")

        # если не прошли проверку
        if not is_valid:
            return jsonify({'statusCode': 400, 'message': name_err })
        
        # записываем проверенное значение
        args[i]['val']=arg_val


    new_rule['args']=args;

    # получаем все правила
    user_rules=session.get('user_rules', [])
    # обновляем список правил пользователя в сессии
    result_update=update_by_id(user_rules, rule_id, new_rule)
    if result_update:
        session['user_rules']=user_rules
        return jsonify({
            'statusCode': 200,
            'message': "Правило успешно обновлено",
            'data': user_rules
            })
    else:
        return jsonify({
            'statusCode': 400,
            'message': "Обновить не удалось",
            'data': user_rules
            })