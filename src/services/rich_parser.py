"""Rich-парсер DOCX: извлекает нормализованные признаки оформления.

Этот парсер не заменяет текущий DocumentParser,
а работает рядом для строгих проверок форматирования.
"""

import os

from docx import Document

from ..models.rich_document_structure import RichDocumentStructure
from .extractors import (
    extract_toc_entries,
    extract_footnote_features,
    extract_figure_caption_features,
    extract_footer_features,
    extract_formula_features,
    extract_links_features,
    extract_notes_features,
    extract_paragraph_features,
    resolve_non_source_links,
    extract_section_page_settings,
    extract_table_features,
)


class RichParser:
    """Сбор rich-признаков документа для валидаторов оформления."""

    def parse(self, file_path: str) -> RichDocumentStructure:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        if not file_path.lower().endswith(".docx"):
            raise ValueError("Ожидается файл .docx")

        doc = Document(file_path)

        paragraph_features = extract_paragraph_features(doc)
        table_features = extract_table_features(doc)
        pages_settings = extract_section_page_settings(doc)
        footer_features = extract_footer_features(doc)
        formula_features = extract_formula_features(doc)
        figure_caption_features = extract_figure_caption_features(doc)
        links_features = extract_links_features(doc)
        links_features = resolve_non_source_links(
            links_features,
            figure_caption_features,
            table_features,
            formula_features,
        )
        notes_features = extract_notes_features(doc)
        footnote_features = extract_footnote_features(doc)
        toc_entries = extract_toc_entries(doc)

        # TODO: language_hint, sections_detected.
        return RichDocumentStructure(
            source_file=os.path.abspath(file_path),
            paragraph_features=paragraph_features,
            table_features=table_features,
            pages_settings=pages_settings,
            footer_features=footer_features,
            formula_features=formula_features,
            figure_caption_features=figure_caption_features,
            links_features=links_features,
            notes_features=notes_features,
            footnote_features=footnote_features,
            toc_entries=toc_entries,
        )
