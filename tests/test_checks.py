"""Each quality check, on tiny tables built for the test."""
import pandas as pd

from pipeline import checks


def rows(**cols):
    return pd.DataFrame(cols).astype({"count": "Float64"})


def statuses(findings):
    return sorted(f["status"] for f in findings)


def one_row(parts, total, breakdown="nationality_gender"):
    """A total in cell F8 and its parts in G8, H8, ... of one Student Data row."""
    n = len(parts)
    return rows(source_file=["f"] * (n + 1), source_cell=[f"{c}8" for c in "FGHIJKL"[:n + 1]],
                stage=["registered"] * (n + 1), period_label=[None] * (n + 1), band_label=[None] * (n + 1),
                breakdown=["total"] + [breakdown] * n, count=[total] + parts,
                university=["U-1"] * (n + 1), file_year=["2024-2025"] * (n + 1))


KEY = ["source_file", "excel_row", "stage", "period_label", "band_label"]


def test_breakdown_statuses():
    assert checks.breakdown_findings("t", one_row([3, 4], 7), KEY) == []
    assert statuses(checks.breakdown_findings("t", one_row([3, 4, None], 7), KEY)) == ["blanks_are_zero"]
    assert statuses(checks.breakdown_findings("t", one_row([3, None], 7), KEY)) == ["partly_withheld"]
    assert statuses(checks.breakdown_findings("t", one_row([None, None], 7), KEY)) == ["withheld"]
    assert statuses(checks.breakdown_findings("t", one_row([None, None], 0), KEY)) == ["formula_zero"]
    mismatch = checks.breakdown_findings("t", one_row([3, 5], 7), KEY)
    assert statuses(mismatch) == ["mismatch"] and mismatch[0]["severity"] == "warning"


def test_computed_totals_are_not_checked_against_themselves():
    t = one_row([3, 4], 9)
    t.loc[0, "source_cell"] = "G8+H8"   # VCU-Q 2021-22 style computed total
    assert checks.breakdown_findings("t", t, KEY) == []


def test_negative_count_is_an_error():
    t = rows(count=[-1], source_file=["f"], source_cell=["B2"], university=["U-1"], file_year=["2024-2025"], stage=["registered"])
    tables = {name: t.iloc[0:0] for name in checks.COUNT_TABLES} | {"ages": t}
    found = checks.negative_counts(tables)
    assert [f["severity"] for f in found] == ["error"]


def test_funnel_is_checked_per_university_not_per_program():
    # 'Undeclared' takes the admissions, majors take the enrollments: fine for the university as a whole
    t = rows(university=["U-1"] * 4, file_year=["2024-2025"] * 4, row_type=["program"] * 4, level=["undergraduate"] * 4,
             breakdown=["total"] * 4, program=["Undeclared", "Undeclared", "Major", "Major"],
             stage=["applied", "admitted", "admitted", "newly_enrolled"], count=[100, 40, 0, 30],
             source_file=["f"] * 4, source_cell=["B2", "C2", "C3", "D3"])
    assert checks.funnel_findings("student_data", t, ["university", "file_year"],
                                  [("applied", "admitted"), ("admitted", "newly_enrolled")]) == []
    t.loc[3, "count"] = 50
    assert statuses(checks.funnel_findings("student_data", t, ["university", "file_year"],
                                           [("applied", "admitted"), ("admitted", "newly_enrolled")])) == \
        ["newly_enrolled_above_admitted"]


def graduation(entered, g100, g150):
    stages = ["entered", "graduated_100", "graduated_150"]
    return rows(source_file=["f"] * 3, source_cell=["E8", "F8", "G8"], cohort=["2018-2019"] * 3,
                stage=stages, count=[entered, g100, g150], breakdown=["total"] * 3, report_status=["used"] * 3,
                university=["U-1"] * 3, file_year=["2024-2025"] * 3)


def test_graduation_within_class():
    assert checks.graduation_within_class({"graduation_rate": graduation(40, 30, 5)}) == []
    assert statuses(checks.graduation_within_class({"graduation_rate": graduation(0, 30, 0)})) == ["no_entrants"]
    assert statuses(checks.graduation_within_class({"graduation_rate": graduation(40, 30, 35)})) == ["150_includes_100"]


def test_outcomes_within_class():
    t = rows(university=["U-1"] * 3, graduating_year=["2022-2023"] * 3, source_file=["f"] * 3, report_status=["used"] * 3,
             breakdown=["total"] * 3, row_type=["program"] * 3, stage=["graduates", "employed", "grad_school"],
             count=[0, 20, 5], file_year=["2023-2024"] * 3, source_cell=["H8", "M8", "R8"])
    assert statuses(checks.outcomes_within_class({"outcomes": t})) == ["class_size_missing"]


def test_report_has_summary_warnings_and_information():
    findings = pd.DataFrame([checks.finding("C03 breakdown adds up", "warning", "mismatch", "t",
                                            {"university": "U-1", "file_year": "2024-2025", "source_file": "a/f.xlsx"},
                                            "Parts add up to 8, total 7", source_cell="F8"),
                             checks.finding("C02 text in a count cell", "info", "text", "t",
                                            {"university": "U-1", "file_year": "2024-2025"}, "1 cell says 'N/A'")],
                            columns=checks.COLUMNS)
    text = checks.report(findings)
    assert "## Summary" in text and "## Warnings" in text and "## Information" in text
    assert "f.xlsx F8" in text
