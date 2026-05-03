"""Проверки для правил TABLE-* (таблицы)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..common.rich_utils import first_alpha_char


SERVICE_TABLE_SECTION_MARKERS = (
	"ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
	"ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
	"ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ",
)


def _normalize_spaces_upper(text: str) -> str:
	return " ".join(str(text or "").split()).upper()


def _text_has_service_section_marker(text: str) -> bool:
	normalized = _normalize_spaces_upper(text)
	return any(marker in normalized for marker in SERVICE_TABLE_SECTION_MARKERS)


def _table_title_after_number_fragment(table: Any) -> str:
	title_text = str(getattr(table, "title_above_text", "") or "")
	table_number = str(getattr(table, "number", "") or "").strip()
	if not title_text or not table_number:
		return ""

	if table_number not in title_text:
		return ""

	return title_text.split(table_number, 1)[-1].strip()


def _table_title_tail(table: Any) -> str:
	fragment = _table_title_after_number_fragment(table)
	if not fragment:
		return ""
	return fragment.lstrip("-–—: ").strip()


def has_table_title_name(table: Any) -> bool:
	"""Есть ли у таблицы наименование после номера."""
	return bool(_table_title_tail(table))


def has_table_caption(table: Any) -> bool:
	"""Есть ли у таблицы подпись (строка заголовка таблицы)."""
	return bool(str(getattr(table, "title_above_text", "") or "").strip())


def has_table_number(table: Any) -> bool:
	"""Есть ли у таблицы распознанный номер."""
	return bool(str(getattr(table, "number", "") or "").strip())


def has_table_caption_and_number(table: Any) -> bool:
	"""Есть ли у таблицы одновременно подпись и номер."""
	return has_table_caption(table) and has_table_number(table)


def has_non_empty_table_header_cells(table: Any) -> bool:
	"""Есть ли непустые ячейки в заголовочной строке таблицы."""
	header_cells = list(getattr(table, "header_row_cells", []) or [])
	return any(str(getattr(cell, "text", "") or "").strip() for cell in header_cells)


def is_service_terms_abbr_table(table: Any) -> bool:
	"""Служебная таблица терминов/сокращений: по section_hint или по тексту заголовка таблицы."""
	section_hint = str(getattr(table, "section_hint", "") or "")
	if section_hint and _text_has_service_section_marker(section_hint):
		return True
	title = str(getattr(table, "title_above_text", "") or "")
	return bool(title and _text_has_service_section_marker(title))


def check_table_title_position_left(table_features: Iterable[Any]) -> list[int]:
	"""заголовок таблицы должен быть сверху и выровнен влево."""
	invalid_indexes: list[int] = []
	for table in table_features:
		table_index = int(getattr(table, "table_index", -1))
		title_text = str(getattr(table, "title_above_text", "") or "").strip()
		title_relative_position = getattr(table, "title_relative_position", "unknown")
		title_alignment = getattr(table, "title_alignment", "unknown")

		if title_text and title_relative_position == "above" and title_alignment == "left":
			continue

		invalid_indexes.append(table_index)

	return invalid_indexes


def check_table_number_pattern(table_features: Iterable[Any]) -> list[int]:
	"""номер таблицы должен соответствовать допустимому паттерну."""
	invalid_indexes: list[int] = []
	allowed_patterns = {
		"table_number_global",
		"table_number_sectional",
		"table_number_appendix",
	}

	for table in table_features:
		table_index = int(getattr(table, "table_index", -1))
		number = str(getattr(table, "number", "") or "").strip()
		number_pattern = getattr(table, "number_pattern", None)
		in_appendix = bool(getattr(table, "in_appendix", False))

		if not number:
			invalid_indexes.append(table_index)
			continue
		if number_pattern not in allowed_patterns:
			invalid_indexes.append(table_index)
			continue
		if number_pattern == "table_number_appendix" and not in_appendix:
			invalid_indexes.append(table_index)
			continue
		if in_appendix and number_pattern != "table_number_appendix":
			invalid_indexes.append(table_index)

	return invalid_indexes


def check_table_title_dash_separator(table_features: Iterable[Any]) -> list[int]:
	"""наименование таблицы (при наличии) должно идти через тире."""
	invalid_indexes: list[int] = []
	for table in table_features:
		table_index = int(getattr(table, "table_index", -1))
		fragment = _table_title_after_number_fragment(table)
		tail = _table_title_tail(table)

		# Наименования нет -> правило не применяем.
		if not tail:
			continue

		if not fragment:
			invalid_indexes.append(table_index)
			continue

		starts_with_dash = fragment[0] in {"-", "–", "—"}
		if starts_with_dash:
			continue

		invalid_indexes.append(table_index)

	return invalid_indexes


def check_table_title_capital_no_period(table_features: Iterable[Any]) -> list[int]:
	"""наименование таблицы (при наличии) с прописной буквы и без точки в конце."""
	invalid_indexes: list[int] = []
	for table in table_features:
		table_index = int(getattr(table, "table_index", -1))
		tail = _table_title_tail(table)
		if not tail:
			continue

		first_alpha = first_alpha_char(tail)
		starts_with_upper = bool(first_alpha and first_alpha.isupper())
		ends_with_period = tail.endswith(".")

		if starts_with_upper and not ends_with_period:
			continue

		invalid_indexes.append(table_index)

	return invalid_indexes


def check_table_no_diagonal_borders(table_features: Iterable[Any]) -> list[int]:
	"""в таблице не должно быть диагональных линий."""
	invalid_indexes: list[int] = []
	for table in table_features:
		if bool(getattr(table, "has_diagonal_borders", False)):
			invalid_indexes.append(int(getattr(table, "table_index", -1)))
	return invalid_indexes


def check_table_header_cells_capital(table_features: Iterable[Any]) -> list[int]:
	"""заголовки граф начинаются с прописной буквы."""
	invalid_indexes: list[int] = []
	for table in table_features:
		table_index = int(getattr(table, "table_index", -1))
		header_cells = list(getattr(table, "header_row_cells", []) or [])

		invalid = False
		for cell in header_cells:
			text = str(getattr(cell, "text", "") or "").strip()
			if not text:
				continue
			first_alpha = first_alpha_char(text)
			if first_alpha is None:
				continue
			if first_alpha.isupper():
				continue
			invalid = True
			break

		if invalid:
			invalid_indexes.append(table_index)

	return invalid_indexes


def check_table_header_cells_no_period(table_features: Iterable[Any]) -> list[int]:
	"""заголовки граф не заканчиваются точкой."""
	invalid_indexes: list[int] = []
	for table in table_features:
		table_index = int(getattr(table, "table_index", -1))
		header_cells = list(getattr(table, "header_row_cells", []) or [])

		invalid = False
		for cell in header_cells:
			text = str(getattr(cell, "text", "") or "").strip()
			if not text:
				continue
			if text.endswith("."):
				invalid = True
				break

		if invalid:
			invalid_indexes.append(table_index)

	return invalid_indexes



