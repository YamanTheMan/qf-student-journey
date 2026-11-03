import pandas as pd

from pipeline.graduates import assign_graduating_class, year_from_label
from pipeline.sources import submissions
from pipeline.student_data import extract_file


def test_graduation_dates_become_academic_years():
    assert year_from_label("May 2024 Graduates") == "2023-2024"
    assert year_from_label("Graduating Class May 2023") == "2022-2023"
    assert year_from_label("Class of 2025") == "2024-2025"
    assert year_from_label("December 2024") == "2024-2025"   # Aug-Dec starts a new academic year


def test_other_labels_are_not_graduation_dates():
    for label in ("As of Fall 2024", "ENROLLMENT", "", None):
        assert year_from_label(label) is None


def graduated_rows(**cols):
    base = {"stage": "graduated", "row_type": "program", "breakdown": "total",
            "period_label": None, "band_label": None}
    return pd.DataFrame([{**base, **row} for row in pd.DataFrame(cols).to_dict("records")])


EXCEPTIONS = pd.DataFrame(
    [("U-1", "2022-2023", "2021-2022", "reported", "remark", "Remark: 'class of 2022'")],
    columns=["university", "file_year", "graduating_year", "status", "evidence_type", "evidence"],
).set_index(["university", "file_year"])


def test_priority_label_then_exception_then_form_default():
    t = graduated_rows(university=["U-1", "U-1", "U-2"], file_year=["2022-2023"] * 3,
                       source_file=["a", "a", "b"], count=[5, 5, 5],
                       period_label=["May 2023", None, None])
    out = assign_graduating_class(t, EXCEPTIONS)
    assert list(out.graduating_year) == ["2022-2023", "2021-2022", "2022-2023"]
    assert list(out.timing_evidence) == ["label", "remark", "form_default"]


def test_all_zero_file_is_not_reported():
    t = graduated_rows(university=["U-2", "U-2"], file_year=["2021-2022"] * 2,
                       source_file=["z", "z"], count=[0, None])
    out = assign_graduating_class(t, EXCEPTIONS)
    assert set(out.graduates_status) == {"not_reported"}


def test_same_class_in_two_files_latest_wins():
    t = graduated_rows(university=["U-2", "U-2"], file_year=["2022-2023", "2023-2024"],
                       source_file=["old", "new"], count=[10, 12],
                       period_label=[None, "May 2023"])
    out = assign_graduating_class(t, EXCEPTIONS)
    assert dict(zip(out.source_file, out.graduates_status)) == {"old": "superseded", "new": "used"}


def test_cmuq_graduates_form_a_continuous_series():
    # D-011 on real files: CMU-Q's Fall files report the previous class; the rule fills 2021-22
    rows = [r for s in submissions() if s.university == "CMU-Q" for r in extract_file(s)]
    out = assign_graduating_class(pd.DataFrame(rows))
    g = out[(out.stage == "graduated") & (out.breakdown == "total") & (out.row_type == "program")
            & (out.graduates_status == "used")]
    series = g.groupby("graduating_year")["count"].sum().to_dict()
    assert series == {"2019-2020": 77, "2020-2021": 95, "2021-2022": 87,
                      "2022-2023": 103, "2023-2024": 120, "2024-2025": 110}
