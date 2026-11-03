# Roadmap

How we work each phase: explain the goal → build it in small steps → check the result together → you approve → commit to GitHub → next phase.

**Status key:** ✅ done · 🔄 in progress · ⬜ not started

| Phase | Goal | Status |
|---|---|---|
| 0. Setup | Project folder, Git, private GitHub repo, Python environment | ✅ |
| 1. Data map | Document every sheet: columns, years, universities, quirks | ✅ |
| 2. Extraction | Read every yearly template version into one tidy format | 🔄 |
| 3. Validation | Automatic checks that run on every upload | ⬜ |
| 4. Metrics | Define and compute the story numbers | ⬜ |
| 5. Dashboard | The story in chapters, running locally | ⬜ |
| 6. Go live | GitHub Action + Streamlit Cloud, push-to-update | ⬜ |
| 7. Insights & delivery | Findings, polish, documentation, final presentation | ⬜ |

---

## Phase 0 — Setup ✅

- [x] Project folder with a clear structure
- [x] Raw Excel files copied into `data/raw/` (60 files, unchanged from the original zip)
- [x] Python environment (`.venv`) with pinned versions in `requirements.txt`
- [x] Skeleton dashboard runs locally and sees the raw data
- [x] README, roadmap, decision log
- [x] Git repository with first commit
- [x] Private GitHub repository, code pushed
- [x] Reinstall packages from `requirements.txt` once PyPI is reachable (done: D-007)

## Phase 1 — Data map ✅

Goal: know exactly what is in every file before writing any extraction code.

- [x] Inventory: one row per file → university, academic year, template version, submission round, sheets (`pipeline/inventory.py`)
- [x] For each sheet type, the columns it contains in each template version
- [x] List of known problems: 14 found, P-01 to P-14 in the data dictionary
- [x] Decide which file wins when a university has two files for the same year (D-008, D-009)
- [x] Reference table of university names (`data/reference/universities.csv`)
- [x] Scope decision for HBKU (D-010)
- [x] Output: `docs/data_dictionary.md`, `data/reference/file_inventory.csv`, `data/reference/file_decisions.csv`
- [x] Tests for the inventory helpers and reference tables (9 passing)

**Carried into Phase 2:** timing rules for graduates (P-07), repeated graduation-rate classes (P-08) and repeated outcome classes (P-09).

## Phase 2 — Extraction 🔄

Goal: every raw sheet becomes rows in one long, consistent table.

- [x] Tidy format agreed: one row per number, with the exact source cell (data dictionary §6)
- [x] Student Data reader for templates v2019–v2022 (`pipeline/student_data.py`): 9,253 numbers from 43 files; matches QF on 34/40 university-years, and the other 6 are explained (P-15)
- [x] Timing rules decided: graduates (D-011), graduation rate (D-012), outcomes (D-013)
- [x] Apply the graduates rule (D-011): graduating class + evidence for every graduated number (`pipeline/graduates.py`, `data/reference/graduate_timing.csv`); confirmed against the next year's Outcomes sheets
- [x] Program mapping table (`data/reference/programs.csv`, `pipeline/programs.py`): 145 spellings → 80 programs in 73 stable groups, with level, qualification and field; fixes P-18 and P-19 (D-015, D-016). A new spelling stops the build.
- [ ] Readers: Student Pipeline, Graduation Rate (D-012), Outcomes (D-013), Nationalities, Ages, Registered Students Detailed, Funding, Internships, Graduate Nationalities
- [ ] Reader for VCU-Q's 2021–22 alternative form (P-04)
- [ ] One command builds every table (`pipeline/build.py`)

## Phase 3 — Validation ⬜

- [ ] Breakdowns add up to the reported totals
- [ ] No negative or non-numeric counts; blanks stay "unknown", never zero
- [ ] Registered counts match the QF consolidated files
- [ ] Quality report listing every issue found
- [ ] Automated tests in `tests/`

## Phase 4 — Metrics ⬜

- [ ] Metric definitions written down (acceptance rate, yield, Qatari share, on-time graduation, employment in Qatar, ...)
- [ ] `pipeline/metrics.py` computes them
- [ ] Small-count suppression rule decided and applied
- [ ] Leave `non_degree` rows out of all student totals (D-016)
- [ ] Decide whether to fill missing graduating classes from the next year's Outcomes sheet (class size only): NU-Q 2021–22 (108), TAMU-Q 2021–22 (110) and 2022–23 (113), WCM-Q 2020–21 (41)

## Phase 5 — Dashboard ⬜

- [ ] Chapter layout and navigation
- [ ] One chapter at a time: Growth → Getting in → Studying → Graduating → After
- [ ] Filters (university, program, nationality, gender, year)
- [ ] Auto-written summary sentences per chapter

## Phase 6 — Go live ⬜

- [ ] GitHub Action: extract → validate → metrics on every push to `data/raw/`
- [ ] Deploy on Streamlit Community Cloud as a private app
- [ ] End-to-end test: add a year's files, confirm the dashboard updates

## Phase 7 — Insights & delivery ⬜

- [ ] Key findings write-up
- [ ] Final documentation
- [ ] Presentation
