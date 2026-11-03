"""QF Student Journey dashboard (Streamlit entry point).

Phase 0 skeleton: confirms the app runs and can see the raw data folder.
The story chapters are built in Phase 5.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

RAW_DIR = Path(__file__).parent / "data" / "raw"

CHAPTERS = [
    ("1. Growth", "How Education City enrolment changed from 2011 to 2025"),
    ("2. Getting in", "Applied → admitted → enrolled, and where students come from"),
    ("3. Studying", "Who the students are: nationality, gender, age, funding, internships"),
    ("4. Graduating", "How many finish, and how long it takes"),
    ("5. After", "Where graduates are one year later: work, further study, still searching"),
]

st.set_page_config(page_title="QF Student Journey", page_icon="🎓", layout="wide")

st.title("QF Student Journey")
st.caption("From application to career: the Education City student story, AY2011–2025")

st.info("**Phase 0: project skeleton.** The environment works. The charts arrive in Phase 5.")

st.subheader("Planned story")
for title, question in CHAPTERS:
    st.markdown(f"**{title}**: {question}")

st.subheader("Raw data check")
files = [p for p in RAW_DIR.rglob("*") if p.suffix in (".xlsx", ".xlsm") and not p.name.startswith("~$")]
if not files:
    st.error(f"No Excel files found in {RAW_DIR}")
else:
    inventory = (
        pd.DataFrame({"Academic year": [p.parent.name if p.parent != RAW_DIR else "All years" for p in files]})
        .value_counts()
        .rename("Files")
        .reset_index()
        .sort_values("Academic year")
    )
    st.metric("Excel files found", len(files))
    st.dataframe(inventory, hide_index=True, width="content")
