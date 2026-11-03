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

### D-007 · Environment rebuilt from PyPI (closes D-005)
**Date:** 2026-11-03
**Decision:** `.venv` was deleted and rebuilt from PyPI. `openpyxl==3.1.5` (Excel reading) was added to `requirements.txt`. `pytest==9.2.0` goes in a new `requirements-dev.txt`, because tests run only locally and in GitHub Actions, never on the live server.
**Why:** It's a standard, reproducible environment. Anyone can rebuild it with one command.

### D-008 · CMU-Q 2020–21: combine the original and revised files (data dictionary P-01, P-02)
**Date:** 2026-11-03
**Decision:**
- The CMU-Q file in the `AY21-22` folder is treated as the quality-checked revision of **2020–21**, and it's the main CMU-Q source for that year.
- CMU-Q has **no 2021–22 data**; that's a real gap.
- For **Computer Science and Computational Biology** only, applied, admitted and newly enrolled come from the original 2020–21 file. In the revision these were moved onto the wrong program when the row labels were swapped.

Recorded in `data/reference/file_decisions.csv`.
**Why:** Neither file is fully right. The original has registered and graduated swapped between the two programs. The revision fixes those, and also corrects graduate counts and nationalities, but swaps the applicant numbers. Combining them keeps the correct part of each, and the rule is written down so anyone can check it.
**Note:** QF's consolidated file uses the original, wrong registered numbers (Computational Biology 88, Computer Science 5). Our pipeline's numbers will differ from QF's for these two cells, on purpose.

### D-009 · GU-Q 2022–23: use the `.submitted` file (P-03)
**Date:** 2026-11-03
**Decision:** Use `AY22-23 GU-Q Student Data Collection.submitted.xlsx` and ignore the `.completed` copy.
**Why:** Every data sheet is identical in both. `.submitted` fixes a typo (CMU-Q written in a GU-Q cell).

### D-010 · HBKU is included and clearly labelled (P-06)
**Date:** 2026-11-03
**Decision:** HBKU is included wherever it has data: registered students for 2011–2019 and 2022–2024, and the other story chapters for 2022–23 and 2023–24. The dashboard gets an **undergraduate / graduate** filter so comparisons with the branch campuses stay fair. HBKU's colleges (CSE, CIS, CHSS, …) roll up to HBKU.
**Why:** HBKU is a QF university, so leaving it out would understate Education City. But it is mostly graduate programs, so it shouldn't be compared directly with undergraduate-only campuses.
