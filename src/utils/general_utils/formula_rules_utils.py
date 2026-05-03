"""Проверки для правил FORMULA-* (формулы)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def has_formula_number(formula: Any) -> bool:
    """Есть ли у формулы распознанный номер."""
    return bool(str(getattr(formula, "number", "") or "").strip())


def check_formula_line_and_spacing(formula_features: Iterable[Any]) -> list[int]:
    """Возвращает paragraph_index формул с нарушением расположения/отбивок."""
    invalid_indexes: list[int] = []
    for formula in formula_features:
        paragraph_index = int(getattr(formula, "paragraph_index", -1))
        has_blank_line_before = bool(getattr(formula, "has_blank_line_before", False))
        has_blank_line_after = bool(getattr(formula, "has_blank_line_after", False))

        if has_blank_line_before and has_blank_line_after:
            continue

        invalid_indexes.append(paragraph_index)

    return invalid_indexes


def check_formula_where_format(formula_features: Iterable[Any]) -> list[int]:
    """Возвращает paragraph_index формул без корректного пояснения с "где"."""
    invalid_indexes: list[int] = []
    for formula in formula_features:
        paragraph_index = int(getattr(formula, "paragraph_index", -1))
        has_explanation_where = bool(getattr(formula, "has_explanation_where", False))

        if has_explanation_where:
            continue

        invalid_indexes.append(paragraph_index)

    return invalid_indexes


def check_formula_number_right(formula_features: Iterable[Any]) -> list[int]:
    """номер формулы (при наличии) должен быть справа."""
    invalid_indexes: list[int] = []
    for formula in formula_features:
        if not has_formula_number(formula):
            continue

        paragraph_index = int(getattr(formula, "paragraph_index", -1))
        number_alignment_right = bool(getattr(formula, "number_alignment_right", False))

        if number_alignment_right:
            continue

        invalid_indexes.append(paragraph_index)

    return invalid_indexes


def check_formula_number_pattern(formula_features: Iterable[Any]) -> list[int]:
    """номер формулы (при наличии) должен соответствовать допустимому шаблону."""
    invalid_indexes: list[int] = []
    allowed_patterns = {
        "formula_number_global",
        "formula_number_sectional",
        "formula_number_appendix",
    }

    for formula in formula_features:
        if not has_formula_number(formula):
            continue

        paragraph_index = int(getattr(formula, "paragraph_index", -1))
        number_pattern = getattr(formula, "number_pattern", None)

        if number_pattern in allowed_patterns:
            continue

        invalid_indexes.append(paragraph_index)

    return invalid_indexes


def check_formula_centered(formula_features: Iterable[Any]) -> list[int]:
    """формула должна быть выровнена по центру."""
    invalid_indexes: list[int] = []
    for formula in formula_features:
        paragraph_index = int(getattr(formula, "paragraph_index", -1))
        alignment = getattr(formula, "alignment", "unknown")

        if alignment == "center":
            continue

        invalid_indexes.append(paragraph_index)

    return invalid_indexes