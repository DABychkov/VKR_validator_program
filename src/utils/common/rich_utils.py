"""Общие утилиты для работы с rich-признаками документа."""

from collections.abc import Iterable
from typing import Any, Callable

from .text_utils import normalize_text_compact_upper


def is_centered(paragraph_feature: Any) -> bool:
    """Проверяет, что абзац выровнен по центру."""
    return getattr(paragraph_feature, "alignment", "unknown") == "center"


def format_indexed_examples(
    text_by_index: dict[int, str],
    indexes: Iterable[int],
    *,
    preview_limit: int = 3,
    max_text_length: int = 80,
    prefix: str = " Примеры ошибки: ",
) -> str:
    """Формирует строку с примерами по словарю {index: text} и списку индексов."""
    unique_indexes = list(dict.fromkeys(indexes))
    snippets: list[str] = []

    for paragraph_index in unique_indexes:
        text = str(text_by_index.get(paragraph_index, "") or "").strip()
        if not text:
            continue

        if len(text) > max_text_length:
            text = f"{text[: max_text_length - 3]}..."

        snippets.append(f'"{text}"')
        if len(snippets) >= preview_limit:
            break

    if not snippets:
        return ""
    return prefix + "; ".join(snippets) + "."


def first_alpha_char(text: str) -> str | None:
    """Возвращает первый буквенный символ строки или None."""
    for ch in str(text or ""):
        if ch.isalpha():
            return ch
    return None


def get_paragraph_index(feature: Any, attr_name: str = "paragraph_index", default: int = -1) -> int:
    """Безопасно получает paragraph index из rich-объекта."""
    raw_index = getattr(feature, attr_name, None)
    if raw_index is None:
        return default
    return int(raw_index)


def is_bold(
    paragraph_feature: Any,
    min_bold_ratio: float = 0.5,
    allow_unknown_bold: bool = False,
) -> bool:
    """Проверяет, что абзац набран преимущественно полужирным."""
    bold_ratio = getattr(paragraph_feature, "bold_ratio", None)
    if bold_ratio is None:
        return allow_unknown_bold

    return bold_ratio >= min_bold_ratio


def is_center_bold(
    paragraph_feature: Any,
    min_bold_ratio: float = 0.5,
    allow_unknown_bold: bool = False,
) -> bool:
    """Проверяет, что абзац отцентрирован и набран преимущественно полужирным."""
    if not is_centered(paragraph_feature):
        return False

    return is_bold(
        paragraph_feature,
        min_bold_ratio=min_bold_ratio,
        allow_unknown_bold=allow_unknown_bold,
    )


def find_paragraph_index_by_text(paragraph_features: Iterable[Any], target_text: str) -> int | None:
    """Ищет индекс блока абзаца по нормализованному тексту."""
    target = normalize_text_compact_upper(target_text)
    if not target:
        return None

    for paragraph in paragraph_features:
        paragraph_text = normalize_text_compact_upper(getattr(paragraph, "text", ""))
        if paragraph_text == target:
            return int(getattr(paragraph, "block_index", -1))
    return None


def find_paragraph_by_text(paragraph_features: Iterable[Any], target_text: str) -> Any | None:
    """Возвращает объект paragraph_feature по нормализованному тексту."""
    target = normalize_text_compact_upper(target_text)
    if not target:
        return None

    for paragraph in paragraph_features:
        paragraph_text = normalize_text_compact_upper(getattr(paragraph, "text", ""))
        if paragraph_text == target:
            return paragraph
    return None


def is_value_within_tolerance(value: float | None, target: float, tolerance: float) -> bool:
    """Проверяет, что значение попадает в целевое +/- допуск."""
    if value is None:
        return False
    return abs(value - target) <= tolerance


def is_within_tolerance(value: float | None, target: float, tolerance: float) -> bool:
    """Совместимость: псевдоним для is_value_within_tolerance."""
    return is_value_within_tolerance(value, target, tolerance)


def is_page_margin_profile_match(
    page_settings_feature: Any,
    *,
    left_mm: float = 30.0,
    right_mm: float = 15.0,
    top_mm: float = 20.0,
    bottom_mm: float = 20.0,
    tolerance_mm: float = 1.0,
) -> bool:
    """Проверяет профиль полей страницы по ГОСТ с допуском."""
    return (
        is_value_within_tolerance(getattr(page_settings_feature, "margin_left_mm", None), left_mm, tolerance_mm)
        and is_value_within_tolerance(getattr(page_settings_feature, "margin_right_mm", None), right_mm, tolerance_mm)
        and is_value_within_tolerance(getattr(page_settings_feature, "margin_top_mm", None), top_mm, tolerance_mm)
        and is_value_within_tolerance(getattr(page_settings_feature, "margin_bottom_mm", None), bottom_mm, tolerance_mm)
    )


