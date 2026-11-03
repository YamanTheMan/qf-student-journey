"""Hand-made tables in data/reference/ must stay consistent with the raw files."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "data" / "reference"


def test_every_decision_points_to_a_real_file():
    decisions = pd.read_csv(REFERENCE / "file_decisions.csv")
    missing = [p for p in decisions["path"] if not (ROOT / "data" / "raw" / p).exists()]
    assert missing == [], f"file_decisions.csv lists files that don't exist: {missing}"


def test_decision_values_are_valid():
    decisions = pd.read_csv(REFERENCE / "file_decisions.csv")
    assert set(decisions["use"]) <= {"yes", "no", "only", "except"}
    assert decisions["decision"].str.fullmatch(r"D-\d{3}").all()
    # 'only' and 'except' need to say which programs and stages they mean
    scoped = decisions[decisions["use"].isin(["only", "except"])]
    assert scoped["programs"].notna().all() and scoped["stages"].notna().all()
    stages = {s for row in scoped["stages"] for s in row.split("|")}
    assert stages <= {"applied", "admitted", "newly_enrolled", "registered", "graduated"}


def test_university_aliases_are_unique():
    universities = pd.read_csv(REFERENCE / "universities.csv")
    aliases = [a.upper() for row in universities["aliases"] for a in row.split("|")]
    assert len(aliases) == len(set(aliases)), "the same spelling is assigned to two universities"
    assert universities["code"].is_unique
