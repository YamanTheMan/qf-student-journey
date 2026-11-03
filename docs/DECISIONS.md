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

### D-011 · Graduates are dated by evidence (data dictionary P-07)
**Date:** 2026-11-03
**Decision:** Each "graduated" number is assigned to the **graduating class** (the academic year students graduated in) using, in order:
1. a label or remark in the file (e.g. "Graduating Class May 2023", "Graduate data for AY 2022-23", "Class of 2025");
2. a small hand-checked exceptions table, where each entry states its evidence;
3. otherwise the form's own definition: the file's current academic year.

A university-wide total of 0 graduates means **not reported**, not zero. If two files give the same class, the later file wins. Every number records which kind of evidence dated it.
**Why:** Universities followed different habits. Most report the current year (GU-Q, TAMU-Q, VCU-Q), while CMU-Q's Fall files report the previous class. Its Outcomes sheets prove it: the 87 graduates in its 2022–23 file are the class of 2022. With this rule CMU-Q gets a continuous series and its 2021–22 gap is filled.

### D-012 · Graduation rate: the latest report of each entering class wins (P-08)
**Date:** 2026-11-03
**Decision:** When the same entering class (cohort) appears in several files, use the most recent report.
**Why:** Later reports are more complete, because more students have had time to graduate within 150% of normal time.

### D-013 · Outcomes: the earliest real report of each graduating class wins (P-09)
**Date:** 2026-11-03
**Decision:** When outcomes for the same graduating class appear in several files, use the earliest report that isn't all zeros. Each record stores how many years after graduation it was measured.
**Why:** It's the closest to the intended "one year after graduation". Storing the gap keeps a late report (e.g. CMU-Q's class of 2023, first reported two years later) visible instead of hidden.
**Clarified when built (2026-11-03):** "the same class" means one university's graduating year, compared as a whole across files, not program by program. CMU-Q's 2023–24 sheet lists its programs without names and the 2024–25 sheet repeats the class with names; a program-by-program comparison counted that class twice (P-29). A report counts only if at least one outcome is non-zero. *Correction to the example above:* CMU-Q's class of 2023 was first reported one year after graduation (in 2023–24, without program names), not two.

### D-014 · Totals keep every reported part; QF's blanking rule is not used
**Date:** 2026-11-03
**Decision:** Each nationality × residency × gender cell is stored separately, and university totals use the universities' own reported totals. A blank part stays blank, but it does **not** blank the rest of its group.
**Why:** QF's consolidated file blanks a whole Non-Qatari group when one part (resident or international) is missing. We reproduced QF's numbers exactly with that rule (5 of 6 cases), and it undercounts: NU-Q 2023–24 shows 260 instead of the 474 the university reported. Our totals match QF exactly in the 34 university-years where no part is missing.

### D-015 · Program mapping: standard names, stable groups, levels (data dictionary P-18)
**Date:** 2026-11-03
**Decision:** `data/reference/programs.csv` has one row for every program spelling found in the files and gives it a standard `program`, a `program_group` that stays stable across all years, a `level` (foundation / undergraduate / graduate / non_degree), a `qualification` and a broad `field` (13 fields). Choices that needed judgment:
- **WCM-Q:** the Six-Year Medical Program (pre-medical years) is **undergraduate**; the Four-Year Medical Curriculum (medical school) is **graduate**. Both belong to the group "Medicine".
- **GU-Q:** "Undeclared" rows and 2024–25's "International Affairs" are one group, "International Affairs (undeclared)": students who haven't yet declared a major.
- **VCU-Q:** all BFA majors, and the years where they were reported as one line, roll up to the group "Fine Arts (BFA)".
- **NU-Q:** 2019–20's "Graduate Degree Program" is the MA in Sports Administration, NU-Q's only graduate program.
- **HEC-Q:** each cohort row maps to its program (Executive MBA, SBUM, GEMM); the raw name keeps the cohort.
- **TAMU-Q 2023–24:** the swapped Degree and Program columns are corrected through the mapping.

A spelling not in the table stops the build and is listed, so nothing unmapped reaches the dashboard.
**Why:** Universities rename and split programs from year to year, so trends need one stable name. Keeping every raw spelling as its own row makes each choice visible and easy to change.

### D-016 · Non-degree rows are labelled and left out of student totals (P-19)
**Date:** 2026-11-03
**Decision:** Exchange students (NU-Q 2019–20: 4), certificates (NU-Q 2020–21: 0) and HBKU's "Non-Degree/Conditional Admits" (2022–23: 24) stay in the data with `level = non_degree`, but they're left out of student totals (applied in Phase 4).
**Why:** The form asks for degree-seeking students only. QF's consolidated file keeps the HBKU rows, so our HBKU total for 2022–23 will be 24 lower than QF's, on purpose.

### D-017 · VCU-Q 2022–23 Student Pipeline: program inferred from the degree column (data dictionary P-21)
**Date:** 2026-11-03
**Decision:** In this one sheet the program column doesn't line up with the degree column. The rows are mapped by degree: BA → Art History, MFA → Design (MFA), Foundation and Pre-BFA → Pre-Art Foundation. Each row's note in `programs.csv` says the program was inferred.
**Why:** VCU-Q's own remark says it admits new students only into Art Foundation, BA Art History and MFA Design, and the degree column lists exactly those routes, while the program column lists BFA majors nobody can apply to. The numbers agree: the "BA" row has 42 applicants / 19 admitted against 53 / 26 for Art History in Student Data. The "Foundation" row has 0 applicants but 15 admitted, the same pattern Pre-Art Foundation shows in other years. This affects 153 numbers in one file.

### D-018 · Skip GU-Q 2022–23's Registered Students Detailed sheet (data dictionary P-32)
**Date:** 2026-11-03
**Decision:** This one sheet in this one file is not read. It's listed in the new `data/reference/sheet_exclusions.csv`, which works like `file_decisions.csv` but for a single sheet.
**Why:** It isn't a detailed list. GU-Q's own remark says it was not able to provide the detail and could give a summary instead, and the sheet holds two summary tables (class year U1–U4 × nationality × gender) whose columns don't line up with the sheet's headers. Reading it as a list doubled GU-Q's 2022–23 total (940 vs 464). Its Student Data and Nationalities sheets still cover that year.
