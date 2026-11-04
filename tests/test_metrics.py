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


def read():
    return pd.read_csv(PROCESSED / "metrics.csv", keep_default_na=False,
                       na_values={c: [""] for c in ("value", "numerator", "denominator", "coverage")})


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
