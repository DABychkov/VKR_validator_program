"""Проверки для правил FOOT-* (сноски)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _paragraph_index(feature: Any) -> int:
    raw_value = getattr(feature, "paragraph_index", None)
    if raw_value is None:
        return -1
    return int(raw_value)


def _as_list(features: Iterable[Any]) -> list[Any]:
    return list(features)


def _all_paragraph_indexes(features: list[Any]) -> list[int]:
    return [_paragraph_index(feature) for feature in features]


def _collect_indexes_if_any_flag_equals(
    features: list[Any],
    *,
    attr_name: str,
    expected_value: bool | None,
) -> list[int]:
    if not features:
        return []

    return [
        _paragraph_index(feature)
        for feature in features
        if getattr(feature, attr_name, None) is expected_value
    ]


def has_any_footnotes(footnote_features: Iterable[Any]) -> bool:
    """Есть ли в документе хоть один маркер сноски."""
    for _ in footnote_features:
        return True
    return False


def check_footnote_markers_resolved(footnote_features: Iterable[Any]) -> list[int]:
    """маркеры сносок должны резолвиться в footnotes.xml.

    Возвращает paragraph_index маркеров, у которых resolved_in_footnotes_part == False.
    Значение None трактуется как "неизвестно" и в эту проверку не включается.

    Важно: тип маркера (xml_reference/asterisk/custom) не важен,
    используется уже рассчитанный флаг resolved_in_footnotes_part.
    """
    invalid_paragraph_indexes: list[int] = []

    for footnote in footnote_features:
        resolved = getattr(footnote, "resolved_in_footnotes_part", None)
        if resolved is False:
            invalid_paragraph_indexes.append(_paragraph_index(footnote))

    return invalid_paragraph_indexes


def check_footnote_markers_resolution_unknown(footnote_features: Iterable[Any]) -> list[int]:
    """Вспомогательная проверка: статус резолва маркера неизвестен (None)."""
    unknown_paragraph_indexes: list[int] = []

    for footnote in footnote_features:
        resolved = getattr(footnote, "resolved_in_footnotes_part", None)
        if resolved is None:
            unknown_paragraph_indexes.append(_paragraph_index(footnote))

    return unknown_paragraph_indexes


def check_footnote_separator_present(footnote_features: Iterable[Any]) -> list[int]:
    """при наличии сносок должна быть обнаружена разделительная линия.

    Возвращает paragraph_index маркеров, у которых has_separator_line == False.
    Значение None трактуется как "неизвестно" и в эту проверку не включается.
    """
    features = _as_list(footnote_features)
    return _collect_indexes_if_any_flag_equals(
        features,
        attr_name="has_separator_line",
        expected_value=False,
    )


def check_footnote_separator_short_left(footnote_features: Iterable[Any]) -> list[int]:
    """разделительная линия сносок должна быть короткой слева (эвристика).

    Возвращает paragraph_index маркеров,
    у которых separator_short_left_heuristic == False.
    Значение None трактуется как "неизвестно" и в эту проверку не включается.
    """
    features = _as_list(footnote_features)
    return _collect_indexes_if_any_flag_equals(
        features,
        attr_name="separator_short_left_heuristic",
        expected_value=False,
    )


def check_footnote_separator_short_left_unknown(footnote_features: Iterable[Any]) -> list[int]:
    """Вспомогательная проверка: short-left эвристика неизвестна (None)."""
    features = _as_list(footnote_features)
    return _collect_indexes_if_any_flag_equals(
        features,
        attr_name="separator_short_left_heuristic",
        expected_value=None,
    )


def check_footnote_separator_unknown(footnote_features: Iterable[Any]) -> list[int]:
    """Вспомогательная проверка: признак разделителя сносок неизвестен (None)."""
    features = _as_list(footnote_features)
    return _collect_indexes_if_any_flag_equals(
        features,
        attr_name="has_separator_line",
        expected_value=None,
    )
