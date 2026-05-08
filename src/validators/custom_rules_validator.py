"""Валидатор пользовательских правил."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models.document_structure import DocumentStructure
from ..models.rule_result import RuleResult
from ..models.validation_result import Severity, ValidationResult
from ..services.custom_rules_adapter import run_custom_check
from .base_validator import BaseValidator


DEFAULT_RULES_DIR = Path(__file__).resolve().parents[1] / "user_rules"


def build_rules_path(user_id: str | None) -> Path | None:
    if not user_id:
        return None
    safe_user_id = "".join(ch for ch in str(user_id) if ch.isalnum() or ch in {"-", "_"})
    if not safe_user_id:
        return None
    return DEFAULT_RULES_DIR / f"user_{safe_user_id}.json"


def _load_rules(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("rules", [])
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _resolve_status(result: dict[str, object]) -> str:
    ok = result.get("ok")
    has_data = bool(result.get("has_data"))
    if not has_data:
        return "SKIP"
    if ok is True:
        return "OK"
    if ok is False:
        return "FAIL"
    return "SKIP"


class CustomRulesValidator(BaseValidator):
    """Применяет пользовательские правила из JSON."""

    def __init__(self, rules_path: Path | None = None, user_id: str | None = None) -> None:
        self.rules_path = rules_path if rules_path is not None else build_rules_path(user_id)

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="CustomRulesValidator")
        rich_doc = document.rich_document
        if rich_doc is None:
            return result

        rules = _load_rules(self.rules_path)
        if not rules:
            return result

        paragraph_features = list(getattr(rich_doc, "paragraph_features", []) or [])

        for rule in rules:
            rule_id = str(rule.get("rule_id", "") or "").strip()
            section = str(rule.get("section", "") or "").strip()
            description = str(rule.get("description", "") or "").strip()
            severity = str(rule.get("severity", "RECOMMENDATION") or "RECOMMENDATION").strip().upper()
            function_id = str(rule.get("function_id", "") or "").strip()
            params = rule.get("params") if isinstance(rule.get("params"), dict) else None

            if not rule_id or not function_id:
                continue

            if section:
                scoped_paragraphs = [
                    paragraph
                    for paragraph in paragraph_features
                    if str(getattr(paragraph, "section_hint", "") or "").strip() == section
                ]
            else:
                scoped_paragraphs = paragraph_features

            check_result = run_custom_check(function_id, scoped_paragraphs, params)
            status = _resolve_status(check_result)

            message = None
            share = check_result.get("share")
            if isinstance(share, (int, float)):
                message = f"Доля: {share * 100:.1f}%"

            rule_result = RuleResult(
                rule_id=rule_id,
                section=section or "НЕ_КЛАССИФИЦИРОВАНО",
                description=description or "Пользовательское правило",
                severity=severity,
                status=status,
                message=message,
                gost_ref="-",
                implemented=True,
            )
            result.rule_results.append(rule_result)

            if status == "FAIL":
                try:
                    severity_enum = Severity(severity)
                except ValueError:
                    severity_enum = Severity.RECOMMENDATION
                result.errors.append((severity_enum, message or f"Нарушено правило {rule_id}"))
                if severity_enum == Severity.CRITICAL:
                    result.is_valid = False

        return result
