"""Каталог доступных пользовательских проверок для фронта."""

CHECKS_CATALOG: list[dict[str, object]] = [
    {
        "id_func": "check_first_line_indent_share",
        "name": "Абзацный отступ",
        "agr": [
            {"name": "expected_mm", "type": "float", "desc": "Целевой отступ",'um':'мм'},
            {"name": "min_valid_share", "type": "float", "desc": "Минимальная доля",'um':'(0-1)'},
        ],
    },
    {
        "id_func": "check_line_spacing_share",
        "name": "Межстрочный интервал",
        "agr": [
            {"name": "allowed_values", "type": "float_list", "desc": "Допустимые значения",'um':'мм'},
            {"name": "min_valid_share", "type": "float", "desc": "Минимальная доля",'um':'(0-1)'},
        ],
    },
    {
        "id_func": "check_min_font_size_share",
        "name": "Минимальный размер шрифта",
        "agr": [
            {"name": "min_size_pt","type": "float", "desc": "Минимальный размер",'um':'pt'},
            {"name": "max_below_threshold_share","type": "float", "desc": "Макс. доля ниже порога",'um':'(0-1)'},
        ],
    },
    {
        "id_func": "check_italic_share",
        "name": "Доля курсива",
        "agr": [
            {"name": "max_italic_share","type": "float", "desc": "Макс. доля курсива",'um':'(0-1)'},
        ],
    },
    {
        "id_func": "check_non_black_share",
        "name": "Доля не-черного цвета",
        "agr": [
            {"name": "max_non_black_share","type": "float", "desc": "Макс. доля не-черного",'um':'(0-1)'},
        ],
    },
    {
        "id_func": "check_target_font_share",
        "name": "Доля целевого шрифта",
        "agr": [
            {"name": "min_target_share","type": "float", "desc": "Минимальная доля",'um':'(0-1)'},
        ],
    },
]
