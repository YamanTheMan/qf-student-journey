import sys

import pandas as pd
import pytest

from pipeline import build


def inventory(rows):
    return pd.DataFrame(rows, columns=["path", "academic_year", "university", "flags"])


def test_a_new_flagged_file_needs_a_decision():
    inv = inventory([("AY25-26/new.xlsx", "2025-2026", "CMU-Q", "unknown_template")])
    assert build.unresolved_flags(inv) == ["AY25-26/new.xlsx: inventory flag 'unknown_template' needs a decision in file_decisions.csv"]


def test_known_flags_are_covered_by_their_decisions():
    # GU-Q 2022-23 has two files; the decision on one of them settles the pair (D-009)
    inv = inventory([
        ("AY22-23/AY22-23 GU-Q Student Data Collection.completed.xlsx", "2022-2023", "GU-Q", "duplicate_university_year"),
        ("AY22-23/AY22-23 GU-Q Student Data Collection.submitted.xlsx", "2022-2023", "GU-Q", "duplicate_university_year"),
    ])
    assert build.unresolved_flags(inv) == []


def test_a_quality_error_also_stops_the_build(monkeypatch, tmp_path):
    from pipeline import checks
    monkeypatch.setattr(build.inventory, "build_inventory", lambda: inventory([]).assign(file_kind="submission"))
    monkeypatch.setattr(build.inventory, "OUTPUT", tmp_path / "file_inventory.csv")
    monkeypatch.setattr(build, "build_tables", lambda: ({"student_data": pd.DataFrame({"source_file": ["f"]})}, []))
    error = checks.finding("C01 negative count", "error", "negative", "ages",
                           {"university": "U-1", "source_file": "f"}, "Negative count -1", source_cell="B2")
    monkeypatch.setattr(build.checks, "run_checks", lambda tables: pd.DataFrame([error], columns=checks.COLUMNS))
    monkeypatch.setattr(build, "PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(sys, "argv", ["build", "--no-tests"])
    with pytest.raises(SystemExit) as stop:
        build.main()
    assert stop.value.code == 1 and not (tmp_path / "processed").exists()


def test_build_writes_nothing_when_a_person_is_needed(monkeypatch, tmp_path):
    monkeypatch.setattr(build.inventory, "build_inventory", lambda: inventory([]).assign(file_kind="submission"))
    monkeypatch.setattr(build.inventory, "OUTPUT", tmp_path / "file_inventory.csv")
    monkeypatch.setattr(build, "build_tables", lambda: ({"student_data": pd.DataFrame({"source_file": ["f"]})},
                                                        ["program spelling not in programs.csv"]))
    monkeypatch.setattr(build, "PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(sys, "argv", ["build", "--no-tests"])
    with pytest.raises(SystemExit) as stop:
        build.main()
    assert stop.value.code == 1
    assert not (tmp_path / "processed").exists()
