# Roadmap

How we work each phase: explain the goal → build it in small steps → check the result together → you approve → commit to GitHub → next phase.

**Status key:** ✅ done · 🔄 in progress · ⬜ not started

| Phase | Goal | Status |
|---|---|---|
| 0. Setup | Project folder, Git, private GitHub repo, Python environment | ✅ |
| 1. Data map | Document every sheet: columns, years, universities, quirks | ✅ |
| 2. Extraction | Read every yearly template version into one tidy format | ✅ |
| 3. Validation | Automatic checks that run on every upload | ✅ |
| 4. Metrics | Define and compute the story numbers | 🔄 |
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

## Phase 2 — Extraction ✅

Goal: every raw sheet becomes rows in one long, consistent table.

- [x] Tidy format agreed: one row per number, with the exact source cell (data dictionary §6)
- [x] Student Data reader for templates v2019–v2022 (`pipeline/student_data.py`): 9,253 numbers from 43 files; matches QF on 34/40 university-years, and the other 6 are explained (P-15)
- [x] Timing rules decided: graduates (D-011), graduation rate (D-012), outcomes (D-013)
- [x] Apply the graduates rule (D-011): graduating class + evidence for every graduated number (`pipeline/graduates.py`, `data/reference/graduate_timing.csv`); confirmed against the next year's Outcomes sheets
- [x] Program mapping table (`data/reference/programs.csv`, `pipeline/programs.py`): 145 spellings → 80 programs in 73 stable groups, with level, qualification and field; fixes P-18 and P-19 (D-015, D-016). A new spelling stops the build.
- [x] Shared sheet reader (`pipeline/tables.py`): each sheet only needs its own header reader. Proven identical on Student Data. Excel errors are never names, and a nameless row holding numbers stops the build.
- [x] Student Pipeline reader (`pipeline/student_pipeline.py`): 5,064 numbers from 28 files; matches Student Data exactly in 37 of 65 checks, within 10% in 56 (D-017)
- [x] Graduation Rate reader (`pipeline/graduation_rate.py`): 5,875 numbers from 22 files; latest real report per class wins (D-012); GU-Q classes back to 2005; class sizes checked against Student Data
- [x] Outcomes reader (`pipeline/outcomes.py`): 4,956 numbers from 28 files; earliest real report per class wins (D-013, clarified); class sizes match dated graduates
- [x] List-sheet reader (`pipeline/lists.py`) for sheets with one row per item instead of per program
- [x] Nationalities reader: 32,353 numbers from 42 files; country names standardised; totals match Student Data in 34 of 41 years
- [x] Registered Students Detailed reader: 2,249 numbers from 24 files; totals match Student Data in 19 of 24 years (D-018)
- [x] Ages, Graduate Nationalities, Internships and Funding readers (`pipeline/student_life.py`), each checked where an independent source exists
- [x] Reader for VCU-Q's 2021–22 alternative form (`pipeline/vcu_2021_22.py`, D-019): matches QF exactly in every nationality × gender group
- [x] One command builds every table: `.venv/bin/python -m pipeline.build` (10 tables from all 60 files in about 30 seconds; writes nothing if a person is needed; runs the tests)

## Phase 3 — Validation ✅

**Step 1: checks inside each table ✅**
- [x] Checks module (`pipeline/checks.py`) run by every build; an error stops the build without writing
- [x] Breakdowns add up to the reported totals (C03): 4 real mismatches; formula zeros recognised as unknown
- [x] No negative counts (C01); text in count cells kept as text (C02)
- [x] Admissions funnel narrows per university and year (C04); graduation and outcomes stay within their class (C05, C06)
- [x] Quality report (`docs/quality_report.md`) and findings table (`data/processed/quality_findings.csv`)
- [x] Automated tests for every check

**Step 2: checks across tables and sources ✅**
- [x] Registered counts match the QF consolidated files (C07): every gap explained by QF's blanking rule, no warnings
- [x] Secondary sheets vs Student Data (C08), Pipeline vs Student Data (C09), class sizes vs dated graduates (C10), entering classes vs newly enrolled (C11)
- [x] A quality flag for every measure × university × year (`pipeline/flags.py`, `data/processed/quality_flags.csv`), shown as grids in the quality report

**Step 3: decisions on the deferred problems ✅**
- [x] Pipeline vs Student Data (P-22): totals from Student Data, Pipeline for the school-type mix only (D-020)
- [x] Outcomes with a class size of 0 (P-27): fallback class size for rates (D-021)
- [x] Partial secondary sheets (P-33): shown as shares, never headcounts (D-022)
- [x] Funding sponsor rows (P-34): never summed; those years flagged partial by check C12 (D-023)
- [x] Graduate-nationality lists that aren't one class (P-36): left out (D-024)
- [x] How the dashboard uses each flag: show / show with note / show marked / leave out (D-025, `use` column)

## Phase 4 — Metrics 🔄

- [x] Metric definitions written down: 25 metrics in [docs/metrics.md](metrics.md)
- [x] `pipeline/metrics.py` framework (bases → formulas, Education City with coverage), run by every build
- [x] Growth and Getting-in metrics M01–M10; the 2011–2019 history equals QF's totals (D-029)
- [x] Studying metrics M11–M15: regions and countries, age bands, attendance / scholarship / class year, funding types, internships
- [x] Graduating and After metrics M16–M25 (D-021, D-027, D-028, D-032, D-033)
- [x] Small-count rule decided and applied: counts below 5 and rates on fewer than 10 hidden (D-026)
- [x] Apply the Phase 3 rules: Pipeline as school-type shares only (D-020); fallback class size for outcome rates (D-021); secondary sheets as shares (D-022); every metric carries its quality flag and `use` (D-025)
- [x] Leave `non_degree` rows out of all student totals (D-016)
- [x] Countries grouped into 12 regions (`data/reference/countries.csv`, D-030)
- [x] Funding types shown separately, never stacked (P-35); QF scholarships left out as not measured (D-031)
- [ ] Sort older internship employers into types (P-37)
- [x] Decided: comparable "by 150%" rate (D-027); classes without entrants give counts, not rates (P-25)
- [x] Decided: missing graduating classes filled from the next year's Outcomes sheet (D-028)

## Phase 5 — Dashboard ⬜

- [ ] Chapter layout and navigation
- [ ] Education City totals offer a "same universities every year" view: HBKU's presence only in 2022–24 lowers the Qatari share from 49% to 40% (45% without HBKU)
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
