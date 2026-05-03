"""Единый набор регулярных выражений проекта."""

import re


# Общие паттерны
RE_HAS_DIGIT = re.compile(r"\d")
RE_INITIALS = re.compile(r"[А-ЯA-Z]\.[А-ЯA-Z]\.")
RE_SURNAME_WITH_INITIALS = re.compile(
    r"[А-ЯA-Z][а-яa-z]*\s+[А-ЯA-Z]\.[А-ЯA-Z]\.",
    re.UNICODE,
)
RE_INITIALS_ANYWHERE = re.compile(
    r"[А-ЯA-Z][а-яa-z]*\s+[А-ЯA-Z]\.\s?[А-ЯA-Z]\.|[А-ЯA-Z]\.\s?[А-ЯA-Z]\.\s?[А-ЯA-Z][а-яa-z]*",
    re.UNICODE,
) 
RE_YEAR_1900_2099 = re.compile(r"\b(19\d{2}|20\d{2})\b")

# Нумерованные строки/списки
RE_NUMBERED_LIST_ITEM_LINE = re.compile(r"^\d{1,3}\.?\s+\S")
RE_NUMBERED_ITEM_PREFIX = re.compile(r"^(\d{1,3})\.?\s")
RE_NUMBERED_PREFIX_GENERIC = re.compile(r"^\d+\.?\s+")

# Оглавление/страницы
RE_TOC_ITEM_WITH_PAGE = re.compile(
    r"^(?P<title>.+?)\s*(?:(?:[.\u2026]{2,})|\t+|\s{2,})?\s*(?P<page>[+-]?\d+)\s*$"
)
RE_DOT_LEADER = re.compile(r"(?:\.{2,}|\u2026{2,})")
RE_WIDE_SPACE_PAGE_SUFFIX = re.compile(r"\s{2,}\d+\s*$")
RE_LINE_ENDS_WITH_DIGITS = re.compile(r"\d+\s*$")
RE_NON_DIGIT_BEFORE_PAGE = re.compile(r"\D\s*\d+\s*$")

# Приложения: строка может не заканчиваться на номер (хвост после заголовка допускаем).
RE_APPENDIX_HEADER = re.compile(
    r"^\s*ПРИЛОЖЕНИЕ\s+([А-ЯA-ZЁ0-9]+)\b",
    re.IGNORECASE,
)

# Титульник/исполнители
RE_EXECUTOR_ON_TITLE = re.compile(r"[Ии]сполнитель[:\s]+.*?[А-ЯA-Z]\.[А-ЯA-Z]\.", re.DOTALL)

# Реферат
RE_ABSTRACT_METRICS = {
    "pages": re.compile(r"(\d+)\s*(?:страниц|страница|сстр|с\.)", re.IGNORECASE),
    "books": re.compile(r"(\d+)\s*(?:книг|книги|кн\.|от книг)", re.IGNORECASE),
    "illustrations": re.compile(r"(\d+)\s*(?:иллюстрац|рисунк|рис\.|фиг|фиг\.)", re.IGNORECASE),
    "tables": re.compile(r"(\d+)\s*(?:табли|таблиц|табл|табл\.)", re.IGNORECASE),
    "sources": re.compile(r"(\d+)\s*(?:источник|использ\s+источник|ист\.|источн|исчисл)", re.IGNORECASE),
    "appendices": re.compile(r"(\d+)\s*(?:прилож|приложен|прил\.|приложён)", re.IGNORECASE),
}
RE_WORD_GOAL = re.compile(r"\bцель")
RE_WORD_OBJECT = re.compile(r"\bобъект")
RE_WORD_RECOMMEND = re.compile(r"\bрекомендац")

# Термины/сокращения
DEFINITION_DASHES = "-–—"
RE_DEFINITION_ITEM_DASH = re.compile(
    rf"^(?P<left>.+?)\s*[{DEFINITION_DASHES}]\s*(?P<right>.+)$"
)
RE_DEFINITION_ITEM_COLON = re.compile(r"^(?P<left>.+?)\s*:\s*(?P<right>.+)$")
RE_LEFT_INDENTATION = re.compile(r"^\s+")

# Основная часть (начало)
RE_MAIN_SECTION_START_PATTERNS = (
    re.compile(r"^\d+\s+[А-ЯA-Z]", re.IGNORECASE),
    re.compile(r"^\d+\.\s+[А-ЯA-Z]", re.IGNORECASE),
    re.compile(r"^Глава\s+\d+", re.IGNORECASE),
    re.compile(r"^ГЛАВА\s+\d+", re.IGNORECASE),
)

# Rich extractors: таблицы / подписи / ссылки
# Пример строки источника: "1 Текст", "1. Текст", "1) Текст"
RE_REFERENCE_LIST_ITEM = re.compile(r"^(\d{1,4})[\.)]?\s+.+")

