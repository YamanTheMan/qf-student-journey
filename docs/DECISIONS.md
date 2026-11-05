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

### D-019 · VCU-Q 2021–22's different form: Fall 2021 snapshot, computed totals (P-04)
**Date:** 2026-11-03
**Decision:** `pipeline/vcu_2021_22.py` turns VCU-Q's alternative form into rows of the standard tables (Student Data, Registered Students Detailed, Nationalities, Ages):
- **Registered students come from the Fall 2021 rows only** (302). The Spring 2022 rows (288) are a second snapshot and are not read.
- The Admission sheet's "Registered" column is **not** read as newly enrolled: it adds up to all 302 registered students, while only 139 were admitted. So VCU-Q has no newly-enrolled figure for 2021–22.
- The form has no totals, so program totals are **computed from their nationality × gender parts**. They say so in `remarks` and list every source cell (e.g. `O3+O5+O9`).
- The Alumni sheet, "Gradautes - 2021-2022", is the class of 2021–22.

**Why:** Fall is the census date the form asks for (data as of September 30), and it's the snapshot QF's consolidated file used. Our numbers match QF's exactly in all four nationality × gender groups (190 / 5 / 96 / 11). The 68 graduates match the 69 that the next year's Outcomes sheet tracks for that class.

### D-020 · Pipeline is used for the school-type mix; totals come from Student Data (data dictionary P-22)
**Date:** 2026-11-03
**Decision:** Applied, admitted and newly-enrolled **totals** always come from Student Data. The Student Pipeline sheet is used only for the **mix of school types** (each type's share of the pipeline's own total, e.g. "private schools: 36% of applicants"), so its totals never compete with Student Data's. University-years flagged ≠ not comparable are left out, e.g. TAMU-Q 2021–22, whose pipeline "enrolled" (495) exceeds its own admitted and is 3.5× Student Data's 140.
**Why:** Pipeline and Student Data disagree by more than 10% in 8 university-years (quality check C09). Student Data is the primary, more complete form. Shares stay meaningful even when a pipeline total is off.

### D-021 · Outcome rates use a fallback class size (P-27)
**Date:** 2026-11-03
**Decision:** The denominator of an outcome rate (e.g. % employed) is, in order: the class size in the Outcomes sheet → the graduates dated in Student Data for that class → the sum of the reported outcomes, marked ◐ partial. Each rate records which denominator it used.
**Why:** CMU-Q's class of 2022–23 (103 outcomes) and VCU-Q's (48) report a class size of 0. CMU-Q's dated graduates (103) fill the first; VCU-Q has no dated graduates for that class, so its reported outcomes are the best available base.

### D-022 · Secondary sheets are shown as shares, never as headcounts (P-33)
**Date:** 2026-11-03
**Decision:** Nationalities, Registered Students Detailed, Ages, Funding and Graduate Nationalities are shown as **percentages of the students they cover** (e.g. "42% from GCC countries"). Headcounts always come from Student Data. Years where a sheet covers fewer students than Student Data are marked ◐ partial.
**Why:** These sheets sometimes cover fewer students than Student Data (quality check C08: e.g. TAMU-Q 2023–24 Nationalities 609 of 672; HEC-Q 2019–20 Ages 34%). Shares stay honest when coverage is incomplete; headcounts would understate.

