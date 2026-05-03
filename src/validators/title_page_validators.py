"""Валидаторы для проверки титульного листа."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.regex_patterns import RE_HAS_DIGIT
from ..utils.title_page_utils import (
    check_approval_stamps,
    check_document_type,
    check_metadata,
    check_organization,
    check_place_and_year,
)
from .base_validator import BaseValidator


class TitlePageValidator(BaseValidator):
    """
    Валидатор титульного листа по ГОСТ 7.32-2017.
    
    Проверяет 10 основных блоков титульника:
    1. Наименование организации
    2. Метаданные (УДК, рег. номера)
    3. Грифы СОГЛАСОВАНО и УТВЕРЖДАЮ
    4. Вид документа (ОТЧЕТ О НИР)
    5. Наименование НИР
    6. Наименование отчета
    7. Вид отчета (промежуточный/заключительный)
    8. Шифр программы/темы
    9. Номер книги
    10. Руководитель + место и год
    """
    
    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="TitlePageValidator")
        
        # Разбиваем титульник на строки (абзацы)
        paragraphs = document.title_page_text.split('\n')
        
        # 1. Проверка организации (обязательно)
        org_block, has_org_keywords = check_organization(paragraphs)
        
        # TITLE-001: блок организации с заглавными буквами
        if not org_block:
            result.add_rule(
                "TITLE-001",
                "FAIL",
                message="Не найдено наименование организации в верхней части титульника, либо оно не написан заглавными буквами",
                implemented=True,
            )
        else:
            result.add_rule("TITLE-001", "OK", implemented=True)
        
        # TITLE-002: ключевые слова в организации
        if org_block and not has_org_keywords:
            result.add_rule(
                "TITLE-002",
                "FAIL",
                message="Наименование организации возможно некорректно (нет ключевых слов: Министерство, Федеральное и т.д.)",
                implemented=True,
            )
        elif org_block:
            result.add_rule("TITLE-002", "OK", implemented=True)
        
        # 2. Проверка метаданных УДК (обязательно)
        has_udk, udk_has_digits, has_nioktr = check_metadata(paragraphs, RE_HAS_DIGIT)
        
        # TITLE-003: найден УДК
        if not has_udk:
            result.add_rule(
                "TITLE-003",
                "FAIL",
                message="Отсутствует индекс УДК на титульном листе",
                implemented=True,
            )
        else:
            result.add_rule("TITLE-003", "OK", implemented=True)
            
            # TITLE-004: УДК содержит цифры
            if not udk_has_digits:
                result.add_rule(
                    "TITLE-004",
                    "FAIL",
                    message="УДК должен содержать цифры",
                    implemented=True,
                )
            else:
                result.add_rule("TITLE-004", "OK", implemented=True)

        # TITLE-005: регистрационный номер НИОКТР
        if not has_nioktr:
            result.add_rule(
                "TITLE-005",
                "FAIL",
                message="Рекомендуется указать регистрационный номер НИОКТР",
                implemented=True,
            )
        else:
            result.add_rule("TITLE-005", "OK", implemented=True)
        
        # 3. Проверка грифов (УТВЕРЖДАЮ обязательно, СОГЛАСОВАНО условно)
        utv, initials_found = check_approval_stamps(paragraphs)
        
        # TITLE-006: гриф УТВЕРЖДАЮ
        if not utv:
            result.add_rule(
                "TITLE-006",
                "FAIL",
                message="Отсутствует гриф УТВЕРЖДАЮ на титульном листе либо он написан не заглавными буквами",
                implemented=True,
            )
        else:
            result.add_rule("TITLE-006", "OK", implemented=True)
            
            # TITLE-007: инициалы после УТВЕРЖДАЮ
            if not initials_found:
                result.add_rule(
                    "TITLE-007",
                    "FAIL",
                    message="После грифа УТВЕРЖДАЮ не найдены инициалы (формат: А.В.)",
                    implemented=True,
                )
            else:
                result.add_rule("TITLE-007", "OK", implemented=True)
        
        # 4. Проверка вида документа (обязательно)
        doc_type, has_two_lines, is_uppercase = check_document_type(paragraphs)
        
        # TITLE-008: вид документа найден
        if not doc_type:
            result.add_rule(
                "TITLE-008",
                "FAIL",
                message="Не найден тип документа (ОТЧЕТ О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ)",
                implemented=True,
            )
        else:
            result.add_rule("TITLE-008", "OK", implemented=True)
            
            # TITLE-009: две строки
            if not has_two_lines:
                result.add_rule(
                    "TITLE-009",
                    "FAIL",
                    message="Тип документа должен быть на двух строках: 'ОТЧЕТ' и 'О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ'",
                    implemented=True,
                )
            else:
                result.add_rule("TITLE-009", "OK", implemented=True)

            # TITLE-010: заглавные буквы
            if not is_uppercase:
                result.add_rule(
                    "TITLE-010",
                    "FAIL",
                    message="Тип документа должен быть написан заглавными буквами",
                    implemented=True,
                )
            else:
                result.add_rule("TITLE-010", "OK", implemented=True)
        
        # 5. Проверка места и года (обязательно)
        place, year, current_year, is_future_year = check_place_and_year(paragraphs)
        
        # TITLE-011: год найден
        if not year:
            result.add_rule(
                "TITLE-011",
                "FAIL",
                message="Не найден год на титульном листе",
                implemented=True,
            )
        else:
            result.add_rule("TITLE-011", "OK", implemented=True)
            
            # TITLE-012: год не в будущем
            if is_future_year:
                result.add_rule(
                    "TITLE-012",
                    "FAIL",
                    message=f"Год на титульном листе ({year}) больше текущего ({current_year})",
                    implemented=True,
                )
            else:
                result.add_rule("TITLE-012", "OK", implemented=True)

            # TITLE-013: место указано
            if not place:
                result.add_rule(
                    "TITLE-013",
                    "FAIL",
                    message="Рекомендуется указать место (город) на титульном листе",
                    implemented=True,
                )
            else:
                result.add_rule("TITLE-013", "OK", implemented=True)
        
        return result
