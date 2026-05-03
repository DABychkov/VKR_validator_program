"""Извлечение встроенного оглавления Word (TOC) из XML content controls (w:sdt)."""

from __future__ import annotations

import re

from docx import Document

from ...models.rich_document_structure import TocEntryFeature


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _join_text_from_element(elem) -> str:
    parts: list[str] = []
    for t in elem.findall(f".//{{{W_NS}}}t"):
        if t.text:
            parts.append(t.text)
    return "".join(parts).strip()


def _extract_title_page(raw_text: str) -> tuple[str | None, int | None, bool]:
    m = re.match(r"^(?P<title>.+?)\s*(?P<page>[+-]?\d+)\s*$", raw_text)
    if not m:
        return None, None, False

    title = m.group("title").strip()
    page_text = m.group("page").strip()
    if not title:
        return None, None, False

    try:
        page = int(page_text)
    except ValueError:
        return None, None, False

    return title, page, True


def extract_toc_entries(doc: Document) -> list[TocEntryFeature]:
    """Возвращает элементы встроенного Word-оглавления (если есть)."""
    entries: list[TocEntryFeature] = []

    body = doc.element.body
    for block_idx, child in enumerate(body.iterchildren()):
        # Ищем именно sdt-блоки (content controls), где Word обычно хранит авто-оглавление.
        if not str(child.tag).endswith("}sdt"):
            continue

        instr_nodes = child.findall(f".//{{{W_NS}}}instrText")
        has_toc_field = any("TOC" in ((n.text or "").upper()) for n in instr_nodes)
        has_pageref = any("PAGEREF" in ((n.text or "").upper()) for n in instr_nodes)

        # Если это не TOC/PAGEREF-блок, пропускаем.
        if not (has_toc_field or has_pageref):
            continue

        for p in child.findall(f".//{{{W_NS}}}p"):
            raw_text = _join_text_from_element(p)
            if not raw_text:
                continue

            has_hyperlink = bool(p.findall(f".//{{{W_NS}}}hyperlink"))
            title, page, parse_ok = _extract_title_page(raw_text)
            entries.append(
                TocEntryFeature(
                    paragraph_index=block_idx,
                    raw_text=raw_text,
                    title=title,
                    page=page,
                    has_toc_field=(has_toc_field or has_pageref),
                    has_hyperlink=has_hyperlink,
                    parse_ok=parse_ok,
                )
            )

    return entries
