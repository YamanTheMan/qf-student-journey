from pathlib import Path

import pandas as pd

from pipeline import metrics

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


def rows(**cols):
    return pd.DataFrame(cols).astype({"count": "Float64"})


def test_a_row_is_split_one_way_only():
    # Row 1 splits nationality x gender; row 2 only has separate gender and nationality splits
    t = rows(university=["U"] * 6, year=["y"] * 6, level=["undergraduate"] * 6, program_group=["P"] * 6,
             row_key=["r1", "r1", "r2", "r2", "r2", "r2"],
             breakdown=["nationality_gender", "nationality_gender", "gender", "gender", "nationality", "nationality"],
             nationality=["Qatari", "Non-Qatari", "All", "All", "Qatari", "Non-Qatari"],
             gender=["Male", "Female", "Male", "Female", "All", "All"], count=[3, 4, 10, 20, 12, 18])
    by_nat = metrics.split_parts(t, "nationality").set_index("nationality")["count"]
    assert by_nat.to_dict() == {"Non-Qatari": 4 + 18, "Qatari": 3 + 12}   # never the gender split as well


def frame(**cols):
    base = {"nationality": "All", "gender": "All", "program_group": "All", "category": None,
            "numerator": None, "denominator": None}
    return pd.DataFrame([{**base, **r} for r in pd.DataFrame(cols).to_dict("records")])


def test_small_numbers_are_hidden():
    m = metrics.hide_small_numbers(frame(
        unit=["count", "count", "count", "share", "share"], value=[3, 3, 12, 0.5, 0.5],
        nationality=["Qatari", "All", "Qatari", "All", "All"], denominator=[None, None, None, 8, 40]))
    assert list(m["display"].fillna("")) == ["<5", "", "", "fewer than 10 students", ""]
    assert m["value"].isna().tolist() == [True, False, False, True, False]   # totals of 3 still show (D-026)


def test_worst_use_wins():
    assert metrics.worst_use("show", "show_marked") == "show_marked"
    assert metrics.worst_use("show_with_note", "leave_out") == "leave_out"


def test_a_share_needs_its_split_to_cover_the_students():
    # D-037: the split's coverage of the total decides the share's use (VCU-Q 2024-25 left its male count blank)
    rows = []
    for uni, female, male in (("U1", 60, 40), ("U2", 60, 33), ("U3", 85, None)):
        for gender, n in (("All", 100), ("Female", female), ("Male", male)):
            rows.append(dict(university=uni, year="y", level="All", program_group="All", stage="registered",
                             nationality="All", gender=gender, count=n, source="student_data", quality="complete",
                             use="show", coverage=1))
    base = pd.DataFrame(rows).astype({"count": "Float64"})
    out = metrics.share(base, "M03", "Female share", "Growth", "registered", "gender", "Female").set_index("university")
    assert out["use"].to_dict() == {"U1": "show", "U2": "show_marked", "U3": "leave_out"}
    assert out.loc["U2", "note"] == "Gender known for 93 of 100 students, so the share could be anywhere from 60% to 67% (D-037)"
    assert out.loc["U1", "note"] is None


def test_vcuq_2024_25_female_share_is_left_out():
    m = read()
    row = total(m, "M03", "VCU-Q", "2024-2025")
    assert row["use"] == "leave_out" and row["note"].startswith("Gender known for 270 of 323 students")


def read():
    return pd.read_csv(PROCESSED / "metrics.csv", keep_default_na=False,
                       na_values={c: [""] for c in ("value", "numerator", "denominator", "coverage",
                                                              "years_after_graduation")})


def total(m, metric, university, year):
    row = m[(m.metric == metric) & (m.university == university) & (m.year == year) & (m.level == "All")
            & (m.program_group == "All") & (m.nationality == "All") & (m.gender == "All")]
    return row.iloc[0]


def test_growth_history_matches_qf_minus_non_degree():
    m = read()
    assert total(m, "M01", "All", "2011-2012")["value"] == 1913
    assert total(m, "M01", "All", "2015-2016")["value"] == 2679   # HBKU's QFIS line counted with level 'unknown'


