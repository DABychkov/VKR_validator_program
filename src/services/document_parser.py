"""Парсер DOCX: извлекает титульник и находит секции документа."""

import os
import re
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..config.validation_constants import (
    PARSER_SECTION_KEYWORDS,
    SECTION_CONTENTS,
    SECTION_REFERENCES,
)
from ..config.regex_patterns import (
    RE_APPENDIX_HEADER,
    RE_LINE_ENDS_WITH_DIGITS,
    RE_MAIN_SECTION_START_PATTERNS,
    RE_NON_DIGIT_BEFORE_PAGE,
    RE_NUMBERED_LIST_ITEM_LINE,
)
from ..models.document_structure import DocumentStructure


class DocumentParser:
    # Ключевые секции по ГОСТ 7.32
    SECTION_KEYWORDS = PARSER_SECTION_KEYWORDS
    TITLE_END_PRIORITY = (
        "СПИСОК ИСПОЛНИТЕЛЕЙ",
        "РЕФЕРАТ",
        "СОДЕРЖАНИЕ",
        "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
        "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
        "ВВЕДЕНИЕ",
        "ЗАКЛЮЧЕНИЕ",
        "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
        "ПРИЛОЖЕНИЕ",
    )
    
    def parse(self, file_path: str) -> DocumentStructure:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        if not file_path.lower().endswith(".docx"):
            raise ValueError("Ожидается файл .docx")

        doc = Document(file_path)

        # Собираем весь текст документа в порядке следования блоков (абзацы + строки таблиц).
        all_paragraphs = self._extract_text_blocks(doc)
        
        # Титульник = от начала документа до приоритетного секционного маркера.
        title_page_text = self._build_title_page_text(all_paragraphs)
        
        # Ищем секции документа
        sections = self._find_sections(all_paragraphs)
        
        return DocumentStructure(
            filename=os.path.basename(file_path),
            title_page_text=title_page_text,
            sections=sections,
            all_paragraphs=all_paragraphs
        )

    def _build_title_page_text(self, paragraphs: list[str]) -> str:
        """Возвращает текст титульника по приоритетной границе секций.

        Граница ищется в порядке:
        1) СПИСОК ИСПОЛНИТЕЛЕЙ
        2) РЕФЕРАТ
        3) затем прочие ключевые секции в фиксированном порядке.
        Если маркер не найден, используем fallback на первые 30 абзацев.
        """
        if not paragraphs:
            return ""

        end_index = self._find_title_end_index(paragraphs)
        if end_index is None:
            end_index = min(30, len(paragraphs))

        return "\n".join(paragraphs[:end_index])

    def _find_title_end_index(self, paragraphs: list[str]) -> int | None:
        """Ищет индекс (exclusive), на котором заканчивается титульник."""
        normalized = [re.sub(r"\s+", " ", line.strip().upper()) for line in paragraphs]

        for marker in self.TITLE_END_PRIORITY:
            marker_upper = re.sub(r"\s+", " ", marker.upper())
            for idx, line in enumerate(normalized):
                if marker_upper in line:
                    return idx

        return None

    def _extract_text_blocks(self, doc: Document) -> list[str]:
        """Извлекает текстовые блоки документа (абзацы и таблицы) в исходном порядке."""
        blocks: list[str] = []
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        for child in doc.element.body.iterchildren():
            if isinstance(child, CT_P):
                paragraph = Paragraph(child, doc)
                raw_text = paragraph.text
                if raw_text and raw_text.strip():
                    # Сохраняем ведущие пробелы для правил, где важен левый отступ
                    # (например, TERMS-004), но убираем хвостовые пробелы/переводы.
                    blocks.append(raw_text.rstrip())
                continue

            if isinstance(child, CT_Tbl):
                table = Table(child, doc)
                for row in table.rows:
                    cells = [
                        cell.text.rstrip()
                        for cell in row.cells
                        if cell.text and cell.text.strip()
                    ]
                    if not cells:
                        continue
                    # Храним строку таблицы как TSV-подобную запись для последующего парсинга.
                    blocks.append("\t".join(cells))
                continue

            # Авто-оглавление Word часто хранится в content control (w:sdt),
            # а не как обычные параграфы body. Подхватываем такие строки отдельно.
            if str(child.tag).endswith("}sdt"):
                instr_nodes = child.findall(f".//{{{w_ns}}}instrText")
                instr_payload = " ".join((n.text or "") for n in instr_nodes).upper()
                is_toc_sdt = ("TOC" in instr_payload) or ("PAGEREF" in instr_payload)
                if not is_toc_sdt:
                    continue

                for p in child.findall(f".//{{{w_ns}}}p"):
                    parts = [t.text for t in p.findall(f".//{{{w_ns}}}t") if t.text]
                    text = "".join(parts).strip()
                    if text:
                        # Для авто-TOC восстанавливаем разделитель только по фактическим XML-маркерам.
                        # Иначе Word-строки вида "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ5" ложно валят CONTENTS-008,
                        # хотя визуальный разделитель в документе есть (tab + dot leader).
                        m = re.match(r"^(?P<title>.+?)\s*(?P<page>[+-]?\d+)\s*$", text)
                        if m:
                            title = m.group("title").strip()
                            page = m.group("page").strip()

                            # Важно: учитываем только фактическую табуляцию в тексте (w:r/w:tab),
                            # а не tab-stop в свойствах абзаца (w:tabs/w:tab).
                            has_tab_node = bool(p.findall(f".//{{{w_ns}}}r/{{{w_ns}}}tab"))
                            tab_stops = p.findall(f".//{{{w_ns}}}tabs/{{{w_ns}}}tab")
                            has_dot_leader = any(
                                (ts.attrib.get(f"{{{w_ns}}}leader", "").lower() == "dot")
                                for ts in tab_stops
                            )

                            if has_tab_node and has_dot_leader:
                                blocks.append(f"{title} .... {page}")
                            elif has_tab_node:
                                blocks.append(f"{title}\t{page}")
                            else:
                                blocks.append(text)
                        else:
                            blocks.append(text)

        return blocks
    
    def _find_sections(self, paragraphs: list[str]) -> dict[str, str]:
        """Находит секции документа (РЕФЕРАТ, ВВЕДЕНИЕ и т.д.)"""
        sections = {}
        current_section = None
        current_text = []

        def _is_contents_section(section_name: str | None) -> bool:
            if not section_name:
                return False
            return SECTION_CONTENTS in section_name.upper()

        def _is_references_section(section_name: str | None) -> bool:
            if not section_name:
                return False
            return SECTION_REFERENCES in section_name.upper()

        for para in paragraphs:
            # Внутри "СОДЕРЖАНИЕ" строки вида "ВВЕДЕНИЕ ... 9" или
            # "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ 67" являются элементами оглавления,
            # а не началом новой секции.
            if _is_contents_section(current_section) and self._is_contents_item_line(para):
                current_text.append(para)
                continue

            # Внутри "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" строки вида
            # "4 Антопольский А.Б. ..." — это записи, а не заголовки разделов.
            if _is_references_section(current_section) and self._is_reference_item_line(para):
                current_text.append(para)
                continue

            # Проверяем, это заголовок секции?
            if self._is_section_header(para):
                # Сохраняем предыдущую секцию
                if current_section:
                    sections[current_section] = "\n".join(current_text)
                # Начинаем новую секцию
                current_section = para.strip()
                current_text = []
            elif current_section:
                # Проверяем, не началась ли основная часть (номер раздела)
                # Паттерны: "1 НАЗВАНИЕ", "1. НАЗВАНИЕ", "Глава 1"
                # ВАЖНО: внутри секции "СОДЕРЖАНИЕ" такие строки нормальны,
                # поэтому преждевременно секцию не обрываем.
                if self._is_main_section_start(para) and not _is_contents_section(current_section):
                    # Основная часть началась - сохраняем текущую секцию и прекращаем
                    sections[current_section] = "\n".join(current_text)
                    current_section = None
                    current_text = []
                    continue
                # Добавляем текст к текущей секции
                current_text.append(para)
        
        # Сохраняем последнюю секцию
        if current_section:
            sections[current_section] = "\n".join(current_text)
        
        return sections

    def _is_reference_item_line(self, text: str) -> bool:
        """Проверяет, является ли строка нумерованной записью списка источников."""
        # Форматы: "1 Автор", "1. Автор", "12 Название"
        # Макс. 3 цифры — чтобы годы (2006, 2009 и т.д.) не совпадали.
        return bool(RE_NUMBERED_LIST_ITEM_LINE.match(text.strip()))

    def _is_contents_item_line(self, text: str) -> bool:
        """Проверяет, является ли строка элементом оглавления с номером страницы."""
        text_strip = text.strip()
        if not text_strip:
            return False

        # Примеры:
        # "ВВЕДЕНИЕ 9"
        # "Глава 1. Теория........5"
        # "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ\t38"
        if not RE_LINE_ENDS_WITH_DIGITS.search(text_strip):
            return False

        # Должен быть некоторый текст до номера страницы.
        return bool(RE_NON_DIGIT_BEFORE_PAGE.search(text_strip))
    
    def _is_section_header(self, text: str) -> bool:
        """Проверяет, является ли текст заголовком секции."""
        text_strip = text.strip()
        text_upper = text_strip.upper()

        if self._is_appendix_header(text_strip):
            return True
        
        # Заголовок должен:
        # 1. Содержать ключевое слово
        # 2. Быть капсом
        # 3. Быть коротким (не более 60 символов - чтобы отсечь длинные строки)
        # 4. Не содержать точек/отточий (чтобы отличить от содержания)
        
        if len(text_strip) > 60:
            return False

        if not text_strip.isupper():
            return False
        
        # Проверяем что это чистое ключевое слово (или почти)
        for keyword in self.SECTION_KEYWORDS:
            if keyword in text_upper:
                # Убираем пробелы и сравниваем длину - должно быть близко к ключевому слову
                clean_text = text_upper.replace(' ', '').replace('\t', '')
                clean_keyword = keyword.replace(' ', '')
                # Допускаем небольшое отличие (например, добавочные пробелы)
                if abs(len(clean_text) - len(clean_keyword)) <= 5:
                    return True

        return False

    def _is_appendix_header(self, text: str) -> bool:
        """Проверяет, является ли строка заголовком приложения."""
        text_strip = text.strip()
        first_line = text_strip.splitlines()[0].strip() if text_strip else ""
        if len(text_strip) > 80:
            return False

        return bool(RE_APPENDIX_HEADER.match(first_line))
    
    def _is_main_section_start(self, text: str) -> bool:
        """Проверяет, началась ли основная часть (номер раздела)."""
        text = text.strip()
        return any(pattern.match(text) for pattern in RE_MAIN_SECTION_START_PATTERNS)

