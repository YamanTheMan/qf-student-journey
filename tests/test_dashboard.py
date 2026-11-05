import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import charts, data as d, story
from pipeline.inventory import ROOT

M = d.load_metrics()
YEARS = d.years_of(M, "M01")


def test_year_labels():
    assert d.year_label("2011-2012") == "2011–12"
    assert d.year_span(["2019-2020", "2020-2021", "2021-2022", "2024-2025"]) == "2019–20 to 2021–22, 2024–25"


def test_same_universities_every_year():
    # D-036: only universities with usable data in all 14 years; the others are left out of every year
    keep, rows = d.same_universities(M, "M01", YEARS)
    assert keep == ["GU-Q", "NU-Q", "TAMU-Q", "WCM-Q", "HEC-Q"]
    by_year = rows.set_index("year")["value"]
    assert (by_year["2011-2012"], by_year["2024-2025"]) == (189 + 141 + 489 + 269 + 44, 2163)


def test_same_universities_judges_each_measure_on_its_own_years():
    # gender starts in 2014-15: the years before stay gaps instead of emptying the set
    keep, rows = d.same_universities(M, "M03", YEARS)
    assert keep == ["GU-Q", "NU-Q", "TAMU-Q", "WCM-Q", "HEC-Q"]
    assert rows.set_index("year")["display"]["2012-2013"] == "no data"


def metric_rows(values, unit="count", display=None):
    """A tiny metrics table: two universities in one year, plus their Education City total."""
    display = display or [""] * len(values)
    rows = [dict(metric="M01", name="Registered students", university=u, year="2024-2025", level="All",
                 program_group="All", nationality="All", gender=g, category="", value=v, numerator=None,
                 denominator=None, unit=unit, use="show", quality="complete", display=s, coverage=1, note="", source="")
            for (u, g), v, s in zip([("CMU-Q", "All"), ("GU-Q", "All"), ("CMU-Q", "Female"), ("GU-Q", "Female")],
                                    values, display)]
    rows.append({**rows[0], "university": "All", "value": values[0] + values[1], "coverage": 2})
    return pd.DataFrame(rows)


def test_a_sum_with_a_hidden_part_is_hidden_too():
    # adding a shown 40 to a hidden '<5' and showing 43 would give the hidden number away (D-026)
    m = metric_rows([300, 200, 40, float("nan")], display=["", "", "", "<5"])
    keep, rows = d.same_universities(m, "M01", ["2024-2025"], group="Female")
    assert keep == ["CMU-Q", "GU-Q"]
    assert rows["value"].isna().all() and rows["display"].iloc[0].startswith("not shown")


def test_why_a_year_is_missing_or_incomplete():
    gone = d.absent(M, "M01", YEARS)
    assert ("VCU-Q", "not reported") in gone["2022-2023"] and ("CMU-Q", "no data") in gone["2021-2022"]
    ec = d.points(M, "M01", YEARS).set_index("year")
    assert ec.loc["2019-2020", "state"] == "incomplete" and "HBKU (no data)" in ec.loc["2019-2020", "why"]
    assert ec.loc["2013-2014", "state"] == "complete"
    vcu = d.points(M, "M03", YEARS, "VCU-Q").set_index("year")
    assert vcu.loc["2024-2025", "state"] == "missing"
    assert vcu.loc["2024-2025", "why"].startswith("Gender known for 270 of 323")   # D-037


def test_every_chart_has_its_numbers():
    pts = d.points(M, "M01", YEARS, "VCU-Q")
    table = charts.table({"Registered students": pts}, "students").set_index("Year")
    assert table.loc["2024–25", "Registered students"] == "323 students"
    assert table.loc["2022–23", "Registered students"] == "–"


def test_growth_sentence():
    text = story.growth(M)
    assert text.startswith("In 2024–25, Education City had **2,940** students (7 universities reported): 47% Qatari")
    assert "went from 1,132 in 2011–12 to 2,163 in 2024–25 (up 91%)" in text
    assert story.growth(M, "HBKU", "foundation") == "No data for this selection."


@pytest.mark.parametrize("page", ["chapters/home.py", "chapters/growth.py"])
def test_pages_run_with_every_filter(page):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    at.switch_page(page).run()
    for key, value in (("university", "VCU-Q"), ("level", "Foundation"), ("group", "Female"),
                       ("university", "Education City"), ("view", "same")):
        (at.segmented_control if key == "view" else at.selectbox)(key=key).set_value(value).run()
        assert not at.exception, (key, value)
