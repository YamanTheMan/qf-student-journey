"""Phase 5: the filters in the sidebar. They apply to every chapter and are kept in the page address,
so a link opens the dashboard with the same selection."""
from dataclasses import dataclass

import streamlit as st

from dashboard import data as d

VIEWS = {"reported": "All that reported", "same": "Same every year"}


@dataclass
class Filters:
    university: str  # d.EDUCATION_CITY or a university code
    same: bool       # Education City from the same universities every year (D-036)
    level: str       # d.ALL or a level as stored in metrics.csv
    group: str       # a key of d.GROUPS

    @property
    def education_city(self):
        return self.university == d.EDUCATION_CITY


def sidebar():
    """Draw the filters (call once, from app.py, before the page runs) and return the selection."""
    names = d.universities()
    with st.sidebar:
        st.markdown("**Filters**")
        # plain codes, so the page address stays short (?university=CMU-Q); the full name is in each caption
        university = st.selectbox("University", [d.EDUCATION_CITY, *names], key="university", bind="query-params")
        view = st.segmented_control(
            "Education City totals", list(VIEWS), format_func=VIEWS.get, default="reported", required=True,
            key="view", bind="query-params", persist_state="session",
            disabled=university != d.EDUCATION_CITY,
            help="**All that reported** adds up every university that sent usable data that year, so the "
                 "number of universities changes from year to year. **Same every year** counts only the "
                 "universities with data in every year shown, so years compare like for like.")
        level = st.selectbox("Level", list(d.LEVELS), key="level", bind="query-params")
        group = st.selectbox("Students", list(d.GROUPS), key="group", bind="query-params",
                             help="One group at a time: the files never split nationality by gender.")
    return Filters(university, view == "same", d.LEVELS[level], group)


def current():
    """The selection, for a page (app.py has already drawn the sidebar)."""
    return st.session_state["filters"]
