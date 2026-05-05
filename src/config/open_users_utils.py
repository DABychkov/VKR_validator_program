"""Каталог доступных пользовательских проверок для фронта."""

CHECKS_CATALOG: list[dict[str, object]] = [
    {
        "id": "check_first_line_indent_share",
        "name": "Абзацный отступ",
        "params": [
            {"name": "expected_mm", "label": "Целевой отступ (мм)", "type": "float"},
            {"name": "min_valid_share", "label": "Минимальная доля", "type": "float"},
        ],
        "returns": "share",
    },
    {
        "id": "check_line_spacing_share",
        "name": "Межстрочный интервал",
        "params": [
            {"name": "allowed_values", "label": "Допустимые значения", "type": "float_list"},
            {"name": "min_valid_share", "label": "Минимальная доля", "type": "float"},
        ],
        "returns": "share",
    },
    {
        "id": "check_min_font_size_share",
        "name": "Минимальный размер шрифта",
        "params": [
            {"name": "min_size_pt", "label": "Минимальный размер (пт)", "type": "float"},
            {"name": "max_below_threshold_share", "label": "Макс. доля ниже порога", "type": "float"},
        ],
        "returns": "share",
    },
    {
        "id": "check_italic_share",
        "name": "Доля курсива",
        "params": [
            {"name": "max_italic_share", "label": "Макс. доля курсива", "type": "float"},
        ],
        "returns": "share",
    },
    {
        "id": "check_non_black_share",
        "name": "Доля не-черного цвета",
        "params": [
            {"name": "max_non_black_share", "label": "Макс. доля не-черного", "type": "float"},
        ],
        "returns": "share",
    },
    {
        "id": "check_target_font_share",
        "name": "Доля целевого шрифта",
        "params": [
            {"name": "min_target_share", "label": "Минимальная доля", "type": "float"},
        ],
        "returns": "share",
    },
]
