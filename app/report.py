import os
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Регистрация обычного и жирного шрифтов из папки static/fonts
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_REGULAR = os.path.join(BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf')
FONT_BOLD = os.path.join(BASE_DIR, 'static', 'fonts', 'DejaVuSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_REGULAR))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', FONT_BOLD))
# Регистрируем семейство для поддержки тегов <b> и <i>
pdfmetrics.registerFontFamily('DejaVuSans',
                              normal='DejaVuSans',
                              bold='DejaVuSans-Bold',
                              italic='DejaVuSans',
                              boldItalic='DejaVuSans-Bold')

def generate_pdf_report_OLD(results: List[Dict[str, Any]], original_filename: str, upload_time: datetime) -> BytesIO:
    # Разделяем результаты на 4 категории
    ok_items = [r for r in results if r.get('status') == 'OK']
    fail_critical = [r for r in results if r.get('status') == 'FAIL' and r.get('severity') == 'CRITICAL']
    fail_recommend = [r for r in results if r.get('status') == 'FAIL' and r.get('severity') == 'RECOMMENDATION']
    skip_items = [r for r in results if r.get('status') == 'SKIP']

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    # Базовые стили с русским шрифтом
    styles = getSampleStyleSheet()
    for style_name in styles.byName:
        styles[style_name].fontName = 'DejaVuSans'

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'],
        alignment=TA_CENTER, spaceAfter=12*mm,
        textColor=colors.darkblue, fontName='DejaVuSans-Bold'
    )
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'],
        spaceAfter=6*mm, spaceBefore=12*mm,
        fontName='DejaVuSans-Bold'
    )
  
    item_style = ParagraphStyle(
        'ItemStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=10,           # межстрочный интервал внутри параграфа (c 12 можно уменьшить до 10)
        leftIndent=5*mm,
        spaceAfter=1*mm,         # убираем отступ после строки section-description
        fontName='DejaVuSans'
    )
    gost_style = ParagraphStyle(
        'GostStyle', parent=styles['Normal'],
        fontSize=9, leftIndent=7*mm,
        textColor=colors.grey, fontName='DejaVuSans'
    )
    message_style = ParagraphStyle(
        'MessageStyle', parent=styles['Normal'],
        fontSize=9, leftIndent=7*mm,
        textColor=colors.red, fontName='DejaVuSans'
    )

    story = []

    # Заголовок
    story.append(Paragraph("Отчёт по анализу документа", title_style))
    # Имя файла в кавычках
    quoted_filename = f"«{original_filename}»"
    info_text = f"Данный отчёт составлен по анализу файла <b>{quoted_filename}</b>, присланного {upload_time.strftime('%d.%m.%Y в %H:%M:%S')}"
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 6*mm))

    # Функция добавления раздела с нумерацией
    def add_section(title, items):
        if not items:
            return
        story.append(Paragraph(title, heading_style))
        for idx, item in enumerate(items, start=1):

            # Номер, жирный section, описание
            # line1 = f"{idx}. <b>{item['section']}</b> - {item['description']}"
            line1 = f"{idx}. <b>{format_section(item['section'])}</b> - {item['description']}"
            story.append(Paragraph(line1, item_style))
            if item.get('gost_ref') and item['gost_ref'] != '0':
                story.append(Paragraph(f"Ссылка: {item['gost_ref']}", gost_style))
            if item.get('message'):
                story.append(Paragraph(f"Сообщение: {item['message']}", message_style))
            story.append(Spacer(1, 2*mm))
        story.append(Spacer(1, 3*mm))

    add_section("1. Пройденные пункты проверки", ok_items)
    add_section("2. Не пройденные пункты проверки, критически важные", fail_critical)
    add_section("3. Не пройденные пункты проверки, рекомендуем обратить внимание", fail_recommend)
    add_section("4. Пропущенные пункты проверки", skip_items)

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_report(results: List[Dict[str, Any]], original_filename: str, upload_time: datetime) -> BytesIO:
    # Разделяем результаты на 4 категории
    ok_items = [r for r in results if r.get('status') == 'OK']
    fail_critical = [r for r in results if r.get('status') == 'FAIL' and r.get('severity') == 'CRITICAL']
    fail_recommend = [r for r in results if r.get('status') == 'FAIL' and r.get('severity') == 'RECOMMENDATION']
    skip_items = [r for r in results if r.get('status') == 'SKIP']

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    # Базовые стили с русским шрифтом
    styles = getSampleStyleSheet()
    for style_name in styles.byName:
        styles[style_name].fontName = 'DejaVuSans'

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'],
        alignment=TA_CENTER, spaceAfter=12*mm,
        textColor=colors.darkblue, fontName='DejaVuSans-Bold'
    )
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'],
        spaceAfter=6*mm, spaceBefore=12*mm,
        fontName='DejaVuSans-Bold'
    )
  
    item_style = ParagraphStyle(
        'ItemStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=10,           # межстрочный интервал внутри параграфа (c 12 можно уменьшить до 10)
        leftIndent=5*mm,
        spaceAfter=1*mm,         # убираем отступ после строки section-description
        fontName='DejaVuSans'
    )
    gost_style = ParagraphStyle(
        'GostStyle', 
        parent=styles['Normal'],
        fontSize=9, 
        leftIndent=7*mm,
        textColor=colors.grey, 
        spaceBefore=0.5*mm,   # маленький отступ перед gost_ref
        spaceAfter=0,
        fontName='DejaVuSans'
    )
    message_style = ParagraphStyle(
        'MessageStyle', 
        parent=styles['Normal'],
        fontSize=9, 
        leftIndent=7*mm,
        textColor=colors.red, 
        spaceAfter=1*mm,
        fontName='DejaVuSans'
    )

    story = []

    # Заголовок
    story.append(Paragraph("Отчёт по анализу документа", title_style))
    # Имя файла в кавычках
    quoted_filename = f"«{original_filename}»"
    info_text = f"Данный отчёт составлен по анализу файла <b>{quoted_filename}</b>, присланного {upload_time.strftime('%d.%m.%Y в %H:%M:%S')}"
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 6*mm))

    # Функция добавления раздела с нумерацией
    # def add_section(title, items):
    #     if not items:
    #         return
    #     story.append(Paragraph(title, heading_style))
    #     for idx, item in enumerate(items, start=1):

    #         # Номер, жирный section, описание
    #         # line1 = f"{idx}. <b>{item['section']}</b> - {item['description']}"
    #         line1 = f"{idx}. <b>{format_section(item['section'])}</b> - {item['description']}"
    #         story.append(Paragraph(line1, item_style))
    #         if item.get('gost_ref') and item['gost_ref'] != '0':
    #             story.append(Paragraph(f"Ссылка: {item['gost_ref']}", gost_style))
    #         if item.get('message'):
    #             story.append(Paragraph(f"Сообщение: {item['message']}", message_style))
    #         story.append(Spacer(1, 2*mm))
    #     story.append(Spacer(1, 3*mm))

    def add_section(title, items, number_color=colors.black):
        """Добавляет раздел с заголовком и списком пунктов, где номера выделены указанным цветом."""
        if not items:
            return
        story.append(Paragraph(title, heading_style))
        for idx, item in enumerate(items, start=1):
            section_text = format_section(item['section'])
            # Оборачиваем номер в цветной шрифт
            colored_number = f'<font color="{number_color}">{idx}</font>'
            line1 = f"{colored_number}. <b>{section_text}</b> - {item['description']}"
            story.append(Paragraph(line1, item_style))
            if item.get('gost_ref') and item['gost_ref'] != '0':
                story.append(Paragraph(f"Ссылка: {item['gost_ref']}", gost_style))
            if item.get('message'):
                story.append(Paragraph(f"Сообщение: {item['message']}", message_style))
            story.append(Spacer(1, 1*mm))
        story.append(Spacer(1, 3*mm))

    # add_section("1. Пройденные пункты проверки", ok_items)
    # add_section("2. Не пройденные пункты проверки, критически важные", fail_critical)
    # add_section("3. Не пройденные пункты проверки, рекомендуем обратить внимание", fail_recommend)
    # add_section("4. Пропущенные пункты проверки", skip_items)

    # Добавляем разделы с разными цветами номеров
    add_section("1. Пройденные пункты проверки", ok_items, number_color=colors.green)
    add_section("2. Не пройденные пункты проверки, критически важные", fail_critical, number_color=colors.red)
    add_section("3. Не пройденные пункты проверки, рекомендуем обратить внимание", fail_recommend, number_color=colors.blue)
    add_section("4. Пропущенные пункты проверки", skip_items, number_color=colors.black)  # или оставить чёрным

    doc.build(story)
    buffer.seek(0)
    return buffer


