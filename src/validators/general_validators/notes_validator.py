"""Валидатор правил оформления примечаний (NOTE-001..NOTE-007)."""

from ...models.document_structure import DocumentStructure
from ...models.validation_result import ValidationResult
from ...utils.common.rich_utils import format_indexed_examples
from ...utils.general_utils import (
    check_note_dash_numbering_consistency,
    check_note_group_header_plural_for_multiple,
    check_note_keyword_capitalized,
    check_note_numbering_without_dot,
    check_note_placement_near_related_material,
    check_note_starts_with_capital,
    check_note_unrecognized_pattern,
)
from ..base_validator import BaseValidator


class NotesValidator(BaseValidator):
    """Проверка оформления примечаний по rich-признакам."""

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="NotesValidator")
        rich_doc = document.rich_document

        if rich_doc is None:
            return result

        notes_features = list(getattr(rich_doc, "notes_features", []) or [])
        if not notes_features:
            # Нет примечаний: все правила остаются в SKIP.
            return result

        note_text_by_index: dict[int, str] = {}
        for note in notes_features:
            paragraph_index = int(getattr(note, "paragraph_index", -1))
            if paragraph_index < 0:
                continue

            preview = str(getattr(note, "raw_text", "") or "").strip()
            if not preview:
                kind = str(getattr(note, "note_kind", "") or "")
                preview = f"Примечание ({kind})"
            note_text_by_index.setdefault(paragraph_index, preview)

        def format_note_examples(paragraph_indexes: list[int], preview_limit: int = 3) -> str:
            return format_indexed_examples(
                note_text_by_index,
                paragraph_indexes,
                preview_limit=preview_limit,
            )

        invalid_unrecognized = check_note_unrecognized_pattern(notes_features)
        invalid_unrecognized_set = set(invalid_unrecognized)
        if invalid_unrecognized:
            result.add_rule(
                "NOTE-001",
                "FAIL",
                "Примечание найдено, но не соответствует шаблону."
                + format_note_examples(invalid_unrecognized),
            )

            # Остальные правила проверяем только для примечаний,
            # прошедших базовую шаблонную валидацию NOTE-001.
            notes_for_followup = [
                note
                for note in notes_features
                if int(getattr(note, "paragraph_index", -1)) not in invalid_unrecognized_set
            ]
            if not notes_for_followup:
                return result
        else:
            result.add_rule("NOTE-001", "OK")
            notes_for_followup = notes_features

        invalid_placement = check_note_placement_near_related_material(notes_for_followup)
        if invalid_placement:
            result.add_rule(
                "NOTE-002",
                "FAIL",
                "Примечание должно быть размещено сразу после связанного материала (рисунок/таблица)."
                + format_note_examples(invalid_placement),
            )
        else:
            result.add_rule("NOTE-002", "OK")

        invalid_keyword_capitalized = check_note_keyword_capitalized(notes_for_followup)
        if invalid_keyword_capitalized:
            result.add_rule(
                "NOTE-003",
                "FAIL",
                "Слово \"Примечание\" или \"Примечания\" должно начинаться с прописной буквы."
                + format_note_examples(invalid_keyword_capitalized),
            )
        else:
            result.add_rule("NOTE-003", "OK")

        invalid_text_capitalized = check_note_starts_with_capital(notes_for_followup)
        if invalid_text_capitalized:
            result.add_rule(
                "NOTE-004",
                "FAIL",
                "Текст примечания должен начинаться с прописной буквы."
                + format_note_examples(invalid_text_capitalized),
            )
        else:
            result.add_rule("NOTE-004", "OK")

        invalid_plural_header = check_note_group_header_plural_for_multiple(notes_for_followup)
        if invalid_plural_header:
            result.add_rule(
                "NOTE-005",
                "FAIL",
                "Если примечаний несколько, должен использоваться заголовок \"Примечания\"."
                + format_note_examples(invalid_plural_header),
            )
        else:
            result.add_rule("NOTE-005", "OK")

        invalid_dash_numbering = check_note_dash_numbering_consistency(notes_for_followup)
        if invalid_dash_numbering:
            result.add_rule(
                "NOTE-006",
                "FAIL",
                "В примечаниях тире и нумерация должны использоваться согласованно."
                + format_note_examples(invalid_dash_numbering),
            )
        else:
            result.add_rule("NOTE-006", "OK")

        invalid_dot_after_number = check_note_numbering_without_dot(notes_for_followup)
        if invalid_dot_after_number:
            result.add_rule(
                "NOTE-007",
                "FAIL",
                "В нумерованных примечаниях после номера не ставится точка."
                + format_note_examples(invalid_dot_after_number),
            )
        else:
            result.add_rule("NOTE-007", "OK")

        return result
