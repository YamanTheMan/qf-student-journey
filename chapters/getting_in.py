"""Chapter 2 · Getting in: applied -> admitted -> enrolled, and which schools students come from (metrics M04-M10)."""
import pandas as pd
import streamlit as st

from dashboard import charts, data as d, filters, story, ui

m = ui.metrics()
f = filters.current()
years = d.years_of(m, "M04")
STAGES = {"M04": "Applicants", "M05": "Admitted", "M06": "New students"}
RATES = {"M07": "Acceptance rate", "M08": "Yield"}
everyone = f.group == "All students"  # rates and Qatari shares exist for all students only

st.title("2 · Getting in")
st.caption(f"Applied → admitted → enrolled, and which schools students come from · {d.year_span(years)}")
st.markdown(story.getting_in(m, f.university, f.level, f.group))

# The 'same universities' set is shared by every admissions chart, so applicants, admissions and new students
# always describe the same universities (D-036)
keep = d.every_year_of_all(m, [(k, None, "") for k in [*STAGES, *RATES]], years)
same = f.education_city and f.same


def series(metric, yrs=years, **kw):
    return d.points(m, metric, yrs, f.university, f.same, f.level, kw.pop("group", f.group),
                    among=keep if same else None, **kw)


def scope():
    if same:
        return f"{ui.selection(f)} · only the {len(keep)} universities with data in every year: {', '.join(keep)}"
    return ui.selection(f)


year = st.segmented_control("Year", years, default=years[-1], format_func=d.year_label, required=True, key="year",
                            bind="query-params", help="For the funnel, the university ranking and the school types.")

# --- The funnel for one year --------------------------------------------------------------------
st.subheader(f"From application to enrolment, {d.year_label(year)}")
one = {k: series(k, [year]).iloc[0] for k in [*STAGES, *RATES]}
labels = dict(STAGES)
if everyone:
    for stage, rate, word in (("M05", "M07", "of applicants"), ("M06", "M08", "of those admitted")):
        if pd.notna(one[rate]["value"]):
            labels[stage] += f" · {d.share_text(one[rate]['value'])} {word}"
st.caption(scope() + (" · lighter bar: incomplete (hover for why)"
                      if any(one[k]["state"] == "incomplete" for k in STAGES) else ""))
if all(one[k]["state"] == "missing" for k in STAGES):
    why = one["M04"]["why"]
    st.info(f"No usable admissions data for this selection in {d.year_label(year)}: "
            f"{why[:1].lower() + why[1:] if why else 'no data'}. Choose another year.")
else:
    ui.chart(charts.funnel({labels[k]: one[k] for k in STAGES}),
             charts.table({STAGES[k]: series(k, [year]) for k in STAGES}))

# --- Over the years -----------------------------------------------------------------------------
st.subheader("Over the years")
st.caption(f"{scope()} · each chart has its own scale: applicants outnumber new students many times over.")
per_stage = {STAGES[k]: series(k) for k in STAGES}
ui.chart(charts.small_multiples(per_stage, shared=False), charts.table(per_stage).drop(columns="Notes"))

if everyone:
    rates = {RATES[k]: series(k) for k in RATES}
    st.caption("**Acceptance rate**: admitted ÷ applicants. **Yield**: new students ÷ admitted.")
    ui.chart(charts.lines(rates), charts.table(rates))

# HBKU's applicants dwarf everyone else's: say so wherever Education City includes it
h = d.headline(m, "M04")
ec = h[h["university"] == d.ALL].set_index("year")["value"]
big = h[(h["university"] != d.ALL)].assign(part=lambda t: t["value"] / t["year"].map(ec))
big = big[big["part"] > 0.5]
if f.education_city and not same and len(big):
    top = big.sort_values("value").iloc[-1]
    st.caption(f"{top.university} reports far more applicants than any other university "
               f"({d.count_text(top.value)} in {d.year_label(top.year)}, {d.share_text(top.part)} of Education City's), "
               "so Education City's applicants and acceptance rate jump in the years it's included. "
               "**Same every year** in the sidebar compares like for like.")

