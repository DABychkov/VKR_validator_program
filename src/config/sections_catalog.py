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
    {"id": SECTION_TITLE_PAGE, "name": "Титульный лист"},
    {"id": SECTION_EXECUTOR_LIST, "name": "Список исполнителей"},
    {"id": SECTION_ABSTRACT, "name": "Реферат"},
    {"id": SECTION_CONTENTS, "name": "Содержание"},
    {"id": SECTION_TERMS, "name": "Термины и определения"},
    {"id": SECTION_ABBREVIATIONS, "name": "Перечень сокращений и обозначений"},
    {"id": SECTION_COMBINED_DEFINITIONS, "name": "Определения, обозначения и сокращения"},
    {"id": SECTION_INTRODUCTION, "name": "Введение"},
    {"id": SECTION_MAIN, "name": "Основная часть"},
    {"id": SECTION_CONCLUSION, "name": "Заключение"},
    {"id": SECTION_REFERENCES, "name": "Список использованных источников"},
    {"id": SECTION_APPENDIX, "name": "Приложения"},
]
