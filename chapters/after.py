"""Chapter 5 · After graduation: where graduates are a year later (metrics M22-M25)."""
import streamlit as st

from dashboard import charts, data as d, filters, story, ui

m = ui.metrics()
f = filters.current()
classes = story.outcome_classes(m, f.university)
every_class = d.years_of(m, "M22")
same = f.education_city and f.same
who = "Education City" if f.education_city else d.universities()[f.university]
OUTCOMES = {"M22": "Employed", "M23": "Further study", "M24": "Still searching"}
GROUPS = {"All graduates": "All students", "Qatari": "Qatari", "Non-Qatari": "Non-Qatari"}
level_name = [k for k, v in d.LEVELS.items() if v == f.level][0].lower()

st.title("5 · After graduation")
st.caption(f"Where graduates are a year later: work, further study or still searching · graduating classes "
           f"{d.year_span(classes)}")
st.markdown(story.after(m, f.university, f.level, f.group))
skipped = [y for y in every_class if y not in classes]
h = d.headline(m, "M22")
alone = sorted(set(h.loc[h["year"].isin(skipped) & (h["university"] != d.ALL), "university"]))
st.info("**How to read this chapter.** Each class is asked about a year after it graduated, so the latest class is "
        f"{d.year_label(every_class[-1])}. Rates are shares of the whole class: graduates whose outcome isn't known "
        "count as neither employed nor studying, and graduates not looking for work aren't shown (D-021)."
        + (f" The class of {d.year_span(skipped)} isn't shown for Education City: only {d.and_list(alone)} "
           "reported it." if skipped else ""))

if f.group in ("Female", "Male"):
    st.caption("Outcomes aren't reported by gender. Choose **All students**, **Qatari** or **Non-Qatari** in the "
               "sidebar.")
    st.stop()

# One 'same universities' set for every outcome chart, so the rates describe the same classes (D-039)
keep = d.every_year_of_all(m, [(k, None, "") for k in [*OUTCOMES, "M25"]], classes)


def series(metric, yrs, group=f.group, university=f.university):
    return d.points(m, metric, yrs, university, f.same, f.level, group, among=keep if same else None)


def scope():
    text = f"{who} · {level_name}"
    if same:
        text += f" · only the {len(keep)} universities with outcomes for every class: {', '.join(keep)}"
    return text


# --- One class, a year on -----------------------------------------------------------------------
st.subheader("A year after graduating")
year = st.segmented_control("Graduating class", classes, default=classes[-1], format_func=d.year_label,
                            required=True, key="class", bind="query-params")
groups = GROUPS if f.group == "All students" else {f.group: f.group}
bars = {label: {OUTCOMES[k]: series(k, [year], g).iloc[0] for k in OUTCOMES} for label, g in groups.items()}
st.caption(f"{scope()} · class of {d.year_label(year)} · share of the class in each situation, for all graduates and "
           "for Qatari and Non-Qatari graduates. Lighter bar: incomplete (hover for why).")
numbers = {f"{label}: {o}": row for label, rows in bars.items() for o, row in rows.items()}
ui.chart(charts.grouped(list(OUTCOMES.values()), bars), charts.ranked_table(numbers, "Share", label="Group"))

# --- Over the classes ---------------------------------------------------------------------------
st.subheader("Class by class")
trend = {label: series(k, classes) for k, label in OUTCOMES.items()}
st.caption(f"{scope()} · {f.group.lower()} · share of each graduating class a year later. Open dot: incomplete "
           "(a university missing from that class, or partial data; hover for which).")
ui.chart(charts.lines(trend), charts.table(trend))

# --- Working in Qatar ---------------------------------------------------------------------------
st.subheader("Working in Qatar")
qatar = {label: series("M25", classes, g) for label, g in groups.items()}
st.caption(f"{scope()} · of the graduates who were employed (or self-employed) a year later, the share working in "
           "Qatar.")
ui.chart(charts.lines(qatar), charts.table(qatar))

# --- Each university ----------------------------------------------------------------------------
if f.education_city:
    st.subheader(f"Each university, class of {d.year_label(year)}")
    in_slice = [u for u in d.universities() if u in set(d.pick(m, "M22", f.level, f.group)["university"])]
    left, right = st.columns(2)
    for column, metric, title in ((left, "M22", "Employed"), (right, "M25", "Working in Qatar (of the employed)")):
        per_uni = {u: d.points(m, metric, [year], u, level=f.level, group=f.group).iloc[0] for u in in_slice}
        with column:
            st.markdown(f"**{title}**")
            ui.chart(charts.ranked(per_uni), charts.ranked_table(per_uni, title))
    st.caption(f"{level_name.capitalize()} · {f.group.lower()} · × marks a university without usable outcomes for this "
               "class (hover for why). WCM-Q's graduates are doctors: nearly all go on to residencies, mostly abroad.")

st.caption("Source: the universities' Outcomes sheets, the earliest real report for each class (D-013). Class sizes "
           "from the Outcomes sheet, or from the graduates dated in Student Data where it gives 0 (D-021).")
