"""Валидатор раздела 1.6 "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ"."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.validation_constants import (
    TERMS_SECTION_KEYWORDS,
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


class TermsValidator(BaseValidator):
    """Проверка структурного элемента 1.6 по ТЗ."""

    EXPECTED_INTRO = (
        "В настоящем отчете о НИР применяют следующие термины "
        "с соответствующими определениями"
    )

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="TermsValidator")

        section_text = find_section_text_by_keywords(document.sections, TERMS_SECTION_KEYWORDS)
        has_combined = has_section_by_keywords(document.sections, COMBINED_DEFINITIONS_SECTION_KEYWORDS)

        # Условно-обязательный: отсутствие = рекомендация, если нет комбинированного варианта.
        if not section_text:
            if not has_combined:
                result.add_rule(
                    "TERMS-001",
                    "FAIL",
                    'Раздел "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" не найден. '
                    'Если в документе используются термины, рекомендуется добавить.',
                )
            else:
                result.add_rule(
                    "TERMS-001",
                    "OK",
                    'Отдельный раздел "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" не найден, '
                    'но обнаружен объединенный раздел с определениями.',
                )
            return result

        result.add_rule("TERMS-001", "OK")

        lines = get_non_empty_lines(section_text, strip=False)
        intro = find_intro_line(lines)
        if not intro:
            result.add_rule(
                "TERMS-002",
                "FAIL",
                'В разделе "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" не найдена вводная формулировка по ГОСТ.',
            )
        elif not intro_phrase_matches(intro, self.EXPECTED_INTRO, min_common_words=9):
            result.add_rule(
                "TERMS-002",
                "FAIL",
                'В разделе "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" отсутствует требуемая вводная формулировка '
                'или она слишком сильно отличается от ГОСТ.',
            )
        else:
            result.add_rule("TERMS-002", "OK")

        items = extract_definition_items(section_text)
        if not items:
            result.add_rule(
                "TERMS-003",
                "FAIL",
                'В разделе "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" не найдены статьи формата '
                '"ТЕРМИН — ОПРЕДЕЛЕНИЕ" (или табличный эквивалент).',
            )
            
            return result

        result.add_rule("TERMS-003", "OK")

        terms = [left for left, _, _ in items]

        # По ТЗ: слева без абзацного отступа.
        indented = [raw for _, _, raw in items if has_left_indentation(raw)]
        if indented:
            result.add_rule(
                "TERMS-004",
                "FAIL",
                'Располагают термины без отступа.',
            )
        else:
            result.add_rule("TERMS-004", "OK")

        # По ТЗ: без знаков препинания в конце термина и определения.
        bad_left = [left for left, _, _ in items if left.rstrip().endswith((".", ";", ":", ","))]
        bad_right = [right for _, right, _ in items if right.rstrip().endswith((".", ";", ":", ","))]
        if bad_left or bad_right:
            result.add_rule(
                "TERMS-005",
                "FAIL",
                'Рекомендуется убрать пунктуацию в конце термина и определения.',
            )
        else:
            result.add_rule("TERMS-005", "OK")

        # По ТЗ: алфавитный порядок.
        if not is_alphabetical(terms):
            result.add_rule(
                "TERMS-006",
                "FAIL",
                'Рекомендуется упорядочить список терминов по алфавиту.',
            )
        else:
            result.add_rule("TERMS-006", "OK")

        return result

    
