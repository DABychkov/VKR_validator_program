"""Содержательные проверки для валидатора раздела "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"."""

from re import Pattern

from .common.regex_utils import extract_numbered_item_number, filter_pattern_matches


def check_numbering_sequence(list_items: list[str]) -> tuple[bool, int | None, int | None]:
    """Проверяет последовательность и возвращает (ok, expected, actual)."""
    expected = 1
    for item in list_items:
        actual = extract_numbered_item_number(item)
        if actual is None:
            continue
        if actual != expected:
            return False, expected, actual
        expected += 1

    return True, None, None


def check_initials_presence(
    list_items: list[str], initials_pattern: Pattern[str]
) -> bool:
    """Возвращает True, если в записях найдено хотя бы одно упоминание инициалов."""
    items_with_initials = filter_pattern_matches(list_items, initials_pattern)
    return bool(items_with_initials)