# Пример: "Таблица 2 - Параметры", "Таблица А.1 - ..."
RE_TABLE_TITLE = re.compile(
    r"^\s*(таблица|table)\s+((?=[A-Za-zА-Яа-я0-9.]*\d)[A-Za-zА-Яа-я0-9]+(?:\.[A-Za-zА-Яа-я0-9]+)*)(?!\.)\s*[\-\u2013\u2014:]\s+.+$",
    re.IGNORECASE,
)
# Пример: "Продолжение таблицы 2", "Продолжения таблицы А.1"
RE_TABLE_CONTINUATION = re.compile(
    r"продолжени[ея]\s+таблиц(?:ы)?\s+((?=[A-Za-zА-Яа-я0-9.]*\d)[A-Za-zА-Яа-я0-9]+(?:\.[A-Za-zА-Яа-я0-9]+)*)(?!\.)",
    re.IGNORECASE,
)

# Пример подписи: "Рисунок 2 - Схема...", "Рис. А.3: ..."
RE_FIGURE_CAPTION = re.compile(
    r"^\s*(рис(?:\.|унок)?|figure)\s+((?=[A-Za-zА-Яа-я0-9.]*\d)[A-Za-zА-Яа-я0-9]+(?:\.[A-Za-zА-Яа-я0-9]+)*)(?!\.)\s*([\-\u2013\u2014:]?)",
    re.IGNORECASE,
)
# Пример ссылок на источники: "[1]" и диапазон "[1] - [4]" / "[1]-[4]"
RE_SOURCE_LINK = re.compile(r"\[(?P<start>\d+)\](?:\s*[-\u2013]\s*\[(?P<end>\d+)\])?")
# Пример: "в рисунке 2", "согласно рисунку 2.1", "см. рис. А.3"
RE_FIGURE_LINK = re.compile(
    r"(?:рис\.|рисунк[а-я]*|figure)\s*\(?((?=[A-Za-zА-Яа-я0-9.]*\d)[A-Za-zА-Яа-я0-9]+(?:\.[A-Za-zА-Яа-я0-9]+)*)(?!\.)\)?",
    re.IGNORECASE,
)
# Пример: "таблица 2", "таблицей 2.1", "табл. А.1"
RE_TABLE_LINK = re.compile(
    r"(?:таблиц[а-я]*|табл\.?|table)\s*\(?\s*((?=[A-Za-zА-Яа-я0-9\s.]*\d)[A-Za-zА-Яа-я0-9]+(?:\s*\.\s*[A-Za-zА-Яа-я0-9]+)*)\s*\)?",
    re.IGNORECASE,
)
# Пример: "формула (3)", "equation 2.1"
RE_FORMULA_LINK = re.compile(
    r"(?:формул(?:а|е|ы|ой)|equation|eq\.)\s*\(?\s*((?:\d+(?:\s*\.\s*\d+)*)|(?:[A-Za-zА-Яа-я]\s*\.\s*\d+(?:\s*\.\s*\d+)*))\s*\)?",
    re.IGNORECASE,
)

# Примечания и сноски
# Пример: "Примечание - Текст"
RE_NOTE_SINGLE = re.compile(r"^\s*примечание\s*[-\u2013\u2014]\s*(.+)$", re.IGNORECASE)
# Пример: "Примечания" / "Примечания:" / "Примечание" / "Примечание:"
RE_NOTES_HEADER = re.compile(r"^\s*примечани[ея]\s*:?\s*$", re.IGNORECASE)
# Пример: "1 К тексту дается...", "1. К тексту..."
RE_NOTES_ITEM = re.compile(r"^\s*(\d{1,3})[\.)]?\s+.+$")
# Пример: "1 Текст", "1. Текст", "1) Текст" (с группой разделителя)
RE_NOTES_ITEM_NUMBER_PREFIX = re.compile(r"^\s*(\d{1,3})([\.)])?\s+")
# Пример: "1 Примечание - Текст", "1. Примечание - Текст"
RE_NUMBERED_NOTE_SINGLE = re.compile(r"^\s*(\d{1,3})[\.)]?\s+примечани[ея]\s*[-\u2013\u2014]\s*.+$", re.IGNORECASE)
# Пример звездочной сноски в тексте: "слово*"
# Фиксируем только маркер, который выглядит как сноска: после буквенно-цифрового
# символа и перед пробелом/знаками препинания/концом строки.
RE_ASTERISK_FOOTNOTE_INLINE_MARKER = re.compile(
    r"(?<=[0-9A-Za-zА-Яа-яЁё])\*(?=(?:[\s\.,;:!\?\)\]\"»]|$))(?!\*)"
)
# Пример строки пояснения сноски: "* Текст пояснения"
RE_ASTERISK_FOOTNOTE_BODY = re.compile(r"^\s*\*\s+.+$")
