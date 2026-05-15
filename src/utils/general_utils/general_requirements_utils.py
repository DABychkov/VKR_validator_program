"""Параметризованные проверки для общих правил оформления."""

from typing import Any, Iterable

from ..common.rich_utils import (
    calc_font_family_share,
    calc_italic_share,
    calc_non_black_color_share,
    is_first_line_indent_match,
    is_line_spacing_allowed,
    is_page_margin_profile_match,
    is_paragraph_font_size_at_least,
)


def _normalize_style_name(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def is_general_body_paragraph(paragraph_feature: Any) -> bool:
    """Исключает служебные абзацы (TOC и похожие) из общих форматных проверок."""
    style_name = _normalize_style_name(getattr(paragraph_feature, "style_name", None))
    text = _normalize_text(getattr(paragraph_feature, "text", ""))
    first_line_indent_mm = getattr(paragraph_feature, "first_line_indent_mm", None)

    # Типовые стили оглавления: "TOC 1", "TOC 2", ...
    if style_name.startswith("toc"):
        return False
    if "содержание" in text:
        return False
    if first_line_indent_mm is not None and first_line_indent_mm < 0 and style_name.startswith("toc"):
        return False
    return True


def check_page_margins(
    pages_settings: Iterable[Any],
    *,
    left_mm: float = 30.0,
    right_mm: float = 15.0,
    top_mm: float = 20.0,
    bottom_mm: float = 20.0,
    tolerance_mm: float = 1.0,
) -> list[int]:
    """Возвращает индексы секций, где профиль полей не соответствует ГОСТ."""
    invalid_sections: list[int] = []
    for section in pages_settings:
        if not is_page_margin_profile_match(
            section,
            left_mm=left_mm,
            right_mm=right_mm,
            top_mm=top_mm,
            bottom_mm=bottom_mm,
            tolerance_mm=tolerance_mm,
        ):
            invalid_sections.append(int(getattr(section, "section_index", -1)))
    return invalid_sections


def check_first_line_indent(
    paragraph_features: Iterable[Any],
    *,
    expected_mm: float = 12.5,
    tolerance_mm: float = 1.0,
) -> list[int]:
    """Возвращает block_index абзацев с недопустимым абзацным отступом."""
    invalid_indexes: list[int] = []
    for paragraph in paragraph_features:
        if not is_first_line_indent_match(
            paragraph,
            expected_mm=expected_mm,
            tolerance_mm=tolerance_mm,
        ):
            invalid_indexes.append(int(getattr(paragraph, "block_index", -1)))
    return invalid_indexes


def check_first_line_indent_share(
    paragraph_features: Iterable[Any],
    *,
    expected_mm: float = 12.5,
    tolerance_mm: float = 1.0,
    min_valid_share: float = 0.8,
    predicate: Any | None = None,
) -> tuple[bool, float | None, list[int]]:
    """Проверяет долю абзацев с корректным абзацным отступом."""
    total = 0
    valid = 0
    invalid_indexes: list[int] = []

    for paragraph in paragraph_features:
        if predicate is not None and not predicate(paragraph):
            continue

        total += 1
        is_valid = is_first_line_indent_match(
            paragraph,
            expected_mm=expected_mm,
            tolerance_mm=tolerance_mm,
        )
        if is_valid:
            valid += 1
            continue
        invalid_indexes.append(int(getattr(paragraph, "block_index", -1)))

    if total == 0:
        return True, None, []

    valid_share = valid / total
    return valid_share >= min_valid_share, valid_share, invalid_indexes


def check_line_spacing(
    paragraph_features: Iterable[Any],
    *,
    allowed_values: tuple[float, ...] = (1.0, 1.5),
    tolerance: float = 0.1,
) -> list[int]:
    """Возвращает block_index абзацев с недопустимым межстрочным интервалом."""
    invalid_indexes: list[int] = []
    for paragraph in paragraph_features:
        if not is_line_spacing_allowed(
            paragraph,
            allowed_values=allowed_values,
            tolerance=tolerance,
        ):
            invalid_indexes.append(int(getattr(paragraph, "block_index", -1)))
    return invalid_indexes


def check_line_spacing_share(
    paragraph_features: Iterable[Any],
    *,
    allowed_values: tuple[float, ...] = (1.0, 1.5),
    tolerance: float = 0.1,
    min_valid_share: float = 0.8,
    predicate: Any | None = None,
) -> tuple[bool, float | None, list[int]]:
    """Проверяет долю абзацев с допустимым межстрочным интервалом."""
    total = 0
    valid = 0
    invalid_indexes: list[int] = []

    for paragraph in paragraph_features:
        if predicate is not None and not predicate(paragraph):
            continue

        total += 1
        is_valid = is_line_spacing_allowed(
            paragraph,
            allowed_values=allowed_values,
            tolerance=tolerance,
        )
        if is_valid:
            valid += 1
            continue
        invalid_indexes.append(int(getattr(paragraph, "block_index", -1)))

    if total == 0:
        return True, None, []

    valid_share = valid / total
    return valid_share >= min_valid_share, valid_share, invalid_indexes


def check_min_font_size_share(
    paragraph_features: Iterable[Any],
    *,
    min_size_pt: float = 12.0,
    max_below_threshold_share: float = 0.05,
    allow_unknown_size: bool = True,
) -> tuple[bool, float]:
    """Проверяет, что доля абзацев с малым шрифтом не превышает порог."""
    total = 0
    invalid = 0
    for paragraph in paragraph_features:
        total += 1
        if not is_paragraph_font_size_at_least(
            paragraph,
            min_size_pt=min_size_pt,
            allow_unknown_size=allow_unknown_size,
        ):
            invalid += 1

    if total == 0:
        return True, 0.0

    share = invalid / total
    return share <= max_below_threshold_share, share


def check_italic_share(
    paragraph_features: Iterable[Any],
    *,
    max_italic_share: float = 0.2,
    by_characters: bool = True,
    treat_unknown_as_non_italic: bool = True,
) -> tuple[bool, float | None]:
    """Проверяет, что доля курсива не превышает порог."""
    share = calc_italic_share(
        paragraph_features,
        by_characters=by_characters,
        skip_unknown=not treat_unknown_as_non_italic,
    )
    if share is None:
        return True, None
    return share <= max_italic_share, share


def check_non_black_share(
    paragraph_features: Iterable[Any],
    *,
    max_non_black_share: float = 0.0,
    by_characters: bool = True,
    treat_unknown_as_black: bool = True,
) -> tuple[bool, float | None]:
    """Проверяет, что доля не-черного текста не превышает порог."""
    share = calc_non_black_color_share(
        paragraph_features,
        by_characters=by_characters,
        treat_unknown_as_black=treat_unknown_as_black,
    )
    if share is None:
        return True, None
    return share <= max_non_black_share, share


def check_target_font_share(
    paragraph_features: Iterable[Any],
    *,
    target_font_names: set[str] | tuple[str, ...] = ("Times New Roman",),
    min_target_share: float = 0.7,
    by_characters: bool = True,
    treat_unknown_as_non_target: bool = True,
) -> tuple[bool, float | None]:
    """Проверяет, что доля целевого шрифта не ниже порога."""
    share = calc_font_family_share(
        paragraph_features,
        target_font_names=target_font_names,
        by_characters=by_characters,
        case_sensitive=False,
        skip_unknown=not treat_unknown_as_non_target,
    )
    if share is None:
        return True, None
    return share >= min_target_share, share


def check_page_numbering_present(
    footer_features: Iterable[Any],
) -> list[int]:
    """Возвращает section_index секций без поля нумерации страницы."""
    invalid_sections: list[int] = []
    for footer in footer_features:
        has_page_field = bool(getattr(footer, "has_page_field", False))
        if has_page_field:
            continue

        invalid_sections.append(int(getattr(footer, "section_index", -1)))

    return invalid_sections


def check_page_numbering_centered(
    footer_features: Iterable[Any],
    *,
    required_alignment: str = "center",
) -> list[int]:
    """Возвращает section_index секций, где номер страницы не выровнен по центру."""
    invalid_sections: list[int] = []

    for footer in footer_features:
        section_index = int(getattr(footer, "section_index", -1))
        has_page_field = bool(getattr(footer, "has_page_field", False))
        if not has_page_field:
            continue

        alignment = getattr(footer, "alignment", "unknown")

        if alignment == required_alignment:
            continue

        invalid_sections.append(section_index)

    return invalid_sections
