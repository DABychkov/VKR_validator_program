"""Проверки для правил LINK-* (ссылки)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _is_resolved(link: Any) -> bool:
    if getattr(link, "resolved_in_target_list", None) is False:
        return False
    if getattr(link, "resolved_with_object", None) is False:
        return False
    return True

def check_link_before_target(
    links_features: Iterable[Any],
    link_type: str,
) -> list[int]:
    """Возвращает paragraph_index ссылок, которые идут не до своей цели.
    Для проверки порядка учитываются только ссылки, уже резолвленные на цель.
    """

    if link_type not in {"figure", "table"}:
        return []

    invalid_link_paragraph_indexes: list[int] = []
    first_link_by_target: dict[str, tuple[int, Any]] = {}
    for link in links_features:
        if getattr(link, "link_type", None) != link_type:
            continue

        paragraph_index_raw = getattr(link, "paragraph_index", None)
        if paragraph_index_raw is None:
            invalid_link_paragraph_indexes.append(-1)
            continue
        paragraph_index = int(paragraph_index_raw)

        target_number = getattr(link, "target_number", None)
        if not target_number:
            invalid_link_paragraph_indexes.append(paragraph_index)
            continue

        current = first_link_by_target.get(target_number)
        if current is None or paragraph_index < current[0]:
            first_link_by_target[target_number] = (paragraph_index, link)

    for paragraph_index, link in first_link_by_target.values():
        if not _is_resolved(link):
            continue

        position = getattr(link, "relative_position_to_target", None) or "unknown"
        if position == "before":
            continue

        invalid_link_paragraph_indexes.append(paragraph_index)

    return invalid_link_paragraph_indexes


def check_figure_link_before_caption(
    links_features: Iterable[Any],
    figure_caption_features: Iterable[Any],
) -> list[int]:
    """Совместимый wrapper: проверка ссылок на рисунки по relative_position_to_target."""
    _ = figure_caption_features
    return check_link_before_target(links_features, link_type="figure")


def check_table_link_before_table(links_features: Iterable[Any], table_features: Iterable[Any]) -> list[int]:
    """Совместимый wrapper: проверка ссылок на таблицы по relative_position_to_target."""
    _ = table_features
    return check_link_before_target(links_features, link_type="table")


def check_links_resolve_to_existing_targets(links_features: Iterable[Any]) -> list[int]:
    """LINK-003: ссылки на источники/рисунки/таблицы/формулы должны резолвиться в существующие цели."""
    invalid_link_paragraph_indexes: list[int] = []
    supported_types = {"source", "figure", "table", "formula"}

    for link in links_features:
        link_type = getattr(link, "link_type", None)
        if link_type not in supported_types:
            continue

        paragraph_index = getattr(link, "paragraph_index", None)
        if paragraph_index is None:
            invalid_link_paragraph_indexes.append(-1)
            continue
        paragraph_index = int(paragraph_index)

        if not _is_resolved(link):
            invalid_link_paragraph_indexes.append(paragraph_index)

    return invalid_link_paragraph_indexes