### D-023 · Funding sponsor rows stay out of totals; those years are partial (P-34)
**Date:** 2026-11-03
**Decision:** Rows that break funding down by named sponsor without a program (`row_type = sponsor_detail`) are never added to funding totals. They're used only as a list of named sponsors. A new quality check (C12) marks Funding for those university-years ◐ partial: GU-Q 2023–24 and VCU-Q 2023–24. VCU-Q 2022–23 reported its funding *only* in sponsor rows (544 students, equal to its sheet total; its program rows are empty), so its program-level funding is ✗ not reported.
**Why:** It differs by university whether these rows repeat the main line or add to it (for GU-Q they look additional; for VCU-Q they don't add up to its main line, 11 vs 126). Adding them could double-count. Leaving them out without a mark would understate.

### D-024 · Graduate-nationality lists that aren't one class are left out (P-36)
**Date:** 2026-11-03
**Decision:** NU-Q 2023–24's list (720, against 112 graduates, likely cumulative) and HEC-Q 2021–22's (128, against 53) are left out of the graduates-by-nationality view. Quality check C10 flags any list more than double its class as ≠ not comparable, so a future one is caught the same way.
**Why:** A list that isn't one graduating class can't be compared with the others, and its shares would describe a different group.

### D-025 · How the dashboard uses the quality flags
**Date:** 2026-11-03
**Decision:** Each flag in `data/processed/quality_flags.csv` carries a `use`:

| Flag | `use` | On the dashboard |
|---|---|---|
| ✓ complete, ◑ breakdown partial | `show` | shown normally |
| ≈ differs | `show_with_note` | shown, with a note on what it differs from |
| ◐ partial | `show_marked` | shown with a "partial" mark |
| ≠ not comparable, ✗ not reported | `leave_out` | a visible gap, with the reason on hover |
| – not in form | `not_applicable` | no gap shown; that year's form didn't ask |

**Why:** Showing only complete data would hide VCU-Q's redacted years, HBKU's graduates and every partial year. This rule keeps all usable data visible while being honest about its limits.

### D-026 · Small numbers are hidden: counts below 5, rates on fewer than 10
**Date:** 2026-11-04
**Decision:** In any breakdown (by nationality, gender, program, country, age, …), a count of 1–4 is shown as "<5", never as the number. A share or rate based on fewer than 10 students isn't shown. University totals and Education City totals are always shown. `pipeline/metrics.py` applies this before anything reaches the dashboard: a hidden value is stored as blank with the label "<5".
**Why:** Tiny groups (e.g. 1 Qatari male in a program) could identify a person. The universities themselves withheld small numbers: VCU-Q blanked everything below 10, and several graduate lists say "less than 5".

### D-027 · The 150% graduation rate counts everyone who graduated by 150% of normal time (P-24)
**Date:** 2026-11-04
**Decision:** "Graduated by 150%" = on-time graduates + later graduates up to 150%. TAMU-Q's "within 150%" already counts everyone, so it's used as is. For the other universities the within-100% and extra-within-150% numbers are added. The convention is detected per entering class (quality check C05: 150% graduates exceeding the class only make sense if they include the on-time ones) and recorded with each rate.
**Why:** Raw, the same column means two different things, which would make TAMU-Q look far better than it is. Converted, every university's rate answers the same question.

### D-028 · Missing graduating classes are filled from the next year's Outcomes sheet
**Date:** 2026-11-04
**Decision:** Where Student Data has no graduate count for a class, the class size in the following year's Outcomes sheet is used, labelled `source = outcomes`: NU-Q 2021–22 (108), TAMU-Q 2021–22 (110) and 2022–23 (113), WCM-Q 2020–21 (41). It gives the total and the Qatari / Non-Qatari split, but no gender or program detail.
**Why:** The Outcomes class size is the same graduating class counted a year later, and where both exist they match (CMU-Q 87 = 87, 103 = 103, 120 = 120; NU-Q 112 = 112; WCM-Q 41/42/50). Filling the gaps gives a continuous graduates series.

### D-029 · Growth uses QF's consolidated file before 2019–20 and our Student Data after
**Date:** 2026-11-04
**Decision:** Registered students for 2011–12 to 2018–19 come from QF's consolidated file, the only source for those years, at university × level × Qatari / Non-Qatari (gender only where QF has it). From 2019–20 they come from our Student Data. Years in which a university has no data are marked through Education City's `coverage`.
**Why:** It gives a 14-year trend. Where QF's numbers are complete they equal ours exactly (34 of 40 university-years). Where QF left out groups with a blank part, ours are more complete (D-014, P-15). Level mapping for QF years: Bachelor's / Undergraduate → undergraduate; Foundation → foundation; Master's, Doctorate, Diploma, Graduate, JD and MD → graduate; Non-degree and Exchange → non-degree. WCM-Q's medical students therefore count as graduate before 2019–20, while from 2019–20 its pre-medical years count as undergraduate (D-015). That's a known break in WCM-Q's level split, though not in its total.

### D-030 · One country table, with 12 regions
**Date:** 2026-11-04
**Decision:** `data/reference/countries.csv` replaces the small alias list (`country_aliases.csv`, removed). It gives every country spelling seen in the files (252) one standard country (209) and one region: Qatar · Other GCC · Other Arab countries · South Asia · East & Southeast Asia & Pacific · Iran, Turkey, Caucasus & Central Asia · Sub-Saharan Africa · Europe · North America · Latin America & Caribbean · Other · Not given. Matching ignores capitals and spaces. A new spelling stops the build until a row is added. Choices that needed judgment: "Korea" = South Korea; "West Bank" = Palestine; Israel sits with Iran, Turkey, the Caucasus and Central Asia; Cyprus with Europe; Puerto Rico with Latin America & Caribbean.
Two refinements to the duplicate rule came with it. The form lists some countries under two names ("Burma" and "Myanmar", "Saint Kitts and Nevis" and "St. Christopher Nevis"), with students under one and 0 under the other. When at most one row has students, both rows are used (adding nothing but the real number). Two *different* non-zero numbers still stop the build.
**Why:** With students from 96 countries a year, regions make the "where students come from" view readable. Separate standardisation per table had left variants ("Burma" / "Myanmar", "BELGIUM" / "Belgium", typos like "Palisrine") that would have split one country into several.

### D-031 · QF scholarships can't be measured from the Funding sheet
**Date:** 2026-11-04
**Decision:** The "QF scholarship" funding type is left out of the funding metric (M14) as a visible gap, with the note "Not measured here: universities leave QF scholarships to QF Financial Services".
**Why:** Every university reports 0 QF-scholarship students in every year (2022–23 to 2024–25), while QF certainly funds Education City students, and the form's notes say these figures are "to be provided by QF financial services". Showing 0% would state something false.

### D-032 · Graduation rates count once their time has passed; unreported drop-outs and impossible splits aren't used (P-38, P-39)
**Date:** 2026-11-04
**Decision:** (1) An on-time rate is computed only when the class's normal time has ended by the end of the report's academic year, and a "by 150%" rate only when 1.5 × normal time has. Normal time is 4 years for every bachelor's class (the form's default; NU-Q's "normal time" column holds years since entry instead) and the program's reported normal time for graduate classes; a graduate class without one gets no rate. (2) A report with 0 drop-outs in every class gives no drop-out rate. (3) A class whose Qatari or Non-Qatari part has more graduates than entrants keeps its totals but not its nationality split; quality check C05 now tests the parts and flags those university-years ◑.
**Why:** (1) Universities also report classes still within their window: CMU-Q's three classes and TAMU-Q's 2020–21 class show 0 "within 150%" only because that time hadn't come, which would read as a collapse (TAMU-Q 88% → 52%). (2) TAMU-Q reports 0 drop-outs in every class but 11–21 non-completers, so its true drop-out rate is unknown, not 0%. (3) HEC-Q's splits gave Education City a Qatari on-time rate of 205%.

### D-033 · D-028 is applied as a rule, which fills six graduating classes
**Date:** 2026-11-04
**Decision:** Every graduating class with no Student Data graduate count takes the next year's Outcomes class size, as D-028 says. Besides the four classes named there, this fills HBKU 2021–22 (151) and NU-Q 2023–24 (127; NU-Q's 2024–25 file gives 118 graduates, dated by the form to 2024–25). The filled classes keep the Outcomes sheet's program and level detail (it uses the same program mapping); they have no gender split. Quality check C10 compares a Graduate Nationalities list of such a class with that class size, so TAMU-Q's 2022–23 list (40 of 113) is now marked ◐ partial.
**Why:** The rule is what D-028 decided; the list of four was what it found at the time. Applying it the same way everywhere avoids hand-picked exceptions, and `source = outcomes` keeps every filled class visible.

