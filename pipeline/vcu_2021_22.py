"""Phase 2: VCU-Q's 2021-22 submission, which uses a completely different form (template v2021-alt, P-04).

Its long tables are turned into rows of the standard tables, so VCU-Q 2021-22 appears wherever
the other years do:
  Admission           -> student_data: applied, admitted (program x nationality x gender); no newly enrolled
  Student Statistics  -> student_data: registered; registered_detailed; nationalities and ages (side tables)
                         Fall 2021 only: the census date the form asks for. The Spring 2022 rows are
                         a second snapshot and are not read (the same choice as QF's consolidated file).
  Alumni              -> student_data: graduated, 'Gradautes - 2021-2022' = the class of 2021-22
The form has no totals, so program totals are computed from their parts and say so in `remarks`.
A number added up from several rows keeps every source cell, e.g. 'O3+O5+O9'.
"""
from collections import defaultdict

from openpyxl.utils import get_column_letter

from pipeline.sources import submissions
from pipeline.workbook import cell, cell_text, clean_text, read_sheet, to_count

TEMPLATE = "v2021-alt"
SNAPSHOT = "Fall 2021"
GENDERS = {"m": "Male", "f": "Female"}
COMPUTED = "Total computed from the nationality x gender rows (this form has no totals)."


def source():
    return next(s for s in submissions((TEMPLATE,)) if s.university == "VCU-Q")


def ref(r, c):
    return f"{get_column_letter(c + 1)}{r + 1}"


def columns(header_row):
    """{lower-case header: column}, first occurrence wins."""
    out = {}
    for c, v in enumerate(header_row):
        text = (clean_text(v) or "").lower()
        if text:
            out.setdefault(text, c)
    return out


def student_record(src, sheet, degree, program, stage, nationality, gender, count, cells, remarks=None, period=None):
    return {
        "file_year": src.academic_year, "university": src.university, "row_type": "program",
        "entity_reported": "VCU-Q", "degree": degree, "program": program, "stage": stage,
        "nationality": nationality, "residency": "All", "gender": gender,
        "breakdown": "total" if nationality == "All" else "nationality_gender",
        "period_label": period, "band_label": None, "count": count, "value_text": None, "remarks": remarks,
        "template": src.template, "source_file": src.path, "source_sheet": sheet, "source_cell": "+".join(cells),
    }


def with_totals(records):
    """Add one computed total per program and stage (blank when every part is blank)."""
    groups = defaultdict(list)
    for r in records:
        groups[(r["degree"], r["program"], r["stage"])].append(r)
    totals = []
    for parts in groups.values():
        filled = [p for p in parts if p["count"] is not None]
        total = {**parts[0], "nationality": "All", "gender": "All", "breakdown": "total", "remarks": COMPUTED,
                 "count": sum(p["count"] for p in filled) if filled else None,
                 "source_cell": "+".join(p["source_cell"] for p in filled)}
        totals.append(total)
    return records + totals


def blocks(rows, start, degree_col, program_col):
    """Yield (row index, degree, program) with each block's names carried down to its rows.

    A block starts on a row with a program name; labels on later rows of the block (VCU-Q row 7
    repeats 'Art Foundation' in the degree column) are ignored.
    """
    degree = program = None
    for r in range(start, len(rows)):
        if clean_text(cell(rows[r], program_col)):
            degree, program = clean_text(cell(rows[r], degree_col)), clean_text(cell(rows[r], program_col))
        if program:
            yield r, degree, program


def admission(src):
    sheet, rows = read_sheet(src.path, "admission")
    col = columns(rows[0])
    # The sheet's 'Registered' column is not read: it adds up to all 302 registered students (not
    # the new ones: only 139 were admitted), and registered students come from Student Statistics.
    stages = {"applied": "applied", "admitted": "admitted"}
    records = []
    for r, degree, program in blocks(rows, 1, 1, 2):
        nationality, gender = clean_text(cell(rows[r], col["nationality"])), GENDERS.get(
            (clean_text(cell(rows[r], col["gender"])) or "").lower())
        if not nationality or not gender:
            continue
        for header, stage in stages.items():
            count, _ = to_count(cell(rows[r], col[header]))
            records.append(student_record(src, sheet, degree, program, stage, nationality, gender, count,
                                          [ref(r, col[header])]))
    return with_totals(records)


