"""Валидатор раздела 1.10 "ПРИЛОЖЕНИЯ"."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.validation_constants import (
    APPENDIX_SECTION_KEYWORDS,
    CONTENTS_SECTION_KEYWORDS,
    SECTION_APPENDIX,
)
from ..config.regex_patterns import RE_APPENDIX_HEADER
from ..utils.appendices_validation_utils import (
    check_contents_mentions,
    check_designation_sequence,
    extract_label,
    extract_status_line_with_fallback,
    extract_title_with_rich_fallback,
    is_valid_label,
)
from ..utils.common.section_utils import (
    find_section_entries_by_keywords,
    find_section_text_by_keywords,
    get_non_empty_lines,
)
from .base_validator import BaseValidator


class AppendicesValidator(BaseValidator):
    """Проверка структурного элемента 1.10 по ТЗ."""

    APPENDIX_KEYWORD = SECTION_APPENDIX
    INVALID_CYRILLIC_LABELS = {"Ё", "З", "Й", "О", "Ч", "Ъ", "Ы", "Ь"}
    INVALID_LATIN_LABELS = {"I", "O"}
    APPENDIX_HEADER_RE = RE_APPENDIX_HEADER

    @staticmethod
    def _format_labels(labels: list[str]) -> str:
        unique_labels = sorted(set(labels), key=labels.index)
        return ", ".join(f'"{label}"' for label in unique_labels)

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="AppendicesValidator")

        appendix_sections = find_section_entries_by_keywords(
            document.sections,
            APPENDIX_SECTION_KEYWORDS,
            match_mode="startswith",
        )
        if not appendix_sections:
            result.add_rule(
                "APPX-001",
                "FAIL",
                'Разделы приложений не найдены. Ожидаются заголовки формата '
                '"ПРИЛОЖЕНИЕ А" или "ПРИЛОЖЕНИЕ 1". '
                'Если в отчете есть дополнительные материалы, рекомендуется оформить их как приложения.',
            )
            return result

        result.add_rule("APPX-001", "OK")

        contents_text = find_section_text_by_keywords(document.sections, CONTENTS_SECTION_KEYWORDS)
        rich_doc = document.rich_document

        appendix_entries: list[tuple[str, str | None, str]] = []
        sequence_labels: list[str] = []
        label_parse_fail_headers: list[str] = []
        invalid_labels: list[str] = []
        missing_status_labels: list[str] = []
        empty_content_labels: list[str] = []
        missing_title_labels: list[str] = []
        title_with_dot_labels: list[str] = []

        for header, section_text in appendix_sections:
            label = extract_label(header, self.APPENDIX_HEADER_RE)
            status_line = extract_status_line_with_fallback(header, section_text)
            title, consumed_title_lines = extract_title_with_rich_fallback(
                header,
                section_text,
                rich_doc,
            )
            if not label:
                label_parse_fail_headers.append(header)
                continue

            if not is_valid_label(label, self.INVALID_CYRILLIC_LABELS, self.INVALID_LATIN_LABELS):
                invalid_labels.append(label)
                appendix_entries.append((label, title, header))
            else:
                sequence_labels.append(label)
                appendix_entries.append((label, title, header))

            if not status_line:
                missing_status_labels.append(label)

            lines = get_non_empty_lines(section_text, strip=True)
            content_lines = lines[consumed_title_lines:]
            if not content_lines:
                empty_content_labels.append(label)

            if not title:
                missing_title_labels.append(label)

            if title and title.endswith("."):
                title_with_dot_labels.append(label)

        if label_parse_fail_headers or invalid_labels:
            parts: list[str] = []
            if label_parse_fail_headers:
                headers_text = "; ".join(f'"{header}"' for header in label_parse_fail_headers)
                parts.append(
                    "Не удалось определить обозначение в заголовках: "
                    f"{headers_text}."
                )
            if invalid_labels:
                parts.append(
                    "Недопустимые обозначения приложений: "
                    f"{self._format_labels(invalid_labels)}."
                )
            result.add_rule("APPX-003", "FAIL", " ".join(parts))
        elif appendix_entries:
            result.add_rule("APPX-003", "OK")

        if missing_status_labels:
            result.add_rule(
                "APPX-009",
                "FAIL",
                "После обозначения не найдена отдельная строка статуса в скобках "
                "(например, \"(рекомендуемое)\") для приложений: "
                f"{self._format_labels(missing_status_labels)}.",
            )
        elif appendix_entries:
            result.add_rule("APPX-009", "OK")

        if empty_content_labels:
            result.add_rule(
                "APPX-004",
                "FAIL",
                "Приложения не содержат основного текста после строки статуса и названия: "
                f"{self._format_labels(empty_content_labels)}.",
            )
        elif appendix_entries:
            result.add_rule("APPX-004", "OK")

        if missing_title_labels:
            result.add_rule(
                "APPX-005",
                "FAIL",
                "Не удалось определить название приложения (ожидается отдельная строка названия "
                "после статуса, оформленная как центрированный полужирный текст) для: "
                f"{self._format_labels(missing_title_labels)}.",
            )
        elif appendix_entries:
            result.add_rule("APPX-005", "OK")

        if title_with_dot_labels:
            result.add_rule(
                "APPX-006",
                "FAIL",
                "Заголовок приложения заканчивается точкой (по ГОСТ без точки в конце) для: "
                f"{self._format_labels(title_with_dot_labels)}.",
            )
        elif appendix_entries:
            result.add_rule("APPX-006", "OK")

        digits_non_sequential, cyrillic_non_sequential, latin_non_sequential = check_designation_sequence(
            sequence_labels,
            self.INVALID_CYRILLIC_LABELS,
            self.INVALID_LATIN_LABELS,
        )
        if digits_non_sequential:
            result.add_rule(
                "APPX-007",
                "FAIL",
                'Обозначения приложений в виде цифр идут не последовательно. '
            )
        elif cyrillic_non_sequential:
            result.add_rule(
                "APPX-007",
                "FAIL",
                'Кириллические обозначения приложений идут не по порядку. '
                'Рекомендуется проверить последовательность приложений.'
            )
        elif latin_non_sequential:
            result.add_rule(
                "APPX-007",
                "FAIL",
                'Латинские обозначения приложений идут не по порядку. '
                'Рекомендуется проверить последовательность приложений.'
            )
        elif sequence_labels:
            result.add_rule("APPX-007", "OK")

        contents_facts = check_contents_mentions(
            contents_text,
            appendix_entries,
            self.APPENDIX_KEYWORD,
        )
        missing_in_contents_labels: list[str] = []
        missing_title_in_contents_labels: list[str] = []
        for label, has_appendix_marker, has_title in contents_facts:
            if not has_appendix_marker:
                missing_in_contents_labels.append(label)
                continue

            if has_title is False:
                missing_title_in_contents_labels.append(label)

        if missing_in_contents_labels or missing_title_in_contents_labels:
            parts: list[str] = []
            if missing_in_contents_labels:
                parts.append(
                    "Не найдены в содержании приложения: "
                    f"{self._format_labels(missing_in_contents_labels)}."
                )
            if missing_title_in_contents_labels:
                parts.append(
                    "В содержании нет названия для приложений: "
                    f"{self._format_labels(missing_title_in_contents_labels)}."
                )
            result.add_rule("APPX-008", "FAIL", " ".join(parts))
        elif contents_text and appendix_entries:
            result.add_rule("APPX-008", "OK")

        return result