"""QF Student Journey dashboard (Streamlit entry point).

Run from the project folder:
    .venv/bin/python -m streamlit run app.py

Each chapter is a page in chapters/. The sidebar filters are drawn here, so they stay the same on every page.
"""
import streamlit as st

from dashboard import filters

st.set_page_config(page_title="QF Student Journey", page_icon="🎓", layout="wide")

page = st.navigation({
    "": [st.Page("chapters/home.py", title="Home", icon=":material/home:", default=True)],
    "The story": [
        st.Page("chapters/growth.py", title="1 · Growth", icon=":material/trending_up:"),
        st.Page("chapters/getting_in.py", title="2 · Getting in", icon=":material/how_to_reg:"),
        st.Page("chapters/studying.py", title="3 · Studying", icon=":material/menu_book:"),
        st.Page("chapters/graduating.py", title="4 · Graduating", icon=":material/school:"),
        st.Page("chapters/after.py", title="5 · After graduation", icon=":material/work:"),
    ],
})
st.session_state["filters"] = filters.sidebar()
page.run()
