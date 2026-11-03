"""The list-sheet reader, tested on a tiny spreadsheet built for each test."""
from dataclasses import replace

import openpyxl

from pipeline.headers import nationalities_header
from pipeline.lists import extract_list
from pipeline.sources import SourceFile

KEYS = {"country_raw": lambda t: t == "nationality"}


def build(tmp_path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Nationalities"
    ws.append(["Nationality", "# Male", "# Female", "Total"])
    for row in rows:
        ws.append(row)
    path = tmp_path / "test.xlsx"
    wb.save(path)
    return SourceFile(path=str(path), university="U-1", academic_year="2020-2021", template="v2020")


def test_reads_rows_until_the_footer_and_leaves_out_blanks(tmp_path):
    src = build(tmp_path, [["Albania", 2, 1, 3], ["Algeria", None, None, None],
                           [None, "# Male Students", "# Female Students", "Total Students"], [None, 2, 1, 3]])
    issues = []
    records = extract_list(src, "student nationalities", KEYS, nationalities_header, issues)
    assert [(r["country_raw"], r["gender"], r["count"]) for r in records] == \
        [("Albania", "Male", 2), ("Albania", "Female", 1), ("Albania", "All", 3)]
    assert issues == []   # the footer's totals are not a nameless row


def test_numbers_without_a_key_are_reported(tmp_path):
    src = build(tmp_path, [["Albania", 2, 1, 3], [None, 5, 0, 5]])
    issues = []
    extract_list(src, "student nationalities", KEYS, nationalities_header, issues)
    assert len(issues) == 1 and "row 3" in issues[0]


def test_an_excluded_sheet_is_not_read(tmp_path):
    src = replace(build(tmp_path, [["Albania", 2, 1, 3]]), skip_sheets=frozenset({"student nationalities"}))
    assert extract_list(src, "student nationalities", KEYS, nationalities_header) == []
