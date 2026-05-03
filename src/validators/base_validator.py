"""Базовый класс для валидаторов."""

from abc import ABC, abstractmethod

from ..models.document_structure import DocumentStructure
from ..models.validation_result import ValidationResult


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, document: DocumentStructure) -> ValidationResult:  # pragma: no cover - интерфейс
        raise NotImplementedError
