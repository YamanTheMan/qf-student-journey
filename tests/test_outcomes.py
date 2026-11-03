from pathlib import Path

import pandas as pd

from pipeline.outcomes import apply_earliest_report, graduating_class

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed" / "outcomes.csv"


def test_class_comes_from_header_then_block_label_then_form():
    assert graduating_class("AY 2021-22", None, "2022-2023") == ("2021-2022", "label")
    assert graduating_class(None, "Class of 2023", "2024-2025") == ("2022-2023", "label")
    assert graduating_class(None, None, "2023-2024") == ("2022-2023", "form_default")  # previous academic year


def rows(**cols):
    base = {"university": "U-1", "period_label": None, "band_label": None}
    return pd.DataFrame([{**base, **r} for r in pd.DataFrame(cols).to_dict("records")])


def test_same_class_unnamed_then_named_is_counted_once():
    # CMU-Q: the 2023-24 sheet lists programs without names; the 2024-25 sheet repeats the class with names
    t = rows(file_year=["2023-2024", "2024-2025"], source_file=["first", "repeat"],
             row_type=["all_programs", "program"], program=["All programs", "Physics"],
             stage=["employed", "employed"], count=[10, 10], band_label=[None, "Class of 2023"])
    out = apply_earliest_report(t)
    assert dict(zip(out.source_file, out.report_status)) == {"first": "used", "repeat": "later_report"}
    assert list(out.years_after_graduation) == [1, 2]


def test_class_size_without_outcomes_is_not_a_report():
    t = rows(file_year=["2023-2024", "2023-2024", "2024-2025"], source_file=["a", "a", "b"],
             row_type=["program"] * 3, program=["Physics"] * 3, stage=["graduates", "employed", "employed"],
             count=[40, 0, 30], band_label=[None, None, "Class of 2023"])
    out = apply_earliest_report(t)
    assert list(out.report_status) == ["empty", "empty", "used"]


def read():
    return pd.read_csv(PROCESSED, dtype={"degree_raw": str, "program_raw": str}, keep_default_na=False,
                       na_values={"count": [""], "level": [""], "program": [""]})


def test_each_class_is_used_from_exactly_one_file():
    used = read().query("report_status == 'used'")
    assert used.groupby(["university", "graduating_year"]).source_file.nunique().max() == 1


def test_wcmq_class_sizes_match_dated_graduates():
    # Independent check: WCM-Q's Student Data graduates were 41, 42, 50 for these classes
    t = read()
    sizes = t[(t.university == "WCM-Q") & (t.report_status == "used") & (t.stage == "graduates")
              & (t.breakdown == "total") & t.row_type.isin(["program", "all_programs"])]
    assert sizes.groupby("graduating_year")["count"].sum().to_dict() == \
        {"2020-2021": 41, "2021-2022": 41, "2022-2023": 42, "2023-2024": 50}


def test_every_program_row_is_mapped():
    t = read()
    assert t[t.row_type.isin(["program", "all_programs"])].level.notna().all()
