"""About the data: which files exist, how good each number is, what's left out, and the rules every chart follows."""
import pandas as pd
import streamlit as st

from dashboard import data as d, ui
from pipeline.checks import LEGEND, MEASURE_NAMES
from pipeline.inventory import REFERENCE_DIR, ROOT

m = ui.metrics()
names = d.universities()


@st.cache_data(show_spinner=False)
def _read(path, changed):
    return pd.read_csv(path, keep_default_na=False)


def read(path):
    return _read(path, path.stat().st_mtime)


inventory = read(REFERENCE_DIR / "file_inventory.csv")
flags = read(ROOT / "data" / "processed" / "quality_flags.csv")
submissions = inventory[inventory["file_kind"] == "submission"]
years = sorted(submissions["academic_year"].unique())

st.title("About the data")
st.caption("Where the numbers come from, how good they are, and the rules every chart follows")

# --- Where the numbers come from ----------------------------------------------------------------
st.subheader("Where the numbers come from")
st.markdown(
    f"Each year, every Education City university fills in Qatar Foundation's **Student Data Collection** form. "
    f"This dashboard reads **{len(inventory)} Excel files**: **{len(submissions)} university submissions** "
    f"({d.year_span(years)}) and QF's own consolidated files, the only source of registered students before "
    "2019–20 (D-029). The files are never edited: every correction is a rule in the pipeline, written down in "
    "the decision log.")
# the university-years the pipeline reads, after the file decisions (a file can sit in another year's folder, D-008)
used = flags[["university", "file_year"]].drop_duplicates().assign(sent="✓")
have = used.pivot(index="university", columns="file_year", values="sent").reindex(index=list(names), columns=years)
have = have.fillna("").rename(columns=d.year_label).rename_axis(index=None, columns=None)
have.index = [f"{u} · {n}" for u, n in names.items()]
st.caption("University submissions by academic year (✓ = the year's data was received)")
st.dataframe(have, width="stretch")

# --- How good each number is --------------------------------------------------------------------
st.subheader("How good each number is")
st.markdown(
    "Every measure, university and year gets a quality flag from the automatic checks. The flag decides what the "
    "charts do: ✓ and ◑ are shown as they are, ≈ with a note, ◐ lighter (marked partial), and ≠ and ✗ are left out "
    "as a visible gap (D-025).")
measures = [k for k in MEASURE_NAMES if k in set(flags["measure"])]
measure = st.selectbox("Measure", measures, format_func=MEASURE_NAMES.get, key="measure")
grid = flags[flags["measure"] == measure].pivot(index="university", columns="file_year", values="symbol")
grid = grid.reindex(index=[u for u in names if u in grid.index]).fillna("").rename(columns=d.year_label)
SHADE = {"◐": "#E9E9E9", "≠": "#C8C9C7", "✗": "#C8C9C7"}  # Cool Gray tints: the worse the flag, the darker
st.dataframe(grid.style.map(lambda v: f"background-color: {SHADE[v]}" if v in SHADE else ""), width="stretch")
st.caption(LEGEND)

# --- What's left out ----------------------------------------------------------------------------
st.subheader("What's left out, and why")
STATUS = {"not_reported": "not reported (the sheet was empty)", "not_comparable": "not comparable"}
gaps = flags[flags["status"].isin(STATUS)].assign(
    Measure=lambda t: t["measure"].map(MEASURE_NAMES), University=lambda t: t["university"],
    Year=lambda t: t["file_year"].map(d.year_label), Why=lambda t: t["status"].map(STATUS),
    Checks=lambda t: t["notes"])[["Measure", "University", "Year", "Why", "Checks"]]
order = {name: i for i, name in enumerate(MEASURE_NAMES.values())}
gaps = gaps.sort_values(["Measure", "University", "Year"], key=lambda s: s.map(order) if s.name == "Measure" else s)
st.caption(f"{len(gaps)} university-years are left out of a measure. They show as × on the charts, with the reason "
           "on hover.")
st.dataframe(gaps, hide_index=True, width="stretch")

st.markdown(
    "**Also worth knowing**\n"
    "- Universities aren't in every year: HBKU's submissions cover only some years, UCL-Q's data ends in 2018–19, "
    "and CMU-Q has no data for 2021–22 (the file in that year's folder is its 2020–21 revision, D-008). **Same every year** in the sidebar compares like for like (D-036).\n"
    "- Graduates are counted by the year they graduated, which isn't always the file's year (D-011). Graduation "
    "rates follow the year students started, and count only once enough time has passed (D-032).\n"
    "- Only some universities report graduation rates; the others report graduates but not how many started "
    "(P-25).\n"
    "- Nationality, age, funding and internship sheets don't always cover every student, so they're shown as "
    "shares of their own total, never as headcounts (D-022).\n"
    "- QF scholarships can't be measured from the funding sheet: every university reports 0 (D-031).")

# --- Rules every chart follows ------------------------------------------------------------------
st.subheader("Rules every chart follows")
st.markdown(
    "- **Small numbers are hidden**: a group of 1–4 students shows as \"<5\", and shares or rates based on fewer "
    "than 10 students aren't shown (D-026). A total that includes a hidden group is hidden too.\n"
    "- **A share needs its split to cover the students**: under 95% coverage it's marked partial, under 90% left "
    "out, with its possible range in the tooltip (D-037).\n"
    "- **A missing split isn't zero**: a university that gives a total but no gender split is listed as missing "
    "from that year's female and male numbers (D-041).\n"
    "- **The dashboard computes nothing new**: every number comes from the tested pipeline, except the "
    "\"same universities\" sums, which add up numbers already shown (D-035, D-036).\n"
    "- **Colours** are Qatar Foundation's primary palette, chosen so that no two series rely on red–green "
    "difference alone (D-043).")
st.caption("More detail in the project repository: docs/quality_report.md (every check result), docs/DECISIONS.md "
           "(every rule and why), docs/metrics.md (every measure's definition) and docs/data_dictionary.md "
           "(every table and known problem).")
