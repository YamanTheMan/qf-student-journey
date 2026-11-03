from pathlib import Path

import pandas as pd

from pipeline.graduation_rate import apply_latest_report, cohort_year

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed" / "graduation_rate.csv"


def test_cohort_labels_become_the_starting_academic_year():
    assert cohort_year("AY2018/2019") == "2018-2019"
    assert cohort_year("2005-2006") == "2005-2006"
    assert cohort_year("2019-20") == "2019-2020"
    assert cohort_year("AY2022/2024") == "2022-2023"   # HEC-Q two-year program starting in 2022
    assert cohort_year("AY2024") == "2024-2025"
    assert cohort_year(None) is None


def reports(**cols):
    base = {"university": "U-1", "program": "Physics", "cohort": "2018-2019", "row_type": "program"}
    return pd.DataFrame([{**base, **r} for r in pd.DataFrame(cols).to_dict("records")])


def test_latest_real_report_wins():
    t = reports(file_year=["2022-2023", "2023-2024"], source_file=["old", "new"], count=[40, 42])
    assert list(apply_latest_report(t).report_status) == ["superseded", "used"]


def test_a_blank_later_listing_does_not_replace_real_numbers():
    t = reports(file_year=["2022-2023", "2023-2024"], source_file=["old", "new"], count=[40, None])
    assert list(apply_latest_report(t).report_status) == ["used", "empty"]


def read():
    return pd.read_csv(PROCESSED, dtype={"degree_raw": str, "program_raw": str, "cohort": str},
                       keep_default_na=False, na_values={"count": [""], "level": [""], "program": [""]})


def class_sizes(t, university):
    used = t[(t.university == university) & (t.report_status == "used") & (t.stage == "entered") & (t.breakdown == "total")]
    return used.groupby("cohort")["count"].sum()


def test_gu_q_university_wide_classes_go_back_to_2005():
    sizes = class_sizes(read(), "GU-Q")
    assert sizes.index.min() == "2005-2006" and len(sizes) >= 16


def test_cmuq_class_sizes_match_newly_enrolled_students():
    # Independent check: CMU-Q's first-time entering classes = newly enrolled in Student Data (124 in 2020-21)
    assert class_sizes(read(), "CMU-Q")["2020-2021"] == 124


def test_every_program_row_is_mapped():
    t = read()
    assert t[t.row_type.isin(["program", "all_programs"])].level.notna().all()
