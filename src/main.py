"""Точка входа: валидация документов по ГОСТ 7.32-2017."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.models.rich_document_structure import RichDocumentStructure
from src.services.document_parser import DocumentParser
from src.services.rich_parser import RichParser
from src.services.validation_service import ValidationService
from src.validators.title_page_validators import TitlePageValidator
from src.validators.executor_list_validator import ExecutorListValidator
from src.validators.abstract_validator import AbstractValidator
from src.validators.contents_validator import ContentsValidator
from src.validators.terms_validator import TermsValidator
from src.validators.abbreviations_validator import AbbreviationsValidator
from src.validators.references_validator import ReferencesValidator
from src.validators.appendices_validator import AppendicesValidator
from src.validators.general_validators import FigureValidator, FootnotesValidator, FormulaValidator, GeneralRequirementsValidator, LinksValidator, NotesValidator, TableValidator
from src.models.validation_result import Severity


def print_rich_summary(rich_doc: RichDocumentStructure) -> None:
    """Печатает краткую сводку rich-признаков в обычном режиме валидации."""
    print("\n" + "=" * 60)
    print("RICH SUMMARY")
    print("=" * 60)
    print(f"Секций страниц: {len(rich_doc.pages_settings)}")
    print(f"Абзацев: {len(rich_doc.paragraph_features)}")
    print(f"Таблиц: {len(rich_doc.table_features)}")
    print(f"Подписей рисунков: {len(rich_doc.figure_caption_features)}")
    print(f"Формул: {len(rich_doc.formula_features)}")
    print(f"Ссылок: {len(rich_doc.links_features)}")
    print(f"Примечаний: {len(rich_doc.notes_features)}")
    print(f"Сносок: {len(rich_doc.footnote_features)}")
    print(f"TOC entries (Word auto): {len(rich_doc.toc_entries)}")


def print_rule_results_table(validator_name: str, results) -> None:
    """Печатает список правил валидатора в табличном виде."""
    if not results:
        print("\n  RULES: каталог не подключен")
        return

    print("\n  RULES:")
    print("    ID           | SEVERITY       | STATUS   | IMPLEMENTED | MESSAGE")
    print("    " + "-" * 78)
    for rule in results:
        message = (rule.message or "").replace("\n", " ").strip()
        if len(message) > 100:
            message = message[:100] + "..."
        print(
            "    "
            f"{rule.rule_id:<12} | "
            f"{rule.severity:<14} | "
            f"{rule.status:<8} | "
            f"{str(rule.implemented):<11} | "
            f"{message}"
        )


def debug_rich_document(file_path: str) -> None:
    """Печатает debug-отчет rich-признаков (этап 1-2)."""
    parser = RichParser()
    rich_doc = parser.parse(file_path)

    print("\n" + "=" * 60)
    print("RICH DEBUG REPORT (ЭТАП 1-2)")
    print("=" * 60)
    print(f"Файл: {rich_doc.source_file}")
    print(f"Секций: {len(rich_doc.pages_settings)}")
    print(f"Абзацев: {len(rich_doc.paragraph_features)}")
    print(f"Футеров: {len(rich_doc.footer_features)}")
    print(f"Таблиц: {len(rich_doc.table_features)}")
    print(f"Подписей рисунков: {len(rich_doc.figure_caption_features)}")
    print(f"Формул: {len(rich_doc.formula_features)}")
    print(f"Ссылок: {len(rich_doc.links_features)}")
    print(f"Примечаний: {len(rich_doc.notes_features)}")
    print(f"Сносок: {len(rich_doc.footnote_features)}")
    print(f"TOC entries (Word auto): {len(rich_doc.toc_entries)}")

    print("\nПараметры страниц по секциям:")
    for section in rich_doc.pages_settings:
        print(
            "  "
            f"section={section.section_index}, "
            f"start={section.start_type}, "
            f"A={section.page_width_mm}x{section.page_height_mm} мм, "
            f"margins(L/R/T/B)={section.margin_left_mm}/{section.margin_right_mm}/"
            f"{section.margin_top_mm}/{section.margin_bottom_mm} мм"
        )

    print("\nПризнаки пагинации в футерах:")
    for footer in rich_doc.footer_features:
        print(
            "  "
            f"section={footer.section_index}, "
            f"has_PAGE={footer.has_page_field}, "
            f"fmt={footer.page_field_format}, "
            f"align={footer.alignment}, "
            f"restart={footer.restart_numbering}, "
            f"start={footer.start_number}"
        )

    print("\nПервые 100 абзацев:")
    for para in rich_doc.paragraph_features[:300]:
        snippet = para.text.replace("\n", " ").strip()
        if len(snippet) > 70:
            snippet = f"{snippet[:67]}..."
        print(
            "  "
            f"#{para.block_index} align={para.alignment} "
            f"indent(first/left/right)={para.first_line_indent_mm}/{para.left_indent_mm}/{para.right_indent_mm} мм "
            f"style_name={para.style_name} "
            #f"first_run={para.runs_features} "
            f"line={para.line_spacing} "
            f"section={para.section_hint} "
            f"bold={para.bold_ratio} italic={para.italic_ratio} "
            f"runs={len(para.runs_features)} text='{snippet}'"
        )

    print("\nПервые 6 таблиц:")
    for table in rich_doc.table_features[:6]:
        title = (table.title_above_text or "")[:60]
        header_runs_count = sum(len(cell.runs_features) for cell in table.header_row_cells)
        first_col_runs_count = sum(len(cell.runs_features) for cell in table.first_column_cells)
        header_text_preview = " | ".join(
            cell.text for cell in table.header_row_cells if cell.text
        )[:80]
        first_col_preview = " | ".join(
            cell.text for cell in table.first_column_cells if cell.text
        )[:80]
        print(
            "  "
            f"table={table.table_index} "
            f"section={table.section_hint} "
            f"size={table.rows_count}x{table.cols_count} "
            f"num={table.number} "
            f"num_pattern={table.number_pattern} "
            f"title_pos={table.title_relative_position} "
            f"in_appendix={table.in_appendix} "
            f"inside(H/V)={table.has_inside_horizontal_borders}/{table.has_inside_vertical_borders} "
            f"outer(T/B/L/R)={table.has_outer_top_border}/{table.has_outer_bottom_border}/"
            f"{table.has_outer_left_border}/{table.has_outer_right_border} "
            f"diag={table.has_diagonal_borders} "
            f"header_cells={len(table.header_row_cells)} "
            f"header_runs={header_runs_count} "
            f"first_col_cells={len(table.first_column_cells)} "
            f"first_col_runs={first_col_runs_count} "
            f"title='{title}'"
        )
        if header_text_preview:
            print(f"    header_preview='{header_text_preview}'")
        if first_col_preview:
            print(f"    first_col_preview='{first_col_preview}'")

    print("\nПервые 15 подписей рисунков:")
    for caption in rich_doc.figure_caption_features[:15]:
        text = caption.caption_text[:80]
        print(
            "  "
            f"p={caption.paragraph_index} "
            f"num={caption.caption_number} "
            f"align={caption.alignment} "
            f"dash={caption.has_dash_separator} "
            f"period={caption.ends_with_period} "
            f"near_drawing={caption.has_nearby_drawing} "
            f"drawing_pos={caption.drawing_relative_position} "
            f"text='{text}' "
            f"pattern={caption.pattern_type} "
            f"in_appendix={caption.in_appendix} "
        )

    print("\nПервые 10 формул:")
    for formula in rich_doc.formula_features[:10]:
        print(
            "  "
            f"p={formula.paragraph_index} "
            f"align={formula.alignment} "
            f"num={formula.number} "
            f"num_pattern={formula.number_pattern} "
            f"num_right={formula.number_alignment_right} "
            f"blank_before={formula.has_blank_line_before} "
            f"blank_after={formula.has_blank_line_after} "
            f"where={formula.has_explanation_where} "
            f"has_omml={formula.omml_xml is not None} "
            f"text='{formula.formula_text[:80]}'"
        )

    print("\nПервые 10 ссылок:")
    for link in rich_doc.links_features[:10]:
        print(
            "  "
            f"p={link.paragraph_index} "
            f"type={link.link_type} "
            f"target={link.target_number} "
            f"range={link.is_range} "
            f"resolved={link.resolved_in_target_list} "
            f"resolved_with_object={link.resolved_with_object} "
            f"raw='{link.raw_text}'"
            f"pos_to_elem={link.relative_position_to_target}"
        )

    print("\nПервые 10 примечаний:")
    for note in rich_doc.notes_features[:10]:
        print(
            "  "
            f"p={note.paragraph_index} "
            f"kind={note.note_kind} "
            f"dot_after_num={note.has_dot_after_number} "
            f"num={note.item_number} "
            f"dash={note.has_dash_separator} "
            f"near_figure={note.near_figure_caption} "
            f"near_table={note.near_table_caption} "
            f"raw='{note.raw_text[:90]}'"
        )

    print("\nПервые 10 сносок:")
    for footnote in rich_doc.footnote_features[:10]:
        print(
            "  "
            f"p={footnote.paragraph_index} "
            f"type={footnote.marker_type} "
            f"marker={footnote.marker_text} "
            f"id={footnote.footnote_id} "
            f"custom={footnote.custom_mark_follows} "
            f"resolved={footnote.resolved_in_footnotes_part} "
            f"sep_line={footnote.has_separator_line} "
            f"sep_short_left={footnote.separator_short_left_heuristic}"
        )

    print("\nВстроенное оглавление Word:")
    if not rich_doc.toc_entries:
        print("  не найдены")
    else:
        for idx, entry in enumerate(rich_doc.toc_entries, start=1):
            print(
                "  "
                f"#{idx} p={entry.paragraph_index} "
                f"parse_ok={entry.parse_ok} "
                f"toc_field={entry.has_toc_field} "
                f"hyperlink={entry.has_hyperlink} "
                f"title={repr(entry.title)} "
                f"page={entry.page} "
                f"raw={repr(entry.raw_text)}"
            )


def validate_document(file_path: str) -> None:
    """Валидирует документ по ГОСТ 7.32-2017."""
    parser = DocumentParser()
    doc = parser.parse(file_path)
    rich_doc = RichParser().parse(file_path)
    doc.rich_document = rich_doc

    # В обычном режиме печатаем краткую сводку rich-признаков.
    print_rich_summary(rich_doc)

    # Показываем найденные секции
    print(f"\nФайл: {doc.filename}")
    print(f"Найдено секций: {len(doc.sections)}")
    if doc.sections:
        print("  Секции документа:", ", ".join(doc.sections.keys()))

    # Регистрируем валидаторы
    service = ValidationService()
    service.register(TitlePageValidator())
    service.register(ExecutorListValidator())
    service.register(AbstractValidator())
    service.register(ContentsValidator())
    service.register(TermsValidator())
    service.register(AbbreviationsValidator())
    service.register(ReferencesValidator())
    service.register(AppendicesValidator())
    service.register(GeneralRequirementsValidator())
    service.register(FigureValidator())
    service.register(TableValidator())
    service.register(FormulaValidator())
    service.register(LinksValidator())
    service.register(NotesValidator())
    service.register(FootnotesValidator())

    # Запускаем проверку
    results = service.validate(doc)

    # Выводим результаты
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
    print("="*60)
    
    for res in results:
        # Если ошибок нет - не выводим
        if not res.has_errors():
            print(f"\n{res.validator_name}: ВСЕ OK")
            print_rule_results_table(res.validator_name, res.rule_results)
            continue
        
        # Иначе выводим ошибки по категориям
        print(f"\n{res.validator_name}:")
        
        # Критические ошибки
        critical = [err for err in res.errors if err[0] == Severity.CRITICAL]
        if critical:
            print("\n  КРИТИЧЕСКИЕ ОШИБКИ (обязательно по ГОСТ):")
            for _, msg in critical:
                print(f"     - {msg}")
        
        # Рекомендации
        recommendations = [err for err in res.errors if err[0] == Severity.RECOMMENDATION]
        if recommendations:
            print("\n  РЕКОМЕНДАЦИИ (желательно исправить):")
            for _, msg in recommendations:
                print(f"     - {msg}")

        print_rule_results_table(res.validator_name, res.rule_results)


def main():
    """Интерактивный режим валидации."""
    print("=" * 60)
    print("ВАЛИДАТОР ГОСТ 7.32-2017")
    print("Проверка титульного листа и структуры документа")
    print("=" * 60)
    print("\nКоманды:")
    print("  1) <path.docx>          - обычная валидация")
    print("  2) rich <path.docx>     - rich debug (этап 1-2)")
    print("  3) exit                 - выход")
    
    while True:
        path = input("\n> ").strip()
        
        if path.lower() in {"exit", "quit", "выход"}:
            print("Завершение работы")
            break
        
        if not path:
            continue

        is_rich_mode = True
        target_path = path
        if path.lower().startswith("rich "):
            is_rich_mode = True
            target_path = path[5:].strip()

        if not target_path:
            print("Укажите путь к файлу после команды")
            continue
        
        if not os.path.exists(target_path):
            print("Файл не найден")
            continue
        
        try:
            if is_rich_mode:
                debug_rich_document(target_path)
            else:
                validate_document(target_path)
        except Exception as exc:
            print(f"Ошибка: {exc}")


if __name__ == "__main__":
    main()
