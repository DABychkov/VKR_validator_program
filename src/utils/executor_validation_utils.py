"""Содержательные проверки для валидатора раздела "СПИСОК ИСПОЛНИТЕЛЕЙ"."""

import re
from re import Pattern

from .common.regex_utils import count_pattern_matches


def check_title_page_executor(
    title_page: str,
    executor_on_title_pattern: Pattern[str],
) -> tuple[bool, bool]:
    """Возвращает флаги: найден исполнитель на титуле, распознаны инициалы."""
    # Ищем маркер роли на титуле, а не любую подстроку "исполнител".
    has_executor_on_title = bool(re.search(r"(?im)^\s*исполнитель\s*:", title_page))
    has_initials_on_title = bool(executor_on_title_pattern.search(title_page)) if has_executor_on_title else False
    return has_executor_on_title, has_initials_on_title


def check_executor_section(
    lines: list[str],
    initials_pattern: Pattern[str],
) -> tuple[bool, int, bool]:
    """Возвращает признаки для проверки секции: роль, количество инициалов, ответственный."""
    # Роль должна быть именно "Исполнители" (а не, например, "Отв. исполнитель").
    has_role = any(re.search(r"^\s*исполнители\b", line, re.IGNORECASE) for line in lines)

    initials_count = count_pattern_matches(lines, initials_pattern)
    # Учитываем только явные формулировки роли ответственного исполнителя.
    has_responsible = any(
        re.search(
            r"^\s*(?:отв\.\s*исполнитель|ответственный\s+исполнитель)\b",
            line,
            re.IGNORECASE,
        )
        for line in lines
    )

    return has_role, initials_count, has_responsible
