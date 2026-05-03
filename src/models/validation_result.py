"""Результат валидации с уровнем серьезности."""

from dataclasses import dataclass, field
from enum import Enum

from .rule_result import RuleResult


class Severity(Enum):
    """Уровень серьезности ошибки."""
    CRITICAL = "CRITICAL"  # Обязательное по ГОСТ
    RECOMMENDATION = "RECOMMENDATION"  # Рекомендация


@dataclass
class ValidationResult:
    """Результат валидации документа."""
    validator_name: str
    is_valid: bool = True
    errors: list[tuple[Severity, str]] = field(default_factory=list)
    rule_results: list[RuleResult] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.rule_results:
            return
        from ..config.rules_catalog import build_default_rule_results

        self.rule_results = build_default_rule_results(self.validator_name)
    
    def add_error(self, severity: Severity, message: str):
        """Добавить ошибку."""
        self.errors.append((severity, message))
        if severity == Severity.CRITICAL:
            self.is_valid = False

    def add_rule(
        self,
        rule_id: str,
        status: str,
        message: str | None = None,
        implemented: bool = True,
    ) -> None:
        """Обновляет правило в rule_results (или добавляет, если его нет в каталоге)."""
        normalized_status = status.upper().strip()
        if normalized_status not in {"SKIP", "OK", "FAIL"}:
            raise ValueError("status must be 'SKIP', 'OK' or 'FAIL'")

        for rule in self.rule_results:
            if rule.rule_id != rule_id:
                continue

            already_failed = rule.status == "FAIL"

            # Если правило уже в FAIL и снова приходит FAIL,
            # сохраняем первое сообщение и не перезаписываем состояние.
            if normalized_status == "FAIL" and already_failed:
                return

            # Не позволяем понизить правило из FAIL обратно в OK/SKIP.
            # Это защищает от случайных перезаписей в циклах валидаторов.
            if already_failed and normalized_status in {"OK", "SKIP"}:
                return

            rule.status = normalized_status
            rule.message = message
            rule.implemented = implemented

            # Добавляем ошибку только если переходим в FAIL и еще не были в FAIL
            if normalized_status == "FAIL" and not already_failed:
                rule_severity = Severity(rule.severity)
                self.errors.append((rule_severity, message or f"Нарушено правило {rule_id}"))
                if rule_severity == Severity.CRITICAL:
                    self.is_valid = False
            return

        # fallback: добавляем правило, если его нет в каталоге
        severity = Severity.RECOMMENDATION
        new_rule = RuleResult(
            rule_id=rule_id,
            section="НЕ_КЛАССИФИЦИРОВАНО",
            description="Правило не найдено в каталоге",
            severity=severity,
            status=normalized_status,
            message=message,
            gost_ref="0",
            implemented=implemented,
        )
        self.rule_results.append(new_rule)

        if normalized_status == "FAIL":
            self.errors.append((severity, message or f"Нарушено правило {rule_id}"))
    
    def has_errors(self) -> bool:
        """Есть ли ошибки."""
        return len(self.errors) > 0
