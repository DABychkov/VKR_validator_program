"""Расширенная модель структуры документа для форматно-стилевых проверок.

Важно:
- Этот модуль дополняет, а не заменяет текущую текстовую модель.
- Старые валидаторы могут продолжать работать по DocumentStructure.
- Новые строгие валидаторы работают по RichDocumentStructure.
"""

from dataclasses import dataclass, field
from typing import Literal


AlignmentValue = Literal[
    "left",
    "center",
    "right",
    "justify",
    "distribute",
    "unknown",
]


@dataclass
class RunFeature:
    """Минимальный фрагмент текста с единым форматированием."""

    text: str  # текст куска
    font_name: str | None = None  # Times New Roman?
    font_size_pt: float | None = None  # 11-14 pt
    bold: bool | None = None  # жирный
    italic: bool | None = None  # наклонный
    underline: bool | None = None  # подчеркнуто
    all_caps: bool | None = None  # ЗАГЛАВНЫЕ
    color_rgb: str | None = None  # RGB или hex
    style_name: str | None = None  # стиль Word


@dataclass
class ParagraphFeature:
    """Снимок признаков абзаца для проверки выравнивания, отступов, интервалов."""

    block_index: int  # порядковый номер абзаца
    text: str  # текст абзаца
    section_hint: str | None = None  # какая секция (введение, основной текст, заключение)
    style_name: str | None = None  # стиль из Word
    alignment: AlignmentValue = "unknown"  # выравнивание (left/center/right/justify)

    first_line_indent_mm: float | None = None  # абзацный отступ
    left_indent_mm: float | None = None  # отступ слева
    right_indent_mm: float | None = None  # отступ справа

    line_spacing: float | None = None  # межстрочный интервал (1.5, 2.0, etc)
    space_before_pt: float | None = None  # отступ перед абзацем
    space_after_pt: float | None = None  # отступ после абзаца

    bold_ratio: float | None = None  # % текста жирным
    italic_ratio: float | None = None  # % текста наклонным
    has_page_break_before: bool = False  # разрыв страницы
    runs_features: list[RunFeature] = field(default_factory=list)  # детальный формат каждого куска


@dataclass
class TableCellFeature:
    """Минимальная информация о ячейке таблицы."""

    row: int  # индекс строки
    col: int  # индекс столбца
    text: str  # текст в ячейке
    is_header_row: bool = False  # принадлежит ли первой строке таблицы
    runs_features: list[RunFeature] = field(default_factory=list)  # форматные признаки run-ов в ячейке


@dataclass
class TableFeature:
    """Признаки таблицы для оформления по ГОСТ."""

    table_index: int  # порядковый номер таблицы
    table_anchor_paragraph_index: int | None = None  # индекс абзаца непосредственно перед таблицей
    section_hint: str | None = None  # какая часть документа
    rows_count: int = 0  # кол-во строк
    cols_count: int = 0  # кол-во столбцов

    title_above_text: str | None = None  # заголовок выше таблицы
    title_paragraph_index: int | None = None  # индекс абзаца заголовка таблицы (если найден)
    title_alignment: AlignmentValue = "unknown"  # выравнивание заголовка
    title_relative_position: Literal["above", "below", "same_paragraph", "unknown"] | None = None
    in_appendix: bool = False  # в приложении ли таблица
    number: str | None = None  # значение номера таблицы: "1", "1.1", "А.1"
    number_pattern: str | None = None  # тип шаблона: table_number_global/sectional/appendix/unknown

    has_inside_horizontal_borders: bool | None = None  # горизонтальные линии внутри
    has_inside_vertical_borders: bool | None = None  # вертикальные линии внутри
    has_outer_top_border: bool | None = None  # верхняя внешняя граница
    has_outer_bottom_border: bool | None = None  # нижняя внешняя граница
    has_outer_left_border: bool | None = None  # левая внешняя граница
    has_outer_right_border: bool | None = None  # правая внешняя граница
    has_diagonal_borders: bool | None = None  # диагональные линии

    continuation_marker: str | None = None  # признак "продолжение таблицы"
    header_row_cells: list[TableCellFeature] = field(default_factory=list)  # ячейки первой строки
    first_column_cells: list[TableCellFeature] = field(default_factory=list)  # ячейки первого столбца
    cell_text_map: list[TableCellFeature] = field(default_factory=list)  # текст в каждой ячейке


@dataclass
class FigureCaptionFeature:
    """Признаки подписи рисунка."""

    paragraph_index: int  # в каком абзаце подпись
    caption_text: str  # текст подписи
    caption_number: str | None = None  # номер подписи (1, 2.1, A.3)
    alignment: AlignmentValue = "unknown"  # выравнивание (часто центр)
    pattern_type: str | None = None  # шаблон: "Fig. 1", "Рис. 1", etc
    has_dash_separator: bool | None = None  # есть ли тире/дефис
    ends_with_period: bool | None = None  # заканчивается на точку
    has_nearby_drawing: bool | None = None  # найден ли рядом XML-объект рисунка
    drawing_relative_position: Literal["above", "below", "same_paragraph", "unknown"] | None = None
    in_appendix: bool = False  # в приложении ли