def is_first_line_indent_match(
    paragraph_feature: Any,
    *,
    expected_mm: float = 12.5,
    tolerance_mm: float = 1.0,
) -> bool:
    """Проверяет абзацный отступ (первая строка) с допуском."""
    return is_value_within_tolerance(
        getattr(paragraph_feature, "first_line_indent_mm", None),
        expected_mm,
        tolerance_mm,
    )


def is_line_spacing_allowed(
    paragraph_feature: Any,
    *,
    allowed_values: tuple[float, ...] = (1.5,),
    tolerance: float = 0.1,
) -> bool:
    """Проверяет, что межстрочный интервал входит в набор допустимых значений."""
    line_spacing = getattr(paragraph_feature, "line_spacing", None)
    if line_spacing is None:
        return False

    return any(abs(line_spacing - expected) <= tolerance for expected in allowed_values)


def is_paragraph_font_size_at_least(
    paragraph_feature: Any,
    *,
    min_size_pt: float = 12.0,
    allow_unknown_size: bool = True,
    require_any_known_size: bool = False,
) -> bool:
    """Проверяет минимальный размер шрифта для run-ов абзаца."""
    runs = getattr(paragraph_feature, "runs_features", []) or []
    known_sizes = [getattr(run, "font_size_pt", None) for run in runs if getattr(run, "font_size_pt", None) is not None]

    if require_any_known_size and not known_sizes:
        return False

    for run in runs:
        size_pt = getattr(run, "font_size_pt", None)
        if size_pt is None:
            if allow_unknown_size:
                continue
            return False
        if size_pt < min_size_pt:
            return False
    return True


def _run_text_weight(run_feature: Any, by_characters: bool) -> int:
    text = getattr(run_feature, "text", "") or ""
    if not by_characters:
        return 1
    return len(text) if text else 1


def calc_run_share(
    paragraph_features: Iterable[Any],
    predicate: Callable[[Any], bool | None],
    *,
    by_characters: bool = True,
    skip_unknown: bool = True,
) -> float | None:
    """Считает долю run-ов, удовлетворяющих predicate (вес по символам или по run-ам)."""
    total_weight = 0
    positive_weight = 0

    for paragraph in paragraph_features:
        runs = getattr(paragraph, "runs_features", []) or []
        for run in runs:
            decision = predicate(run)
            if decision is None and skip_unknown:
                continue

            weight = _run_text_weight(run, by_characters=by_characters)
            total_weight += weight
            if bool(decision):
                positive_weight += weight

    if total_weight == 0:
        return None
    return positive_weight / total_weight


def calc_italic_share(
    paragraph_features: Iterable[Any],
    *,
    by_characters: bool = True,
    skip_unknown: bool = True,
) -> float | None:
    """Считает долю курсивного текста по run-признакам."""
    return calc_run_share(
        paragraph_features,
        lambda run: getattr(run, "italic", None),
        by_characters=by_characters,
        skip_unknown=skip_unknown,
    )


def calc_non_black_color_share(
    paragraph_features: Iterable[Any],
    *,
    by_characters: bool = True,
    treat_unknown_as_black: bool = True,
) -> float | None:
    """Считает долю не-черного цвета шрифта по run-признакам."""

    def _is_non_black(run: Any) -> bool | None:
        color = getattr(run, "color_rgb", None)
        if color is None:
            return False if treat_unknown_as_black else None
        normalized = str(color).upper().replace("#", "")
        return normalized not in {"000000", "AUTO"}

    return calc_run_share(
        paragraph_features,
        _is_non_black,
        by_characters=by_characters,
        skip_unknown=not treat_unknown_as_black,
    )


def calc_font_family_share(
    paragraph_features: Iterable[Any],
    *,
    target_font_names: set[str] | tuple[str, ...],
    by_characters: bool = True,
    case_sensitive: bool = False,
    skip_unknown: bool = True,
) -> float | None:
    """Считает долю текста в заданных семействах шрифта."""
    def _normalize_font(value: str) -> str:
        compact = "".join(ch for ch in value.strip().lower() if ch.isalnum())
        # Word иногда возвращает варианты вроде TimesNewRomanPSMT/Times New Roman Cyr.
        if compact.startswith("timesnewroman"):
            return "timesnewroman"
        return compact

    if case_sensitive:
        normalized_targets = {name.strip() for name in target_font_names}
    else:
        normalized_targets = {_normalize_font(name) for name in target_font_names}

    def _is_target_font(run: Any) -> bool | None:
        font_name = getattr(run, "font_name", None)
        if not font_name:
            return None

        normalized_font = font_name.strip() if case_sensitive else _normalize_font(font_name)
        return normalized_font in normalized_targets

    return calc_run_share(
        paragraph_features,
        _is_target_font,
        by_characters=by_characters,
        skip_unknown=skip_unknown,
    )
