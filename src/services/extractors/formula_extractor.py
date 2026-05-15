"""Извлечение признаков формул/уравнений.
Реализация опирается на OMML XML (m:oMath / m:oMathPara) и
текстовые эвристики (номер формулы, "где", пустые строки)
"""

from __future__ import annotations

import re

from docx import Document
from lxml import etree

from ...models.rich_document_structure import FormulaFeature
from .common import clean_text, resolve_paragraph_alignment


_FORMULA_NUMBER_RE = re.compile(
    r"\(((?:\d+(?:\.\d+)*)|(?:[A-Za-zА-Яа-я]\.\d+(?:\.\d+)*))\)\s*$"
)
_WHERE_MARKER_RE = re.compile(r"^\s*(где|where)\b", re.IGNORECASE)
_WHERE_RE = re.compile(r"^\s*(где|where)\b(?!\s*:)", re.IGNORECASE)


def _formula_number_pattern(number_token: str | None) -> str | None:
    if not number_token:
        return None
    if re.match(r"^[A-Za-zА-Яа-я]\.\d+$", number_token):
        return "formula_number_appendix"
    if re.match(r"^\d+\.\d+$", number_token):
        return "formula_number_sectional"
    if re.match(r"^\d+$", number_token):
        return "formula_number_global"
    return "formula_number_unknown"


def _has_omml(paragraph: object) -> bool:
    p = paragraph._p
    return bool(
        p.findall(".//m:oMath", p.nsmap) or p.findall(".//m:oMathPara", p.nsmap)
    )


def _extract_omml_xml(paragraph: object) -> str | None:
    p = paragraph._p
    nodes = p.findall(".//m:oMathPara", p.nsmap) or p.findall(".//m:oMath", p.nsmap)
    if not nodes:
        return None
    return etree.tostring(nodes[0], encoding="unicode")


def _display_formula_text(text: str, omml_exists: bool) -> str:
    if not omml_exists:
        return text

    stripped = text.strip()
    if stripped == "":
        return "[OMML_FORMULA]"
    if _FORMULA_NUMBER_RE.fullmatch(stripped):
        return "[OMML_FORMULA_WITH_NUMBER]"
    return text


def _looks_like_formula_text(text: str) -> bool:
    if not text:
        return False

    lowered = text.lower()
    if any(token in lowered for token in ("http", "url", "удк", "vol.", "doi", "isbn")):
        return False

    if "=" in text:
        return True

    operator_hits = sum(int(op in text) for op in ["+", "-", "*", "/", "<", ">", "×", ":"])
    has_digits = any(ch.isdigit() for ch in text)
    words_count = len([token for token in re.split(r"\s+", text) if token])

    # Строгая эвристика: формула обычно компактна и операторная.
    if operator_hits >= 2 and has_digits and words_count <= 6:
        return True

    # Нумерованную формулу считаем только если в строке есть явные математические операторы.
    if _FORMULA_NUMBER_RE.search(text) and operator_hits >= 1 and words_count <= 8:
        return True

    return False


def _number_alignment_right(paragraph: object, formula_number: str | None) -> bool | None:
    if formula_number is None:
        return None

    alignment = resolve_paragraph_alignment(paragraph, default_left=False)
    if alignment == "right":
        return True

    p = paragraph._p
    for tab in p.findall(".//w:tab", p.nsmap):
        val = (tab.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") or "").lower()
        if val == "right":
            return True

    # Если формула центрирована, но номер есть в конце строки, считаем это допустимым правым номером.
    if alignment in {"center", "unknown"} and _FORMULA_NUMBER_RE.search(clean_text(paragraph.text)):
        return True
    return False


def extract_formula_features(doc: Document) -> list[FormulaFeature]:
    """Возвращает признаки формул: text/regex признаки (номер, где, пустые строки) и
    опционально OMML XML для точной диагностики
    """
    features: list[FormulaFeature] = []
    paragraphs = list(doc.paragraphs)

    for paragraph_index, paragraph in enumerate(paragraphs):
        text = clean_text(paragraph.text)
        omml_exists = _has_omml(paragraph)

        if not omml_exists: #and not _looks_like_formula_text(text):
            continue

        number_match = _FORMULA_NUMBER_RE.search(text)
        number = number_match.group(1) if number_match else None
        number_pattern = _formula_number_pattern(number)

        prev_text = clean_text(paragraphs[paragraph_index - 1].text) if paragraph_index > 0 else ""
        next_text = clean_text(paragraphs[paragraph_index + 1].text) if paragraph_index + 1 < len(paragraphs) else ""
        has_where_marker = bool(next_text and _WHERE_MARKER_RE.match(next_text))
        has_where = bool(next_text and _WHERE_RE.match(next_text))

        features.append(
            FormulaFeature(
                paragraph_index=paragraph_index,
                formula_text=_display_formula_text(text, omml_exists),
                alignment=resolve_paragraph_alignment(paragraph),
                number=number,
                number_pattern=number_pattern,
                number_alignment_right=_number_alignment_right(paragraph, number),
                has_blank_line_before=(paragraph_index > 0 and prev_text == ""),
                has_blank_line_after=(next_text == ""),
                has_where_marker=has_where_marker,
                has_explanation_where=has_where,
                explanation_sequence_score=1.0 if has_where else None,
                omml_xml=_extract_omml_xml(paragraph),
            )
        )

    return features
