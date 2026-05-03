"""Вспомогательные функции для валидации реферата."""

from ..config.regex_patterns import (
    RE_ABSTRACT_METRICS,
    RE_NUMBERED_PREFIX_GENERIC,
    RE_WORD_GOAL,
    RE_WORD_OBJECT,
    RE_WORD_RECOMMEND,
)
from .common.regex_utils import extract_int_by_pattern
from .common.text_utils import count_non_whitespace_characters


def extract_volume_metrics(text: str) -> dict[str, int | None]:
    """
    Извлекает метрики объема (страницы, книги, иллюстрации и т.д.) из текста.
    
    Возвращает словарь вида:
    {"pages": 150, "books": 2, "illustrations": 5, "tables": 3, "sources": 10, "appendices": 2}
    """
    metrics = {
        "pages": None,
        "books": None,
        "illustrations": None,
        "tables": None,
        "sources": None,
        "appendices": None
    }
    
    for key, pattern in RE_ABSTRACT_METRICS.items():
        metrics[key] = extract_int_by_pattern(text, pattern, group=1)
    
    return metrics


def find_keywords_section(paragraphs: list[str]) -> str | None:
    """
    Ищет БЛОК ключевых слов (может быть несколько строк).
    
    Критерии:
    - Строки преимущественно капсом (>=80% букв в верхнем регистре)
    - Это не якорь/нумерация (не начинается с "1.1 ", "1.2 " и т.д.)
    - Для ОДНОСТРОЧНОГО: обязательно хотя бы одна запятая
    - Для МНОГОСТРОЧНОГО: хотя бы в одной строке запятая + большинство строк(>=50%) с запятыми
    """
    import re
    
    if not paragraphs:
        return None
    
    keywords_lines = []
    
    for line in paragraphs:
        stripped = line.strip()
        
        # Пропускаем пустые строки
        if not stripped:
            continue
        
        # Проверяем буквы / капс
        letters = [c for c in stripped if c.isalpha()]
        if not letters:
            continue
        
        uppercase_letters = [c for c in letters if c.isupper()]
        uppercase_ratio = len(uppercase_letters) / len(letters)
        # На этапе извлечения используем мягкий порог.
        # Строгая 100% проверка остается в check_keywords_format().
        is_caps_like = uppercase_ratio >= 0.8
        
        # Якорь/нумерация - пропускаем начало блока
        if not keywords_lines and re.match(r'^\d+\.\d*', stripped):  # "1.1 ", "1.2 " и т.д.
            continue
        
        # До старта блока используем более строгий порог (>=80%).
        if not keywords_lines:
            if is_caps_like:
                keywords_lines.append(stripped)
            continue

        # После старта блока собираем его целиком мягче,
        # чтобы format_check мог валидировать весь фрагмент.
        # В блок включаем строки с запятыми или с заметной долей капса.
        keep_in_block = (',' in stripped) or (uppercase_ratio >= 0.5)
        if keep_in_block:
            keywords_lines.append(stripped)
        else:
            break
    
    if not keywords_lines:
        return None
    
    # Проверяем что это действительно ключевые слова по запятам
    comma_count_lines = sum(1 for line in keywords_lines if ',' in line)
    total_commas = sum(line.count(',') for line in keywords_lines)
    total_lines = len(keywords_lines)
    
    if total_lines == 1:
        # Однострочный блок: хотя бы одна запятая
        if ',' not in keywords_lines[0]:
            return None
    else:
        # Многострочный блок: 
        # - хотя бы одна запятая в блоке
        # - хотя бы 50% строк с запятыми
        if total_commas == 0:
            return None
        
        comma_ratio = comma_count_lines / total_lines
        if comma_ratio < 0.5:
            return None
    
    return '\n'.join(keywords_lines)


