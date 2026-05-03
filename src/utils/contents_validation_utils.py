"""Содержательные проверки для валидатора раздела "СОДЕРЖАНИЕ"."""

import re

from ..config.regex_patterns import RE_DOT_LEADER, RE_TOC_ITEM_WITH_PAGE, RE_WIDE_SPACE_PAGE_SUFFIX
from .common.regex_utils import has_pattern_match


RE_LEADING_NUMBERING = re.compile(r"^\d+(?:\.\d+)*\.?\s*")


def _normalize_toc_title(title: str) -> str:
    """Нормализует название пункта оглавления для точного сравнения."""
    t = title.strip()
    t = RE_LEADING_NUMBERING.sub("", t)
    t = re.sub(r"\s+", " ", t)
    return t.upper()


def _find_page_by_exact_required_title(
    toc_items: list[dict[str, int | str]],
    required_title: str,
) -> int | None:
    required_normalized = _normalize_toc_title(required_title)
    for item in toc_items:
        if _normalize_toc_title(str(item["title"])) == required_normalized:
            return int(item["page"])
    return None


def extract_toc_items(lines: list[str]) -> list[dict[str, int | str]]:
    """Извлекает элементы содержания в формате title + page."""
    items: list[dict[str, int | str]] = []

    for line in lines:
        line_upper = line.upper()
        if line_upper == "СОДЕРЖАНИЕ":
            continue

        match = RE_TOC_ITEM_WITH_PAGE.match(line)
        if not match:
            continue

        title = match.group("title").strip()
        page_text = match.group("page").strip()

        if not title:
            continue

        try:
            page = int(page_text)
        except ValueError:
            continue

        items.append({"title": title, "title_upper": title.upper(), "page": page})

    return items


def extract_toc_items_with_invalid_lines(
    lines: list[str],
) -> tuple[list[dict[str, int | str]], list[str]]:
    """
    Возвращает распознанные элементы и проблемные строки содержания.

    Проблемной считаем строку с буквами (кроме заголовка "СОДЕРЖАНИЕ"),
    которую не удалось распарсить как пункт с номером страницы.
    """
    items: list[dict[str, int | str]] = []
    invalid_lines: list[str] = []

    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        if raw.upper() == "СОДЕРЖАНИЕ":
            continue

        has_letters = any(ch.isalpha() for ch in raw)
        match = RE_TOC_ITEM_WITH_PAGE.match(raw)

        if not match:
            if has_letters:
                invalid_lines.append(raw)
            continue

        title = match.group("title").strip()
        page_text = match.group("page").strip()

        if not title:
            if has_letters:
                invalid_lines.append(raw)
            continue

        try:
            page = int(page_text)
        except ValueError:
            invalid_lines.append(raw)
            continue

        items.append({"title": title, "title_upper": title.upper(), "page": page})

    return items, invalid_lines


def check_required_item_order(toc_items: list[dict[str, int | str]]) -> tuple[int | None, int | None, int | None]:
    """Возвращает страницы обязательных разделов для проверки порядка в валидаторе."""

    intro_page = _find_page_by_exact_required_title(toc_items, "ВВЕДЕНИЕ")
    conclusion_page = _find_page_by_exact_required_title(toc_items, "ЗАКЛЮЧЕНИЕ")
    sources_page = _find_page_by_exact_required_title(toc_items, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ")

    return intro_page, conclusion_page, sources_page

def check_required_items(
    toc_items: list[dict[str, int | str]],
    required_items: dict[str, str],
) -> list[str]:
    """Возвращает обязательные позиции, которые не найдены в содержании."""
    present = {_normalize_toc_title(str(item["title"])) for item in toc_items}
    missing: list[str] = []
    for required in required_items.keys():
        if _normalize_toc_title(required) not in present:
            missing.append(required)
    return missing


def check_page_numbers_are_positive(
    toc_items: list[dict[str, int | str]],
) -> list[dict[str, int | str]]:
    """Возвращает элементы с невалидными номерами страниц."""
    return [item for item in toc_items if int(item["page"]) <= 0]


def check_dot_leaders_hint(lines: list[str]) -> bool:
    """
    Возвращает True, если есть хотя бы один пункт содержания без явного разделителя.

    Проверяем построчно: у каждого распознанного пункта должен быть один из признаков:
    - отточие (... или …)
    - табуляция
    - широкий пробел перед номером страницы
    """
    toc_items, _ = extract_toc_items_with_invalid_lines(lines)
    if not toc_items:
        return False

    for line in lines:
        raw = line.strip()
        if not raw or raw.upper() == "СОДЕРЖАНИЕ":
            continue
        if not RE_TOC_ITEM_WITH_PAGE.match(raw):
            continue

        has_dots = RE_DOT_LEADER.search(raw) is not None
        has_tab_separator = "\t" in raw
        has_wide_space_separator = RE_WIDE_SPACE_PAGE_SUFFIX.search(raw) is not None
        if not (has_dots or has_tab_separator or has_wide_space_separator):
            return True

    return False
