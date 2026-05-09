"""Список структурных секций для фронта."""

from .validation_constants import (
    SECTION_ABSTRACT,
    SECTION_ABBREVIATIONS,
    SECTION_APPENDIX,
    SECTION_COMBINED_DEFINITIONS,
    SECTION_CONTENTS,
    SECTION_EXECUTOR_LIST,
    SECTION_INTRODUCTION,
    SECTION_MAIN,
    SECTION_CONCLUSION,
    SECTION_REFERENCES,
    SECTION_TERMS,
    SECTION_TITLE_PAGE,
)

SECTIONS_CATALOG: list[dict[str, str]] = [
    {"id_section": SECTION_TITLE_PAGE, "name": "Титульный лист"},
    {"id_section": SECTION_EXECUTOR_LIST, "name": "Список исполнителей"},
    {"id_section": SECTION_ABSTRACT, "name": "Реферат"},
    {"id_section": SECTION_CONTENTS, "name": "Содержание"},
    {"id_section": SECTION_TERMS, "name": "Термины и определения"},
    {"id_section": SECTION_ABBREVIATIONS, "name": "Перечень сокращений и обозначений"},
    {"id_section": SECTION_COMBINED_DEFINITIONS, "name": "Определения, обозначения и сокращения"},
    {"id_section": SECTION_INTRODUCTION, "name": "Введение"},
    {"id_section": SECTION_MAIN, "name": "Основная часть"},
    {"id_section": SECTION_CONCLUSION, "name": "Заключение"},
    {"id_section": SECTION_REFERENCES, "name": "Список использованных источников"},
    {"id_section": SECTION_APPENDIX, "name": "Приложения"},
]
