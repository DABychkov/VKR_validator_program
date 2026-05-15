"""Извлечение признаков абзацев и run-ов.
"""

from __future__ import annotations

from docx import Document

from ...config.regex_patterns import RE_MAIN_SECTION_START_PATTERNS
from ...config.validation_constants import (
    PARSER_SECTION_KEYWORDS,
    SECTION_APPENDIX,
    SECTION_INTRODUCTION,
    SECTION_MAIN,
    SECTION_TITLE_PAGE,
)
from ...models.rich_document_structure import ParagraphFeature, RunFeature
from .common import (
    extract_run_feature,
    resolve_paragraph_alignment,
    resolve_paragraph_first_line_indent_mm,
    resolve_paragraph_line_spacing,
    safe_style_name,
    to_mm,
    to_pt,
)
def _calc_ratio(runs: list[RunFeature], flag_name: str) -> float | None:
    weighted_total = 0
    weighted_true = 0
    fallback_total = 0
    fallback_true = 0

    for run_feature in runs:
        text_weight = len(run_feature.text) if run_feature.text else 0
        flag_value = getattr(run_feature, flag_name)

        if flag_value is None:
            continue

        if text_weight > 0:
            weighted_total += text_weight
            if flag_value:
                weighted_true += text_weight

        fallback_total += 1
        if flag_value:
            fallback_true += 1

    if weighted_total > 0:
        return weighted_true / weighted_total
    if fallback_total > 0:
        return fallback_true / fallback_total
    return None


def _normalize_header_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().upper().split())


def _normalize_style_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _is_heading_level_one(style_name: str | None) -> bool:
    normalized = _normalize_style_name(style_name)
    return normalized in {"heading 1", "заголовок 1"}


def _resolve_section_hint(
    text: str | None,
    alignment: str,
    current_section: str | None,
    style_name: str | None,
) -> str | None:
    if alignment != "center":
        return current_section

    raw_text = str(text or "").strip()
    normalized = _normalize_header_text(raw_text)
    if not normalized:
        return current_section

    for keyword in PARSER_SECTION_KEYWORDS:
        if keyword == SECTION_APPENDIX:
            if normalized.startswith(keyword):
                return keyword
            continue
        if normalized == keyword:
            return keyword

    if current_section == SECTION_INTRODUCTION:
        if _is_heading_level_one(style_name):
            return SECTION_MAIN
        if any(pattern.match(raw_text) for pattern in RE_MAIN_SECTION_START_PATTERNS):
            return SECTION_MAIN

    return current_section


def extract_paragraph_features(doc: Document) -> list[ParagraphFeature]:
    """Возвращает признаки абзацев документа в исходном порядке.
    """
    paragraph_features: list[ParagraphFeature] = []

    current_section: str | None = SECTION_TITLE_PAGE

    for block_index, paragraph in enumerate(doc.paragraphs):
        paragraph_runs_features: list[RunFeature] = []

        for run in paragraph.runs:
            paragraph_runs_features.append(extract_run_feature(run))

        paragraph_format = paragraph.paragraph_format
        alignment = resolve_paragraph_alignment(paragraph)
        style_name = safe_style_name(paragraph)
        current_section = _resolve_section_hint(paragraph.text, alignment, current_section, style_name)
        paragraph_features.append(
            ParagraphFeature(
                block_index=block_index,
                text=paragraph.text,
                style_name=style_name,
                alignment=alignment,
                section_hint=current_section,
                first_line_indent_mm=resolve_paragraph_first_line_indent_mm(paragraph),
                left_indent_mm=to_mm(paragraph_format.left_indent),
                right_indent_mm=to_mm(paragraph_format.right_indent),
                line_spacing=resolve_paragraph_line_spacing(paragraph),
                space_before_pt=to_pt(paragraph_format.space_before),
                space_after_pt=to_pt(paragraph_format.space_after),
                bold_ratio=_calc_ratio(paragraph_runs_features, "bold"),
                italic_ratio=_calc_ratio(paragraph_runs_features, "italic"),
                has_page_break_before=bool(paragraph_format.page_break_before),
                runs_features=paragraph_runs_features,
            )
        )

    return paragraph_features
