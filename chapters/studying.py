"""Chapter 3 · Studying: who the students are, how they study and pay, where they intern (metrics M11-M15)."""
import streamlit as st

from dashboard import charts, data as d, filters, story, ui

m = ui.metrics()
f = filters.current()
years = d.years_of(m, "M11", category="region: Qatar")
same = f.education_city and f.same
by_level = f.level != d.ALL
who = "Education City" if f.education_city else f.university

st.title("3 · Studying")
st.caption(f"Who the students are: nationality, age, attendance, funding and internships · {d.year_span(years)}")
st.markdown(story.studying(m, f.university, f.level))
if f.group != "All students":
    st.info("The sheets behind this chapter aren't split by nationality or gender, so it shows all students.")

year = st.segmented_control("Year", years, default=years[-1], format_func=d.year_label, required=True, key="year",
                            bind="query-params", help="For the one-year charts: nationalities, ages and funding.")


def scope(keep, what=""):
    """The caption's first part: whose numbers these are."""
    text = f"{who} · {[k for k, v in d.LEVELS.items() if v == f.level][0].lower()}"
    if same:
        text += (f" · only the {len(keep)} universities with {what or 'data'} in every year: {', '.join(keep)}"
                 if keep else f" · no university has {what or 'this'} in every year")
    return text


def label(category):
    return category.replace("-", "–")


def has_values(rows):
    """True if any row of a one-year mix has a number to draw."""
    return any(r["value"] == r["value"] for r in rows.values())  # NaN != NaN


def nothing(what):
    st.caption(f"No {what} for {who} in {d.year_label(year)}. Choose another year or university.")


# --- Where students come from -------------------------------------------------------------------
st.subheader(f"Where students come from, {d.year_label(year)}")
if by_level:
    st.caption("Nationalities aren't reported by level. Choose **All levels** in the sidebar to see them.")
else:
    keep = d.every_year_in(m, "M11", years, "region: ")
    regions = {r: row for r, row in d.mix_year(m, "M11", "region: ", year, f.university, f.same, among=keep).items()
               if r != "Other"}
    countries = {c: row for c, row in d.mix_year(m, "M11", "country: ", year, f.university, f.same,
                                                  among=keep).items()
                 if "not given" not in c.lower() and row["value"] > 0}  # NaN > 0 is False: hidden ones drop out
    top = dict(sorted(countries.items(), key=lambda kv: -kv[1]["value"])[:15])
    st.caption(f"{scope(keep, 'nationality data')} · share of students from each region of the world, and the 15 "
               "largest countries. Countries with fewer than 5 students aren't shown by name.")
    if has_values(regions):
        left, right = st.columns(2)
        with left:
            st.markdown("**By region**")
            ui.chart(charts.ranked(regions), charts.ranked_table(regions, "Share", label="Region"))
        with right:
            st.markdown("**Largest countries**")
            ui.chart(charts.ranked(top), charts.ranked_table(top, "Share", label="Country"))
    else:
        nothing("nationality data")

    st.markdown("**Regions over the years**")
    over_years = {r: d.points(m, "M11", years, f.university, f.same, category=f"region: {r}",
                              among=keep if same else None)
                  for r in d.categories(m, "M11", "region: ") if r != "Other"}
    order = sorted(over_years, key=lambda r: (r == "Not given", -over_years[r]["value"].fillna(0).iloc[-1]))
    over_years = {r: over_years[r] for r in order}
    st.caption(f"{scope(keep, 'nationality data')} · darker = a larger share. A dash: no data, or a group of fewer "
               "than 5 students (hover for which).")
    ui.chart(charts.heatmap(over_years), charts.table(over_years).drop(columns="Notes"))

# --- Age ----------------------------------------------------------------------------------------
st.subheader(f"Age, {d.year_label(year)}")
BANDS = ["under 18", "18-20", "21-23", "24-29", "30 and over", "not given"]
if by_level:
    st.caption("Ages aren't reported by level. Choose **All levels** in the sidebar to see them.")
else:
    keep = [u for u in d.every_year_in(m, "M12", years, "registered: ")
            if u in d.every_year_in(m, "M12", years, "new entrants: ")]
    groups = {}
    for family, row_label in (("registered: ", "All students"), ("new entrants: ", "New students")):
        ages = d.mix_year(m, "M12", family, year, f.university, f.same, among=keep)
        groups[row_label] = {label(b): ages[b] for b in BANDS if b in ages}
    st.caption(f"{scope(keep, 'ages')} · share of students in each age group, for all students and for those "
               "starting that year")
    numbers = {f"{g}: {b}": row for g, bands in groups.items() for b, row in bands.items()}
    if has_values(numbers):
        ui.chart(charts.stacked_shares(groups, [label(b) for b in BANDS], charts.ORDINAL + [charts.NOT_GIVEN]),
                 charts.ranked_table(numbers, "Share", label="Group"))
    else:
        nothing("ages")

