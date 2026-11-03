from pipeline.headers import parse_measure


def m(text):
    p = parse_measure(text)
    return None if p is None else (p.stage, p.nationality, p.residency, p.gender, p.breakdown, p.period)


def test_v2022_headers():
    assert m("# Applied Qatari Male") == ("applied", "Qatari", "All", "Male", "nationality_gender", None)
    assert m("# Admitted Resident\nNon-Qatari  Female") == ("admitted", "Non-Qatari", "Resident", "Female", "nationality_gender", None)
    assert m("# Newly Enrolled International Non-Qatari Male") == ("newly_enrolled", "Non-Qatari", "International", "Male", "nationality_gender", None)
    assert m("Total Registered\nStudents") == ("registered", "All", "All", "All", "total", None)


def test_older_templates():
    assert m("# Accepted Qatari") == ("admitted", "Qatari", "All", "All", "nationality", None)
    assert m("# Applied Non-Qatari") == ("applied", "Non-Qatari", "All", "All", "nationality", None)


def test_periods_inside_headers():
    assert m("# Graduated Qatari Female May 2025")[5] == "May 2025"
    assert m("Total Graduated\nStudents May 2025") == ("graduated", "All", "All", "All", "total", "May 2025")


def test_vcu_2023_24_marginal_splits():
    # VCU-Q split applicants by gender and by nationality separately, never crossed
    assert m("# Applied Male")[4] == "gender"
    assert m("# Applied Resident Qatari") == ("applied", "Qatari", "All", "All", "nationality", None)
    assert m("# Applied Students")[4] == "total"


def test_female_is_not_read_as_male():
    assert m("# Registered Qatari Female")[3] == "Female"


def test_non_count_columns_are_ignored():
    for text in ("Entity name ", "Degree", "Program", "Column4", "Remarks ", None, 42):
        assert parse_measure(text) is None
