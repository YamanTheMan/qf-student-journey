"""Phase 2: extract the Student Data sheet from every university submission.

Writes data/processed/student_data.csv with one row per number found:
what it counts (stage, nationality, residency, gender), where it belongs
(year, university, program) and exactly where it came from (file and cell).

Run from the project folder:
    .venv/bin/python -m pipeline.student_data
"""
import pandas as pd

from pipeline.graduates import assign_graduating_class
from pipeline.headers import parse_measure
from pipeline.inventory import ROOT
from pipeline.programs import apply_program_map
from pipeline.sources import submissions
from pipeline.workbook import cell, cell_ref, clean_text, read_sheet, to_count

OUTPUT = ROOT / "data" / "processed" / "student_data.csv"
TEMPLATES = ("v2019", "v2020", "v2021", "v2022")  # v2021-alt (VCU-Q 2021-22) has its own reader
MIN_MEASURES = 3       # a row with at least this many count headers is a header row
MAX_BAND_LENGTH = 60   # longer text above the table is instructions, not a period label


def find_header_rows(rows):
    """[(row index, {column: Measure}, {label: column})] for every header row in the sheet."""
    headers = []
    for i, row in enumerate(rows):
        measures = {c: m for c, v in enumerate(row) if (m := parse_measure(v))}
        if len(measures) >= MIN_MEASURES:
            labels = {}
            for c, v in enumerate(row):
                text = (clean_text(v) or "").lower()
                for label in ("entity name", "degree", "program", "remarks"):
                    if text == label or (label == "remarks" and text.startswith("remarks")):
                        labels.setdefault(label, c)
            headers.append((i, measures, labels))
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


def extract_file(src):
    """Every number in one file's Student Data sheet, as a list of row dicts."""
    sheet, rows = read_sheet(src.path, "student data")
    if sheet is None:
        raise ValueError("no Student Data sheet")
    headers = find_header_rows(rows)
    if not any("program" in labels for _, _, labels in headers):
        raise ValueError("no header row with a Program column")

    records = []
    for h, (hdr_idx, measures, labels) in enumerate(headers):
        end = headers[h + 1][0] if h + 1 < len(headers) else len(rows)

        if "program" in labels:
            bands = band_labels(rows, hdr_idx, min(measures))
            # A data row names a program, an entity or a degree; empty placeholder rows are skipped.
            # (Never test the text against header words: real programs are called things like
            # 'Applied Islamic Ethics'.)
            id_cols = [labels[k] for k in ("entity name", "degree", "program") if k in labels]
            data_rows = [r for r in range(hdr_idx + 1, end) if any(clean_text(cell(rows[r], c)) for c in id_cols)]
            has_named_programs = any(clean_text(cell(rows[r], labels["program"])) for r in data_rows)
        else:
            # A header row without a Program column is the footer: its first row of numbers
            # holds the university totals (data dictionary: VCU-Q footers).
            bands = {}
            data_rows = [next((r for r in range(hdr_idx + 1, end)
                               if any(to_count(cell(rows[r], c))[0] is not None for c in measures)), None)]
            data_rows = [r for r in data_rows if r is not None]

        for r in data_rows:
            row = rows[r]
            program = clean_text(cell(row, labels["program"])) if "program" in labels else None
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
            for col, m in measures.items():
                if not src.keeps(program, m.stage):
                    continue
                count, text = to_count(cell(row, col))
                records.append({
                    "file_year": src.academic_year,
                    "university": src.university,
                    "row_type": row_type,
                    "entity_reported": clean_text(cell(row, labels["entity name"])) if "entity name" in labels else None,
                    "degree": clean_text(cell(row, labels["degree"])) if "degree" in labels else None,
                    "program": program,
                    "stage": m.stage,
                    "nationality": m.nationality,
                    "residency": m.residency,
                    "gender": m.gender,
                    "breakdown": m.breakdown,
                    "period_label": m.period,
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


def extract_all():
    records, problems = [], []
    for src in submissions(TEMPLATES):
        try:
            records.extend(extract_file(src))
        except ValueError as err:
            problems.append(f"{src.path}: {err}")
    table = pd.DataFrame(records)
    table["count"] = table["count"].astype("Int64")
    table, unmapped = apply_program_map(assign_graduating_class(table))
    problems += [f"program spelling not in data/reference/programs.csv: {u} | {d or '(blank)'} | {p or '(blank)'}"
                 for u, d, p in unmapped]
    return table, problems


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files\n")
    filled = table[table["count"].notna()]
    print("Numbers found per year and stage (blank cells excluded):")
    print(pd.crosstab(filled["file_year"], filled["stage"]).to_string(), "\n")
    print("Rows per breakdown:", table["breakdown"].value_counts().to_dict())
    print("Row types:", table["row_type"].value_counts().to_dict())
    print(f"Blank cells: {table['count'].isna().sum():,}   non-numeric text cells: {table['value_text'].notna().sum():,}")
    grad = table[table["stage"] == "graduated"]
    print("Graduated numbers by status:", grad["graduates_status"].value_counts().to_dict())
    print("...and by timing evidence:", grad["timing_evidence"].value_counts().to_dict())
    reg = table[(table["stage"] == "registered") & (table["breakdown"] == "total") & table["level"].notna()]
    print("\nRegistered students by level (reported totals):")
    print(reg.pivot_table(index="file_year", columns="level", values="count", aggfunc="sum").to_string())
    if problems:
        print(f"\nProblems that need a person ({len(problems)}):")
        for p in problems:
            print("  ", p)
        raise SystemExit(1)  # stop the build: nothing unmapped or unreadable reaches the dashboard


if __name__ == "__main__":
    main()
