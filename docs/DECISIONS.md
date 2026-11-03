# Decision log

Every important choice, why it was made, and when. Add new decisions at the bottom; don't edit old ones. If a decision changes, add a new entry that replaces the old one.

---

### D-001 · Raw and processed data live in a private GitHub repository
**Date:** 2026-11-03
**Decision:** The original Excel submissions (`data/raw/`) and the generated tables (`data/processed/`) are both committed to a **private** repository.
**Why:** It allows the full automated flow: upload next year's files, and GitHub rebuilds and validates everything. The data is aggregated counts with no personal information, and the project owner confirmed it may be stored in a private repository.
**Consequence:** The repository must stay private. Anyone given access can see all institutional data.

### D-002 · Technology stack
**Date:** 2026-11-03
**Decision:** Python, pandas, Streamlit and Plotly for the pipeline and dashboard; GitHub Actions for automation; Streamlit Community Cloud for hosting.
**Why:** It's the same push-to-update pattern as the reference Qatar labour-market dashboard. It's all Python, free to host, and the dashboard redeploys automatically when the repository changes.

### D-003 · `data/raw/` is read-only
**Date:** 2026-11-03
**Decision:** Files in `data/raw/` are never edited by hand. All fixes (wrong year, renamed programs, duplicate files) are made in the pipeline code or in mapping tables in `data/reference/`.
**Why:** Every number on the dashboard can be traced back to the exact file it came from, and every correction is visible and reversible.

### D-004 · Exact library versions
**Date:** 2026-11-03
**Decision:** `requirements.txt` pins exact versions (Python 3.11).
**Why:** The reference dashboard didn't pin versions, so a library update could break the live site without anyone changing the code. With pinned versions, nothing changes until we change it on purpose.

### D-005 · Temporary: packages copied from another local environment
**Date:** 2026-11-03
**Decision:** PyPI (the Python package server) was blocked on the network in use, so `.venv` was created by copying the same package versions from another local environment on this Mac.
**Why:** It unblocked Phase 0 without changing any versions.
**To do:** On a network where PyPI works, run `.venv/bin/python -m pip install -r requirements.txt` to make the environment standard. Add `openpyxl` (Excel reading) and `pytest` (tests) at the same time, for Phases 1–3.

### D-006 · Commit identity
**Date:** 2026-11-03
**Decision:** Commits use the GitHub no-reply email for the account `YamanTheMan`, set for this repository only.
**Why:** It keeps a personal email address out of the commit history.
