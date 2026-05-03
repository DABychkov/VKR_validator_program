"""Валидатор списка исполнителей по ГОСТ 7.32-2017."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.regex_patterns import RE_EXECUTOR_ON_TITLE, RE_INITIALS
from ..config.validation_constants import EXECUTOR_SECTION_KEYWORDS
from ..utils.executor_validation_utils import check_executor_section, check_title_page_executor
from ..utils.common.section_utils import find_section_text_by_keywords, get_non_empty_lines
from .base_validator import BaseValidator


class ExecutorListValidator(BaseValidator):
    """
    Валидатор списка исполнителей (структурный элемент 1.3 по ТЗ).
    
    Правила:
    - Условный элемент (если исполнителей > 2)
    - Если 1 исполнитель -> должен быть на титульнике "Исполнитель:"
    - Формат: слева должности/степени, справа инициалы+фамилия
    - Обязательные роли: "Исполнители:"
    - Условные роли: "Отв. Исполнитель", "Соисполнители:"
    """
    
    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="ExecutorListValidator")
        
        # Проверяем наличие секции "СПИСОК ИСПОЛНИТЕЛЕЙ"
        section_text = find_section_text_by_keywords(document.sections, EXECUTOR_SECTION_KEYWORDS)
        
        if not section_text:
            # Если секции нет, проверяем титульник
            has_executor_on_title, has_initials_on_title = check_title_page_executor(
                document.title_page_text,
                RE_EXECUTOR_ON_TITLE,
            )
            if not has_executor_on_title:
                missing_executor_msg = (
                    'Не найдена секция "СПИСОК ИСПОЛНИТЕЛЕЙ" и нет фразы "Исполнитель:" на титульнике. '
                    'Если исполнителей >2, добавьте структурный элемент "СПИСОК ИСПОЛНИТЕЛЕЙ"'
                )
                result.add_rule("EXEC-001", "FAIL", message=missing_executor_msg, implemented=True)
            elif not has_initials_on_title:
                bad_initials_msg = 'Исполнитель на титульнике найден, но инициалы не распознаны (формат: А.В.)'
                result.add_rule("EXEC-001", "OK", implemented=True)
                result.add_rule("EXEC-002", "FAIL", message=bad_initials_msg, implemented=True)
            else:
                result.add_rule("EXEC-001", "OK", implemented=True)
                result.add_rule("EXEC-002", "OK", implemented=True)
        else:
            result.add_rule("EXEC-001", "OK", implemented=True)

            # Если секция есть, валидируем её
            lines = get_non_empty_lines(section_text, strip=False)
            has_role, initials_count, has_responsible = check_executor_section(lines, RE_INITIALS)

            if not has_role:
                result.add_rule(
                    "EXEC-003",
                    "FAIL",
                    message='В списке исполнителей отсутствует роль "Исполнители:"',
                    implemented=True,
                )
            else:
                result.add_rule("EXEC-003", "OK", implemented=True)

            if initials_count == 0:
                result.add_rule(
                    "EXEC-004",
                    "FAIL",
                    message='В списке исполнителей не найдены инициалы (формат: А.В.)',
                    implemented=True,
                )
            elif initials_count < 2:
                result.add_rule("EXEC-004", "OK", implemented=True)
                result.add_rule(
                    "EXEC-005",
                    "FAIL",
                    message=(
                        f'В списке исполнителей найден только {initials_count} человек. '
                        'Если исполнителей 1, список можно разместить на титульнике'
                    ),
                    implemented=True,
                )
            else:
                result.add_rule("EXEC-004", "OK", implemented=True)
                result.add_rule("EXEC-005", "OK", implemented=True)

            if not has_responsible:
                result.add_rule(
                    "EXEC-006",
                    "FAIL",
                    message='Рекомендуется указать ответственного исполнителя ("Отв. Исполнитель")',
                    implemented=True,
                )
            else:
                result.add_rule("EXEC-006", "OK", implemented=True)
        
        return result
