from pathlib import Path

import pandas as pd

from pipeline import checks
from pipeline.flags import status_of

FLAGS = Path(__file__).resolve().parent.parent / "data" / "processed" / "quality_flags.csv"


def f(status, severity="warning", found=None, expected=None):
    return {"status": status, "severity": severity, "found": found, "expected": expected}


def test_findings_map_to_flags():
    assert status_of(f("not_one_class")) == "not_comparable"
    assert status_of(f("higher", found=495, expected=140)) == "not_comparable"   # 3.5x
    assert status_of(f("higher", found=156, expected=143)) == "differs"
    assert status_of(f("lower", found=609, expected=672)) == "partial"
    assert status_of(f("no_entrants")) == "partial"
    assert status_of(f("withheld", severity="info")) == "breakdown_partial"
    assert status_of(f("close", severity="info")) is None
    assert status_of(f("formula_zero", severity="info")) is None


def test_compare_statuses():
    ours = pd.Series({("U-1", "y1"): 10, ("U-1", "y2"): 99, ("U-1", "y3"): 60, ("U-1", "y4"): 150, ("U-1", "y5"): 40})
    ref = pd.Series({("U-1", "y1"): 10, ("U-1", "y2"): 100, ("U-1", "y3"): 100, ("U-1", "y4"): 100, ("U-1", "y5"): 0})
    found = {(x["file_year"], x["status"], x["severity"]) for x in checks.compare("C", "t", ours, ref, "ref")}
    assert found == {("y2", "close", "info"), ("y3", "lower", "warning"), ("y4", "higher", "warning"),
                     ("y5", "fills_gap", "info")}


def read():
    return pd.read_csv(FLAGS, keep_default_na=False).set_index(["measure", "university", "file_year"])["status"]


def test_flags_on_real_data():
    flags = read()
    assert flags[("registered", "VCU-Q", "2022-2023")] == "not_reported"       # registered left blank (P-05)
    assert flags[("registered", "VCU-Q", "2023-2024")] == "breakdown_partial"  # small numbers withheld
    assert flags[("graduated", "TAMU-Q", "2022-2023")] == "not_reported"       # D-011: incomplete early count
    assert flags[("graduate_nationalities", "NU-Q", "2023-2024")] == "not_comparable"   # P-36, cumulative
    assert flags[("graduation_rate", "GU-Q", "2023-2024")] == "partial"        # graduates without entrants (P-25)
    assert flags[("student_pipeline", "TAMU-Q", "2021-2022")] == "not_comparable"       # P-22, 3.5x
    assert flags[("funding", "CMU-Q", "2019-2020")] == "not_in_form"
    assert flags[("registered", "CMU-Q", "2024-2025")] == "complete"