def test_getting_in_rates():
    m = read()
    acceptance = total(m, "M07", "CMU-Q", "2024-2025")
    assert (acceptance["numerator"], acceptance["denominator"]) == (204, 2886)
    assert round(total(m, "M08", "CMU-Q", "2024-2025")["value"], 3) == round(118 / 204, 3)


def test_education_city_leaves_out_unreported_universities():
    m = read()
    # VCU-Q 2022-23 registered is 'not reported' (formula zeros): left out, so 7 universities, not 8
    assert total(m, "M01", "All", "2022-2023")["coverage"] == 7


def test_age_bands():
    assert [metrics.age_band(a) for a in ("<15", "17", "18", "20", "21", "23", "24", "29", "30", "35-39", ">59", "Age unknown")] == \
        ["under 18", "under 18", "18-20", "18-20", "21-23", "21-23", "24-29", "24-29", "30 and over", "30 and over",
         "30 and over", "not given"]


def test_mix_shares_and_education_city():
    rows = pd.DataFrame({"university": ["A", "A", "B", "B", "C"], "year": ["y"] * 5, "level": ["All"] * 5,
                         "category": ["x", "z", "x", "z", "x"], "count": [30, 10, 20, 40, 99]})
    use = {"A": "show", "B": "show_marked", "C": "leave_out"}
    m = metrics.mix(rows, "M", "n", "c", lambda us, ys: [use[u] for u in us])
    a = m[(m.university == "A")].set_index("category")["value"]
    assert a.to_dict() == {"x": 0.75, "z": 0.25}
    ec = m[m.university == "All"].set_index("category")
    assert ec.loc["x", "numerator"] == 50 and ec.loc["x", "denominator"] == 100   # C is left out (D-025)
    assert ec.loc["x", "coverage"] == 2 and ec.loc["x", "use"] == "show_marked"


def test_a_small_share_in_a_breakdown_is_hidden():
    m = metrics.hide_small_numbers(frame(unit=["share"], value=[0.01], numerator=[3], denominator=[300],
                                         category=["country: Iceland"]))
    assert m["display"].iloc[0] == "<5" and pd.isna(m["value"].iloc[0])   # 1% of 300 would reveal 3 students


def test_studying_metrics_on_real_data():
    m = read()
    ec = m[(m.university == "All") & (m.year == "2024-2025") & (m.level == "All")]
    regions = ec[(ec.metric == "M11") & ec.category.str.startswith("region:")]
    assert abs(regions["value"].sum() - 1) < 0.01
    internships = ec[(ec.metric == "M15") & (ec.unit == "count")]["value"].sum()
    assert internships == 512
    qf = m[m.category == "funding: qf scholarship"]
    assert len(qf) and (qf.use == "leave_out").all()   # D-031: not measured in this sheet


def test_a_window_counts_once_it_has_closed():
    # CMU-Q's class entering 2018-19, reported in 2022-23: 4 years done, 150% (6 years) not yet
    assert metrics.window_closed("2018-2019", "2022-2023", 4)
    assert not metrics.window_closed("2018-2019", "2022-2023", 6)
    assert metrics.window_closed("2019-2020", "2024-2025", 6)


def graduation_rows(university, entered, g100, g150, dropouts=0):
    stages = ["entered", "graduated_100", "graduated_150", "dropouts"]
    return pd.DataFrame({"university": university, "file_year": "2024-2025", "cohort": "2017-2018",
                         "report_status": "used", "row_type": "program", "level": "undergraduate", "normal_years": "4",
                         "source_file": university, "source_cell": [f"{c}8" for c in "EFGH"], "nationality": "All",
                         "stage": stages, "count": [entered, g100, g150, dropouts]})


