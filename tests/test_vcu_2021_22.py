"""VCU-Q 2021-22 uses a different form; its numbers must land in the standard tables correctly."""
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
READ = dict(keep_default_na=False, na_values={"count": [""], "level": [""]}, dtype={"degree_raw": str, "program_raw": str})


def vcu(table):
    t = pd.read_csv(PROCESSED / f"{table}.csv", **READ)
    return t[(t.university == "VCU-Q") & (t.file_year == "2021-2022")]


def test_registered_matches_qf_consolidated_in_every_group():
    sd = vcu("student_data")
    reg = sd[(sd.stage == "registered") & (sd.breakdown == "nationality_gender")]
    assert reg.groupby(["nationality", "gender"])["count"].sum().to_dict() == {
        ("Non-Qatari", "Female"): 96, ("Non-Qatari", "Male"): 11, ("Qatari", "Female"): 190, ("Qatari", "Male"): 5}


def test_only_the_fall_2021_snapshot_is_used():
    sd = vcu("student_data")
    assert sd[(sd.stage == "registered") & (sd.breakdown == "total")]["count"].sum() == 302   # Spring 2022 would be 288


def test_admission_registered_column_is_not_read_as_new_students():
    assert not (vcu("student_data").stage == "newly_enrolled").any()


def test_graduates_are_the_class_of_2021_22():
    g = vcu("student_data").query("stage == 'graduated' and breakdown == 'total'")
    assert g["count"].sum() == 68 and set(g.graduating_year) == {"2021-2022"}


def test_side_tables_add_up_to_the_fall_total():
    assert vcu("nationalities").query("breakdown == 'total'")["count"].sum() == 302
    assert vcu("ages")["count"].sum() == 302   # the 'Total Students' row is not an age
    assert vcu("registered_detailed")["count"].sum() == 302


def test_computed_totals_keep_their_source_cells():
    totals = vcu("student_data").query("breakdown == 'total' and stage == 'registered'")
    assert totals.remarks.str.startswith("Total computed").all()
    assert totals.source_cell.str.contains(r"\+").any()
