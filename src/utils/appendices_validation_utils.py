"""Содержательные проверки для валидатора раздела "ПРИЛОЖЕНИЯ"."""

from re import Pattern
from typing import Any

from .common.rich_utils import find_paragraph_index_by_text, is_center_bold
from .common.section_utils import check_is_sequential
from .common.text_utils import is_parenthesized_text


def extract_label(header: str, appendix_header_re: Pattern[str]) -> str | None:
    """Извлекает обозначение приложения из заголовка."""
    header_strip = header.strip()
    first_line = header_strip.splitlines()[0].strip() if header_strip else ""
    match = appendix_header_re.match(first_line)
    if not match:
        return None
    return match.group(1).upper()


def extract_title(header: str) -> str | None:
    """Извлекает название приложения из заголовка."""
    lines = [line.strip() for line in header.splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    # Якорная логика: после первой строки "ПРИЛОЖЕНИЕ X"
    # берем первую осмысленную строку, исключая строку статуса и
    # случайное повторение строки "ПРИЛОЖЕНИЕ ...".
    for candidate in lines[1:]:
        if is_parenthesized_text(candidate):
            continue
        if candidate.upper().startswith("ПРИЛОЖЕНИЕ"):
            continue
        return candidate

    return None


def _normalize_for_match(text: str) -> str:
    return " ".join(text.split()).strip().upper()


def extract_status_line(header: str) -> str | None:
    """Извлекает строку статуса приложения (в скобках)."""
    lines = [line.strip() for line in header.splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    status_line = lines[1]
    if is_parenthesized_text(status_line):
        return status_line
    return None


def extract_status_line_with_fallback(header: str, section_text: str) -> str | None:
    """Извлекает строку статуса из header, либо из первых строк тела секции."""
    status_line = extract_status_line(header)
    if status_line:
        return status_line

    body_lines = [line.strip() for line in section_text.split("\n") if line.strip()]
    if not body_lines:
        return None

    candidate = body_lines[0]
    if is_parenthesized_text(candidate):
        return candidate
    return None


def _find_header_paragraph_index(rich_doc: Any, header: str) -> int | None:
    paragraph_features = getattr(rich_doc, "paragraph_features", [])

    # Сначала пытаемся найти полный header как есть.
    full_match_index = find_paragraph_index_by_text(paragraph_features, header)
    if full_match_index is not None:
        return full_match_index

    # Если header многострочный (например, "ПРИЛОЖЕНИЕ А\nНазвание"),
    # в rich-потоке это часто два отдельных абзаца. Берем первую строку-якорь.
    header_lines = [line.strip() for line in header.splitlines() if line.strip()]
    if not header_lines:
        return None

    return find_paragraph_index_by_text(paragraph_features, header_lines[0])


def extract_title_with_rich_fallback(
    header: str,
    section_text: str,
    rich_doc: Any | None,
) -> tuple[str | None, int]:
    """Извлекает название приложения и число строк section_text, занятых заголовком.

    consumed_lines относится только к строкам section_text. Поэтому в rich-ветке,
    когда заголовок найден по paragraph_features, увеличиваем consumed только на
    строки, реально относящиеся к section_text (например, fallback-статус),
    но не на абзацы rich-заголовка.
    """
    title = extract_title(header)
    if title:
        return title, 0

    body_lines = [line.strip() for line in section_text.split("\n") if line.strip()]
    if not body_lines:
        return None, 0

    status_consumed = 1 if is_parenthesized_text(body_lines[0]) else 0

    # Если rich не подключен, используем текстовый fallback.
    if rich_doc is None:
        start_index = status_consumed
        if start_index >= len(body_lines):
            return None, status_consumed
        candidate = body_lines[start_index]
        if candidate.upper().startswith("ПРИЛОЖЕНИЕ"):
            return None, status_consumed
        return candidate, start_index + 1

    header_index = _find_header_paragraph_index(rich_doc, header)
    if header_index is None:
        start_index = status_consumed
        if start_index >= len(body_lines):
            return None, status_consumed
        candidate = body_lines[start_index]
        if candidate.upper().startswith("ПРИЛОЖЕНИЕ"):
            return None, status_consumed
        return candidate, start_index + 1

    title_parts: list[str] = []
    paragraphs = getattr(rich_doc, "paragraph_features", [])
    current_index = header_index + 1

    while current_index < len(paragraphs):
        para = paragraphs[current_index]
        para_text = (getattr(para, "text", "") or "").strip()
        if not para_text:
            current_index += 1
            continue

        if is_parenthesized_text(para_text):
            current_index += 1
            continue

        if not is_center_bold(para, allow_unknown_bold=True):
            break

        title_parts.append(para_text)
        current_index += 1

    if title_parts:
        consumed = status_consumed
        body_index = status_consumed

        # Учитываем в consumed только те rich-строки заголовка,
        # которые реально присутствуют в начале section_text.
        for title_part in title_parts:
            if body_index >= len(body_lines):
                break
            if _normalize_for_match(body_lines[body_index]) != _normalize_for_match(title_part):
                break
            consumed += 1
            body_index += 1

        return " ".join(title_parts), consumed

    # Rich-контекст найден, но строк в стиле center+bold после статуса нет:
    # считаем, что корректного заголовка приложения не обнаружено.
    return None, status_consumed


def is_valid_label(
    label: str,
    invalid_cyrillic_labels: set[str],
    invalid_latin_labels: set[str],
) -> bool:
    """Проверяет соответствие обозначения приложения допустимому формату."""
    if label.isdigit():
        return True

    if len(label) != 1:
        return False

    if "А" <= label <= "Я":
        return label not in invalid_cyrillic_labels

    if "A" <= label <= "Z":
        return label not in invalid_latin_labels

    return False


def check_designation_sequence(
    labels: list[str],
    invalid_cyrillic_labels: set[str],
    invalid_latin_labels: set[str],
) -> tuple[bool, bool, bool]:
    """Проверяет последовательность обозначений приложений."""
    if len(labels) < 2:
        return False, False, False

    digits_non_sequential = False
    cyrillic_non_sequential = False
    latin_non_sequential = False

    def _check_letter_sequence(
        alphabet: str,
        invalid_labels: set[str],
    ) -> bool:
        order = [char for char in alphabet if char not in invalid_labels]
        indexes = [order.index(label) for label in labels if label in order]
        return len(indexes) == len(labels) and not check_is_sequential(indexes)

    if all(label.isdigit() for label in labels):
        numbers = [int(label) for label in labels]
        digits_non_sequential = not check_is_sequential(numbers)
        return digits_non_sequential, cyrillic_non_sequential, latin_non_sequential

    if all(len(label) == 1 and "А" <= label <= "Я" for label in labels):
        cyrillic_non_sequential = _check_letter_sequence(
            alphabet="АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ",
            invalid_labels=invalid_cyrillic_labels,
        )
        return digits_non_sequential, cyrillic_non_sequential, latin_non_sequential

    if all(len(label) == 1 and "A" <= label <= "Z" for label in labels):
        latin_non_sequential = _check_letter_sequence(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            invalid_labels=invalid_latin_labels,
        )
    return digits_non_sequential, cyrillic_non_sequential, latin_non_sequential


def check_contents_mentions(
    contents_text: str | None,
    appendix_entries: list[tuple[str, str | None, str]],
    appendix_keyword: str,
) -> list[tuple[str, bool, bool | None]]:
    """Проверяет, что приложения и их названия указаны в содержании."""
    if not contents_text:
        return []

    facts: list[tuple[str, bool, bool | None]] = []

    contents_upper = contents_text.upper()
    for label, title, _ in appendix_entries:
        appendix_marker = f"{appendix_keyword} {label}".upper()
        has_appendix_marker = appendix_marker in contents_upper
        if not has_appendix_marker:
            facts.append((label, False, None))
            continue

        if not title:
            # Название не удалось извлечь, проверяем только наличие обозначения в содержании.
            facts.append((label, True, None))
            continue

        normalized_title = title.upper()
        has_title = normalized_title in contents_upper
        facts.append((label, True, has_title))
    return facts
