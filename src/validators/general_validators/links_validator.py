"""Валидатор правил ссылок (LINK-001..LINK-003)."""

from ...models.document_structure import DocumentStructure
from ...models.validation_result import ValidationResult
from ...utils.common.rich_utils import format_indexed_examples
from ...utils.general_utils import (
    check_figure_link_before_caption,
    check_links_resolve_to_existing_targets,
    check_table_link_before_table,
)
from ..base_validator import BaseValidator


class LinksValidator(BaseValidator):
    """Проверка ссылок на рисунки/таблицы/формулы/источники."""

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="LinksValidator")
        rich_doc = document.rich_document

        if rich_doc is None:
            return result

        links_features = list(getattr(rich_doc, "links_features", []) or [])
        if not links_features:
            return result

        figure_caption_features = list(getattr(rich_doc, "figure_caption_features", []) or [])
        table_features = list(getattr(rich_doc, "table_features", []) or [])

        link_text_by_index: dict[int, str] = {}
        for link in links_features:
            paragraph_index = getattr(link, "paragraph_index", None)
            if paragraph_index is None:
                continue
            paragraph_index = int(paragraph_index)

            link_type = str(getattr(link, "link_type", "") or "").strip()
            target_number = str(getattr(link, "target_number", "") or "").strip()
            raw_text = str(getattr(link, "raw_text", "") or "").strip()
            preview = raw_text or f"Ссылка {link_type}:{target_number}" if target_number else f"Ссылка {link_type}@p{paragraph_index}"
            link_text_by_index[paragraph_index] = preview

        def format_link_examples(paragraph_indexes: list[int], preview_limit: int = 3) -> str:
            return format_indexed_examples(
                link_text_by_index,
                paragraph_indexes,
                preview_limit=preview_limit,
            )
        
        resolvable_links = [
            link
            for link in links_features
            if getattr(link, "link_type", None) in {"source", "figure", "table", "formula"}
        ]
        if resolvable_links:
            invalid_resolved = check_links_resolve_to_existing_targets(resolvable_links)
            if invalid_resolved:
                result.add_rule(
                    "LINK-001",
                    "FAIL",
                    "Ссылки должны указывать на существующие объекты или источники."
                    + format_link_examples(invalid_resolved),
                )
            else:
                result.add_rule("LINK-001", "OK")

            resolved_links = [
                link
                for link in resolvable_links
                if getattr(link, "resolved_in_target_list", None) is not False
                and getattr(link, "resolved_with_object", None) is not False
            ]
                
            table_links = [link for link in resolved_links if getattr(link, "link_type", None) == "table"]
            if table_links:
                invalid_table_before = check_table_link_before_table(table_links, table_features)
                if invalid_table_before:
                    result.add_rule(
                        "LINK-002",
                        "FAIL",
                        "Ссылка на таблицу должна идти до соответствующей таблицы."
                        + format_link_examples(invalid_table_before),
                    )
                else:
                    result.add_rule("LINK-002", "OK")

            figure_links = [link for link in resolved_links if getattr(link, "link_type", None) == "figure"]
            if figure_links:
                invalid_figure_before = check_figure_link_before_caption(figure_links, figure_caption_features)
                if invalid_figure_before:
                    result.add_rule(
                        "LINK-003",
                        "FAIL",
                        "Ссылка на рисунок должна располагаться до соответствующей подписи."
                        + format_link_examples(invalid_figure_before),
                    )
                else:
                    result.add_rule("LINK-003", "OK")

        return result
