"""Валидатор правил оформления сносок (FOOT-001..FOOT-003)."""

from ...models.document_structure import DocumentStructure
from ...models.validation_result import ValidationResult
from ...utils.common.rich_utils import format_indexed_examples
from ...utils.general_utils import (
    check_footnote_markers_resolved,
    check_footnote_markers_resolution_unknown,
    check_footnote_separator_present,
    check_footnote_separator_short_left,
    check_footnote_separator_short_left_unknown,
    check_footnote_separator_unknown,
    has_any_footnotes,
)
from ..base_validator import BaseValidator


class FootnotesValidator(BaseValidator):
    """Проверка оформления сносок по rich-флагам."""

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="FootnotesValidator")
        rich_doc = document.rich_document

        if rich_doc is None:
            return result

        footnote_features = list(getattr(rich_doc, "footnote_features", []) or [])

        if not has_any_footnotes(footnote_features):
            return result

        footnote_text_by_index: dict[int, str] = {}
        for footnote in footnote_features:
            paragraph_index = int(getattr(footnote, "paragraph_index", -1))
            if paragraph_index < 0:
                continue

            marker_text = str(getattr(footnote, "marker_text", "") or "").strip()
            footnote_id = getattr(footnote, "footnote_id", None)
            is_custom_mark = bool(getattr(footnote, "custom_mark_follows", False))

            if marker_text:
                preview = marker_text
            elif footnote_id is not None and not is_custom_mark:
                preview = str(footnote_id)
            else:
                preview = "?"

            footnote_text_by_index.setdefault(paragraph_index, preview)

        def format_footnote_examples(paragraph_indexes: list[int], preview_limit: int = 3) -> str:
            return format_indexed_examples(
                footnote_text_by_index,
                paragraph_indexes,
                preview_limit=preview_limit,
            )

        # FOOT-001
        invalid_markers_resolved = check_footnote_markers_resolved(footnote_features)
        if invalid_markers_resolved:
            result.add_rule(
                "FOOT-001",
                "FAIL",
                "Маркер сноски должен резолвиться в блок сносок."
                + format_footnote_examples(invalid_markers_resolved),
            )
        else:
            unknown_markers_resolved = check_footnote_markers_resolution_unknown(footnote_features)
            if unknown_markers_resolved:
                return result
            else:
                result.add_rule("FOOT-001", "OK")

        invalid_separator_present = check_footnote_separator_present(footnote_features)
        if invalid_separator_present:
            result.add_rule(
                "FOOT-002",
                "FAIL",
                "При наличии сносок должна быть обнаружена разделительная линия."
                + format_footnote_examples(invalid_separator_present),
            )
            # Если линия не найдена, проверка ее "короткости" не имеет смысла.
            return result
        else:
            unknown_separator_present = check_footnote_separator_unknown(footnote_features)
            if unknown_separator_present:
                # При неизвестном наличии линии короткость также не проверяем.
                return result
            else:
                result.add_rule("FOOT-002", "OK")

        invalid_separator_short = check_footnote_separator_short_left(footnote_features)
        if invalid_separator_short:
            result.add_rule(
                "FOOT-003",
                "FAIL",
                "Разделительная линия сносок должна быть короткой."
                + format_footnote_examples(invalid_separator_short),
            )
        else:
            unknown_separator_short = check_footnote_separator_short_left_unknown(footnote_features)
            if unknown_separator_short:
                return result
            else:
                result.add_rule("FOOT-003", "OK")

        return result
