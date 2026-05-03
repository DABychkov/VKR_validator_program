"""Валидатор структурного элемента "СОДЕРЖАНИЕ" по ГОСТ 7.32-2017."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.validation_constants import CONTENTS_SECTION_KEYWORDS
from ..utils.contents_validation_utils import (
    check_dot_leaders_hint,
    check_page_numbers_are_positive,
    check_required_item_order,
    check_required_items,
    extract_toc_items_with_invalid_lines,
)
from ..utils.common.section_utils import (
    find_section_text_by_keywords,
    get_non_empty_lines,
)
from .base_validator import BaseValidator


class ContentsValidator(BaseValidator):
    """
    Валидатор содержания (структурный элемент 1.5 по ТЗ).

    Логика по ТЗ:
    - "СОДЕРЖАНИЕ" может отсутствовать для коротких работ (< 10 страниц),
      поэтому отсутствие секции помечается как рекомендация.
    - Если секция есть, в ней должны быть ключевые элементы:
      "ВВЕДЕНИЕ", "ЗАКЛЮЧЕНИЕ", "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ".
    - Для строк оглавления ожидается номер страницы в конце строки.
    - Проверяется базовая консистентность номеров страниц обязательных пунктов.
    """

    REQUIRED_ITEMS = {
        "РЕФЕРАТ": "РЕФЕРАТ",
        "ВВЕДЕНИЕ": "ВВЕДЕНИЕ",
        "ЗАКЛЮЧЕНИЕ": "ЗАКЛЮЧЕНИЕ",
        "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ": "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
    }

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="ContentsValidator")

        contents_text = find_section_text_by_keywords(document.sections, CONTENTS_SECTION_KEYWORDS)

        if contents_text is None:
            result.add_rule(
                "CONTENTS-001",
                "FAIL",
                message='Структурный элемент "СОДЕРЖАНИЕ" не найден. '
                'Если документ больше 10 страниц, рекомендуется добавить содержание.',
            )
            return result

        result.add_rule("CONTENTS-001", "OK")

        lines = get_non_empty_lines(contents_text, strip=True)

        if not lines:
            result.add_rule(
                "CONTENTS-002",
                "FAIL",
                message='Раздел "СОДЕРЖАНИЕ" найден, но он пустой, мы проверяем только рукописное содержание',
            )
            return result

        result.add_rule("CONTENTS-002", "OK")

        toc_items, invalid_toc_lines = extract_toc_items_with_invalid_lines(lines)
        if not toc_items:
            result.add_rule(
                "CONTENTS-003",
                "FAIL",
                message='Не удалось распознать строки содержания с номерами страниц. '
                'Ожидается формат: "Название раздела ... 12" или "Название раздела 12".',
            )
            return result

        if invalid_toc_lines:
            sample = "; ".join(invalid_toc_lines[:3])
            result.add_rule(
                "CONTENTS-003",
                "FAIL",
                message=(
                    "Часть строк содержания не удалось распознать как пункты с номером страницы: "
                    f"{sample}"
                ),
            )
        else:
            result.add_rule("CONTENTS-003", "OK")

        missing_required = check_required_items(toc_items, self.REQUIRED_ITEMS)
        if missing_required:
            result.add_rule(
                "CONTENTS-004",
                "FAIL",
                message=(
                    "В содержании отсутствуют обязательные пункты: "
                    + ", ".join(missing_required)
                ),
            )
        else:
            result.add_rule("CONTENTS-004", "OK")

        intro_page, conclusion_page, sources_page = check_required_item_order(toc_items)

        if intro_page is None or conclusion_page is None:
            result.add_rule(
                "CONTENTS-005",
                "SKIP",
                message='Проверка порядка страниц "ВВЕДЕНИЕ" и "ЗАКЛЮЧЕНИЕ" пропущена: один из разделов не найден',
            )
        elif intro_page >= conclusion_page:
            result.add_rule(
                "CONTENTS-005",
                "FAIL",
                message='В содержании номер страницы раздела "ВВЕДЕНИЕ" должен быть меньше номера страницы "ЗАКЛЮЧЕНИЕ"',
            )
        else:
            result.add_rule("CONTENTS-005", "OK")

        if conclusion_page is None or sources_page is None:
            result.add_rule(
                "CONTENTS-006",
                "SKIP",
                message='Проверка порядка страниц "ЗАКЛЮЧЕНИЕ" и "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ" пропущена: один из разделов не найден',
            )
        elif conclusion_page >= sources_page:
            result.add_rule(
                "CONTENTS-006",
                "FAIL",
                message='В содержании номер страницы раздела "ЗАКЛЮЧЕНИЕ" должен быть меньше номера страницы "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"',
            )
        else:
            result.add_rule("CONTENTS-006", "OK")

        invalid_pages = check_page_numbers_are_positive(toc_items)
        if invalid_pages:
            pages_text = "; ".join(
                f'"{item["title"]}" -> {item["page"]}' for item in invalid_pages
            )
            result.add_rule(
                "CONTENTS-007",
                "FAIL",
                message=f"В содержании обнаружены некорректные номера страниц: {pages_text}",
            )
        else:
            result.add_rule("CONTENTS-007", "OK")

        if check_dot_leaders_hint(lines):
            result.add_rule(
                "CONTENTS-008",
                "FAIL",
                "В содержании не обнаружен явный разделитель между названием раздела и номером страницы "
                "(отточия, табуляция или расширенный пробел). Проверьте визуальное оформление оглавления.",
            )
        else:
            result.add_rule("CONTENTS-008", "OK")

        return result
