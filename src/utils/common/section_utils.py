"""Общие функции поиска и проверки секций документа."""

from typing import Any, Callable, Literal

from ...models.validation_result import Severity, ValidationResult


MatchMode = Literal["contains", "startswith", "equals"]


def find_section_text_by_keywords(
    sections: dict[str, str],
    keywords: tuple[str, ...] | list[str],
    match_mode: MatchMode = "contains",
) -> str | None:
    """Возвращает текст первой секции, имя которой совпадает с ключевыми словами."""
    for section_name, section_text in sections.items():
        name_upper = section_name.upper().strip()
        for keyword in keywords:
            keyword_upper = keyword.upper().strip()
            if _matches(name_upper, keyword_upper, match_mode):
                return section_text
    return None


def get_non_empty_lines(section_text: str, strip: bool = True) -> list[str]:
    """Возвращает непустые строки секции с опциональным strip()."""
    if strip:
        return [line.strip() for line in section_text.split("\n") if line.strip()]
    return [line for line in section_text.split("\n") if line.strip()]


def has_section_by_keywords(
    sections: dict[str, str],
    keywords: tuple[str, ...] | list[str],
    match_mode: MatchMode = "contains",
) -> bool:
    """Проверяет наличие секции по ключевым словам."""
    return find_section_text_by_keywords(sections, keywords, match_mode) is not None


def find_section_entries_by_keywords(
    sections: dict[str, str],
    keywords: tuple[str, ...] | list[str],
    match_mode: MatchMode = "contains",
) -> list[tuple[str, str]]:
    """Возвращает все секции (имя, текст), совпавшие по ключевым словам."""
    found: list[tuple[str, str]] = []
    for section_name, section_text in sections.items():
        name_upper = section_name.upper().strip()
        for keyword in keywords:
            keyword_upper = keyword.upper().strip()
            if _matches(name_upper, keyword_upper, match_mode):
                found.append((section_name, section_text))
                break
    return found


def _matches(name_upper: str, keyword_upper: str, match_mode: MatchMode) -> bool:
    if match_mode == "contains":
        return keyword_upper in name_upper
    if match_mode == "startswith":
        return name_upper.startswith(keyword_upper)
    return name_upper == keyword_upper


def find_first_by_key(
    items: list,
    key_fn: callable,
    search_value: str,
) -> Any | None:
    """Найти первый элемент где key_fn(item) содержит search_value."""
    for item in items:
        key_value = str(key_fn(item)).upper()
        if search_value.upper() in key_value:
            return item
    return None


def check_is_sequential(values: list[int]) -> bool:
    """Проверяет что числовые значения идут подряд (1,2,3 или 5,6,7)."""
    if len(values) < 2:
        return True

    expected = list(range(values[0], values[0] + len(values)))
    return values == expected


def validate_pairwise_order(
    val1: int | None,
    val2: int | None,
    error_msg: str,
    result: ValidationResult,
    severity: Severity = Severity.RECOMMENDATION,
) -> bool:
    """Проверяет что val1 < val2. Если нет - добавляет ошибку."""
    if val1 and val2 and val1 >= val2:
        result.add_error(severity, error_msg)
        return False
    return True


def add_errors_for_invalid_items(
    items: list[Any],
    predicate: Callable[[Any], bool],
    error_message_builder: Callable[[Any], str],
    result: ValidationResult,
    severity: Severity = Severity.CRITICAL,
) -> None:
    """Добавляет ошибки для элементов, не прошедших predicate."""
    for item in items:
        if not predicate(item):
            result.add_error(severity, error_message_builder(item))


def text_contains_any(
    text: str,
    needles: tuple[str, ...] | list[str],
    case_sensitive: bool = False,
) -> bool:
    """Проверяет, что text содержит хотя бы одну из строк needles."""
    if case_sensitive:
        return any(needle in text for needle in needles)

    text_lower = text.lower()
    return any(needle.lower() in text_lower for needle in needles)


def text_contains_all(
    text: str,
    needles: tuple[str, ...] | list[str],
    case_sensitive: bool = False,
) -> bool:
    """Проверяет, что text содержит все строки из needles."""
    if case_sensitive:
        return all(needle in text for needle in needles)

    text_lower = text.lower()
    return all(needle.lower() in text_lower for needle in needles)


def any_item_contains(
    items: list[str],
    needle: str,
    case_sensitive: bool = False,
) -> bool:
    """Проверяет, что хотя бы один элемент списка содержит подстроку needle."""
    if case_sensitive:
        return any(needle in item for item in items)

    needle_lower = needle.lower()
    return any(needle_lower in item.lower() for item in items)


def any_item_contains_all(
    items: list[str],
    needles: tuple[str, ...] | list[str],
    case_sensitive: bool = False,
) -> bool:
    """Проверяет, что существует элемент, содержащий все needles одновременно."""
    if case_sensitive:
        return any(all(needle in item for needle in needles) for item in items)

    needles_lower = [needle.lower() for needle in needles]
    return any(all(needle in item.lower() for needle in needles_lower) for item in items)


def find_missing_needles(
    items: list[str],
    required_needles: tuple[str, ...] | list[str],
    case_sensitive: bool = False,
) -> list[str]:
    """Возвращает список обязательных подстрок, которые не найдены ни в одном элементе items."""
    missing: list[str] = []
    for needle in required_needles:
        if not any_item_contains(items, needle, case_sensitive=case_sensitive):
            missing.append(needle)
    return missing


def find_first_index_contains(
    items: list[str],
    needle: str,
    case_sensitive: bool = False,
) -> int | None:
    """Возвращает индекс первого элемента, содержащего needle, или None."""
    if case_sensitive:
        for index, item in enumerate(items):
            if needle in item:
                return index
        return None

    needle_lower = needle.lower()
    for index, item in enumerate(items):
        if needle_lower in item.lower():
            return index
    return None
