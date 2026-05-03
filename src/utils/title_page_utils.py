"""Вспомогательные функции для работы с титульным листом."""

from datetime import datetime
import re

from ..config.regex_patterns import RE_INITIALS, RE_YEAR_1900_2099
from .common.regex_utils import extract_int_by_pattern, find_last_int_by_pattern
from .common.section_utils import find_first_index_contains, text_contains_all, text_contains_any
from .common.text_utils import is_uppercase_text


def find_organization_block(paragraphs: list[str], start_idx: int = 0, end_idx: int = 15) -> list[str]:
    """
    Ищет блок с наименованием организации (верхняя часть титульника).
    
    Блок должен быть в верхних строках (0-15) и состоять из текста капсом.
    Пропускаем начальные не-капс строки (министерство может быть не капсом).
    """
    service_tokens = ("УДК", "РЕГ", "НИОКТР", "ИКРБС", "УТВЕРЖДАЮ", "СОГЛАСОВАНО", "ОТЧЕТ")

    def _is_caps_line(text: str) -> bool:
        letters = [ch for ch in text if ch.isalpha()]
        return len(letters) > 1 and all(ch.upper() == ch for ch in letters)

    def _extract_caps_in_quotes(text: str) -> str | None:
        # Ищем фрагмент в кавычках, где все буквы прописные
        for chunk in re.findall(r'["«]([^"»]+)["»]', text):
            letters = [ch for ch in chunk if ch.isalpha()]
            if letters and all(ch.upper() == ch for ch in letters):
                return chunk.strip()
        return None

    def _has_caps_in_parentheses(text: str) -> bool:
        for chunk in re.findall(r"\(([^)]*)\)", text):
            letters = [ch for ch in chunk if ch.isalpha()]
            if letters and all(ch.upper() == ch for ch in letters):
                return True
        return False

    window = paragraphs[start_idx:end_idx]
    org_block: list[str] = []
    block_end: int | None = None
    quoted_anchor = False

    # 1) Первый организационный якорь
    for i, para in enumerate(window):
        text = para.strip()
        if not text:
            continue

        text_upper = text.upper()
        if any(token in text_upper for token in service_tokens):
            continue

        # Вариант A: первая капс-строка -> собираем подряд идущий капс-блок
        if _is_caps_line(text) and not text.startswith(("(", '"', "«")):
            org_block = [text]
            block_end = i
            j = i + 1
            while j < len(window):
                nxt = window[j].strip()
                if not nxt:
                    j += 1
                    continue
                nxt_upper = nxt.upper()
                if any(token in nxt_upper for token in service_tokens):
                    break
                if _is_caps_line(nxt) and not nxt.startswith(("(", '"', "«")):
                    org_block.append(nxt)
                    block_end = j
                    j += 1
                    continue
                break
            break

        # Вариант B: строка с капсом в кавычках (например: ... "РИННОТЕХ")
        quoted = _extract_caps_in_quotes(text)
        if quoted:
            org_block = [quoted]
            block_end = i
            quoted_anchor = True
            break

    if not org_block or block_end is None:
        return []

    # 2) Следующий непустой элемент после блока
    next_non_empty: str | None = None
    for para in window[block_end + 1:]:
        candidate = para.strip()
        if candidate:
            next_non_empty = candidate
            break

    # Если якорь был из кавычек, а следующего элемента нет, считаем валидным
    if next_non_empty is None:
        return org_block if quoted_anchor else []

    starts = next_non_empty.lstrip()
    if starts.startswith(('"', "«")):
        return org_block
    if starts.startswith("(") and _has_caps_in_parentheses(starts):
        return org_block
    return []



def find_metadata_block(paragraphs: list[str]) -> dict[str, str]:
    """
    Ищет блок с УДК, регистрационными номерами (левая сторона титульника).
    
    Возвращает словарь: {"УДК": "...", "Рег. N НИОКТР": "...", ...}
    """
    metadata = {}
    for para in paragraphs[:30]:  # Первые 30 строк титульника
        para_upper = para.upper()
        if "УДК" in para_upper:
            metadata["УДК"] = para.strip()
        elif text_contains_all(para_upper, ["РЕГ", "НИОКТР"], case_sensitive=True):
            metadata["Рег. N НИОКТР"] = para.strip()
        elif text_contains_all(para_upper, ["РЕГ", "ИКРБС"], case_sensitive=True):
            metadata["Рег. N ИКРБС"] = para.strip()
    return metadata


def find_approval_stamp(paragraphs: list[str]) -> tuple[str | None, str | None]:
    """
    Ищет грифы СОГЛАСОВАНО и УТВЕРЖДАЮ.
    
    Возвращает кортеж: (согласовано_текст, утверждаю_текст)
    """
    sogl = None
    utv = None
    
    for para in paragraphs:#[:30]:
        para_upper = para.upper()
        if "СОГЛАСОВАНО" in para_upper:
            sogl = para.strip()
        if "УТВЕРЖДАЮ" in para_upper:
            utv = para.strip()
    
    return sogl, utv


