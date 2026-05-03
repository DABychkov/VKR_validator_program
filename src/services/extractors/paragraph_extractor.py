"""Извлечение признаков абзацев и run-ов.

Текущий файл — скелет. Реализацию добавляем поэтапно.
"""

from __future__ import annotations

from docx import Document

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


def extract_paragraph_features(doc: Document) -> list[ParagraphFeature]:
    """Возвращает признаки абзацев документа в исходном порядке.

    Этап 1 (минимум):
    - text
    - alignment
    - first_line_indent_mm
    - runs_features (font_name/font_size/bold/italic)

    TODO:
    - Добавить section_hint через внешний маппинг секций.
    - Добавить ratio-метрики (bold_ratio/italic_ratio).
    """
    paragraph_features: list[ParagraphFeature] = []

    for block_index, paragraph in enumerate(doc.paragraphs):
        paragraph_runs_features: list[RunFeature] = []

        for run in paragraph.runs:
            paragraph_runs_features.append(extract_run_feature(run))

        paragraph_format = paragraph.paragraph_format
        paragraph_features.append(
            ParagraphFeature(
                block_index=block_index,
                text=paragraph.text,
                style_name=safe_style_name(paragraph),
                alignment=resolve_paragraph_alignment(paragraph),
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
