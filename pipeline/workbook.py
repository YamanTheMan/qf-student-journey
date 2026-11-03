"""Small helpers for reading the Excel submissions."""
import re
import warnings

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from pipeline.inventory import RAW_DIR, normalise_sheet_name

MISSING_MARKERS = {"-", "n/a", "na", "none", "nil"}
EXCEL_ERRORS = {"#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!"}


def read_sheet(rel_path, sheet_name):
    """All rows of one sheet as lists of cell values (saved values, never formulas).

    Helper copies whose name starts with '0' (e.g. '0A. Student Data') are skipped;
    they repeat the real sheet (data dictionary P-14). Returns (sheet title, rows),
    or (None, []) when the file has no such sheet.
    """
    # openpyxl warns about Excel features it can't read (data validation, headers/footers)
    # while it reads rows, so the whole read is wrapped. Cell values are unaffected.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = load_workbook(RAW_DIR / rel_path, read_only=True, data_only=True)
        try:
            matches = [ws for ws in wb.worksheets
                       if normalise_sheet_name(ws.title) == sheet_name and not ws.title.strip().startswith("0")]
            if not matches:
                return None, []
            if len(matches) > 1:
                raise ValueError(f"several '{sheet_name}' sheets: {[ws.title for ws in matches]}")
            ws = matches[0]
            return ws.title, [list(r) for r in ws.iter_rows(values_only=True)]
        finally:
            wb.close()


def cell(row, col):
    """Value at a 0-based column, or None when the row is shorter."""
    return row[col] if col < len(row) else None


def cell_ref(row_idx, col_idx):
    """0-based indexes -> Excel reference such as 'AB8'."""
    return f"{get_column_letter(col_idx + 1)}{row_idx + 1}"


def clean_text(value):
    if not isinstance(value, str):
        return None
    text = re.sub(r"\s+", " ", value).strip()
    return text or None


def clean_name(value):
    """Text of a name cell (entity, degree, program). An Excel error such as '#REF!' is not a name:
    it comes from a broken formula that was meant to copy the name from another tab."""
    text = clean_text(value)
    return None if text in EXCEL_ERRORS else text


def to_count(value):
    """Turn a cell into (count, text).

    count is a whole number, or None when the cell is blank or not a usable number.
    text keeps the original content whenever it isn't a clean number (e.g. 'N/A'),
    so nothing is silently lost. Blank stays blank: it is never turned into zero.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, None
    if isinstance(value, bool):
        return None, str(value)
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return int(value), None
        return None, str(value)
    text = str(value).strip()
    if re.fullmatch(r"-?\d+(\.0+)?", text):
        return int(float(text)), None
    if text.lower() in MISSING_MARKERS:
        return None, text
    return None, text
