"""Валидатор "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.regex_patterns import RE_INITIALS_ANYWHERE, RE_NUMBERED_LIST_ITEM_LINE
from ..config.validation_constants import (
    REFERENCES_SECTION_KEYWORDS,
)
from ..utils.references_validation_utils import check_initials_presence, check_numbering_sequence
from ..utils.common.section_utils import find_section_text_by_keywords, get_non_empty_lines
from .base_validator import BaseValidator


class ReferencesValidator(BaseValidator):
    # Шаблон элемента списка: «1.», «2.» и т.д., а также «1 Автор» (без точки).
    _LIST_ITEM_RE = RE_NUMBERED_LIST_ITEM_LINE

    # Шаблон инициалов: Ф.И. или Фамилия И.О. - ищем хотя бы «Х.Х.» (буква, точка, буква, точка)
    _INITIALS_RE = RE_INITIALS_ANYWHERE

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="ReferencesValidator")

        section_text = find_section_text_by_keywords(document.sections, REFERENCES_SECTION_KEYWORDS)

        if section_text is None:
            result.add_rule(
                "REFS-001",
                "FAIL",
                'Обязательный раздел "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" не найден.',
            )
            return result

        result.add_rule("REFS-001", "OK")

        lines = get_non_empty_lines(section_text, strip=True)

        if not lines:
            result.add_rule(
                "REFS-002",
                "FAIL",
                'Раздел "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" найден, но он пустой.',
            )
            return result

        result.add_rule("REFS-002", "OK")

        # Проверяем, что список начинается с "1."
        if not self._LIST_ITEM_RE.match(lines[0]):
            result.add_rule(
                "REFS-003",
                "FAIL",
                'Список использованных источников должен начинаться с нумерованного пункта "1. ...".',
            )
        else:
            result.add_rule("REFS-003", "OK")

        # Собираем элементы списка (строки, начинающиеся с числа и точки)
        list_items = [line for line in lines if self._LIST_ITEM_RE.match(line)]

        if not list_items:
            result.add_rule(
                "REFS-004",
                "FAIL",
                'В разделе "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" не обнаружено нумерованных записей '
                '(ожидается формат "1. Автор И.О. Название...").',
            )
            return result

        result.add_rule("REFS-004", "OK")

        numbering_ok, expected, actual = check_numbering_sequence(list_items)
        if not numbering_ok:
            result.add_rule(
                "REFS-005",
                "FAIL",
                f"Нарушена нумерация в списке использованных источников: "
                f"ожидался номер {expected}, найден {actual}.",
            )
        else:
            result.add_rule("REFS-005", "OK")

        has_initials = check_initials_presence(list_items, self._INITIALS_RE)
        if list_items and not has_initials:
            result.add_rule(
                "REFS-006",
                "FAIL",
                'В записях "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" не обнаружены инициалы авторов '
                '(ожидается формат "Фамилия И.О." или "И.О. Фамилия"). '
                'Рекомендуется проверить оформление источников.',
            )
        else:
            result.add_rule("REFS-006", "OK")

        return result
