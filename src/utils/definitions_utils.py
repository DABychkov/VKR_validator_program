"""Утилиты для разбора разделов терминов и сокращений."""

from typing import Optional

from ..config.regex_patterns import (
    RE_DEFINITION_ITEM_DASH,
    RE_LEFT_INDENTATION,
)
from .common.section_utils import get_non_empty_lines
from .common.text_utils import (
    find_intro_line,
    intro_phrase_matches,
    is_alphabetical,
)


def split_definition_item(line: str) -> Optional[tuple[str, str]]:
    """
    Пытается извлечь пару (левый термин, правое определение) из строки.

    Поддерживаем варианты:
    - "TERM — definition"
    - "TERM – definition"
    - "TERM - definition"
    - "TERM\tdefinition" (Word-табуляция)
    """
    raw = line.strip()
    if not raw:
        return None

    # Приоритет 1: табуляция (часто используется в DOCX как псевдотаблица)
    if "\t" in raw:
        parts = [p.strip() for p in raw.split("\t") if p.strip()]
        if len(parts) >= 2:
            left = parts[0]
            right = " ".join(parts[1:]).strip()
            if left and right:
                return left, right

    # Приоритет 2: тире/дефис
    dash_match = RE_DEFINITION_ITEM_DASH.match(raw)
    if dash_match:
        left = dash_match.group("left").strip()
        right = dash_match.group("right").strip()
        if left and right:
            return left, right

    return None


def extract_definition_items(section_text: str) -> list[tuple[str, str, str]]:
    """
    Извлекает элементы списка определений.

    Возвращает список тройек:
    - left: термин/сокращение
    - right: определение
    - raw_line: исходная строка (для диагностики)
    """
    items: list[tuple[str, str, str]] = []
    for line in get_non_empty_lines(section_text, strip=False):
        parsed = split_definition_item(line)
        if parsed:
            items.append((parsed[0], parsed[1], line))
    return items


def has_left_indentation(raw_line: str) -> bool:
    """Проверяет наличие отступа перед термином/сокращением."""
    return bool(RE_LEFT_INDENTATION.match(raw_line))