@dataclass
class FormulaFeature:
    """Признаки формул/уравнений."""

    paragraph_index: int  # в каком абзаце формула
    formula_text: str  # текст/восстановленная формула
    alignment: AlignmentValue = "unknown"  # выравнивание
    number: str | None = None  # значение номера без скобок: "1", "1.2", "А.2"
    number_pattern: str | None = None  # тип шаблона: formula_number_global/sectional/appendix/unknown
    number_alignment_right: bool | None = None  # номер справа

    has_blank_line_before: bool | None = None  # пустая строка перед
    has_blank_line_after: bool | None = None  # пустая строка после формулы (валидатор смотрит на has_explanation_where отдельно)
    has_where_marker: bool | None = None  # есть ли вообще маркер "где"/"where" (в т.ч. с двоеточием)
    has_explanation_where: bool | None = None  # есть "где"/"where" объяснение
    explanation_sequence_score: float | None = None  # качество объяснения

    omml_xml: str | None = None  # низкоуровневый Office Open XML (если нужен)


@dataclass
class LinkFeature:
    """Ссылка на источник/рисунок/таблицу/формулу."""

    link_type: Literal["source", "figure", "table", "formula", "standard"]  # тип ссылки
    raw_text: str  # текст как в документе
    paragraph_index: int | None = None  # индекс абзаца, в котором встретилась ссылка
    target_number: str | None = None  # номер цели (1, 1.2, диапазон)
    is_range: bool = False  # диапазон ли (1-5, 1.2-1.5)
    resolved_in_target_list: bool | None = None  # найдена ли цель в документе
    resolved_with_object: bool | None = None  # для figure/table: подтверждена ли цель как реальный объект
    relative_position_to_target: Literal["before", "after", "same", "unknown"] | None = None


@dataclass
class NoteFeature:
    """Примечания в тексте по шаблонам ГОСТ."""

    paragraph_index: int  # индекс абзаца
    raw_text: str  # исходный текст абзаца
    note_kind: Literal["single", "group_header", "group_item", "numbered_single", "unknown"] = "single"
    item_number: int | None = None  # номер пункта примечания, если есть
    has_dot_after_number: bool | None = None  # есть ли точка сразу после номера ("1." vs "1")
    has_dash_separator: bool | None = None  # есть ли разделитель "-" после слова "Примечание"
    near_figure_caption: bool = False  # рядом есть подпись рисунка
    near_table_caption: bool = False  # рядом есть подпись/заголовок таблицы


@dataclass
class FootnoteFeature:
    """Признаки сносок в тексте и их связь с footnotes.xml."""

    paragraph_index: int  # индекс абзаца, где найден маркер
    marker_text: str  # отображаемый маркер (* или id)
    marker_type: Literal["xml_reference", "asterisk"] = "xml_reference"
    footnote_id: int | None = None  # id из w:footnoteReference
    custom_mark_follows: bool | None = None  # кастомный маркер (например *) вместо номера
    resolved_in_footnotes_part: bool | None = None  # найден ли id в /word/footnotes.xml
    has_separator_line: bool | None = None  # обнаружена ли разделительная линия сноски
    separator_short_left_heuristic: bool | None = None  # линия похожа на короткую левую (эвристика)


@dataclass
class SectionPageSettingsFeature:
    """Параметры страницы в секции."""

    section_index: int  # порядковый номер секции
    start_type: str | None = None  # разрыв: непрерывная, новая страница, столбец
    page_width_mm: float | None = None  # ширина листа (обычно 210 A4)
    page_height_mm: float | None = None  # высота листа (обычно 297 A4)

    margin_left_mm: float | None = None  # левое поле (30 мм)
    margin_right_mm: float | None = None  # правое поле (15 мм)
    margin_top_mm: float | None = None  # верхнее поле (20 мм)
    margin_bottom_mm: float | None = None  # нижнее поле (20 мм)


@dataclass
class FooterFeature:
    """Признаки нумерации страниц в нижнем колонтитуле."""

    section_index: int  # какая секция
    has_page_field: bool = False  # есть ли поле "PAGE"
    page_field_format: str | None = None  # формат: "1", "I", "A", etc
    alignment: AlignmentValue = "unknown"  # выравнивание (обычно центр)
    restart_numbering: bool | None = None  # перезапуск нумерации в секции
    start_number: int | None = None  # с какого номера начинается


@dataclass
class TocEntryFeature:
    """Элемент встроенного оглавления Word (field TOC/PAGEREF)."""

    paragraph_index: int | None = None  # индекс p внутри body, если удалось определить
    raw_text: str = ""  # исходный текст строки оглавления
    title: str | None = None  # название пункта без номера страницы
    page: int | None = None  # номер страницы
    has_toc_field: bool = False  # содержит ли строка поле TOC/PAGEREF
    has_hyperlink: bool = False  # есть ли hyperlink-якорь
    parse_ok: bool = False  # успешно ли выделены title/page


@dataclass
class RichDocumentStructure:
    """Нормализованные признаки для строгих проверок оформления."""

    source_file: str  # путь к исходному DOCX
    language_hint: str | None = None  # язык документа (ru, en, mixed)
    sections_detected: list[str] = field(default_factory=list)  # какие секции обнаружены

    pages_settings: list[SectionPageSettingsFeature] = field(default_factory=list)  # поля, размеры листа
    footer_features: list[FooterFeature] = field(default_factory=list)  # нумерация страниц

    paragraph_features: list[ParagraphFeature] = field(default_factory=list)  # все абзацы
    table_features: list[TableFeature] = field(default_factory=list)  # все таблицы
    figure_caption_features: list[FigureCaptionFeature] = field(default_factory=list)  # подписи под рисунки
    formula_features: list[FormulaFeature] = field(default_factory=list)  # формулы/уравнения
    links_features: list[LinkFeature] = field(default_factory=list)  # ссылки на источники, таблицы, рисунки
    notes_features: list[NoteFeature] = field(default_factory=list)  # примечания
    footnote_features: list[FootnoteFeature] = field(default_factory=list)  # сноски
    toc_entries: list[TocEntryFeature] = field(default_factory=list)  # встроенное оглавление Word
