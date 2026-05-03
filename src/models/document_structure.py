"""Модель структуры документа."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .rich_document_structure import RichDocumentStructure


@dataclass
class DocumentStructure:
    filename: str
    title_page_text: str  # Первые ~30 абзацев (титульник)
    rich_document: "RichDocumentStructure | None" = None
    sections: dict[str, str] = field(default_factory=dict)  # {"РЕФЕРАТ": "текст...", "ВВЕДЕНИЕ": "текст..."}
    all_paragraphs: list[str] = field(default_factory=list)  # Все абзацы документа

