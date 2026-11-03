# Roadmap

How we work each phase: explain the goal → build it in small steps → check the result together → you approve → commit to GitHub → next phase.

**Status key:** ✅ done · 🔄 in progress · ⬜ not started

| Phase | Goal | Status |
|---|---|---|
| 0. Setup | Project folder, Git, private GitHub repo, Python environment | ✅ |
| 1. Data map | Document every sheet: columns, years, universities, quirks | ⬜ |
| 2. Extraction | Read every yearly template version into one tidy format | ⬜ |
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
- [ ] Reinstall packages from `requirements.txt` once PyPI is reachable (see D-005)

## Phase 1 — Data map ⬜

Goal: know exactly what is in every file before writing any extraction code.

- [ ] Inventory: one row per file → university, academic year, template version, sheets present
- [ ] For each sheet type, the columns it contains in each template version
- [ ] List of known problems (wrong year inside a file, duplicate versions, different templates, missing universities)
- [ ] Decide which file wins when a university has two files for the same year
- [ ] Reference table of university names (e.g. `WCM-Q` / `WCMC-Q` / `WCMQ` → one code)
- [ ] Output: `docs/data_dictionary.md` and `data/reference/file_inventory.csv`

## Phase 2 — Extraction ⬜

Goal: every raw sheet becomes rows in one long, consistent table.

- [ ] Agree on the tidy format (year, university, degree, program, stage, nationality, gender, count)
- [ ] One reader per sheet type, handling all template versions
- [ ] Program-name mapping table in `data/reference/`
- [ ] Output: `data/processed/*.csv` produced by one command

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
