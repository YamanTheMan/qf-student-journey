from pathlib import Path

import pandas as pd

from pipeline.nationalities import mark_duplicates, standardise_countries
from pipeline.registered_detailed import ATTENDANCE, standard_value

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
READ = dict(keep_default_na=False, na_values={"count": [""], "level": [""]}, dtype={"degree_raw": str, "program_raw": str})
COUNTRIES = pd.DataFrame({"spelling": ["Qatar", "Viet Nam", "Vietnam", "Non-Qatari"],
                          "country": ["Qatar", "Vietnam", "Vietnam", "Non-Qatari (country not given)"],
                          "region": ["Qatar", "East & Southeast Asia & Pacific", "East & Southeast Asia & Pacific", "Not given"]})


def test_country_names_and_regions_are_standardised():
    t = pd.DataFrame({"country_raw": ["QATAR", "Qatar", " Viet Nam ", "NON-QATARI"]})
    out, problems = standardise_countries(t, COUNTRIES)
    assert list(out.country) == ["Qatar", "Qatar", "Vietnam", "Non-Qatari (country not given)"]
    assert list(out.region) == ["Qatar", "Qatar", "East & Southeast Asia & Pacific", "Not given"]
    assert problems == []


def test_an_unknown_country_spelling_stops_the_build():
    _, problems = standardise_countries(pd.DataFrame({"country_raw": ["Atlantis"]}), COUNTRIES)
    assert problems == ["country spelling not in data/reference/countries.csv: 'Atlantis'"]


def test_a_country_listed_twice_is_used_once_or_stops_the_build():
    t = pd.DataFrame({"source_file": ["f"] * 6, "country": ["Qatar", "Qatar", "Oman", "Oman", "Myanmar", "Myanmar"],
                      "stage": ["registered"] * 6, "gender": ["All"] * 6, "count": [174, 174, 3, 4, 0, 1]})
    out, problems = mark_duplicates(t)
    # repeated summary row -> once; two different non-zero numbers -> a person decides;
    # 'Burma' (0) and 'Myanmar' (1) under two names in the form -> both used, adding up to 1
    assert list(out.row_status) == ["used", "duplicate", "used", "used", "used", "used"]
    assert problems == ["f: 'Oman' is listed twice with different numbers"]


def test_nuq_2019_20_summary_rows_are_not_counted_twice():
    nat = pd.read_csv(PROCESSED / "nationalities.csv", **READ)
    used = nat[(nat.university == "NU-Q") & (nat.file_year == "2019-2020") & (nat.row_status == "used")
               & (nat.stage == "registered") & (nat.breakdown == "total")]
    assert used["count"].sum() == 379   # Student Data: 381


def test_detailed_values_are_standardised():
    raw = pd.Series(["FT", "Full-Time", "part time", "Majority Full-Time", None, "n/a"])
    assert list(standard_value(raw, ATTENDANCE).fillna("(blank)")) == \
        ["Full-time", "Full-time", "Part-time", "Mixed", "(blank)", "(blank)"]   # 'n/a' says nothing (D-040)


def test_detailed_sheet_matches_student_data_and_skips_gu_q_summary():
    rd = pd.read_csv(PROCESSED / "registered_detailed.csv", **READ)
    assert not ((rd.university == "GU-Q") & (rd.file_year == "2022-2023")).any()   # D-018
    assert rd[(rd.university == "CMU-Q") & (rd.file_year == "2024-2025")]["count"].sum() == 454
    assert rd[rd.row_type.isin(["program", "all_programs"])].level.notna().all()
