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