def test_by_150_is_made_comparable():
    # A reports the extra graduates after normal time; B's 150% already includes the on-time ones (D-027)
    t = pd.concat([graduation_rows("A", 40, 20, 10, dropouts=2), graduation_rows("B", 80, 40, 60)])
    flags = pd.DataFrame(columns=["measure", "university", "file_year", "use"])
    classes = metrics.graduation_classes({"graduation_rate": t}, flags).set_index(["university", "level"])
    assert classes.loc[("A", "All"), "by_150"] == 30 and classes.loc[("B", "All"), "by_150"] == 60
    by_150 = metrics.class_rate(classes.reset_index(), "M19", "n", "by_150", "closed_150")
    by_150 = by_150[by_150.level == "All"].set_index("university")
    assert by_150.loc["All", "numerator"] == 90 and by_150.loc["All", "denominator"] == 120
    dropouts = metrics.class_rate(classes.reset_index(), "M20", "n", "dropouts", "dropouts_known")
    assert set(dropouts["university"]) == {"A", "All"}   # B's report has no drop-outs at all: not reported


def by_class(m, metric, university, year, nationality="All", unit=None):
    rows = m[(m.metric == metric) & (m.university == university) & (m.year == year) & (m.level == "All")
             & (m.program_group == "All") & (m.nationality == nationality) & (m.gender == "All")]
    return rows[rows.unit == unit] if unit else rows


def test_graduates_series_with_classes_filled_from_outcomes():
    m = read()
    cmu = [by_class(m, "M16", "CMU-Q", f"{y}-{y + 1}").iloc[0]["value"] for y in range(2019, 2025)]
    assert cmu == [77, 95, 87, 103, 120, 110]
    for university, year, size in (("NU-Q", "2021-2022", 108), ("TAMU-Q", "2021-2022", 110),
                                   ("TAMU-Q", "2022-2023", 113), ("WCM-Q", "2020-2021", 41)):
        row = by_class(m, "M16", university, year).iloc[0]
        assert (row["value"], row["source"]) == (size, "outcomes")   # D-028


def test_graduation_rates_on_real_data():
    m = read()
    on_time = by_class(m, "M18", "CMU-Q", "2018-2019").iloc[0]
    assert (on_time["numerator"], on_time["denominator"]) == (79, 96)
    assert by_class(m, "M19", "CMU-Q", "2018-2019").empty            # its 150% window hadn't closed (D-032)
    assert by_class(m, "M19", "TAMU-Q", "2017-2018").iloc[0]["numerator"] == 64   # 150% used as is (D-027)
    assert by_class(m, "M19", "WCM-Q", "2016-2017").iloc[0]["numerator"] == 23 + 13
    assert by_class(m, "M20", "TAMU-Q", "2017-2018").empty           # drop-outs not reported
    assert by_class(m, "M18", "HEC-Q", "2022-2023", "Qatari").empty  # 86 Qatari graduates of 42 entrants (C05)
    assert by_class(m, "M18", "GU-Q", "2010-2011", unit="count").iloc[0]["value"] == 39   # no entrants (P-25)
    rates = m[m.metric.isin(["M17", "M18", "M19", "M20", "M21", "M22", "M23", "M24", "M25"]) & (m.unit != "count")]
    assert (rates["value"].dropna() <= 1).all()


def test_outcome_rates_use_the_fallback_class_size():
    m = read()
    cmu = by_class(m, "M22", "CMU-Q", "2022-2023").iloc[0]
    assert (cmu["numerator"], cmu["denominator"]) == (73, 103) and "Student Data" in cmu["note"]   # D-021
    vcu = by_class(m, "M22", "VCU-Q", "2022-2023").iloc[0]
    assert (vcu["numerator"], vcu["denominator"], vcu["use"]) == (28, 48, "show_marked")
    assert by_class(m, "M25", "WCM-Q", "2023-2024").iloc[0]["years_after_graduation"] == 1


def test_older_internships_are_sorted_into_types():
    m = read()
    internships = m[(m.metric == "M15") & (m.unit == "count") & (m.university == "All") & (m.year == "2019-2020")]
    assert set(internships["category"]) <= {f"employer: {t}" for t in ("QF", "Public", "Private", "Abroad", "Other")}
    assert internships["value"].sum() == 188   # every named employer has a type (D-034)
