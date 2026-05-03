"""Валидатор правил оформления формул (FORMULA-001..FORMULA-005)."""

from ...models.document_structure import DocumentStructure
from ...models.validation_result import ValidationResult
from ...utils.common.rich_utils import format_indexed_examples
from ...utils.general_utils import (
    check_formula_centered,
    check_formula_line_and_spacing,
    check_formula_number_pattern,
    check_formula_number_right,
    check_formula_where_format,
    has_formula_number,
)
from ..base_validator import BaseValidator


class FormulaValidator(BaseValidator):
    """Проверка оформления формул по rich-признакам."""

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="FormulaValidator")
        rich_doc = document.rich_document

        if rich_doc is None:
            return result

        formula_features = list(getattr(rich_doc, "formula_features", []) or [])
        if not formula_features:
            return result

        formula_text_by_index: dict[int, str] = {}
        for formula in formula_features:
            paragraph_index = int(getattr(formula, "paragraph_index", -1))
            if paragraph_index < 0:
                continue

            number = str(getattr(formula, "number", "") or "").strip()
            preview = f"Формула {number}" if number else f"Формула @p{paragraph_index}"
            formula_text_by_index.setdefault(paragraph_index, preview)

        def format_formula_examples(paragraph_indexes: list[int], preview_limit: int = 3) -> str:
            return format_indexed_examples(
                formula_text_by_index,
                paragraph_indexes,
                preview_limit=preview_limit,
            )

        invalid_line_and_spacing = check_formula_line_and_spacing(formula_features)
        if invalid_line_and_spacing:
            result.add_rule(
                "FORMULA-001",
                "FAIL",
                "Формула должна быть на отдельной строке с корректными отбивками до и после."
                + format_formula_examples(invalid_line_and_spacing),
            )
        else:
            result.add_rule("FORMULA-001", "OK")

        formulas_with_where_marker = [
            formula
            for formula in formula_features
            if bool(getattr(formula, "has_where_marker", False))
        ]
        if formulas_with_where_marker:
            invalid_where_format = check_formula_where_format(formulas_with_where_marker)
            if invalid_where_format:
                result.add_rule(
                    "FORMULA-002",
                    "FAIL",
                    "Пояснение с \"где\" должно быть оформлено корректно."
                    + format_formula_examples(invalid_where_format),
                )
            else:
                result.add_rule("FORMULA-002", "OK")

        formulas_with_number = [
            formula
            for formula in formula_features
            if has_formula_number(formula)
        ]
        if formulas_with_number:
            invalid_number_right = check_formula_number_right(formulas_with_number)
            if invalid_number_right:
                result.add_rule(
                    "FORMULA-003",
                    "FAIL",
                    "Номер формулы должен быть расположен справа."
                    + format_formula_examples(invalid_number_right),
                )
            else:
                result.add_rule("FORMULA-003", "OK")

            invalid_centered = check_formula_centered(formulas_with_number)
            if invalid_centered:
                result.add_rule(
                    "FORMULA-004",
                    "FAIL",
                    "Формула должна быть выровнена по центру."
                    + format_formula_examples(invalid_centered),
                )
            else:
                result.add_rule("FORMULA-004", "OK")

            invalid_number_pattern = check_formula_number_pattern(formulas_with_number)
            if invalid_number_pattern:
                result.add_rule(
                    "FORMULA-005",
                    "FAIL",
                    "Номер формулы должен соответствовать допустимому шаблону."
                    + format_formula_examples(invalid_number_pattern),
                )
            else:
                result.add_rule("FORMULA-005", "OK")

        return result
