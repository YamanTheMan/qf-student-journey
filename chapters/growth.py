"""Chapter 1 · Growth: how many students Education City has, and who they are (metrics M01-M03)."""
import streamlit as st

from dashboard import charts, data as d, filters, story, ui

m = ui.metrics()
f = filters.current()
years = d.years_of(m, "M01")
SOURCE_CHANGE = ("2019-2020", "QF consolidated file", "University submissions")  # D-029

st.title("1 · Growth")
st.caption(f"How many students Education City has, and who they are · {d.year_span(years)}")
st.markdown(story.growth(m, f.university, f.level, f.group))

# --- Registered students per year -------------------------------------------------------------
st.subheader("Registered students")
pts = d.points(m, "M01", years, f.university, f.same, f.level, f.group)
if f.education_city and f.same:
    keep, _ = d.same_universities(m, "M01", years)
    st.caption(f"{ui.selection(f)} · only the {len(keep)} universities with data in every year: {', '.join(keep)}")
elif f.education_city:
    st.caption(f"{ui.selection(f)} · every university that reported. Lighter bars: a university is missing "
               "that year, or its data is partial (hover for which). Switch **Education City totals** to "
               "**Same every year** in the sidebar to compare years like for like.")
else:
    st.caption(ui.selection(f))
fig = charts.mark_change(charts.bars(pts), years, *SOURCE_CHANGE)
ui.chart(fig, charts.table({"Registered students": pts}))

if f.level in ("undergraduate", "graduate"):
    st.caption("WCM-Q's medical students count as graduate students before 2019–20; from 2019–20 the "
               "pre-medical years count as undergraduate. Its total doesn't change, only the split (D-029).")

# --- One small chart per university -------------------------------------------------------------
if f.education_city:
    st.subheader("Students at each university")
    st.caption(f"{ui.selection(f)} · same scale for every university. × marks a year with no usable data "
               "(hover for why).")
    in_slice = set(d.pick(m, "M01", f.level, f.group)["university"])
    per_uni = {u: d.points(m, "M01", years, u, level=f.level, group=f.group)
               for u in d.universities() if u in in_slice}
    numbers = charts.table(per_uni).drop(columns="Notes")
    ui.chart(charts.small_multiples(per_uni), numbers)

# --- Who the students are -----------------------------------------------------------------------
st.subheader("Qatari and female students")
if f.group != "All students":
    st.caption("These shares are of all students. Choose **All students** in the sidebar to see them.")
else:
    shares = {"Qatari": d.points(m, "M02", years, f.university, f.same, f.level),
              "Female": d.points(m, "M03", years, f.university, f.same, f.level)}
    no_gender = [y for y in years if y not in d.years_of(m, "M03")]
    who = ""
    if f.education_city and f.same:
        sets = {tuple(d.same_universities(m, metric, years)[0]) for metric in ("M02", "M03")}
        who = " · only the universities with data in every year: " + " / ".join(", ".join(s) for s in sets)
    st.caption(f"{ui.selection(f)}{who} · share of students whose nationality (or gender) is reported."
               + (f" Gender isn't reported for {d.year_span(no_gender)}." if no_gender else ""))
    fig = charts.mark_change(charts.lines(shares), years, *SOURCE_CHANGE)
    ui.chart(fig, charts.table(shares))

st.caption("Sources: QF's consolidated file before 2019–20 and the universities' own Student Data submissions "
           "from 2019–20 (D-029). Where both exist they agree in 34 of 40 university-years.")