def alumni(src):
    sheet, rows = read_sheet(src.path, "alumni")
    hdr = next(i for i, row in enumerate(rows) if "college" in columns(row))
    col = columns(rows[hdr])
    records = []
    for r, degree, program in blocks(rows, hdr + 1, col["student level"], col["student major"]):
        nationality = clean_text(cell(rows[r], col["nationality"]))
        gender = GENDERS.get((clean_text(cell(rows[r], col["gender"])) or "").lower())
        if not nationality or not gender:
            continue
        count, _ = to_count(cell(rows[r], col["total"]))
        records.append(student_record(src, sheet, degree, program, "graduated", nationality, gender, count,
                                      [ref(r, col["total"])], period="Class of 2022"))
    return with_totals(records)


def fall_detail(src):
    """Student Statistics detail rows of the Fall 2021 snapshot: (row index, {field: value}, count)."""
    sheet, rows = read_sheet(src.path, "student statistics")
    col = columns(rows[0])
    fields = {"degree": "qualification", "program": "student major", "nationality": "nationality",
              "country": "country", "gender": "gender", "attendance": "ft-pt indicator",
              "sponsorship": "sponsorship", "scholarship": "scholarship", "language": "language of study",
              "year_class": "class levels"}
    out = []
    for r in range(1, len(rows)):
        if clean_text(cell(rows[r], col["strarting date"])) != SNAPSHOT:
            continue
        values = {k: cell_text(cell(rows[r], col[h])) for k, h in fields.items()}
        count, _ = to_count(cell(rows[r], col["total"]))
        out.append((r, values, count))
    return sheet, rows, col, out


def registered(src):
    sheet, _, col, detail = fall_detail(src)
    groups = defaultdict(lambda: [0, []])
    for r, v, count in detail:
        key = (v["degree"], v["program"], v["nationality"], GENDERS.get((v["gender"] or "").lower(), v["gender"]))
        if count is not None:
            groups[key][0] += count
            groups[key][1].append(ref(r, col["total"]))
    records = [student_record(src, sheet, d, p, "registered", n, g, total, cells, period=SNAPSHOT)
               for (d, p, n, g), (total, cells) in groups.items()]
    return with_totals(records)


def student_data_records():
    src = source()
    return admission(src) + registered(src) + alumni(src)


def detailed_records():
    """Rows in the shape of registered_detailed.csv, one per Fall 2021 detail row."""
    src = source()
    sheet, _, col, detail = fall_detail(src)
    return [{
        "file_year": src.academic_year, "university": src.university, "entity_reported": "VCU-Q",
        "degree": v["degree"], "program": v["program"], "nationality": v["country"] or v["nationality"],
        "gender": GENDERS.get((v["gender"] or "").lower(), v["gender"]), "attendance": v["attendance"],
        "scholarship": v["scholarship"], "sponsorship": v["sponsorship"], "language": v["language"],
        "year_class": v["year_class"], "stage": "registered", "count": count, "value_text": None,
        "template": src.template, "source_file": src.path, "source_sheet": sheet, "source_cell": ref(r, col["total"]),
    } for r, v, count in detail if count is not None]


def side_table(src, key_header, value_headers, key_name):
    """A side table of Student Statistics (countries or ages): its key column is the one whose
    header is directly followed by the value headers."""
    sheet, rows = read_sheet(src.path, "student statistics")
    hdr = rows[0]
    texts = [(clean_text(v) or "").lower() for v in hdr]
    key_col = next(c for c, t in enumerate(texts) if t == key_header and texts[c + 1:c + 1 + len(value_headers)]
                   == [h for h, _ in value_headers])
    records = []
    for r in range(1, len(rows)):
        key = cell_text(cell(rows[r], key_col))
        if not key or key.lower().startswith("total"):
            continue  # 'Total' / 'Total Students' rows are totals, not an age or a country
        for offset, (_, gender) in enumerate(value_headers, start=1):
            count, text = to_count(cell(rows[r], key_col + offset))
            if count is None and text is None:
                continue
            records.append({
                "file_year": src.academic_year, "university": src.university, key_name: key,
                "stage": "registered", "gender": gender, "breakdown": "gender" if gender != "All" else "total",
                "count": count, "value_text": text, "template": src.template, "source_file": src.path,
                "source_sheet": sheet, "source_cell": ref(r, key_col + offset),
            })
    return records


def nationality_records():
    return side_table(source(), "nationality", [("# male", "Male"), ("# female", "Female"), ("total", "All")],
                      "country_raw")


def age_records():
    return side_table(source(), "age", [("# male students", "Male"), ("# female students", "Female")], "age")
