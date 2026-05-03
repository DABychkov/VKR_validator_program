"""Валидатор правил оформления таблиц (TABLE-001..TABLE-007)."""

from ...models.document_structure import DocumentStructure
from ...models.validation_result import ValidationResult
from ...utils.common.rich_utils import format_indexed_examples
from ...utils.general_utils import (
    check_table_header_cells_capital,
    check_table_header_cells_no_period,
    check_table_no_diagonal_borders,
    check_table_number_pattern,
    check_table_title_capital_no_period,
    check_table_title_dash_separator,
    check_table_title_position_left,
    has_non_empty_table_header_cells,
    has_table_caption,
    has_table_caption_and_number,
    has_table_title_name,
    is_service_terms_abbr_table,
)
from ..base_validator import BaseValidator


class TableValidator(BaseValidator):
    """Проверка оформления таблиц по rich-признакам."""

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="TableValidator")
        rich_doc = document.rich_document

        if rich_doc is None:
            return result

        table_features = list(getattr(rich_doc, "table_features", []) or [])
        if not table_features:
            return result

        table_features = [
            table
            for table in table_features
            if not is_service_terms_abbr_table(table)
        ]
        if not table_features:
            return result

        table_text_by_index: dict[int, str] = {}
        for table in table_features:
            table_index = int(getattr(table, "table_index", -1))
            if table_index < 0:
                continue

            title_text = str(getattr(table, "title_above_text", "") or "").strip()
            table_number = str(getattr(table, "number", "") or "").strip()
            preview = title_text or (f"Таблица {table_number}" if table_number else f"Таблица #{table_index}")
            table_text_by_index.setdefault(table_index, preview)

        def format_table_examples(table_indexes: list[int], preview_limit: int = 3) -> str:
            return format_indexed_examples(
                table_text_by_index,
                table_indexes,
                preview_limit=preview_limit,
            )

        tables_with_caption = [
            table
            for table in table_features
            if has_table_caption(table)
        ]
        if tables_with_caption:
            invalid_title_position_left = check_table_title_position_left(tables_with_caption)
            if invalid_title_position_left:
                result.add_rule(
                    "TABLE-001",
                    "FAIL",
                    "Подпись таблицы должна быть расположена сверху и выровнена влево."
                    + format_table_examples(invalid_title_position_left),
                )
            else:
                result.add_rule("TABLE-001", "OK")

        tables_with_caption_and_number = [
            table
            for table in table_features
            if has_table_caption_and_number(table)
        ]
        if tables_with_caption_and_number:
            invalid_number_pattern = check_table_number_pattern(tables_with_caption_and_number)
            if invalid_number_pattern:
                result.add_rule(
                    "TABLE-002",
                    "FAIL",
                    "Подпись таблицы должна соответствовать паттерну: 1 / 1.1 / А.3 (в приложении)."
                    + format_table_examples(invalid_number_pattern),
                )
            else:
                result.add_rule("TABLE-002", "OK")

        tables_with_title_name = [
            table
            for table in table_features
            if has_table_title_name(table)
        ]
        if tables_with_title_name:
            invalid_title_dash_separator = check_table_title_dash_separator(tables_with_title_name)
            if invalid_title_dash_separator:
                result.add_rule(
                    "TABLE-003",
                    "FAIL",
                    "Наименование таблицы (при наличии) должно приводиться через тире."
                    + format_table_examples(invalid_title_dash_separator),
                )
            else:
                result.add_rule("TABLE-003", "OK")

            invalid_title_capital_no_period = check_table_title_capital_no_period(tables_with_title_name)
            if invalid_title_capital_no_period:
                result.add_rule(
                    "TABLE-004",
                    "FAIL",
                    "Наименование таблицы (при наличии) должно начинаться с прописной буквы и не заканчиваться точкой."
                    + format_table_examples(invalid_title_capital_no_period),
                )
            else:
                result.add_rule("TABLE-004", "OK")

        invalid_diagonal = check_table_no_diagonal_borders(table_features)
        if invalid_diagonal:
            result.add_rule(
                "TABLE-005",
                "FAIL",
                "В таблице должны отсутствовать диагональные линии."
                + format_table_examples(invalid_diagonal),
            )
        else:
            result.add_rule("TABLE-005", "OK")

        tables_with_headers = [
            table
            for table in table_features
            if has_non_empty_table_header_cells(table)
        ]
        if tables_with_headers:
            invalid_header_capital = check_table_header_cells_capital(tables_with_headers)
            if invalid_header_capital:
                result.add_rule(
                    "TABLE-006",
                    "FAIL",
                    "Заголовки граф должны начинаться с прописной буквы."
                    + format_table_examples(invalid_header_capital),
                )
            else:
                result.add_rule("TABLE-006", "OK")

            invalid_header_no_period = check_table_header_cells_no_period(tables_with_headers)
            if invalid_header_no_period:
                result.add_rule(
                    "TABLE-007",
                    "FAIL",
                    "Заголовки граф не должны заканчиваться точкой."
                    + format_table_examples(invalid_header_no_period),
                )
            else:
                result.add_rule("TABLE-007", "OK")

        return result
