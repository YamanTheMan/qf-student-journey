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


def test_getting_in_compares_the_same_universities_at_every_stage():
    # applicants, admitted and new students share one set; VCU-Q (no 2022-23 new students) and
    # TAMU-Q (2024-25 left out, D-038) aren't in it
    admissions = [(k, None, "") for k in ("M04", "M05", "M06")]
    assert d.every_year_of_all(M, admissions, d.years_of(M, "M04")) == ["GU-Q", "NU-Q", "WCM-Q", "HEC-Q"]
    assert d.years_of(M, "M10", category="applied: QF schools") == ["2021-2022", "2022-2023", "2023-2024", "2024-2025"]


def test_getting_in_sentence():
    text = story.getting_in(M)
    assert text.startswith("In 2024–25, Education City had **7,539** applicants (6 universities reported) and admitted "
                           "**1,730** (23%).")
    assert "applicants went from 1,825 in 2019–20 to 4,361 in 2024–25 (up 139%)" in text
    # TAMU-Q's latest usable year is 2023-24
    assert story.getting_in(M, "TAMU-Q").startswith("In 2023–24, TAMU-Q had **1,317** applicants")


def mix_rows():
    """Two universities' region mix in one year. GU-Q has no students from Europe, so it has no Europe row."""
    rows = [("CMU-Q", "region: Qatar", 50, 100), ("CMU-Q", "region: Europe", 10, 100), ("GU-Q", "region: Qatar", 30, 60)]
    out = [dict(metric="M11", name="Nationality mix", university=u, year="2024-2025", level="All", program_group="All",
                nationality="All", gender="All", category=c, value=n / t, numerator=n, denominator=t, unit="share",
                use="show", quality="complete", display="", coverage=1, note="", source="") for u, c, n, t in rows]
    out.append({**out[0], "university": "All", "value": 80 / 160, "numerator": 80, "denominator": 160, "coverage": 2})
    return pd.DataFrame(out)


def test_a_mix_counts_every_universitys_students_in_the_whole():
    # D-036 for a mix: GU-Q's 60 students count in the whole of every region, even without a Europe row
    m = mix_rows()
    _, rows = d.same_universities(m, "M11", ["2024-2025"], category="region: Europe", among=["CMU-Q", "GU-Q"])
    assert (rows["numerator"].iloc[0], rows["denominator"].iloc[0]) == (10, 160)
    one = d.mix_year(m, "M11", "region: ", "2024-2025", same=True, among=["CMU-Q", "GU-Q"])
    assert one["Europe"]["value"] == 10 / 160 and one["Qatar"]["value"] == 80 / 160
    assert d.every_year_in(m, "M11", ["2024-2025"], "region: ") == ["CMU-Q", "GU-Q"]


def test_studying_sentence():
    text = story.studying(M)
    assert text.startswith("In 2024–25, Education City's students came from **95** countries: 45% from Qatar")
    assert "the share from Qatar went from 45% in 2019–20 to 51% in 2024–25" in text
    assert story.studying(M, level="graduate").startswith("36% of graduate students studied full-time in 2024–25")


def test_a_university_without_a_split_is_missing_not_zero():
    # graduating classes filled from Outcomes (D-028) have no gender: they're missing from the female total
    years = d.years_of(M, "M16")
    gone = dict(d.absent(M, "M16", years, group="Female")["2021-2022"])
    assert gone["NU-Q"] == "no gender split" and gone["TAMU-Q"] == "no gender split"
    assert d.points(M, "M16", ["2021-2022"], group="Female")["state"].iloc[0] == "incomplete"
    # in the 'same universities' sum they'd count as zero, so that class isn't shown
    _, rows = d.same_universities(M, "M16", years, group="Female")
    assert rows.set_index("year").loc["2021-2022", "display"].startswith("not shown")
    # a level a university doesn't teach is zero, not missing (CMU-Q has no graduate programs)
    assert "CMU-Q" not in dict(d.absent(M, "M16", years, level="graduate")["2023-2024"])


def test_graduation_rates_and_sentence():
    rates = story.rates_only(M)
    assert not ((rates["metric"] == "M18") & (rates["unit"] == "count")).any()   # P-25 counts aren't rates
    text = story.graduating(M)
    assert text.startswith("Education City's class of 2024–25 had **719** graduates (7 universities reported), 44% "
                           "of them Qatari.")
    assert "ranges from 52% (TAMU-Q, entered 2020–21) to 81% (CMU-Q, entered 2020–21)" in text
    assert story.graduating(M, "TAMU-Q").endswith("of those who entered in 2019–20, 88% graduated within 150% of "
                                                  "normal time.")


@pytest.mark.parametrize("page", ["chapters/home.py", "chapters/growth.py", "chapters/getting_in.py",
                                  "chapters/studying.py", "chapters/graduating.py"])
def test_pages_run_with_every_filter(page):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    at.switch_page(page).run()
    steps = [("university", "VCU-Q"), ("level", "Foundation"), ("group", "Female"), ("university", "Education City"),
             ("view", "same"), ("level", "All levels"), ("group", "All students")]
    if page.endswith(("getting_in.py", "studying.py")):
        steps += [("year", "2021-2022"), ("view", "reported"), ("year", "2019-2020")]
    if page.endswith("graduating.py"):
        steps += [("class", "2022-2023"), ("view", "reported"), ("university", "GU-Q")]
    for key, value in steps:
        (at.segmented_control if key in ("view", "year", "class") else at.selectbox)(key=key).set_value(value).run()
        assert not at.exception, (key, value)
