"""Набор экстракторов rich-метаданных документа."""

from .paragraph_extractor import extract_paragraph_features
from .table_extractor import extract_table_features
from .footer_extractor import extract_footer_features, extract_section_page_settings
from .formula_extractor import extract_formula_features
from .caption_link_extractor import (
    extract_figure_caption_features,
    extract_links_features,
    resolve_non_source_links,
)
from .notes_footnotes_extractor import extract_footnote_features, extract_notes_features
from .toc_extractor import extract_toc_entries

__all__ = [
    "extract_paragraph_features",
    "extract_table_features",
    "extract_footer_features",
    "extract_section_page_settings",
    "extract_formula_features",
    "extract_figure_caption_features",
    "extract_links_features",
    "resolve_non_source_links",
    "extract_notes_features",
    "extract_footnote_features",
    "extract_toc_entries",
]
