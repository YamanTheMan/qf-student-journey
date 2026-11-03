"""Read any sheet laid out as 'one row per program, one column per count'.

Most sheets in the form share this layout: a header row naming each column, then one row
per program, sometimes a footer with university totals. Only the meaning of the headers
differs, so each sheet supplies its own header reader and everything else is shared:
finding header rows, telling programs from subtotals and footers, applying the file
decisions, and recording the exact source cell of every number.
"""
import pandas as pd

from pipeline.programs import apply_program_map
from pipeline.sources import submissions
from pipeline.workbook import cell, cell_ref, clean_name, clean_text, read_sheet, to_count

MIN_HEADERS = 3        # a row with at least this many count headers is a header row
MAX_BAND_LENGTH = 60   # longer text above the table is instructions, not a period label
ID_LABELS = ("entity name", "degree", "program", "remarks")


def find_header_rows(rows, parse_header, row_fields=None):
    """[(row index, {column: header attributes}, {label: column})] for every header row.

    row_fields maps an extra output column to a test on the header text, for sheets with more
    than names per row (e.g. Graduation Rate's cohort year).
    """
    row_fields = row_fields or {}
    headers = []
    for i, row in enumerate(rows):
        parsed = {c: attrs for c, v in enumerate(row) if (attrs := parse_header(v))}
        if len(parsed) >= MIN_HEADERS:
            labels = {}
            for c, v in enumerate(row):
                text = (clean_text(v) or "").lower()
                for label in ID_LABELS:
                    if text == label or (label == "remarks" and text.startswith("remarks")):
                        labels.setdefault(label, c)
                for field, matches in row_fields.items():
                    if text and matches(text):
                        labels.setdefault(field, c)
            headers.append((i, parsed, labels))
    return headers


def band_labels(rows, header_idx, first_col):
    """Short text above the table (e.g. 'As of Fall 2024', 'May 2024 Graduates') for each column.

    A band label sits above the first column of the block it describes, so each column takes
    the nearest label to its left, row by row.
    """
    bands = [(c, text) for row in rows[:header_idx] for c, v in enumerate(row)
             if c >= first_col and (text := clean_text(v)) and len(text) <= MAX_BAND_LENGTH]
    width = max((len(r) for r in rows), default=0)
    by_column = {}
    for col in range(first_col, width):
        left = [text for c, text in bands if c <= col]
        by_column[col] = left[-1] if left else None
    return by_column


def extract_table(src, sheet_name, parse_header, issues=None, row_fields=None):
    """Every number in one file's sheet, as a list of row dicts.

    parse_header(text) returns a dict describing a count column (it must include 'stage'),
    or None for any other column. Rows that look wrong are described in `issues`.
    """
    sheet, rows = read_sheet(src.path, sheet_name)
    if sheet is None:
        raise ValueError(f"no '{sheet_name}' sheet")
    row_fields = row_fields or {}
    headers = find_header_rows(rows, parse_header, row_fields)
    if not any("program" in labels for _, _, labels in headers):
        raise ValueError(f"'{sheet_name}': no header row with a Program column")

    records = []
    for h, (hdr_idx, columns, labels) in enumerate(headers):
        end = headers[h + 1][0] if h + 1 < len(headers) else len(rows)

        if "program" in labels:
            bands = band_labels(rows, hdr_idx, min(columns))
            # A data row names a program, an entity or a degree; empty placeholder rows are skipped.
            # (Never test the text against header words: real programs are called things like
            # 'Applied Islamic Ethics'.)
            # Extra row fields (e.g. a cohort year) also mark a data row: GU-Q 2023-24 reports one
            # unnamed row per entering class for the whole university.
            id_cols = [labels[k] for k in ("entity name", "degree", "program", *row_fields) if k in labels]
            named = {r: any(clean_name(cell(rows[r], c)) for c in id_cols) for r in range(hdr_idx + 1, end)}
            data_rows = [r for r, has_name in named.items() if has_name]
            has_named_programs = any(clean_name(cell(rows[r], labels["program"])) for r in data_rows)
            # Guard: a row skipped for having no name must not hold real numbers, so nothing
            # is ever dropped silently. (Empty placeholder rows hold blanks or formula zeros.)
            for r, has_name in named.items():
                if not has_name and issues is not None and \
                        any((to_count(cell(rows[r], c))[0] or 0) != 0 for c in columns):
                    issues.append(f"{src.path} '{sheet}' row {r + 1}: has numbers but no program name")
        else:
            # A header row without a Program column is the footer: its first row of numbers
            # holds the university totals (data dictionary: VCU-Q footers).
            bands = {}
            data_rows = [next((r for r in range(hdr_idx + 1, end)
                               if any(to_count(cell(rows[r], c))[0] is not None for c in columns)), None)]
            data_rows = [r for r in data_rows if r is not None]

        for r in data_rows:
            row = rows[r]
            program = clean_name(cell(row, labels["program"])) if "program" in labels else None
            if "program" not in labels:
                row_type = "sheet_total"
            elif program:
                row_type = "program"
            elif has_named_programs:
                # No name among named programs: a subtotal (HEC-Q 2022-23 row 12 adds two
                # cohorts) or an empty placeholder. Kept for checking, never added to programs.
                row_type = "unnamed_row"
            else:
                # The university reported one line for all programs together (GU-Q 2023-24).
                row_type = "all_programs"
            for col, attrs in columns.items():
                if not src.keeps(program, attrs["stage"]):
                    continue
                count, text = to_count(cell(row, col))
                records.append({
                    "file_year": src.academic_year,
                    "university": src.university,
                    "row_type": row_type,
                    "entity_reported": clean_name(cell(row, labels["entity name"])) if "entity name" in labels else None,
                    "degree": clean_name(cell(row, labels["degree"])) if "degree" in labels else None,
                    "program": program,
                    **{f: _field_value(cell(row, labels[f])) if f in labels else None for f in row_fields},
                    **attrs,
                    "band_label": bands.get(col),
                    "count": count,
                    "value_text": text,
                    "remarks": clean_text(cell(row, labels["remarks"])) if "remarks" in labels else None,
                    "template": src.template,
                    "source_file": src.path,
                    "source_sheet": sheet,
                    "source_cell": cell_ref(r, col),
                })
    return records


def _field_value(value):
    """An extra row field as text ('AY2018/2019', '4'), so mixed text and numbers stay comparable."""
    count, text = to_count(value)
    return str(count) if count is not None else clean_name(text)


def extract_sheet(sheet_name, parse_header, templates, row_fields=None):
    """Extract one sheet from every submission using these templates.

    Returns (table, problems). Problems are files that couldn't be read and program
    spellings missing from programs.csv; a build with problems must stop.
    """
    records, problems = [], []
    for src in submissions(templates):
        try:
            records.extend(extract_table(src, sheet_name, parse_header, problems, row_fields))
        except ValueError as err:
            problems.append(f"{src.path}: {err}")
    table = pd.DataFrame(records)
    table["count"] = table["count"].astype("Int64")
    return table, problems


def map_programs(table, problems):
    """Add the standard program columns; unknown spellings become problems."""
    table, unmapped = apply_program_map(table)
    problems = problems + [
        f"program spelling not in data/reference/programs.csv: {u} | {d or '(blank)'} | {p or '(blank)'}"
        for u, d, p in unmapped]
    return table, problems


def report_problems(problems):
    """Print problems and stop the build, so nothing unreadable or unmapped reaches the dashboard."""
    if problems:
        print(f"\nProblems that need a person ({len(problems)}):")
        for p in problems:
            print("  ", p)
        raise SystemExit(1)
