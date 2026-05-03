"""Общие константы для валидации и парсинга документа."""

from pathlib import Path

# Путь к тестовому документу для локальных запусков.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DOCX_PATH = str(PROJECT_ROOT / "uploads" / "document.docx")

# Ключевые секции
SECTION_CONTENTS = "СОДЕРЖАНИЕ"
SECTION_ABSTRACT = "РЕФЕРАТ"
SECTION_TERMS = "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ"
SECTION_ABBREVIATIONS = "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ"
SECTION_COMBINED_DEFINITIONS = "ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ"
SECTION_REFERENCES = "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"
SECTION_EXECUTOR_LIST = "СПИСОК ИСПОЛНИТЕЛЕЙ"
SECTION_EXECUTOR_LIST_TYPO = "СПИСОК ИСПОЛЬНИТЕЛЕЙ"
SECTION_APPENDIX = "ПРИЛОЖЕНИЕ"

# Наборы ключевых слов для поиска секций
CONTENTS_SECTION_KEYWORDS = (SECTION_CONTENTS,)
ABSTRACT_SECTION_KEYWORDS = (SECTION_ABSTRACT,)
TERMS_SECTION_KEYWORDS = (SECTION_TERMS,)
ABBREVIATIONS_SECTION_KEYWORDS = (SECTION_ABBREVIATIONS,)
COMBINED_DEFINITIONS_SECTION_KEYWORDS = (SECTION_COMBINED_DEFINITIONS,)
REFERENCES_SECTION_KEYWORDS = (SECTION_REFERENCES,)
EXECUTOR_SECTION_KEYWORDS = (
    SECTION_EXECUTOR_LIST,
    SECTION_EXECUTOR_LIST_TYPO,
    "ИСПОЛНИТЕЛИ",
)
APPENDIX_SECTION_KEYWORDS = (SECTION_APPENDIX,)

# Ключевые секции для парсера
PARSER_SECTION_KEYWORDS = [
    SECTION_EXECUTOR_LIST,
    SECTION_ABSTRACT,
    SECTION_CONTENTS,
    SECTION_TERMS,
    SECTION_ABBREVIATIONS,
    "ВВЕДЕНИЕ",
    "ЗАКЛЮЧЕНИЕ",
    SECTION_REFERENCES,
    SECTION_APPENDIX,
    SECTION_COMBINED_DEFINITIONS,
]

# Общие регулярные выражения вынесены в config/regex_patterns.py
