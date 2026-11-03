"""Read 'list' sheets: one row per item (a country, an age, a detailed student group) rather than
one row per program.

A list table starts at a header row that has every key column (e.g. 'Nationality') and at least
one count column. It ends at the footer: the next row with a count header and no key text, whose
inconsistently worded totals are not read (totals are rebuilt by adding up the rows and checked
against Student Data instead). Every row with key text is read; a row inside the table with
numbers but no key text is reported, so nothing is dropped silently. Blank cells are left out:
in a list every item is printed in advance, so a blank says nothing that a missing row doesn't.
"""
import re

import pandas as pd

from pipeline.sources import submissions
from pipeline.workbook import cell, cell_ref, cell_text, clean_text, read_sheet, to_count


def _header_row(row, keys, parse_value):
    """({key: column}, {column: value attributes}) found in one row."""
    key_cols, value_cols = {}, {}
    for c, v in enumerate(row):
        text = (clean_text(v) or "").lower()
        if not text:
            continue
        for key, matches in keys.items():
            if matches(text):
                key_cols.setdefault(key, c)
        if (attrs := parse_value(v)) is not None:
            value_cols[c] = attrs
    return key_cols, value_cols


def extract_list(src, sheet_name, keys, parse_value, issues=None, required=None):
    """Every number in one file's list sheet, as a list of row dicts.

    `required` names the key columns the header row must have (default: all of them); the
    others are read when the file has them.
    """
    if sheet_name in src.skip_sheets:
        return []  # excluded by a decision in data/reference/sheet_exclusions.csv
    sheet, rows = read_sheet(src.path, sheet_name)
    if sheet is None:
        raise ValueError(f"no '{sheet_name}' sheet")
    required = set(required or keys)
    start = None
    for i, row in enumerate(rows):
        key_cols, value_cols = _header_row(row, keys, parse_value)
        if required <= set(key_cols) and value_cols:
            start = i
            break
    if start is None:
        raise ValueError(f"'{sheet_name}': no header row with {', '.join(sorted(required))}")

    records = []
    for r in range(start + 1, len(rows)):
        row = rows[r]
        # cell_text: ages and dates are often stored as numbers, not text
        key_values = {k: cell_text(cell(row, key_cols[k])) if k in key_cols else None for k in keys}
        if not any(key_values.values()) and _header_row(row, {}, parse_value)[1]:
            break  # the footer
        if re.match(r"(grand )?total\b", (key_values[next(iter(keys))] or "").lower()):
            break  # a 'Total ...' row is the footer too, never an item called 'Total'
        if not any(key_values.values()):
            if issues is not None and any((to_count(cell(row, c))[0] or 0) != 0 for c in value_cols):
                issues.append(f"{src.path} '{sheet}' row {r + 1}: has numbers but no {next(iter(keys))}")
            continue
        for c, attrs in value_cols.items():
            if not src.keeps(key_values.get("program"), attrs["stage"]):
                continue
            count, text = to_count(cell(row, c))
            if count is None and text is None:
                continue
            records.append({
                "file_year": src.academic_year,
                "university": src.university,
                **key_values,
                **attrs,
                "count": count,
                "value_text": text,
                "template": src.template,
                "source_file": src.path,
                "source_sheet": sheet,
                "source_cell": cell_ref(r, c),
            })
    return records


def extract_list_sheet(sheet_name, keys, parse_value, templates, required=None, missing_ok=False):
    """Extract one list sheet from every submission using these templates: (table, problems).

    missing_ok: some template variants leave the sheet out (e.g. two 2021-22 files have no
    Registered Students Detailed); those files are listed but don't stop the build.
    """
    records, problems = [], []
    for src in submissions(templates):
        try:
            records.extend(extract_list(src, sheet_name, keys, parse_value, problems, required))
        except ValueError as err:
            if missing_ok and str(err).startswith("no '"):
                print(f"(no '{sheet_name}' sheet in {src.path})")
            else:
                problems.append(f"{src.path}: {err}")
    table = pd.DataFrame(records)
    table["count"] = table["count"].astype("Int64")
    return table, problems
