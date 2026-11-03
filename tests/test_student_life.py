from datetime import datetime
from pathlib import Path

import pandas as pd

from pipeline.student_life import employer_type, graduating_class
from pipeline.workbook import cell_text

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
READ = dict(keep_default_na=False, na_values={"count": [""], "amount_qar": [""], "level": [""]},
            dtype={"remarks": str, "age": str, "degree_raw": str, "program_raw": str})


def test_label_cells_become_text_whatever_excel_stored():
    assert cell_text(17) == "17"                      # ages are often numbers
    assert cell_text(datetime(2024, 5, 1)) == "2024-05-01"
    assert cell_text(" <15 ") == "<15"
    assert cell_text("#REF!") is None and cell_text(None) is None


def test_graduate_nationalities_are_dated_like_the_files_graduates():
    classes = {"cmu-2023-24.xlsx": {"2022-2023"}, "two-classes.xlsx": {"2023-2024", "2024-2025"}}
    assert graduating_class("2024-05-01", "two-classes.xlsx", "2024-2025", classes) == ("2023-2024", "label")
    assert graduating_class(None, "cmu-2023-24.xlsx", "2023-2024", classes) == ("2022-2023", "student_data")
    assert graduating_class(None, "two-classes.xlsx", "2024-2025", classes) == ("2024-2025", "form_default")


def test_employer_types():
    assert [employer_type(t) for t in ("QF", "Public", "Private", "Abroad", "Other", "Qatar Museums")] == \
        ["QF", "Public", "Private", "Abroad", "Other", "Named employer"]


def test_cmuq_graduate_nationalities_match_its_graduates():
    gn = pd.read_csv(PROCESSED / "graduate_nationalities.csv", **READ)
    cmu = gn[(gn.university == "CMU-Q") & (gn.row_status == "used")].groupby("graduating_year")["count"].sum()
    assert cmu["2023-2024"] == 120   # Student Data: 120 graduates in May 2024


def test_funding_keeps_money_out_of_student_counts():
    fu = pd.read_csv(PROCESSED / "funding.csv", **READ)
    money = fu[fu.measure == "average_amount_qar"]
    assert money["count"].isna().all() and money["amount_qar"].notna().any()
    assert fu[fu.measure == "students"]["amount_qar"].isna().all()


def test_sponsor_rows_are_kept_but_never_mapped_or_summed():
    fu = pd.read_csv(PROCESSED / "funding.csv", **READ)
    sponsors = fu[fu.row_type == "sponsor_detail"]
    assert sponsors.source_file.str.contains("GUQ_Fall").any()
    assert sponsors.level.isna().all()
    assert fu[fu.row_type.isin(["program", "all_programs"])].level.notna().all()
