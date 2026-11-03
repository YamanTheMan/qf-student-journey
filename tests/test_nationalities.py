from pathlib import Path

import pandas as pd

from pipeline.nationalities import mark_duplicates, standardise_countries
from pipeline.registered_detailed import ATTENDANCE, standard_value

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
READ = dict(keep_default_na=False, na_values={"count": [""], "level": [""]}, dtype={"degree_raw": str, "program_raw": str})
ALIASES = pd.DataFrame({"alias": ["Viet Nam", "Non-Qatari"], "country": ["Vietnam", "Non-Qatari (country not given)"]})


def test_country_names_are_standardised():
    t = pd.DataFrame({"country_raw": ["QATAR", "Qatar", "Qatar", "Viet Nam", "NON-QATARI"]})
    assert list(standardise_countries(t, ALIASES).country) == \
        ["Qatar", "Qatar", "Qatar", "Vietnam", "Non-Qatari (country not given)"]


def test_a_country_listed_twice_is_used_once_or_stops_the_build():
    t = pd.DataFrame({"source_file": ["f"] * 4, "country": ["Qatar", "Qatar", "Oman", "Oman"],
                      "stage": ["registered"] * 4, "gender": ["All"] * 4, "count": [174, 174, 3, 4]})
    out, problems = mark_duplicates(t)
    assert list(out.row_status) == ["used", "duplicate", "used", "used"]
    assert problems == ["f: 'Oman' is listed twice with different numbers"]


def test_nuq_2019_20_summary_rows_are_not_counted_twice():
    nat = pd.read_csv(PROCESSED / "nationalities.csv", **READ)
    used = nat[(nat.university == "NU-Q") & (nat.file_year == "2019-2020") & (nat.row_status == "used")
               & (nat.stage == "registered") & (nat.breakdown == "total")]
    assert used["count"].sum() == 379   # Student Data: 381


def test_detailed_values_are_standardised():
    raw = pd.Series(["FT", "Full-Time", "part time", "Majority Full-Time", None])
    assert list(standard_value(raw, ATTENDANCE).fillna("(blank)")) == \
        ["Full-time", "Full-time", "Part-time", "Mixed", "(blank)"]


def test_detailed_sheet_matches_student_data_and_skips_gu_q_summary():
    rd = pd.read_csv(PROCESSED / "registered_detailed.csv", **READ)
    assert not ((rd.university == "GU-Q") & (rd.file_year == "2022-2023")).any()   # D-018
    assert rd[(rd.university == "CMU-Q") & (rd.file_year == "2024-2025")]["count"].sum() == 454
    assert rd[rd.row_type.isin(["program", "all_programs"])].level.notna().all()