def check_keywords_format(keywords_block: str) -> dict[str, bool]:
    """
    Проверяет формат ключевых слов (блок может быть многострочным).
    
    Требования ГОСТ:
    1. is_uppercase: все буквы в каждой строке прописные (капс)
    2. has_commas: большинство строк содержат запятые как разделители
    3. no_trailing_period: последняя строка не заканчивается точкой
    4. no_line_breaks: не более 4 строк и без признаков переноса слова
    """
    results = {
        "is_uppercase": True,
        "has_commas": True,
        "no_trailing_period": True,
        "no_line_breaks": True
    }
    
    if not keywords_block:
        return {k: False for k in results.keys()}
    
    # Разбиваем блок на строки
    lines = keywords_block.split('\n') if '\n' in keywords_block else [keywords_block]
    
    # 1. Проверка капс в каждой строке
    for line in lines:
        letters = [c for c in line if c.isalpha()]
        if letters:
            uppercase_letters = [c for c in letters if c.isupper()]
            if len(uppercase_letters) != len(letters):
                # Не все буквы капс
                results["is_uppercase"] = False
                break
    
    # 2. Проверка запятых (хотя бы в большинстве строк)
    lines_with_commas = sum(1 for line in lines if ',' in line)
    lines_total = len(lines)
    # Нужно чтобы в большей части строк были запятые (>=50%)
    if lines_with_commas < (lines_total / 2):
        results["has_commas"] = False
    else:
        # Кроме того, нужна хотя бы одна запятая
        if sum(line.count(',') for line in lines) == 0:
            results["has_commas"] = False
    
    # 3. Проверка отсутствия точки в конце ПОСЛЕДНЕЙ строки
    if lines:
        last_line = lines[-1].rstrip()
        if last_line.endswith('.'):
            results["no_trailing_period"] = False
    
    # 4. Проверка переносов: не более 4 строк и без дефиса/тире в конце строки.
    # Внутрисловные дефисы (например, "организации-соисполнителя") допускаются,
    # т.к. запрещаем только символ переноса в конце строки.
    hyphen_like_endings = ("-", "–", "—", "‑")
    for line in lines:
        if line.rstrip().endswith(hyphen_like_endings):
            results["no_line_breaks"] = False
            break

    if '\n\n' in keywords_block:
        results["no_line_breaks"] = False
    if len(lines) > 4:
        results["no_line_breaks"] = False
    
    return results


def find_text_keywords_in_abstract(text: str) -> dict[str, bool]:
    """
    Ищет ключевые фразы в тексте реферата.
    
    Возвращает словарь с наличием ключевых фраз.
    """
    keywords = {
        "goal": False,      # "цель"
        "object": False,    # "объект"
        "recommendations": False  # "рекомендац"
    }
    
    text_lower = text.lower()
    
    if RE_WORD_GOAL.search(text_lower):
        keywords["goal"] = True
    
    if RE_WORD_OBJECT.search(text_lower):
        keywords["object"] = True
    
    if RE_WORD_RECOMMEND.search(text_lower):
        keywords["recommendations"] = True
    
    return keywords


def check_volume_info(lines: list[str]) -> tuple[list[str], bool]:
    """Возвращает найденные метрики и флаг некорректного формата разделителей."""
    required_metrics = ["pages", "books", "illustrations", "tables", "sources"]
    first_lines = lines[:5]

    # Формируем блок по строкам, где реально встречаются метрики объема.
    metric_lines = [
        line for line in first_lines
        if any(RE_ABSTRACT_METRICS[key].search(line) for key in required_metrics)
    ]
    volume_block = " ".join(metric_lines) if metric_lines else "\n".join(first_lines)

    metrics = extract_volume_metrics(volume_block)
    found_metrics = [k for k, v in metrics.items() if v is not None and k in required_metrics]

    # Для n найденных метрик ожидаем минимум (n-1) запятых как разделители между ними.
    expected_min_commas = max(0, len(found_metrics) - 1)
    actual_commas = volume_block.count(",")
    has_invalid_separator = len(found_metrics) >= 2 and actual_commas < expected_min_commas

    return found_metrics, has_invalid_separator


def check_keywords(lines: list[str]) -> tuple[str | None, dict[str, bool] | None]:
    """Возвращает найденную строку ключевых слов и результаты проверки формата."""
    keywords_section = find_keywords_section(lines)

    if not keywords_section:
        return None, None

    format_check = check_keywords_format(keywords_section)
    return keywords_section, format_check

def check_abstract_text(abstract_text: str) -> list[str]:
    """Возвращает список отсутствующих ключевых фраз текста реферата."""
    keywords = find_text_keywords_in_abstract(abstract_text)
    missing_keywords = [k for k, v in keywords.items() if not v]
    return missing_keywords


def check_abstract_size(abstract_text: str) -> int:
    """Возвращает размер текста реферата без пробельных символов."""
    return count_non_whitespace_characters(abstract_text)
