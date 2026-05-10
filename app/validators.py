import re

def validate_str(name: str, isEmpty = False, maxLen=100) -> tuple[bool, str, str]:
    """Проверяет имя: не пустое, только буквы, пробелы, дефисы, длина не более 100."""
    if isEmpty==True and len(name)==0 :
        return True, "",""  # возвращаем очищенное значение
    if isEmpty == False and (not name or not isinstance(name, str)):
        return False, "", "Строка обязательно"
    name = name.strip()
    if isEmpty== False and len(name) == 0:
        return False, "","Строка не может быть пустым"
    if len(name) > maxLen:
        return False,"", "Строка слишком длинная"
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ_0-9\s\-\/']+$", name):
        return False, "","Строка может содержать только буквы, пробелы, дефис и апостроф"
    return True, name,""  # возвращаем очищенное значение

def validate_int(age_str) -> tuple[bool, int | None, str]:
    """Проверяет возраст: целое число от 0 до 120."""
    try:
        age = int(age_str)
    except (ValueError, TypeError):
        return False, None, "Число должен быть целым числом"
    return True, age, ""

def validate_float(weight_str) -> tuple[bool, float | None, str]:
    """Проверяет вес: float от 0 до 500."""
    try:
        weight = float(weight_str)
    except (ValueError, TypeError):
        return False, None, "Число должно быть числом"
    return True, weight, ""


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _parse_float_list(value: str | None) -> list[float] | None:
    if value is None:
        return None
    text = str(value)
    for sep in [";", " "]:
        text = text.replace(sep, ",")
    items = [item for item in (part.strip() for part in text.split(",")) if item]
    values: list[float] = []
    for item in items:
        parsed = _parse_float(item)
        if parsed is None:
            return None
        values.append(parsed)
    return values


def validate_rule_arg(name: str, raw_value: str | None) -> tuple[bool, object | None, str]:
    float_list_params = {"allowed_values"}
    string_params = {"target_font_names"}

    if name in float_list_params:
        parsed = _parse_float_list(raw_value)
        if parsed is None:
            return False, None, "Список должен быть числами"
        return True, raw_value or "", ""

    if name in string_params:
        return validate_str(raw_value or "")

    if name.endswith("_share") or name.endswith("_mm") or name.endswith("_pt"):
        parsed = _parse_float(raw_value)
        if parsed is None:
            return False, None, "Число должно быть числом"
        return True, raw_value or "", ""

    return validate_str(raw_value or "")

# Можно добавить санитизацию для вывода, если данные вставляются в HTML-атрибуты
def sanitize_for_html(text: str) -> str:
    """Экранирует специальные символы для безопасного вывода в HTML."""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))