def find_document_type(paragraphs: list[str]) -> str | None:
    """
    Ищет тип документа (ОТЧЕТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ).
    
    Должно быть капсом, две строки: "ОТЧЕТ" и "О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ".
    """
    def _normalize(text: str) -> str:
        normalized = text.upper().replace("Ё", "Е")
        normalized = normalized.replace("–", "-").replace("—", "-")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    expected_full = "ОТЧЕТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ"

    for i, para in enumerate(paragraphs[:30]):
        first_line = _normalize(para)

        # Однострочный вариант.
        if first_line == expected_full:
            return para.strip()

        # Двухстрочный вариант с любым местом переноса внутри полной фразы.
        if i + 1 < len(paragraphs):
            next_para = paragraphs[i + 1]
            second_line = _normalize(next_para)
            combined = f"{first_line} {second_line}".strip()
            if combined == expected_full:
                return f"{para.strip()}\n{next_para.strip()}"
    return None


def extract_initials(text: str) -> list[str]:
    """
    Извлекает инициалы из текста (например, 'А.В. Иванов' → ['А.В.']).
    
    Паттерн: заглавная буква + точка + заглавная буква + точка
    """
    return RE_INITIALS.findall(text)


def find_place_and_year(paragraphs: list[str]) -> tuple[str | None, int | None]:
    """
    Ищет место и год на титульнике.
    
    Формат: "Москва 2026" или "Москва, 2026" или просто "2026"
    Ищет снизу вверх по всем строкам титульника.
    Возвращает: (место, год)
    """
    # Ищем последний год (снизу вверх) через общий helper.
    year = find_last_int_by_pattern(paragraphs, RE_YEAR_1900_2099, group=1)
    if year is None:
        return None, None

    # Место берем из той же строки, где впервые снизу встретился этот год.
    for para in reversed(paragraphs):
        if not para.strip():
            continue

        found_year = extract_int_by_pattern(para, RE_YEAR_1900_2099, group=1)
        if found_year == year:
            place = RE_YEAR_1900_2099.sub('', para).strip(' ,')
            return place if place else None, year
    
    return None, None


def check_organization(paragraphs: list[str]) -> tuple[list[str], bool]:
    """Проверка блока организации (верх титульника, капсом, по центру)."""
    org_block = find_organization_block(paragraphs)

    if not org_block:
        return [], False

    org_text = ' '.join(org_block).upper()
    keywords = ["МИНИСТЕРСТВО", "ФЕДЕРАЛЬНОЕ", "АГЕНТСТВО", "УНИВЕРСИТЕТ", "ИНСТИТУТ", "НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ", "КОНЦЕРН", "КОМПАНИЯ", "ОРГАНИЗАЦИЯ"]
    has_keywords = text_contains_any(org_text, keywords, case_sensitive=True)
    return org_block, has_keywords


def check_metadata(paragraphs: list[str], has_digit_pattern) -> tuple[bool, bool, bool]:
    """Проверка УДК и регистрационных номеров (левая сторона)."""
    metadata = find_metadata_block(paragraphs)

    has_udk = "УДК" in metadata
    udk_has_digits = False
    if has_udk:
        udk_line = metadata["УДК"]
        udk_has_digits = bool(has_digit_pattern.search(udk_line))

    has_nioktr = "Рег. N НИОКТР" in metadata
    return has_udk, udk_has_digits, has_nioktr


def check_approval_stamps(paragraphs: list[str]) -> tuple[str | None, bool]:
    """Проверка грифов СОГЛАСОВАНО и УТВЕРЖДАЮ."""
    _, utv = find_approval_stamp(paragraphs)

    if not utv:
        return None, False

    initials_found = True
    utv_idx = find_first_index_contains(paragraphs, "УТВЕРЖДАЮ")
    if utv_idx is not None:
        context = '\n'.join(paragraphs[utv_idx:utv_idx + 5])
        initials = extract_initials(context)
        initials_found = bool(initials)

    return utv, initials_found


def check_document_type(paragraphs: list[str]) -> tuple[str | None, bool, bool]:
    """Проверка вида документа (ОТЧЕТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ)."""
    doc_type = find_document_type(paragraphs)

    if not doc_type:
        return None, False, False

    def _normalize(text: str) -> str:
        normalized = text.upper().replace("Ё", "Е")
        normalized = normalized.replace("–", "-").replace("—", "-")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    lines = doc_type.split('\n')
    has_two_lines = False
    if len(lines) == 2:
        has_two_lines = (
            _normalize(lines[0]) == "ОТЧЕТ"
            and _normalize(lines[1]) == "О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ"
        )

    is_uppercase = all(is_uppercase_text(line) for line in lines)
    return doc_type, has_two_lines, is_uppercase


def check_place_and_year(paragraphs: list[str]) -> tuple[str | None, int | None, int, bool]:
    """Проверка места и года (низ титульника)."""
    place, year = find_place_and_year(paragraphs)
    current_year = datetime.now().year
    is_future_year = bool(year and year > current_year)
    return place, year, current_year, is_future_year
