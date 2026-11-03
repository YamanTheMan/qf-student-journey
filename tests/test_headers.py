from pipeline.headers import graduation_rate_header, parse_measure, student_pipeline_header


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


def p(text):
    h = student_pipeline_header(text)
    return None if h is None else (h["stage"], h["school_type"])


def test_pipeline_headers():
    assert p("# Admitted from International Schools outside of Qatar") == ("admitted", "International schools")
    assert p("# Enrolled from Independent / Public Schools") == ("newly_enrolled", "Independent/public schools")
    assert p("# Applied from ABP") == ("applied", "Academic Bridge Program")
    assert p("# Denied from QF Schools") == ("denied", "QF schools")


def test_recommended_for_abp_belongs_to_the_school_after_from():
    assert p("# Recommended for ABP Year from QF Schools") == ("recommended_abp", "QF schools")
    assert p("# Recommended for ABP Year from from Private Schools") == ("recommended_abp", "Private schools")


def test_pipeline_reader_ignores_other_headers():
    for text in ("# Applied Qatari Male", "#REF!", "Program", None):
        assert student_pipeline_header(text) is None


def g(text):
    h = graduation_rate_header(text)
    return None if h is None else (h["stage"], h["nationality"], h["gender"], h["breakdown"])


def test_graduation_rate_headers():
    assert g("# Non-Qatari Females Graduated within 150% of Normal Time") == ("graduated_150", "Non-Qatari", "Female", "nationality_gender")
    assert g("# Qatari Males Graduated within 100% of Normal Time") == ("graduated_100", "Qatari", "Male", "nationality_gender")
    assert g("# Total First-time Degree Seeking Enrolled Students") == ("entered", "All", "All", "total")
    assert g("# Drop-outs Qatari Males") == ("dropouts", "Qatari", "Male", "nationality_gender")
    assert g("# Total Non-Completers") == ("non_completers", "All", "All", "total")


def test_graduation_rate_reader_skips_percentages_and_row_fields():
    for text in ("% Overall Graduation Rate (AY20/21)", "# Normal Time to Completion (Years)", "Cohort Year"):
        assert graduation_rate_header(text) is None


def test_non_count_columns_are_ignored():
    for text in ("Entity name ", "Degree", "Program", "Column4", "Remarks ", None, 42):
        assert parse_measure(text) is None
