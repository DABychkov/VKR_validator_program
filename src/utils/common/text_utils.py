"""Общие текстовые утилиты для валидаторов."""

from .regex_utils import split_words_by_non_word


def normalize_text(text: str) -> str:
    """Нормализует пробелы и регистр для устойчивых текстовых сравнений."""
    return " ".join(text.replace("\t", " ").split()).strip().lower()


def normalize_text_compact_upper(text: str) -> str:
    """Нормализует пробелы и переводит текст в верхний регистр."""
    return " ".join(text.replace("\t", " ").split()).strip().upper()


def is_parenthesized_text(text: str) -> bool:
    """Проверяет, что строка целиком заключена в круглые скобки."""
    stripped = text.strip()
    return len(stripped) >= 2 and stripped.startswith("(") and stripped.endswith(")")


def find_intro_line(lines: list[str], search_depth: int = 5) -> str:
    """Возвращает первую непустую строку среди первых search_depth строк."""
    for line in lines[:search_depth]:
        clean = line.strip()
        if clean:
            return clean
    return ""


def intro_phrase_matches(actual_line: str, expected_phrase: str, min_common_words: int = 9) -> bool:
    """Проверяет близость фактической вводной фразы к ожидаемой по общим словам."""
    actual_words = split_words_by_non_word(normalize_text(actual_line))
    expected_words = split_words_by_non_word(normalize_text(expected_phrase))

    if not actual_words or not expected_words:
        return False

    common = sum(1 for word in expected_words if word in actual_words)
    return common >= min_common_words


def is_alphabetical(values: list[str]) -> bool:
    """Проверяет алфавитный порядок без учета регистра и лишних пробелов."""
    normalized = [normalize_text(value) for value in values if value.strip()]
    if len(normalized) < 2:
        return True
    return normalized == sorted(normalized)


def is_uppercase_text(text: str) -> bool:
    """Проверяет, что буквенная часть текста набрана заглавными буквами."""
    letters_only = "".join(char for char in text if char.isalpha())
    if not letters_only:
        return False
    return letters_only.isupper()


def count_non_whitespace_characters(text: str) -> int:
    """Считает символы, исключая пробелы, табы и переводы строк."""
    clean_text = text.replace(" ", "").replace("\n", "").replace("\t", "")
    return len(clean_text)