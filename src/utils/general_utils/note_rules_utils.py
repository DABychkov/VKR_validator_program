"""Проверки для правил NOTE-* (примечания)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..common.rich_utils import first_alpha_char, get_paragraph_index


def _note_kind(note: Any) -> str:
    return str(getattr(note, "note_kind", "") or "")


def _is_unknown_note(note: Any) -> bool:
    return _note_kind(note) == "unknown"


def _is_note_keyword_kind(note: Any) -> bool:
    """применяем только к single/group_header."""
    return _note_kind(note) in {"single", "group_header"}


def _has_group_items_after(notes: list[Any], header_index: int) -> bool:
    for next_note in notes[header_index + 1 :]:
        kind = _note_kind(next_note)
        if kind == "unknown":
            continue
        return kind == "group_item"
    return False


def _normalize_spaces(text: str) -> str:
    return " ".join(str(text or "").split())


def _strip_number_prefix(text: str) -> str:
    """Убирает префикс вида "1 ", "1. ", "1) "."""
    normalized = _normalize_spaces(text)
    if not normalized:
        return ""

    pos = 0
    while pos < len(normalized) and normalized[pos].isdigit():
        pos += 1
    while pos < len(normalized) and normalized[pos] in {".", ")", ":", " ", "\t"}:
        pos += 1
    return normalized[pos:].strip()


def _note_keyword_is_capitalized(raw_text: str) -> bool | None:
    """Проверяет, что слово Примечание/Примечания начинается с прописной буквы.

    Возвращает:
    - True/False если ключевое слово найдено,
    - None если в начале строки нет слова-маркера примечания.
    """
    stripped = _strip_number_prefix(raw_text)
    lowered = stripped.lower()

    if lowered.startswith("примечания"):
        return stripped.startswith("П")
    if lowered.startswith("примечание"):
        return stripped.startswith("П")
    return None


def _extract_note_body(raw_text: str, note_kind: str | None = None) -> str:
    """Возвращает содержательную часть примечания после служебного префикса.

    Для group_item не удаляем слово "Примечание", если оно является частью текста.
    """
    text = _normalize_spaces(raw_text)
    if not text:
        return ""

    text = _strip_number_prefix(text)
    lowered = text.lower()

    if note_kind == "group_item":
        return text.strip()

    if lowered.startswith("примечания"):
        body = text[len("Примечания") :].lstrip(" :.-–—\t")
        return body.strip()

    if lowered.startswith("примечание"):
        body = text[len("Примечание") :].lstrip(" :.-–—\t")
        return body.strip()

    # Для group_item / numbered_single берем часть после номера.
    return text.strip()


def check_note_unrecognized_pattern(note_features: Iterable[Any]) -> list[int]:
    """примечание найдено, но не соответствует шаблону."""
    invalid_paragraph_indexes: set[int] = set()

    for note in note_features:
        kind = _note_kind(note)
        raw_text = _normalize_spaces(getattr(note, "raw_text", ""))
        text_wo_number = _strip_number_prefix(raw_text)
        lowered_wo_number = text_wo_number.lower()

        if kind == "unknown":
            invalid_paragraph_indexes.add(get_paragraph_index(note))
            continue

        if kind == "group_header":
            # Для header разрешаем только слово-маркер без произвольного текста.
            header_text = lowered_wo_number.rstrip(":").strip()
            if header_text not in {"примечание", "примечания"}:
                invalid_paragraph_indexes.add(get_paragraph_index(note))
            continue

        if kind == "single":
            # Одиночное примечание должно быть шаблона "Примечание - Текст".
            has_keyword = lowered_wo_number.startswith("примечание")
            has_dash_separator = getattr(note, "has_dash_separator", None) is True
            if not has_keyword or not has_dash_separator:
                invalid_paragraph_indexes.add(get_paragraph_index(note))
            continue

    return sorted(invalid_paragraph_indexes)


def check_note_placement_near_related_material(note_features: Iterable[Any]) -> list[int]:
    """примечание размещено рядом с рисунком/таблицей по rich-флагам."""
    invalid_paragraph_indexes: list[int] = []

    for note in note_features:
        if _is_unknown_note(note):
            continue

        near_figure = bool(getattr(note, "near_figure_caption", False))
        near_table = bool(getattr(note, "near_table_caption", False))

        if near_figure or near_table:
            continue

        invalid_paragraph_indexes.append(get_paragraph_index(note))

    return invalid_paragraph_indexes


def check_note_keyword_capitalized(note_features: Iterable[Any]) -> list[int]:
    """слово Примечание/Примечания начинается с прописной буквы."""
    invalid_paragraph_indexes: list[int] = []

    for note in note_features:
        if _is_unknown_note(note) or not _is_note_keyword_kind(note):
            continue

        decision = _note_keyword_is_capitalized(getattr(note, "raw_text", ""))
        if decision is None:
            continue
        if decision:
            continue

        invalid_paragraph_indexes.append(get_paragraph_index(note))

    return invalid_paragraph_indexes


def check_note_starts_with_capital(note_features: Iterable[Any]) -> list[int]:
    """текст примечания начинается с прописной буквы."""
    invalid_paragraph_indexes: list[int] = []

    for note in note_features:
        kind = _note_kind(note)
        if kind in {"unknown", "group_header"}:
            continue

        # Проверяем именно содержательную часть: после номера и/или префикса "Примечание".
        body = _extract_note_body(getattr(note, "raw_text", ""), note_kind=kind)
        first_alpha = first_alpha_char(body)

        if first_alpha is not None and first_alpha.isupper():
            continue

        invalid_paragraph_indexes.append(get_paragraph_index(note))

    return invalid_paragraph_indexes


def check_note_group_header_plural_for_multiple(note_features: Iterable[Any]) -> list[int]:
    """для нескольких примечаний заголовок должен быть "Примечания"."""
    notes = list(note_features)
    invalid_paragraph_indexes: list[int] = []

    for index, note in enumerate(notes):
        if _note_kind(note) != "group_header":
            continue

        if not _has_group_items_after(notes, index):
            continue

        raw_text = _normalize_spaces(getattr(note, "raw_text", "")).lower()
        if raw_text.startswith("примечания"):
            continue

        invalid_paragraph_indexes.append(get_paragraph_index(note))

    return invalid_paragraph_indexes


def check_note_dash_numbering_consistency(note_features: Iterable[Any]) -> list[int]:
    """тире и нумерация должны использоваться согласованно.

    Логика по ТЗ:
    - если есть тире, то у текущего примечания не должно быть item_number;
    - для одиночного примечания используется тире и нет нумерации;
    - для группы: заголовок без тире, а пункты группы с нумерацией.
    """
    notes = list(note_features)
    invalid_paragraph_indexes: set[int] = set()

    for index, note in enumerate(notes):
        kind = _note_kind(note)
        if kind == "unknown":
            continue

        has_dash_separator = getattr(note, "has_dash_separator", None)
        item_number = getattr(note, "item_number", None)

        if kind == "single":
            if has_dash_separator is not True or item_number is not None:
                invalid_paragraph_indexes.add(get_paragraph_index(note))
            continue

        if kind == "numbered_single":
            # По ГОСТ для одиночного примечания номер не используется.
            invalid_paragraph_indexes.add(get_paragraph_index(note))
            continue

        if kind == "group_header":
            if has_dash_separator is True or not _has_group_items_after(notes, index):
                invalid_paragraph_indexes.add(get_paragraph_index(note))
            continue

        if kind == "group_item":
            if item_number is None:
                invalid_paragraph_indexes.add(get_paragraph_index(note))
            if has_dash_separator is True:
                invalid_paragraph_indexes.add(get_paragraph_index(note))

    return sorted(invalid_paragraph_indexes)


def check_note_numbering_without_dot(note_features: Iterable[Any]) -> list[int]:
    """в нумерованных примечаниях после номера не ставится точка."""
    invalid_paragraph_indexes: list[int] = []

    for note in note_features:
        if _is_unknown_note(note):
            continue

        if getattr(note, "item_number", None) is None:
            continue

        if getattr(note, "has_dot_after_number", None) is True:
            invalid_paragraph_indexes.append(get_paragraph_index(note))

    return invalid_paragraph_indexes
