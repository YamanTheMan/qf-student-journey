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
    # parts that are all 0 under a positive total: formulas over withheld numbers (VCU-Q 2023-24 footer)
    assert statuses(checks.breakdown_findings("t", one_row([0, 0], 311), KEY)) == ["withheld"]


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


def graduation(entered, g100, g150, qatari=None):
    """One program row's totals and, optionally, its Qatari part (entered, within 100%, within 150%)."""
    stages = ["entered", "graduated_100", "graduated_150"]
    common = dict(source_file=["f"] * 3, cohort=["2018-2019"] * 3, stage=stages, report_status=["used"] * 3,
                  university=["U-1"] * 3, file_year=["2024-2025"] * 3)
    t = rows(source_cell=["E8", "F8", "G8"], count=[entered, g100, g150], breakdown=["total"] * 3,
             nationality=["All"] * 3, **common)
    if qatari:
        t = pd.concat([t, rows(source_cell=["H8", "I8", "J8"], count=list(qatari), breakdown=["nationality_gender"] * 3,
                               nationality=["Qatari"] * 3, **common)], ignore_index=True)
    return t


def test_graduation_within_class():
    assert checks.graduation_within_class({"graduation_rate": graduation(40, 30, 5)}) == []
    assert statuses(checks.graduation_within_class({"graduation_rate": graduation(0, 30, 0)})) == ["no_entrants"]
    assert statuses(checks.graduation_within_class({"graduation_rate": graduation(40, 30, 35)})) == ["150_includes_100"]


def test_a_nationality_part_cannot_outnumber_its_entrants():
    fine = graduation(40, 30, 5, qatari=(10, 8, 2))
    assert checks.graduation_within_class({"graduation_rate": fine}) == []
    # HEC-Q 2022-23: 86 Qatari on-time graduates from 42 Qatari entrants, while the totals add up
    wrong = graduation(40, 30, 5, qatari=(10, 12, 0))
    assert statuses(checks.graduation_within_class({"graduation_rate": wrong})) == ["split_exceeds_class"]
    # at a university whose '150%' already includes the on-time graduates, 150% is compared as is
    cumulative = graduation(40, 30, 35, qatari=(10, 8, 10))
    assert statuses(checks.graduation_within_class({"graduation_rate": cumulative})) == ["150_includes_100"]


def test_outcomes_within_class():
    t = rows(university=["U-1"] * 3, graduating_year=["2022-2023"] * 3, source_file=["f"] * 3, report_status=["used"] * 3,
             breakdown=["total"] * 3, row_type=["program"] * 3, stage=["graduates", "employed", "grad_school"],
             count=[0, 20, 5], file_year=["2023-2024"] * 3, source_cell=["H8", "M8", "R8"])
    assert statuses(checks.outcomes_within_class({"outcomes": t})) == ["class_size_missing"]


def test_funding_sponsor_rows_are_reported():
    t = rows(university=["U-1"] * 3, file_year=["2023-2024"] * 3, row_type=["program", "sponsor_detail", "sponsor_detail"],
             measure=["students"] * 3, count=[10, 256, 12], source_file=["f"] * 3, source_cell=["E8", "U18", "P19"],
             company_sponsor_details=[None, "GU-Q Grant", "QF Scholarship"])
    found = checks.funding_sponsor_rows({"funding": t})
    assert statuses(found) == ["sponsor_rows"] and found[0]["found"] == 268
    assert "2 sponsor row(s)" in found[0]["message"] and "GU-Q Grant" in found[0]["message"]


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
    flags = pd.DataFrame({"measure": ["registered"], "university": ["U-1"], "file_year": ["2024-2025"], "symbol": ["◐"]})
    assert "| U-1 | ◐ |" in checks.report(findings, flags)
