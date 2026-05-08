"""Адаптер для запуска пользовательских проверок."""

from __future__ import annotations

from inspect import signature
from typing import Any, Callable

from ..utils.general_utils import general_requirements_utils as gru


CHECK_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "check_first_line_indent_share": gru.check_first_line_indent_share,
    "check_line_spacing_share": gru.check_line_spacing_share,
    "check_min_font_size_share": gru.check_min_font_size_share,
    "check_italic_share": gru.check_italic_share,
    "check_non_black_share": gru.check_non_black_share,
    "check_target_font_share": gru.check_target_font_share,
}


def _filter_params(func: Callable[..., Any], params: dict[str, object] | None) -> dict[str, object]:
    if not params:
        return {}
    allowed = set(signature(func).parameters)
    allowed.discard("paragraph_features")
    return {key: value for key, value in params.items() if key in allowed}


def _normalize_result(result: Any) -> dict[str, object]:
    ok: bool | None = None
    share: float | None = None
    invalid_indexes: list[int] = []

    if isinstance(result, tuple):
        if len(result) == 3:
            ok, share, invalid_indexes = result
        elif len(result) == 2:
            ok, share = result
        elif len(result) == 1:
            ok = result[0]
    elif isinstance(result, list):
        invalid_indexes = [int(item) for item in result]
        ok = len(invalid_indexes) == 0
    elif isinstance(result, bool):
        ok = result

    has_data = share is not None or bool(invalid_indexes)

    return {
        "ok": ok,
        "share": share,
        "invalid_indexes": invalid_indexes,
        "has_data": has_data,
        "raw": result,
    }


def run_custom_check(
    check_id: str,
    paragraph_features: list[Any],
    params: dict[str, object] | None = None,
) -> dict[str, object]:
    func = CHECK_FUNCTIONS.get(check_id)
    if func is None:
        return {
            "ok": None,
            "share": None,
            "invalid_indexes": [],
            "has_data": False,
            "raw": None,
        }

    safe_params = _filter_params(func, params)
    result = func(paragraph_features, **safe_params)
    return _normalize_result(result)
