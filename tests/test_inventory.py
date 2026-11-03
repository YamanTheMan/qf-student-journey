import pandas as pd

from pipeline.inventory import (
    detect_template,
    detect_university,
    filename_year,
    flag_problems,
    folder_year,
    load_university_aliases,
    submission_round,
)

ALIASES = load_university_aliases()


def test_university_spellings_map_to_one_code():
    assert detect_university("TAMUQ Student Data Collection AY2020-2021_070121.xlsx", ALIASES) == "TAMU-Q"
    assert detect_university("AY22-23 WCMC-Q Student Data Collection[10].xlsx", ALIASES) == "WCM-Q"
    assert detect_university("WCMQ_Student Data Collection AY2023-2024.xlsx", ALIASES) == "WCM-Q"
    assert detect_university("VCU_Q Fall Student Data Collection AY2023-2024 (updated).xlsx", ALIASES) == "VCU-Q"
    assert detect_university("Copy of Higher Education Data Template 2022_VCU.xlsx", ALIASES) == "VCU-Q"
    assert detect_university("AY24-25 HEC-Doha Student Data - Spring 2025_20July2025.xlsx", ALIASES) == "HEC-Q"
    assert detect_university("GUQ_Fall Student Data Collection AY2023-2024 final.xlsx", ALIASES) == "GU-Q"


def test_unknown_university_is_not_guessed():
    assert detect_university("Some Other School Data.xlsx", ALIASES) is None


def test_years():
    assert folder_year("AY19-20") == "2019-2020"
    assert folder_year("misc") is None
    assert filename_year("REVISED.CMU-Q Student Data Collection AY2020-2021 qc Aug 25, 2022.xlsx") == "2020-2021"
    assert filename_year("AY22-23 CMU-Q Student Data Collection.xlsx") == "2022-2023"
    assert filename_year("HBKU Student Data Collection 2023 - 2024 (003).xlsx") == "2023-2024"
    assert filename_year("Copy of Higher Education Data Template 2022_VCU.xlsx") is None


def test_submission_round():
    assert submission_round("AY23-24 Fall_Student Data Collection_HEC-Q.xlsx") == "fall"
    assert submission_round("AY24-25 NU-Q Student Data - Spring 2025.xlsx") == "spring"
    assert submission_round("AY22-23 CMU-Q Student Data Collection.xlsx") is None


def test_template_detection():
    assert detect_template(["How to Fill", "A. Student Data", "DD Lists"]) == "v2019"
    assert detect_template(["Welcome", "0.Control Sheet", "A. Student Data"]) == "v2020"
    assert detect_template(["Student Data", "Student Pipeline", "Graduation Rate"]) == "v2021"
    assert detect_template(["Student Data", "Student Pipeline", "Student Funding"]) == "v2022"
    assert detect_template(["Admission", "Alumni"]) == "v2021-alt"
    assert detect_template(["Sheet1"]) == "unknown"


def test_missing_values_do_not_raise_false_flags():
    # Regression: pandas stores a missing year as NaN, which Python treats as True.
    inv = pd.DataFrame({
        "file_kind": ["submission", "submission"],
        "academic_year": ["2021-2022", "2021-2022"],
        "university": ["VCU-Q", None],
        "template": ["v2021-alt", "v2021"],
        "filename_year": [None, "2020-2021"],
    })
    assert flag_problems(inv) == ["", "university_not_detected;filename_year_mismatch"]
