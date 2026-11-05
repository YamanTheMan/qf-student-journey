"""Chapter 4 · Graduating: how many graduate, how many finish on time, where graduates come from (M16-M21)."""
import streamlit as st

from dashboard import charts, data as d, filters, story, ui

m = ui.metrics()
f = filters.current()
years = d.years_of(m, "M16")
same = f.education_city and f.same
who = "Education City" if f.education_city else d.universities()[f.university]
RATES = {"M18": "On time", "M19": "Within 150% of normal time", "M20": "Dropped out"}

st.title("4 · Graduating")
st.caption(f"How many graduate, how long it takes, and where graduates come from · graduating classes "
           f"{d.year_span(years)}")
st.markdown(story.graduating(m, f.university, f.level, f.group))
st.info("**How years work in this chapter.** Graduates are counted by **graduating class**: the class of 2023–24 "
        "graduated during 2023–24, whichever year's file reported them (D-011). Graduation rates follow an "
        "**entering class**: of the students who started in a year, how many graduated within normal time (4 years "
        "for a bachelor's) or within 150% of it (6 years). A rate appears only once that time has passed (D-032).")

# --- Graduates per class ------------------------------------------------------------------------
st.subheader("Graduates per class")
pts = d.points(m, "M16", years, f.university, f.same, f.level, f.group)
if same:
    keep, _ = d.same_universities(m, "M16", years, f.level, f.group)
    st.caption(f"{ui.selection(f)} · only the {len(keep)} universities with graduates in every class: {', '.join(keep)}")
elif f.education_city:
    st.caption(f"{ui.selection(f)} · every university that reported. Lighter bars: a university is missing from "
               "that class (hover for which). Classes a university's Student Data lacks come from the next year's "
               "Outcomes sheet (D-028).")
else:
    st.caption(ui.selection(f))
ui.chart(charts.bars(pts, noun="graduates"), charts.table({"Graduates": pts}, "graduates"))

if f.education_city:
    in_slice = set(d.pick(m, "M16", f.level, f.group)["university"])
    per_uni = {u: d.points(m, "M16", years, u, level=f.level, group=f.group)
               for u in d.universities() if u in in_slice}
    st.caption(f"{ui.selection(f)} · graduates at each university, on one scale. × marks a class with no usable data "
               "(hover for why).")
    ui.chart(charts.small_multiples(per_uni, noun="graduates"), charts.table(per_uni, "graduates").drop(columns="Notes"))

# --- Qatari share of graduates ------------------------------------------------------------------
st.subheader("Qatari graduates")
if f.group != "All students":
    st.caption("This share is of all graduates. Choose **All students** in the sidebar to see it.")
else:
    qatari = {"Qatari share of graduates": d.points(m, "M17", years, f.university, f.same, f.level)}
    note = ""
    if same:
        keep, _ = d.same_universities(m, "M17", years, f.level)
        note = f" · only the {len(keep)} universities with data in every class: {', '.join(keep)}"
    st.caption(f"{ui.selection(f)}{note} · share of each graduating class who are Qatari, where nationality is known")
    ui.chart(charts.lines(qatari), charts.table(qatari))

# --- Graduation rates ---------------------------------------------------------------------------
st.subheader("Graduation rates by entering class")
rates_m = story.rates_only(m)
if f.group in ("Female", "Male"):
    st.caption("Graduation rates aren't reported by gender. Choose **All students**, **Qatari** or **Non-Qatari**.")
else:
    rate_years = sorted(set(rates_m.loc[rates_m["metric"].isin(RATES) & (rates_m["unit"] == "rate"), "year"]))
    unis = [f.university] if not f.education_city else d.universities()
    panels = {}
    for u in unis:
        series = {label: d.points(rates_m, k, rate_years, u, level=f.level, group=f.group) for k, label in RATES.items()}
        if any(s["value"].notna().any() for s in series.values()):
            panels[u] = series
    # universities that report graduates of a class but not its entrants have counts, never rates (P-25)
    counts_only = sorted(set(m.loc[(m["metric"] == "M18") & (m["unit"] == "count") & (m["university"] != d.ALL),
                                   "university"]) - set(panels))
    st.caption(f"{who} · {[k for k, v in d.LEVELS.items() if v == f.level][0].lower()} · {f.group.lower()} · of the "
               "students who entered in a year: the share who graduated on time, within 150% of normal time (D-027), "
               "and who dropped out. Each university's rates come from its latest report (D-012). "
               "The rates are shown for each university: they cover different classes, so an Education City average "
               "would mix different universities from year to year."
               + (f" {d.and_list(counts_only)} report graduates of a class but not how many entered, so they have "
                  "no rates (P-25)." if counts_only and f.education_city else "")
               + " A report with no drop-outs in any class (TAMU-Q) hasn't reported them (P-39).")
    if not panels:
        st.caption(f"No graduation rates for {who} at this level.")
    elif len(panels) == 1:
        series = next(iter(panels.values()))
        ui.chart(charts.lines(series), charts.table(series))
    else:
        numbers = {f"{u}: {label}": s for u, series in panels.items() for label, s in series.items()}
        ui.chart(charts.small_lines(panels), charts.table(numbers).drop(columns="Notes"))

# --- Where graduates come from ------------------------------------------------------------------
st.subheader("Where graduates come from")
classes = d.years_of(m, "M21", category="region: Qatar")
if f.level != d.ALL:
    st.caption("Graduate nationalities aren't reported by level. Choose **All levels** in the sidebar to see them.")
else:
    year = st.segmented_control("Graduating class", classes, default=classes[-1], format_func=d.year_label,
                                required=True, key="class", bind="query-params")
    keep = d.every_year_in(m, "M21", classes, "region: ")
    regions = {r: row for r, row in d.mix_year(m, "M21", "region: ", year, f.university, f.same, among=keep).items()
               if r != "Other"}
    caption = f"{who} · class of {d.year_label(year)} · share of graduates from each region of the world"
    if same:
        caption += (f" · only the {len(keep)} universities with lists for every class: {', '.join(keep)}" if keep
                    else " · no university has a list for every class")
    st.caption(caption + ". From the Graduate Nationalities sheet; lists that aren't one class are left out (D-024).")
    if any(r["value"] == r["value"] for r in regions.values()):
        ui.chart(charts.ranked(regions), charts.ranked_table(regions, "Share", label="Region"))
    else:
        st.caption(f"No graduate nationality list for {who} for the class of {d.year_label(year)}.")

st.caption("Sources: the universities' Student Data (graduates, dated by class, D-011), Graduation Rate and Graduate "
           "Nationalities sheets; missing classes from the next year's Outcomes sheet (D-028).")
