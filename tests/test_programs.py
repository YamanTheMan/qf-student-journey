from pathlib import Path

import pandas as pd

from pipeline.programs import apply_program_map, load_program_map

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed" / "student_data.csv"
MAPPING = pd.DataFrame(
    [("U-1", "BS", "Cyber Security", "Cybersecurity", "Cybersecurity", "graduate", "Master's", "Computing & Data"),
     ("U-1", "", "Foundation", "Foundation Program", "Foundation Program", "foundation", "Foundation", "General & Foundation")],
    columns=["university", "degree_raw", "program_raw", "program", "program_group", "level", "qualification", "field"])


def test_spellings_map_and_raw_names_are_kept():
    t = pd.DataFrame({"university": ["U-1", "U-1"], "degree": ["BS", None], "program": ["Cyber Security", "Foundation"],
                      "row_type": ["program", "program"]})
    out, unmapped = apply_program_map(t, MAPPING)
    assert list(out.program) == ["Cybersecurity", "Foundation Program"]
    assert list(out.program_raw) == ["Cyber Security", "Foundation"]
    assert list(out.level) == ["graduate", "foundation"]
    assert unmapped == []


def test_new_spellings_are_reported_not_guessed():
    t = pd.DataFrame({"university": ["U-1"], "degree": ["MS"], "program": ["Cybersecurity"], "row_type": ["program"]})
    out, unmapped = apply_program_map(t, MAPPING)
    assert out.program.isna().all()
    assert unmapped == [("U-1", "MS", "Cybersecurity")]


def test_subtotals_and_footers_get_no_program():
    t = pd.DataFrame({"university": ["U-1", "U-1"], "degree": ["BS", None], "program": ["Cyber Security", None],
                      "row_type": ["unnamed_row", "sheet_total"]})
    out, unmapped = apply_program_map(t, MAPPING)
    assert out.program.isna().all() and unmapped == []


def read_processed():
    # Text such as 'N/A' must stay text: pandas would otherwise read it as missing
    return pd.read_csv(PROCESSED, dtype={"degree_raw": str, "program_raw": str}, keep_default_na=False,
                       na_values={"count": [""], "level": [""], "program": [""]})


def test_every_program_row_in_the_processed_table_is_mapped():
    sd = read_processed()
    rows = sd[sd.row_type.isin(["program", "all_programs"])]
    assert rows.level.notna().all()


def test_known_fixes_on_real_data():
    sd = read_processed()
    def first(uni, year, raw, degree=None):
        rows = sd[(sd.university == uni) & (sd.file_year == year) & (sd.program_raw == raw)]
        if degree is not None:
            rows = rows[rows.degree_raw == degree]
        return rows.iloc[0].program, rows.iloc[0].level
    # TAMU-Q 2023-24 swapped its Degree and Program columns (P-18)
    assert first("TAMU-Q", "2023-2024", "Undergraduate", "Chemical Engineering") == ("Chemical Engineering", "undergraduate")
    assert first("TAMU-Q", "2023-2024", "Undergraduate", "Aggie Gateway Program") == ("Gateway Program", "foundation")
    assert first("TAMU-Q", "2023-2024", "Graduate", "MS-CHEN") == ("Chemical Engineering (graduate)", "graduate")
    assert first("HBKU", "2023-2024", "Cyber Security") == ("Cybersecurity", "graduate")
    assert first("VCU-Q", "2019-2020", "Bachelor of Fine Arts (Pre-Art Foundation, for Qatari students only)", "N/A") \
        == ("Pre-Art Foundation", "foundation")
    assert first("WCM-Q", "2024-2025", "Six-Year Medical Program") == ("Six-Year Medical Program (pre-medical)", "undergraduate")
    assert first("HBKU", "2022-2023", "Non-Degree/Conditional Admits")[1] == "non_degree"