def format_section(section: str) -> str:
    """
    Преобразует SECTION_NAME в Section name.
    Заменяет подчёркивания на пробелы, приводит все буквы к нижнему регистру,
    затем делает заглавной только первый символ строки.
    """
    # Заменяем подчёркивания на пробелы
    spaced = section.replace('_', ' ')
    # Приводим всю строку к нижнему регистру и затем делаем заглавной первый символ
    return spaced.lower().capitalize()


    # Разделение на категории
    ok_items = [r for r in results if r.get('status') == 'OK']
    fail_critical = [r for r in results if r.get('status') == 'FAIL' and r.get('severity') == 'CRITICAL']
    fail_recommend = [r for r in results if r.get('status') == 'FAIL' and r.get('severity') == 'RECOMMENDATION']
    skip_items = [r for r in results if r.get('status') == 'SKIP']

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    # Стили (как у вас, но с отрегулированными отступами)
    styles = getSampleStyleSheet()
    for style_name in styles.byName:
        styles[style_name].fontName = 'DejaVuSans'

    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'],
        alignment=TA_CENTER, spaceAfter=12*mm,
        textColor=colors.darkblue, fontName='DejaVuSans-Bold'
    )
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'],
        spaceAfter=6*mm, spaceBefore=12*mm,
        fontName='DejaVuSans-Bold'
    )
    item_style = ParagraphStyle(
        'ItemStyle', parent=styles['Normal'],
        fontSize=10, leading=12, leftIndent=5*mm,
        spaceAfter=0, spaceBefore=0,  # убираем лишние отступы
        fontName='DejaVuSans'
    )
    gost_style = ParagraphStyle(
        'GostStyle', parent=styles['Normal'],
        fontSize=9, leftIndent=7*mm,
        textColor=colors.grey,
        spaceBefore=0.5*mm, spaceAfter=0,
        fontName='DejaVuSans'
    )
    message_style = ParagraphStyle(
        'MessageStyle', parent=styles['Normal'],
        fontSize=9, leftIndent=7*mm,
        textColor=colors.red,
        spaceBefore=0.5*mm, spaceAfter=0,
        fontName='DejaVuSans'
    )

    story = []

    # Заголовок и вводная информация
    story.append(Paragraph("Отчёт по анализу документа", title_style))
    quoted_filename = f"«{original_filename}»"
    info_text = f"Данный отчёт составлен по анализу файла <b>{quoted_filename}</b>, присланного {upload_time.strftime('%d.%m.%Y в %H:%M:%S')}"
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 6*mm))


    def add_section_with_color(title, items, color):
        if not items:
            return
        
        # Формируем содержимое раздела (без заголовка, заголовок внутри)
        content = []
        content.append(Paragraph(title, heading_style))
        for idx, item in enumerate(items, start=1):
            section_text = format_section(item['section'])
            line1 = f"{idx}. <b>{section_text}</b> - {item['description']}"
            content.append(Paragraph(line1, item_style))
            if item.get('gost_ref') and item['gost_ref'] != '0':
                content.append(Paragraph(f"Ссылка: {item['gost_ref']}", gost_style))
            if item.get('message'):
                content.append(Paragraph(f"Сообщение: {item['message']}", message_style))
            content.append(Spacer(1, 2*mm))
        content.append(Spacer(1, 3*mm))
        
        # Левая ячейка – цветная полоса (пустой параграф, чтобы ячейка имела высоту)
        # Помещаем туда очень тонкий Spacer, который растянется по высоте содержимого правой ячейки
        color_cell = [Spacer(1, 1)]  # Spacer с нулевой шириной и высотой 1 pt (будет растянут)
        # Но Spacer не растягивается. Лучше использовать Paragraph с неразрывным пробелом
        color_cell = [Paragraph("&nbsp;", item_style)]  # параграф с пробелом
        
        # Создаём таблицу: две колонки
        data = [[color_cell, content]]
        col_widths = [4*mm, doc.width - 4*mm]
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), color),      # заливка левой ячейки
            ('LEFTPADDING', (1,0), (1,-1), 5*mm),      # отступ слева в основной ячейке
            ('RIGHTPADDING', (1,0), (1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('BOX', (0,0), (-1,-1), 0, None),          # убираем все границы
            ('GRID', (0,0), (-1,-1), 0, None),
        ]))
        story.append(table)

    

    # Добавляем разделы с соответствующими цветами
    add_section_with_color("1. Пройденные пункты проверки (OK)", ok_items, colors.green)
    add_section_with_color("2. Не пройденные пункты проверки, критические (FAIL + CRITICAL)", fail_critical, colors.red)
    add_section_with_color("3. Не пройденные пункты проверки, рекомендуемые (FAIL + RECOMMENDATION)", fail_recommend, colors.orange)  # или colors.gold
    add_section_with_color("4. Пропущенные пункты проверки (SKIP)", skip_items, colors.lightgrey)

    doc.build(story)
    buffer.seek(0)
    return buffer