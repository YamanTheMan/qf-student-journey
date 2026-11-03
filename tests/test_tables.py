"""The shared sheet reader, tested on a tiny spreadsheet built for each test."""
import openpyxl

from pipeline.headers import student_data_header
from pipeline.sources import SourceFile
from pipeline.tables import extract_table
from pipeline.workbook import clean_name

HEADER = ["Entity name", "Degree", "Program", "# Applied Qatari Male", "# Applied Qatari Female", "Total Applied Students"]


def build(tmp_path, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Data"
    ws.append(HEADER)
    for row in rows:
        ws.append(row)
    path = tmp_path / "test.xlsx"
    wb.save(path)
    # an absolute path works because data/raw / <absolute path> is that absolute path
    return SourceFile(path=str(path), university="U-1", academic_year="2024-2025", template="v2022")


def test_excel_errors_are_not_names():
    assert clean_name("#REF!") is None
    assert clean_name(" Computer  Science ") == "Computer Science"


def test_named_rows_are_read_and_empty_placeholders_skipped(tmp_path):
    src = build(tmp_path, [["U-1", "BS", "Physics", 3, 4, 7], [None, None, None, 0, 0, 0]])
    issues = []
    records = extract_table(src, "student data", student_data_header, issues)
    assert {r["source_cell"] for r in records} == {"D2", "E2", "F2"}
    assert issues == []


def test_a_row_with_numbers_but_no_name_stops_the_build(tmp_path):
    # '#REF!' names count as no name; real numbers on such a row must never vanish silently
    src = build(tmp_path, [["U-1", "BS", "Physics", 3, 4, 7], ["#REF!", "#REF!", "#REF!", 5, 0, 5]])
    issues = []
    extract_table(src, "student data", student_data_header, issues)
    assert len(issues) == 1 and "row 3" in issues[0]
