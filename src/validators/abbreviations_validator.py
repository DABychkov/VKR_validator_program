"""Валидатор раздела 1.7 "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ"."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.validation_constants import (
    ABBREVIATIONS_SECTION_KEYWORDS,
    COMBINED_DEFINITIONS_SECTION_KEYWORDS,
)
from ..utils.definitions_utils import (
    extract_definition_items,
    find_intro_line,
    has_left_indentation,
    intro_phrase_matches,
    is_alphabetical,
)
from ..utils.common.section_utils import (
    find_section_text_by_keywords,
    get_non_empty_lines,
    has_section_by_keywords,
)
from .base_validator import BaseValidator


class AbbreviationsValidator(BaseValidator):
    """Проверка структурного элемента 1.7 по ТЗ."""

    EXPECTED_INTRO = "В настоящем отчете о НИР применяют следующие сокращения и обозначения"

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="AbbreviationsValidator")

        section_text = find_section_text_by_keywords(document.sections, ABBREVIATIONS_SECTION_KEYWORDS)
        has_combined = has_section_by_keywords(document.sections, COMBINED_DEFINITIONS_SECTION_KEYWORDS)

        # Условно-обязательный: если нету этого структурного элемента и нет объединенного раздела -> рекомендация.
        if not section_text:
            if not has_combined:
                result.add_rule(
                    "ABBR-001",
                    "FAIL",
                    'Раздел "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" не найден. '
                    'Если в документе используются сокращения/обозначения, рекомендуется добавить'
                    'или объединенный раздел "ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ".',
                )
            else:
                result.add_rule(
                    "ABBR-001",
                    "OK",
                    'Отдельный раздел "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" не найден, '
                    'но обнаружен объединенный раздел с определениями.',
                )
            return result

        result.add_rule("ABBR-001", "OK")

        lines = get_non_empty_lines(section_text, strip=False)
        intro = find_intro_line(lines)
        if not intro:
            result.add_rule(
                "ABBR-002",
                "FAIL",
                'В разделе "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" не найдена вводная формулировка по ГОСТ.',
            )
        elif not intro_phrase_matches(intro, self.EXPECTED_INTRO, min_common_words=8):
            result.add_rule(
                "ABBR-002",
                "FAIL",
                'В разделе "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" отсутствует '
                'требуемая вводная формулировка или она слишком сильно отличается от ГОСТ.',
            )
        else:
            result.add_rule("ABBR-002", "OK")

        items = extract_definition_items(section_text)
        if not items:
            result.add_rule(
                "ABBR-003",
                "FAIL",
                'В разделе "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" не найдены строки '
                'формата "СОКРАЩЕНИЕ — РАСШИФРОВКА".',
            )
            return result

        result.add_rule("ABBR-003", "OK")

        abbreviations = [left for left, _, _ in items]

        # По ТЗ: без отступа в левой колонке.
        indented = [raw for _, _, raw in items if has_left_indentation(raw)]
        if indented:
            result.add_rule(
                "ABBR-004",
                "FAIL",
                'В части строк обнаружен абзацный отступ перед сокращением. '
                'Рекомендуется располагать сокращения без отступа.',
            )
        else:
            result.add_rule("ABBR-004", "OK")

        # По ТЗ: алфавитный порядок.
        if not is_alphabetical(abbreviations):
            result.add_rule(
                "ABBR-005",
                "FAIL",
                'Сокращения не в алфавитном порядке. '
                'Рекомендуется упорядочить список по алфавиту.',
            )
        else:
            result.add_rule("ABBR-005", "OK")

        # По ТЗ: без знаков препинания в конце сокращения и расшифровки.
        bad_left = [left for left, _, _ in items if left.rstrip().endswith((".", ";", ":", ","))]
        bad_right = [right for _, right, _ in items if right.rstrip().endswith((".", ";", ":", ","))]
        if bad_left or bad_right:
            result.add_rule(
                "ABBR-006",
                "FAIL",
                'Рекомендуется убрать пунктуацию в конце сокращения и расшифровки.',
            )
        else:
            result.add_rule("ABBR-006", "OK")

        return result

    
