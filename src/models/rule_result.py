"""Модель результата проверки одного правила ТЗ/ГОСТ."""

from dataclasses import dataclass


@dataclass
class RuleResult:
    """Статус выполнения отдельного правила."""

    rule_id: str
    section: str
    description: str
    severity: str  # CRITICAL | RECOMMENDATION
    status: str = "SKIP"  # SKIP | OK | FAIL
    message: str | None = None
    gost_ref: str = "0"
    implemented: bool = False
