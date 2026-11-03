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


def test_every_sheet_exclusion_points_to_a_real_file():
    exclusions = pd.read_csv(REFERENCE / "sheet_exclusions.csv")
    assert all((ROOT / "data" / "raw" / p).exists() for p in exclusions["path"])
    assert exclusions["decision"].str.fullmatch(r"D-\d{3}").all()
    assert exclusions["note"].str.len().gt(10).all()


def test_graduate_timing_table_is_valid():
    timing = pd.read_csv(REFERENCE / "graduate_timing.csv")
    codes = set(pd.read_csv(REFERENCE / "universities.csv")["code"])
    assert set(timing["university"]) <= codes
    assert not timing.duplicated(["university", "file_year"]).any()
    for col in ("file_year", "graduating_year"):
        assert timing[col].str.fullmatch(r"20\d\d-20\d\d").all()
    assert set(timing["status"]) <= {"reported", "not_reported"}
    assert set(timing["evidence_type"]) <= {"remark", "outcomes"}
    assert timing["evidence"].str.len().gt(10).all()


LEVELS = {"foundation", "undergraduate", "graduate", "non_degree"}
QUALIFICATIONS = {"Foundation", "Bachelor's", "Master's", "Doctorate", "Doctor of Medicine (MD)",
                  "Juris Doctor (JD)", "Certificate", "Non-degree"}
FIELDS = {"Art & Design", "Business & Management", "Computing & Data", "Energy & Environment", "Engineering",
          "General & Foundation", "Humanities & Social Sciences", "International Affairs", "Islamic Studies", "Law",
          "Media & Communication", "Medicine & Health", "Sciences"}


def test_program_table_is_valid():
    programs = pd.read_csv(REFERENCE / "programs.csv", dtype=str, keep_default_na=False)
    codes = set(pd.read_csv(REFERENCE / "universities.csv")["code"])
    assert set(programs["university"]) <= codes
    assert not programs.duplicated(["university", "degree_raw", "program_raw"]).any(), "a spelling is listed twice"
    for col in ("program", "program_group", "level", "qualification", "field"):
        assert (programs[col] != "").all(), f"blank {col}"
    assert set(programs["level"]) <= LEVELS
    assert set(programs["qualification"]) <= QUALIFICATIONS
    assert set(programs["field"]) <= FIELDS
    # spellings that match each other (ignoring capitals and spaces) must say the same thing
    from pipeline.programs import match_key
    keyed = programs.assign(d=match_key(programs["degree_raw"]), p=match_key(programs["program_raw"]))
    disagree = keyed.groupby(["university", "d", "p"])[["program", "level"]].nunique().max(axis=1)
    assert (disagree <= 1).all(), f"spellings differing only in capitals disagree: {list(disagree[disagree > 1].index)}"
    # one group never mixes levels, except where a program spans them on purpose (D-015)
    mixed = programs[programs["level"] != "non_degree"].groupby(["university", "program_group"])["level"].nunique()
    assert set(mixed[mixed > 1].index) <= {("WCM-Q", "Medicine")}


def test_university_aliases_are_unique():
    universities = pd.read_csv(REFERENCE / "universities.csv")
    aliases = [a.upper() for row in universities["aliases"] for a in row.split("|")]
    assert len(aliases) == len(set(aliases)), "the same spelling is assigned to two universities"
    assert universities["code"].is_unique
