"""Валидатор реферата по ГОСТ 7.32-2017."""

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult
from ..config.validation_constants import ABSTRACT_SECTION_KEYWORDS
from ..utils.abstract_utils import (
    check_abstract_size,
    check_abstract_text,
    check_keywords,
    check_volume_info,
)
from ..utils.common.section_utils import find_section_text_by_keywords, get_non_empty_lines
from .base_validator import BaseValidator


class AbstractValidator(BaseValidator):
    """
    Валидатор реферата (структурный элемент 1.4 по ТЗ).
    
    Проверяет:
    1. Наличие сведений об объеме (страницы, книги, иллюстрации, таблицы, источники, приложения)
    2. Формат ключевых слов (капс, запятые, без точки)
    3. Ключевые фразы в тексте реферата (цель, объект - рекомендация)
    4. Объем реферата (>= 850 символов - рекомендация)
    """
    
    MIN_ABSTRACT_SIZE = 850  # Минимум символов в реферате
    
    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="AbstractValidator")
        
        # Ищем секцию РЕФЕРАТ
        abstract_text = find_section_text_by_keywords(document.sections, ABSTRACT_SECTION_KEYWORDS)
        
        if not abstract_text:
            result.add_rule(
                "ABSTRACT-001",
                "FAIL",
                message='Структурный элемент "РЕФЕРАТ" не найден',
                implemented=True,
            )
            return result

        result.add_rule("ABSTRACT-001", "OK", implemented=True)
        
        # Разбиваем реферат на строки
        lines = get_non_empty_lines(abstract_text, strip=False)
        
        # 1. Проверка сведений об объеме
        found_metrics, has_invalid_volume_separator = check_volume_info(lines)
        if len(found_metrics) < 3:
            result.add_rule(
                "ABSTRACT-002",
                "FAIL",
                f'Неполна информация об объеме отчета. Найдено: {found_metrics}. '
                'Требуется указать: страницы, книги, иллюстрации, таблицы, источники',
                implemented=True,
            )
        else:
            result.add_rule("ABSTRACT-002", "OK", implemented=True)

        # ABSTRACT-003: Проверка формата разделителей
        if len(found_metrics) < 2:
            result.add_rule(
                "ABSTRACT-003",
                "SKIP",
                message='Проверка формата разделителей пропускается (недостаточно метрик)',
                implemented=True,
            )
        elif has_invalid_volume_separator:
            result.add_rule(
                "ABSTRACT-003",
                "FAIL",
                message='Сведения об объеме должны разделяться запятыми и располагаться в строку',
                implemented=True,
            )
        else:
            result.add_rule("ABSTRACT-003", "OK", implemented=True)
        
        # 2. Проверка ключевых слов
        keywords_section, format_check = check_keywords(lines)
        
        # ABSTRACT-004: Наличие ключевых слов
        if not keywords_section:
            result.add_rule(
                "ABSTRACT-004",
                "FAIL",
                message='Ключевые слова не найдены',
                implemented=True,
            )
        else:
            result.add_rule("ABSTRACT-004", "OK", implemented=True)

            # ABSTRACT-005: Капс
            if not format_check["is_uppercase"]:
                result.add_rule(
                    "ABSTRACT-005",
                    "FAIL",
                    message='Ключевые слова должны быть написаны прописными буквами',
                    implemented=True,
                )
            else:
                result.add_rule("ABSTRACT-005", "OK", implemented=True)

            # ABSTRACT-006: Запятые как разделители
            if not format_check["has_commas"]:
                result.add_rule(
                    "ABSTRACT-006",
                    "FAIL",
                    message='Ключевые слова должны разделяться запятыми. В большей части строк должна быть хотя бы одна запятая.',
                    implemented=True,
                )
            else:
                result.add_rule("ABSTRACT-006", "OK", implemented=True)

            # ABSTRACT-007: Без точки в конце
            if not format_check["no_trailing_period"]:
                result.add_rule(
                    "ABSTRACT-007",
                    "FAIL",
                    message='Ключевые слова не должны заканчиваться точкой',
                    implemented=True,
                )
            else:
                result.add_rule("ABSTRACT-007", "OK", implemented=True)

            # ABSTRACT-008: Нет переносов (не более 4 строк)
            if not format_check["no_line_breaks"]:
                result.add_rule(
                    "ABSTRACT-008",
                    "FAIL",
                    message='Ключевые слова должны располагаться компактно. Избегайте нежелательных переносов.',
                    implemented=True,
                )
            else:
                result.add_rule("ABSTRACT-008", "OK", implemented=True)
        
        # 3. Проверка текста реферата (рекомендации)
        missing_keywords = check_abstract_text(abstract_text)
        if missing_keywords:
            missing_labels = {
                "goal": "цель",
                "object": "объект",
                "recommendations": "рекомендации"
            }
            missing_text = ", ".join(missing_labels.get(k, k) for k in missing_keywords)
            result.add_rule(
                "ABSTRACT-009",
                "FAIL",
                message=f'Рекомендуется уточнить в тексте реферата: {missing_text}',
                implemented=True,
            )
        else:
            result.add_rule("ABSTRACT-009", "OK", implemented=True)
        
        # 4. Проверка объема реферата
        char_count = check_abstract_size(abstract_text)
        if char_count < self.MIN_ABSTRACT_SIZE:
            result.add_rule(
                "ABSTRACT-010",
                "FAIL",
                message=(
                    f'Рекомендуется расширить реферат. '
                    f'Текущий объем: {char_count} символов, '
                    f'рекомендуемый минимум: {self.MIN_ABSTRACT_SIZE} символов'
                ),
                implemented=True,
            )
        else:
            result.add_rule("ABSTRACT-010", "OK", implemented=True)
        
        return result
