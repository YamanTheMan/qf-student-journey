"""Home: what the dashboard is, one key number per chapter, the five chapters, and how to read the charts."""
import streamlit as st

from dashboard import data as d, story, ui
from pipeline.inventory import REFERENCE_DIR

m = ui.metrics()
years = d.years_of(m, "M01")

st.title("QF Student Journey")
st.markdown(f"The Education City student story, from application to career · {d.year_span(years)}")
st.markdown(
    "Every number here comes from the yearly **Student Data Collection** files that Education City universities "
    "send Qatar Foundation. A pipeline reads every file, checks it, and records how good each number is. "
    "This dashboard shows the result, including where the data is incomplete.")

st.subheader("At a glance")
st.caption("Education City as reported, in the latest year each measure has. Open a chapter for the full story.")
numbers = story.key_numbers(m)
for column, n in zip(st.columns(len(numbers)), numbers):
    with column:
        st.metric(n["label"], n["value"], border=True)
        st.caption(n["detail"])
        st.page_link(n["page"], label="Read the chapter", icon=":material/arrow_forward:")

st.subheader("The story in five chapters")
CHAPTERS = [
    ("chapters/growth.py", "1 · Growth", "How many students Education City has, and who they are"),
    ("chapters/getting_in.py", "2 · Getting in", "Applied → admitted → enrolled, and which schools students come from"),
    ("chapters/studying.py", "3 · Studying", "Nationality, age, funding and internships"),
    ("chapters/graduating.py", "4 · Graduating", "How many finish, and how long it takes"),
    ("chapters/after.py", "5 · After graduation", "Work, further study or still searching, a year later"),
]
for path, title, question in CHAPTERS:
    st.page_link(path, label=f"**{title}**: {question}")

st.subheader("How to read the charts")
st.markdown(
    "- **Solid bar or dot**: complete data.\n"
    "- **Lighter bar or open dot**: incomplete. A university is missing from that year's total, or its data is "
    "partial. Hover to see which.\n"
    "- **×** on the baseline: no usable data that year. Hover to see why (not reported, not comparable, …).\n"
    "- **<5**: a group of fewer than 5 students, hidden to protect privacy. Shares and rates based on fewer than "
    "10 students aren't shown either.\n"
    "- **Education City totals**: *All that reported* adds up every university that sent usable data that year. "
    "*Same every year* counts only universities with data in every year, so years compare like for like. "
    "Change it in the sidebar.\n"
    "- **Show the numbers**, under each chart, opens the table behind it.")
st.page_link("chapters/about.py", label="**About the data**: where the numbers come from, and how good they are",
             icon=":material/fact_check:")

inventory = ui.table(REFERENCE_DIR / "file_inventory.csv")
file_years = sorted(set(inventory["academic_year"]) - {"all"})
st.divider()
st.caption(f"Built from {len(inventory)} Excel files ({d.year_span(file_years)}). Every push to GitHub is rebuilt, "
           "checked and tested before it reaches this page (D-044).")
