"""Валидатор пользовательских правил."""

from __future__ import annotations

from typing import Any

from ..config.sections_catalog import SECTIONS_CATALOG
from ..models.document_structure import DocumentStructure
from ..models.rule_result import RuleResult
from ..models.validation_result import Severity, ValidationResult
from ..services.custom_rules_adapter import run_custom_check
from .base_validator import BaseValidator


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


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _build_section_name_map() -> dict[str, str]:
    return {
        _normalize_text(item.get("name")): str(item.get("id_section", ""))
        for item in SECTIONS_CATALOG
        if isinstance(item, dict)
    }


def _coerce_value(raw: Any, value_type: str | None) -> Any:
    if raw is None:
        return None
    if value_type == "float_list":
        if isinstance(raw, (list, tuple)):
            items = raw
        else:
            text = str(raw)
            for sep in [";", " "]:
                text = text.replace(sep, ",")
            items = [item for item in (part.strip() for part in text.split(",")) if item]
        values: list[float] = []
        for item in items:
            try:
                values.append(float(str(item).replace(",", ".")))
            except ValueError:
                return None
        return values
    if value_type == "float":
        try:
            return float(str(raw).replace(",", "."))
        except ValueError:
            return None
    if value_type == "int":
        try:
            return int(str(raw))
        except ValueError:
            return None
    if value_type == "bool":
        return str(raw).strip().lower() in {"1", "true", "да", "yes"}
    return str(raw).strip()


def _build_params(args_list: list[dict[str, Any]] | None) -> dict[str, object]:
    if not args_list:
        return {}
    params: dict[str, object] = {}
    for arg in args_list:
        if not isinstance(arg, dict):
            continue
        name = str(arg.get("name", "") or "").strip()
        if not name:
            continue
        value_type = str(arg.get("type", "") or "").strip().lower() or None
        coerced = _coerce_value(arg.get("val"), value_type)
        if coerced is None:
            continue
        params[name] = coerced
    return params


class CustomRulesValidator(BaseValidator):
    """Применяет пользовательские правила из сессии."""

    def __init__(self) -> None:
        self.section_name_map = _build_section_name_map()

    def _load_rules(self) -> list[dict[str, Any]]:
        try:
            from app.utils import get_all_user_rules_from_session
        except Exception:
            return []

        try:
            rules = get_all_user_rules_from_session()
        except Exception:
            return []

        if not isinstance(rules, list):
            return []

        return [rule for rule in rules if isinstance(rule, dict)]

    def validate(self, document: DocumentStructure) -> ValidationResult:
        result = ValidationResult(validator_name="CustomRulesValidator")
        rich_doc = document.rich_document
        if rich_doc is None:
            return result

        rules = self._load_rules()
        if not rules:
            return result

        paragraph_features = list(getattr(rich_doc, "paragraph_features", []) or [])

        for rule in rules:
            rule_id = str(rule.get("rule_id", "") or "").strip()
            section = str(rule.get("section", "") or "").strip()
            description = str(rule.get("description", "") or "").strip()
            severity = str(rule.get("severity", "RECOMMENDATION") or "RECOMMENDATION").strip().upper()
            function_id = str(rule.get("func", "") or "").strip()
            args_list = rule.get("args") if isinstance(rule.get("args"), list) else None
            params = _build_params(args_list)
            gost_ref = str(rule.get("gost_ref", "") or "").strip() or "-"

            if not rule_id or not function_id:
                continue

            section_key = self.section_name_map.get(_normalize_text(section), section)
            if section_key:
                scoped_paragraphs = [
                    paragraph
                    for paragraph in paragraph_features
                    if str(getattr(paragraph, "section_hint", "") or "").strip() == section_key
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
                gost_ref=gost_ref,
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