# --- Full-time and scholarships -----------------------------------------------------------------
detail_years = d.years_of(m, "M13", "Attendance mix", "attendance: Full-time")
st.subheader("Full-time study and scholarships")
st.caption("From the Registered Students Detailed sheet, " + d.year_span(detail_years) + ". **Mixed**: the university "
           "answered for a whole group ('Majority full-time', 'Various'). **Not given**: no answer. Class year "
           "isn't shown: each university labels it its own way.")
left, right = st.columns(2)
for column, name, family, cats in ((left, "Attendance mix", "attendance: ", ["Full-time", "Part-time", "Mixed", "Not given"]),
                                   (right, "Scholarship share", "scholarship: ", ["Yes", "No", "Mixed", "Not given"])):
    keep = d.every_year_in(m, "M13", detail_years, family, name)
    groups = {d.year_label(y): d.mix_year(m, "M13", family, y, f.university, f.same, f.level, name, among=keep)
              for y in detail_years}
    with column:
        st.markdown(f"**{'Full- or part-time' if family == 'attendance: ' else 'On a scholarship'}**")
        st.caption(scope(keep))
        numbers = {f"{g}: {c}": row for g, cats_ in groups.items() for c, row in cats_.items()}
        ui.chart(charts.stacked_shares(groups, cats, charts.SERIES[:3] + [charts.NOT_GIVEN]),
                 charts.ranked_table(numbers, "Share", label="Year"))

# --- How students pay ---------------------------------------------------------------------------
funding_years = d.years_of(m, "M14", category="funding: self funded")
st.subheader(f"How students pay, {d.year_label(year)}")
if year not in funding_years:
    st.caption(f"Funding is reported from {d.year_label(funding_years[0])} on. Choose a later year.")
else:
    keep = d.every_year_in(m, "M14", funding_years, "funding: ")
    types = {t.capitalize().replace("Qf", "QF").replace("Self funded", "Self-funded"): row
             for t, row in d.mix_year(m, "M14", "funding: ", year, f.university, f.same, f.level,
                                      among=keep).items()}
    st.caption(f"{scope(keep, 'funding data')} · share of registered students with each type of funding. A student "
               "can have more than one, so the bars don't add up to 100% (P-35). QF scholarships aren't measured by "
               "this sheet (D-031).")
    if has_values(types):
        ui.chart(charts.ranked(types, last=("QF scholarship",)), charts.ranked_table(types, "Share", label="Funding"))
    else:
        nothing("funding data")

# --- Internships --------------------------------------------------------------------------------
st.subheader("Internships by type of employer")
TYPES = ["QF", "Public", "Private", "Abroad", "Other"]
NAME = "Internships by employer type"
intern_years = d.years_of(m, "M15", NAME, "employer: Private")
keep = d.every_year_in(m, "M15", intern_years, "employer: ", NAME)
if by_level:
    st.caption("Internships aren't reported by level. Choose **All levels** in the sidebar to see them.")
elif same and not keep:
    st.caption("No university reported internships in every year, so there's nothing to compare like for like. "
               "Choose **All that reported** in the sidebar.")
else:
    groups = {d.year_label(y): d.mix_year(m, "M15", "employer: ", y, f.university, f.same, name=NAME, among=keep)
              for y in intern_years}
    reported = m[(m["metric"] == "M15") & (m["name"] == NAME) & (m["university"] != d.ALL)]
    by_year = reported.groupby("year")["university"].agg(lambda s: ", ".join(u for u in d.universities() if u in set(s)))
    st.caption(f"{scope(keep)} · share of internships by type of employer. Not every university reports every year: "
               + "; ".join(f"{d.year_label(y)}: {by_year.get(y, 'none')}" for y in intern_years)
               + ". Employers named in 2019–21 were sorted into these types (D-034).")
    counts = {f"{g}: {t}": row for y, g in zip(intern_years, groups)
              for t, row in d.mix_year(m, "M15", "employer: ", y, f.university, f.same,
                                       name=NAME + " (count)", among=keep).items()}
    ui.chart(charts.stacked_shares(groups, TYPES), charts.ranked_table(counts, "Internships", label="Year"))

st.caption("Sources: the universities' Nationalities, Student Ages, Registered Students Detailed, Student Funding and "
           "Internships sheets. Each is shown as shares of its own total (D-022).")
