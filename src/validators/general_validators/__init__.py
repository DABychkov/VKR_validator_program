"""Валидаторы общих форматно-стилевых требований."""

from .figure_validator import FigureValidator
from .footnotes_validator import FootnotesValidator
from .formula_validator import FormulaValidator
from .general_requirements_validator import GeneralRequirementsValidator
from .links_validator import LinksValidator
from .notes_validator import NotesValidator
from .table_validator import TableValidator

__all__ = [
    "GeneralRequirementsValidator",
    "FigureValidator",
    "FootnotesValidator",
    "TableValidator",
    "FormulaValidator",
    "LinksValidator",
    "NotesValidator",
]