# --- Each university ----------------------------------------------------------------------------
if f.education_city and everyone:
    st.subheader(f"Each university, {d.year_label(year)}")
    in_slice = [u for u in d.universities() if u in set(d.pick(m, "M04", f.level)["university"])]
    left, right = st.columns(2)
    for column, metric in ((left, "M07"), (right, "M08")):
        per_uni = {u: d.points(m, metric, [year], u, level=f.level).iloc[0] for u in in_slice}
        with column:
            st.markdown(f"**{RATES[metric]}**")
            ui.chart(charts.ranked(per_uni), charts.ranked_table(per_uni, RATES[metric]))
    st.caption(f"{ui.selection(f)} · × marks a university without usable data that year (hover for why).")

# --- Qatari students at each stage --------------------------------------------------------------
if everyone:
    st.subheader("Qatari students at each stage")
    shares = {label: series("M09", category=stage, group="All students")
              for stage, label in (("applied", "Applicants"), ("admitted", "Admitted"), ("newly_enrolled", "New students"))}
    st.caption(f"{scope()} · Qatari share of applicants, of those admitted, and of new students. A share that "
               "rises from stage to stage means Qatari applicants were more likely to be admitted and to enroll.")
    ui.chart(charts.lines(shares), charts.table(shares))

# --- Which schools new students come from -------------------------------------------------------
st.subheader(f"Which schools students come from, {d.year_label(year)}")
SCHOOLS = ["QF schools", "Independent/public schools", "Private schools", "International schools",
           "Academic Bridge Program"]  # QF's own schools first, in Sidra Green
mix_years = d.years_of(m, "M10", category="applied: QF schools")
if not everyone or f.level == "graduate":
    st.caption("Reported for undergraduate and foundation students only, and not by nationality or gender. "
               "Choose **All levels** (or Undergraduate / Foundation) and **All students** to see it.")
elif year not in mix_years:
    st.caption(f"Reported from {d.year_label(mix_years[0])} on (the Student Pipeline sheet). Choose a later year.")
else:
    mix_keep = d.every_year_of_all(m, [("M10", None, f"applied: {s}") for s in SCHOOLS], mix_years)
    groups = {}
    for stage, label in (("applied", "Applicants"), ("admitted", "Admitted"), ("newly_enrolled", "New students")):
        groups[label] = {s: d.points(m, "M10", [year], f.university, f.same, "undergraduate+foundation",
                                     category=f"{stage}: {s}", among=mix_keep if same else None).iloc[0]
                         for s in SCHOOLS}
    caption = (f"{'Education City' if f.education_city else f.university} · undergraduate and foundation students, "
               "from the Student Pipeline sheet · share of each stage by type of school")
    if same:
        caption += f" · only the {len(mix_keep)} universities with data every year from " \
                   f"{d.year_label(mix_years[0])}: {', '.join(mix_keep)}"
    if any(r["state"] == "incomplete" for g in groups.values() for r in g.values()):
        caption += " · partial: hover a segment for what's missing"
    if any(r["state"] == "missing" for g in groups.values() for r in g.values()):
        caption += (" · a segment that includes a group of fewer than 5 students isn't shown, so that bar stops "
                    "short of 100%")
    st.caption(caption)
    numbers = {f"{label}: {s}": d.points(m, "M10", [year], f.university, f.same, "undergraduate+foundation",
                                         category=f"{stage}: {s}", among=mix_keep if same else None)
               for stage, label in (("applied", "Applicants"), ("admitted", "Admitted"),
                                    ("newly_enrolled", "New students")) for s in SCHOOLS}
    ui.chart(charts.stacked_shares(groups, SCHOOLS), charts.table(numbers))

st.caption("Source: the universities' Student Data sheets (2019–20 on); school types from their Student Pipeline "
           "sheets (D-020). TAMU-Q's 2024–25 file reports admissions for its graduate program only, so that year is "
           "left out (D-038).")