### D-034 · Older internship employers are sorted into the form's five types (P-37)
**Date:** 2026-11-04
**Decision:** The employers that the 2019–20 and 2020–21 forms name (180 spellings, 425 internships) get one of the five types the form asks for from 2021–22, through `data/reference/employers.csv`:
- **QF**: Qatar Foundation and its members (Sidra, QCRI / HBKU, WISE, Doha Debates, QCDC, Qatar Green Building Council, Al Shaqab) and Education City universities.
- **Public**: Qatari government bodies and companies the state owns (ministries, Qatar Museums, Hamad Medical, Supreme Committee, the QFC authorities, Qatar Airways, QAPCO, Al Jazeera, beIN).
- **Private**: companies in Qatar, including firms whose name doesn't say where they are (assumed to be in Qatar).
- **Abroad**: any employer based outside Qatar, whatever its sector, including Qatar's own embassies.
- **Other**: non-profits, think tanks and foreign embassies in Qatar (Brookings Doha Center, Education Above All, US Embassy Doha), and the few names that couldn't be identified.

Each row says whether its type is clear from the `name` (48 spellings, 104 internships), `known` (77, 227) or a `guess` (55, 94), with the reason. A new name stops the build until a row is added.
**Why:** It makes the internship story comparable across all six years instead of starting in 2021–22. The guesses are mostly small firms (1–2 internships each) and are marked, so they can be corrected one row at a time. Caveat: 2019–21 lists come from four universities, and many 2020 internships were likely remote, so "Abroad" there means a foreign employer, not necessarily travel.

