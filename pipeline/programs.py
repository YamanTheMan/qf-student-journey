"""Phase 2: give every program a standard name, a stable group, a level, a qualification and a field.

Universities spell the same program differently from year to year ('Cyber Security' /
'Cybersecurity', one row per HEC-Q cohort, VCU-Q's BFA majors sometimes combined). The
hand-made table data/reference/programs.csv has one row per spelling found in the files
and says what it means (decisions D-015, D-016).
"""
import pandas as pd

from pipeline.inventory import REFERENCE_DIR

PROGRAMS = REFERENCE_DIR / "programs.csv"
STANDARD = ["program", "program_group", "level", "qualification", "field"]
MAPPED_ROWS = ("program", "all_programs")  # subtotals and footers have no program to map
BLANK = ""  # stands in for a missing degree or program name when matching


def load_program_map(path=PROGRAMS):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def apply_program_map(table, mapping=None):
    """Rename the raw columns to degree_raw / program_raw and add the standard columns.

    Returns (table, unmapped) where unmapped lists the (university, degree, program)
    spellings that need a new row in programs.csv.
    """
    mapping = load_program_map() if mapping is None else mapping
    out = table.rename(columns={"degree": "degree_raw", "program": "program_raw"})
    keys = pd.DataFrame({
        "university": out["university"],
        "degree_raw": out["degree_raw"].fillna(BLANK),
        "program_raw": out["program_raw"].fillna(BLANK),
    })
    lookup = mapping.set_index(["university", "degree_raw", "program_raw"])[STANDARD]
    matched = lookup.reindex(pd.MultiIndex.from_frame(keys))
    matched.index = out.index

    eligible = out["row_type"].isin(MAPPED_ROWS)
    for col in STANDARD:
        out[col] = matched[col].where(eligible).astype("string")

    missing = eligible & matched["program"].isna()
    unmapped = sorted(set(map(tuple, keys[missing].values)))
    return out, unmapped
