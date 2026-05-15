"""Общие функции для extractor-модулей."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Length

from ...config.regex_patterns import RE_APPENDIX_HEADER, RE_DOT_LEADER, RE_TOC_ITEM_WITH_PAGE, RE_WIDE_SPACE_PAGE_SUFFIX
from ...models.rich_document_structure import AlignmentValue, RunFeature


def clean_text(text: str | None) -> str:
    """Нормализует строку: убирает лишние пробелы и переносы."""
    return " ".join((text or "").split())


def _normalize_upper(text: str | None) -> str:
    return clean_text(text).upper()


def is_probably_toc_entry(text: str | None) -> bool:
    """Эвристика: строка похожа на пункт оглавления с номером страницы."""
    value = clean_text(text)
    if not value:
        return False
    if RE_TOC_ITEM_WITH_PAGE.match(value):
        return True
    if RE_DOT_LEADER.search(value):
        return True
    if RE_WIDE_SPACE_PAGE_SUFFIX.search(value):
        return True
    return False


def is_appendix_heading_paragraph(text: str | None) -> bool:
    """Проверяет, что строка является заголовком приложения, а не пунктом оглавления."""
    value = clean_text(text)
    if not value:
        return False
    if is_probably_toc_entry(value):
        return False
    return bool(RE_APPENDIX_HEADER.match(value))


def is_section_heading_paragraph(text: str | None, marker: str) -> bool:
    """Проверяет, что строка является заголовком секции (с отсевом TOC-строк)."""
    normalized = _normalize_upper(text)
    normalized_marker = clean_text(marker).upper()
    if not normalized or not normalized_marker:
        return False
    if is_probably_toc_entry(normalized):
        return False
    return normalized == normalized_marker or normalized.startswith(f"{normalized_marker} ")


def find_first_intro_heading_index(paragraphs: list[object]) -> int | None:
    """Индекс первого реального заголовка «ВВЕДЕНИЕ» (не из оглавления)."""
    for index, paragraph in enumerate(paragraphs):
        if is_section_heading_paragraph(getattr(paragraph, "text", ""), "ВВЕДЕНИЕ"):
            return index
    return None


def alignment_to_value(alignment: WD_ALIGN_PARAGRAPH | int | None) -> AlignmentValue:
    """Нормализует выравнивание Word в наш enum-строковый формат."""
    if alignment is None:
        return "unknown"

    mapping: dict[int, AlignmentValue] = {
        int(WD_ALIGN_PARAGRAPH.LEFT): "left",
        int(WD_ALIGN_PARAGRAPH.CENTER): "center",
        int(WD_ALIGN_PARAGRAPH.RIGHT): "right",
        int(WD_ALIGN_PARAGRAPH.JUSTIFY): "justify",
        int(WD_ALIGN_PARAGRAPH.DISTRIBUTE): "distribute",
    }
    return mapping.get(int(alignment), "unknown")


def to_mm(value: Length | None) -> float | None:
    """Переводит длину из внутренних единиц Word в миллиметры."""
    if value is None:
        return None
    return float(value.mm)


def to_pt(value: Length | None) -> float | None:
    """Переводит длину из внутренних единиц Word в пункты (pt)."""
    if value is None:
        return None
    return float(value.pt)


def safe_style_name(run_or_paragraph: object) -> str | None:
    """Возвращает имя стиля, если оно задано на объекте."""
    style = getattr(run_or_paragraph, "style", None)
    if style is None:
        return None
    return getattr(style, "name", None)


def run_color_rgb(run: object) -> str | None:
    """Возвращает RGB-цвет run, если он задан явно."""
    font = getattr(run, "font", None)
    if font is None or font.color is None or font.color.rgb is None:
        return None
    return str(font.color.rgb)


def _font_name_from_rfonts(rfonts: object | None) -> str | None:
    """Читает имя шрифта из w:rFonts с приоритетом ascii/hAnsi."""
    if rfonts is None:
        return None

    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        value = rfonts.get(qn(attr))
        if value:
            return value
    return None


def _font_name_from_rpr(rpr: object | None) -> str | None:
    """Читает имя шрифта из w:rPr/w:rFonts."""
    if rpr is None:
        return None
    return _font_name_from_rfonts(rpr.find(qn("w:rFonts")))


def _twips_to_mm(value: str | None) -> float | None:
    """Конвертирует twips-значение в мм."""
    if value is None:
        return None
    try:
        twips = int(value)
    except (TypeError, ValueError):
        return None
    return float(twips * 25.4 / 1440.0)


def _first_line_indent_mm_from_ppr(ppr: object | None) -> float | None:
    """Читает first-line indent из w:pPr/w:ind (twips)."""
    if ppr is None:
        return None

    ind = ppr.find(qn("w:ind"))
    if ind is None:
        return None

    first_line = _twips_to_mm(ind.get(qn("w:firstLine")))
    if first_line is not None:
        return first_line

    # Hanging indent фактически означает отрицательный first-line.
    hanging = _twips_to_mm(ind.get(qn("w:hanging")))
    if hanging is not None:
        return -hanging
    return None


def _line_spacing_from_ppr(ppr: object | None) -> float | None:
    """Читает межстрочный интервал из w:pPr/w:spacing."""
    if ppr is None:
        return None

    spacing = ppr.find(qn("w:spacing"))
    if spacing is None:
        return None

    line_raw = spacing.get(qn("w:line"))
    if line_raw is None:
        return None

    try:
        line_value = int(line_raw)
    except (TypeError, ValueError):
        return None

    line_rule = (spacing.get(qn("w:lineRule")) or "auto").lower()
    # lineRule=auto: значение в 1/240 строки (360 => 1.5).
    if line_rule == "auto":
        return float(line_value / 240.0)

    # atLeast/exact: значение в twips, конвертируем в "pt-эквивалент",
    # чтобы сохранить сигнал вместо потери данных.
    return float(line_value / 20.0)


def resolve_paragraph_first_line_indent_mm(paragraph: object) -> float | None:
    """Определяет effective first-line indent: direct -> style chain -> docDefaults."""
    paragraph_format = getattr(paragraph, "paragraph_format", None)
    if paragraph_format is not None:
        direct_indent = getattr(paragraph_format, "first_line_indent", None)
        if direct_indent is not None:
            return to_mm(direct_indent)

    p = getattr(paragraph, "_p", None)
    if p is not None:
        from_xml = _first_line_indent_mm_from_ppr(p.find(qn("w:pPr")))
        if from_xml is not None:
            return from_xml

    style = getattr(paragraph, "style", None)
    checked_styles = 0
    while style is not None and checked_styles < 20:
        style_element = getattr(style, "element", None)
        if style_element is not None:
            style_indent = _first_line_indent_mm_from_ppr(style_element.find(qn("w:pPr")))
            if style_indent is not None:
                return style_indent
        style = getattr(style, "base_style", None)
        checked_styles += 1

    part = getattr(paragraph, "part", None)
    styles = getattr(part, "styles", None) if part is not None else None
    styles_element = getattr(styles, "element", None) if styles is not None else None
    if styles_element is not None:
        doc_defaults = styles_element.find(qn("w:docDefaults"))
        if doc_defaults is not None:
            ppr_default = doc_defaults.find(qn("w:pPrDefault"))
            if ppr_default is not None:
                default_indent = _first_line_indent_mm_from_ppr(ppr_default.find(qn("w:pPr")))
                if default_indent is not None:
                    return default_indent

    return None


def resolve_paragraph_line_spacing(paragraph: object) -> float | None:
    """Определяет effective line spacing: direct -> xml -> style chain -> docDefaults."""
    paragraph_format = getattr(paragraph, "paragraph_format", None)
    if paragraph_format is not None:
        direct_spacing = getattr(paragraph_format, "line_spacing", None)
        if direct_spacing is not None:
            if isinstance(direct_spacing, (int, float)):
                return float(direct_spacing)
            return float(direct_spacing.pt)

    p = getattr(paragraph, "_p", None)
    if p is not None:
        from_xml = _line_spacing_from_ppr(p.find(qn("w:pPr")))
        if from_xml is not None:
            return from_xml

    style = getattr(paragraph, "style", None)
    checked_styles = 0
    while style is not None and checked_styles < 20:
        style_p_format = getattr(style, "paragraph_format", None)
        if style_p_format is not None:
            style_spacing = getattr(style_p_format, "line_spacing", None)
            if style_spacing is not None:
                if isinstance(style_spacing, (int, float)):
                    return float(style_spacing)
                return float(style_spacing.pt)

        style_element = getattr(style, "element", None)
        if style_element is not None:
            style_spacing_xml = _line_spacing_from_ppr(style_element.find(qn("w:pPr")))
            if style_spacing_xml is not None:
                return style_spacing_xml

        style = getattr(style, "base_style", None)
        checked_styles += 1

    part = getattr(paragraph, "part", None)
    styles = getattr(part, "styles", None) if part is not None else None
    styles_element = getattr(styles, "element", None) if styles is not None else None
    if styles_element is not None:
        doc_defaults = styles_element.find(qn("w:docDefaults"))
        if doc_defaults is not None:
            ppr_default = doc_defaults.find(qn("w:pPrDefault"))
            if ppr_default is not None:
                default_spacing = _line_spacing_from_ppr(ppr_default.find(qn("w:pPr")))
                if default_spacing is not None:
                    return default_spacing

    return None


def _resolve_run_font_name(run: object) -> str | None:
    """Определяет effective font name: direct/style chain/docDefaults."""
    direct_font_name = getattr(getattr(run, "font", None), "name", None)
    if direct_font_name:
        return direct_font_name

    run_element = getattr(run, "_element", None)
    if run_element is not None:
        run_xml_font = _font_name_from_rpr(run_element.find(qn("w:rPr")))
        if run_xml_font:
            return run_xml_font

    run_style = getattr(run, "style", None)
    if run_style is not None:
        run_style_font_name = getattr(getattr(run_style, "font", None), "name", None)
        if run_style_font_name:
            return run_style_font_name
        run_style_element = getattr(run_style, "element", None)
        if run_style_element is not None:
            run_style_xml_font = _font_name_from_rpr(run_style_element.find(qn("w:rPr")))
            if run_style_xml_font:
                return run_style_xml_font

    paragraph = getattr(run, "_parent", None)
    paragraph_style = getattr(paragraph, "style", None)
    checked_styles = 0
    while paragraph_style is not None and checked_styles < 20:
        paragraph_style_font_name = getattr(getattr(paragraph_style, "font", None), "name", None)
        if paragraph_style_font_name:
            return paragraph_style_font_name
        paragraph_style_element = getattr(paragraph_style, "element", None)
        if paragraph_style_element is not None:
            paragraph_style_xml_font = _font_name_from_rpr(paragraph_style_element.find(qn("w:rPr")))
            if paragraph_style_xml_font:
                return paragraph_style_xml_font
        paragraph_style = getattr(paragraph_style, "base_style", None)
        checked_styles += 1

    part = getattr(run, "part", None)
    styles = getattr(part, "styles", None) if part is not None else None
    styles_element = getattr(styles, "element", None) if styles is not None else None
    if styles_element is not None:
        doc_defaults = styles_element.find(qn("w:docDefaults"))
        if doc_defaults is not None:
            rpr_default = doc_defaults.find(qn("w:rPrDefault"))
            if rpr_default is not None:
                default_rpr = rpr_default.find(qn("w:rPr"))
                default_font_name = _font_name_from_rpr(default_rpr)
                if default_font_name:
                    return default_font_name

    return None


def _resolve_run_font_size_pt(run: object) -> float | None:
    """Определяет effective font size c учетом run/символьного стиля/стиля абзаца."""
    direct_size = getattr(getattr(run, "font", None), "size", None)
    if direct_size is not None:
        return float(direct_size.pt)

    run_style = getattr(run, "style", None)
    if run_style is not None:
        run_style_size = getattr(getattr(run_style, "font", None), "size", None)
        if run_style_size is not None:
            return float(run_style_size.pt)

    paragraph = getattr(run, "_parent", None)
    paragraph_style = getattr(paragraph, "style", None)
    checked_styles = 0
    while paragraph_style is not None and checked_styles < 10:
        paragraph_style_size = getattr(getattr(paragraph_style, "font", None), "size", None)
        if paragraph_style_size is not None:
            return float(paragraph_style_size.pt)
        paragraph_style = getattr(paragraph_style, "base_style", None)
        checked_styles += 1

    return None


def extract_run_feature(run: object) -> RunFeature:
    """Нормализует python-docx run в RunFeature."""
    return RunFeature(
        text=run.text,
        font_name=_resolve_run_font_name(run),
        font_size_pt=_resolve_run_font_size_pt(run),
        bold=run.bold,
        italic=run.italic,
        underline=bool(run.underline) if run.underline is not None else None,
        all_caps=run.font.all_caps,
        color_rgb=run_color_rgb(run),
        style_name=safe_style_name(run),
    )


def _alignment_from_xml(paragraph: object) -> AlignmentValue | None:
    """Читает w:pPr/w:jc напрямую из XML абзаца, если доступно."""
    p = getattr(paragraph, "_p", None)
    if p is None:
        return None

    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        return None

    jc = ppr.find(qn("w:jc"))
    if jc is None:
        return None

    val = (jc.get(qn("w:val")) or "").lower()
    xml_map: dict[str, AlignmentValue] = {
        "left": "left",
        "center": "center",
        "right": "right",
        "both": "justify",
        "justify": "justify",
        "distribute": "distribute",
    }
    return xml_map.get(val)


def resolve_paragraph_alignment(paragraph: object, default_left: bool = True) -> AlignmentValue:
    """Определяет эффективное выравнивание абзаца с учетом наследования стиля."""
    direct_alignment = getattr(paragraph, "alignment", None)
    if direct_alignment is not None:
        return alignment_to_value(direct_alignment)

    paragraph_format = getattr(paragraph, "paragraph_format", None)
    if paragraph_format is not None:
        paragraph_format_alignment = getattr(paragraph_format, "alignment", None)
        if paragraph_format_alignment is not None:
            return alignment_to_value(paragraph_format_alignment)

    style = getattr(paragraph, "style", None)
    checked_styles = 0
    while style is not None and checked_styles < 10:
        style_p_format = getattr(style, "paragraph_format", None)
        if style_p_format is not None:
            style_alignment = getattr(style_p_format, "alignment", None)
            if style_alignment is not None:
                return alignment_to_value(style_alignment)
        style = getattr(style, "base_style", None)
        checked_styles += 1

    xml_alignment = _alignment_from_xml(paragraph)
    if xml_alignment is not None:
        return xml_alignment

    return "left" if default_left else "unknown"
