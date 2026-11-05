"""Phase 5: page pieces every chapter shares."""
import streamlit as st

from dashboard import charts, data as d


@st.cache_data(show_spinner=False)
def _metrics(changed):
    return d.load_metrics()


def metrics():
    """metrics.csv, read once and read again whenever the file changes (a new build, or a push in Phase 6)."""
    return _metrics(d.METRICS.stat().st_mtime)


def chart(fig, numbers=None):
    """A chart, and its numbers in a table underneath (every chart has one, D-035)."""
    st.plotly_chart(fig, config=charts.CONFIG)
    if numbers is not None:
        with st.expander("Show the numbers"):
            st.dataframe(numbers, hide_index=True)


def selection(f):
    """One line saying what the charts on this page show."""
    who = "Education City" if f.education_city else d.universities()[f.university]
    level = {v: k for k, v in d.LEVELS.items()}[f.level].lower()
    group = f.group.lower()
    return f"{who} · {level} · {group}"