### D-035 · The dashboard: one page per chapter, shared filters, and one way of drawing data quality
**Date:** 2026-11-05
**Decision:** The dashboard (`app.py`, `chapters/`, `dashboard/`) has a Home page and one page per story chapter, listed in the sidebar. The filters sit below that list and apply to every page: university (or Education City), level, and one student group at a time (all, Qatari, Non-Qatari, female, male; the files never split nationality by gender). The selection is kept in the page address, so a link reopens the same view. The dashboard computes nothing new: every number comes from `metrics.csv`, except the sums in D-036. Every chart follows the same rules for D-025's flags:
- **Solid** bar or dot: complete.
- **Lighter** bar or **open** dot: incomplete. A university is missing from that year's Education City total, or the data is partial. The tooltip says which.
- **×** on the baseline: no usable data that year (left out, not reported, or a hidden small number). The tooltip says why.
- Every chart has its numbers in a table underneath ("Show the numbers").
- Colours: two validated categorical colours (blue, orange) plus a lighter step of the blue for "incomplete". No chart uses more than two series colours; nine universities get small multiples instead of nine colours.
- Each chapter opens with a sentence written from the numbers (`dashboard/story.py`). It always compares years like for like (D-036), whatever the chart shows.
**Why:** One set of rules makes the gaps readable everywhere: a reader learns once what a light bar or an × means. Keeping all arithmetic in the tested pipeline means the dashboard can't drift from the numbers in the report.

### D-036 · "Same universities every year" view of Education City
**Date:** 2026-11-05
**Decision:** A sidebar switch shows Education City either as **all that reported** (the default: every university with usable data that year, as `metrics.csv` has it) or as the **same universities every year**: only universities with usable data in every year of that measure, summed by the dashboard (counts added; shares and rates add their numerators and denominators). Years in which a measure doesn't exist at all (gender before 2014–15) don't narrow the set; they stay gaps. A university without a row in a slice (no students at that level) adds nothing. If any part is hidden (D-026) or left out, that year's sum isn't shown either, because adding a hidden part to shown ones would give it away. For Growth the set is GU-Q, NU-Q, TAMU-Q, WCM-Q and HEC-Q: together they went from 1,132 students in 2011–12 to 2,163 in 2024–25.
**Why:** Universities come and go from the data (HBKU only in some years, UCL-Q until 2018–19, CMU-Q missing 2021–22, VCU-Q 2022–23 not reported), so the all-that-reported total jumps for reasons that have nothing to do with students. Example: the Qatari share drops from 49% to 40% in 2022–23, because HBKU appears and VCU-Q (65% Qatari) is missing; the same five universities stay at 46–47% in both years. Doing the sum in the dashboard lets it follow whatever years a chart shows, and summing only values that are shown can't reveal a hidden number.

### D-037 · A share needs its split to cover the students (P-40)
**Date:** 2026-11-05
**Decision:** The Qatari and female shares (M02, M03, M09, M17) divide by the students whose nationality (or gender) is known. Each share now compares that number with the stage's total. If the split covers at least 95% of the students, the share is used as before. From 90% to under 95% it's marked partial (`show_marked`); under 90% it's left out (`leave_out`). Both get quality `breakdown_partial` and a note with the share's possible range, e.g. "Gender known for 270 of 323 students, so the share could be anywhere from 84% to 100%". This changes 28 values, among them VCU-Q 2024–25 (100% female, now left out) and Education City 2023–24 (marked: VCU-Q gave no split).
**Why:** A blank part (VCU-Q blanks small numbers) made the known part look like everyone: the dashboard showed VCU-Q as 100% female. The range in the note says exactly how wrong a share could be. Under 90% coverage the range is over 10 points, too wide to put on a chart. These thresholds are a judgment call and can be changed in one place (`KNOWN_FOR_SHARE` in `pipeline/metrics.py`).

### D-038 · A year far below the one before is not comparable (P-41)
**Date:** 2026-11-05
**Decision:** New quality check C13: if a Student Data stage (applied, admitted, newly enrolled or registered) for a university is under a quarter of its previous year, that stage's flag becomes ≠ not comparable, and the dashboard leaves it out with the reason on hover. It catches TAMU-Q 2024–25: its Spring 2025 file reports admissions for the graduate program only (30 applicants, 14 admitted, 4 new students against 1,317, 340 and 152 the year before). Education City's 2024–25 admissions now cover 6 universities instead of 7.
**Why:** Formula zeros in a few programs are normal (GU-Q and NU-Q admit students undeclared, so their per-major rows stay empty), so they can't flag a year on their own. A collapse is different: no real year falls to a quarter of the one before. Every other fall in these four stages stays above half (the largest: HEC-Q's applicants, 251 → 134 in 2020–21), so the threshold leaves real declines alone. Zeros across the board were already "not reported".

### D-039 · Charts shown together use one "same universities" set
**Date:** 2026-11-05
**Decision:** Where a chapter shows related measures together (applicants, admitted, new students, acceptance rate, yield), the "same universities every year" view uses the universities with data in every year for **all** of them, not a set per measure. For Getting in that's GU-Q, NU-Q, WCM-Q and HEC-Q (VCU-Q has no 2022–23 new students; TAMU-Q no 2024–25 admissions, D-038). The school-type mix has its own years (2021–22 on) and so its own set (GU-Q, NU-Q, WCM-Q). Each chart's caption names its set.
**Why:** With a set per measure, the funnel could compare applicants from five universities with new students from four, and its percentages would mean nothing.
