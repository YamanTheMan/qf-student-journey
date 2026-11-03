# Data dictionary

What is in `data/raw/`, what each number means, and what's wrong with it. This is the reference for building the pipeline (Phase 2) and its checks (Phase 3).

- **File-by-file list:** [`data/reference/file_inventory.csv`](../data/reference/file_inventory.csv), regenerated with `.venv/bin/python -m pipeline.inventory`.
- **University names:** [`data/reference/universities.csv`](../data/reference/universities.csv) maps every spelling found in the files to one code.
- **Which files to use:** [`data/reference/file_decisions.csv`](../data/reference/file_decisions.csv) lists the exceptions. Every other file is used as-is. `use` is one of: `no` (skip the file), `only` (use only the listed `programs` × `stages`), `except` (use everything but the listed `programs` × `stages`), or `yes`. `academic_year` overrides the year implied by the folder.

---

## 1. Two kinds of source

| Kind | Files | What it is |
|---|---|---|
| **University submissions** | 45 | Each university fills QF's *Student Data Collection* Excel form once or twice a year. They contain **all the story data**. Available **2019–20 → 2024–25**. |
| **QF consolidated** | 15 | QF's cleaned table of **registered students only**, by year × university × program × nationality × gender. Available **2011–12 → 2024–25**. Includes an *Issues* sheet with 152 documented data problems. |

All numbers are **aggregated counts**: no names, IDs or personal records exist in any file.

## 2. Coverage

### Registered students, 2011–2025 (QF consolidated)

| University | Years with data | Gaps |
|---|---|---|
| CMU-Q, Carnegie Mellon | 2011–12 → 2024–25 | 2021–22 |
| GU-Q, Georgetown | all 14 | none |
| HBKU, Hamad Bin Khalifa | 2011–12 → 2018–19, 2022–23, 2023–24 | 2019–22, 2024–25 |
| HEC-Q, HEC Paris | all 14 | none |
| NU-Q, Northwestern | all 14 | none |
| TAMU-Q, Texas A&M | all 14 | none |
| UCL-Q, UCL Qatar | 2012–13 → 2018–19 | closed afterwards |
| VCU-Q, VCUarts | 2011–12 → 2021–22, 2024–25 | 2022–23, 2023–24 (registered not supplied / withheld) |
| WCM-Q, Weill Cornell | all 14 | none |

### University submissions, 2019–2025

One file per university per year, except: **no HBKU file before 2022–23 or in 2024–25**, **two GU-Q files in 2022–23**, and **the CMU-Q file in the 2021–22 folder actually contains 2020–21 data** (see P-01).

### Which story data exists for which years

| Chapter | Data | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Growth | Registered (QF consolidated, back to 2011) | ■ | ■ | ■ | ■ | ■ | ■ |
| Getting in | Applied → admitted → newly enrolled | ■ | ■ | ■ | ■ | ■ | ■ |
| Getting in | Pipeline by school type | | | ■ | ■ | ■ | ■ |
| Studying | Nationalities, ages | ■ | ■ | ■ | ■ | ■ | ■ |
| Studying | Class year, full/part time, scholarship | | | ■ | ■ | ■ | ■ |
| Studying | Funding | | | | ■ | ■ | ■ |
| Studying | Internships by employer type | ■ | ■ | ■ | ■ | ■ | ■ |
| Graduating | Graduated counts | ■ | ■ | ■ | ■ | ■ | ■ |
| Graduating | Graduation rate by entering class | | | ■ | ■ | ■ | ■ |
| After | Outcomes one year after graduation | | | ■ | ■ | ■ | ■ |

## 3. Template versions

QF changed the form several times. `pipeline/inventory.py` recognises each version from the sheets only it has.

| Template | Used in | Files | Recognised by | Key differences |
|---|---|:-:|---|---|
| **v2019** | 2019–20 | 7 | `DD Lists` + `Student Data` | Lettered sheet names (`A. Student Data`). Extra `Year / Half Year / Division` columns. Applied/accepted/enrolled split **Qatari / Non-Qatari only** (no gender). |
| **v2020** | 2020–21 | 8 | `Control Sheet` + `Student Data` | Same measures as v2019. Adds helper sheets (`0A. Student Data`, `Student Data Summary`) that repeat the data; ignore them. |
| **v2021** | 2021–22 | 5 | `Student Pipeline` + `Graduation Rate` | Adds **gender** to applied/admitted/enrolled, plus Pipeline, Graduation Rate, Outcomes and Internships sheets. |
| **v2021-alt** | VCU-Q 2021–22 | 1 | `Admission` + `Alumni` | A completely different form: long tables (`Student Statistics`, `Admission`, `Alumni`) with Fall 2021 and Spring 2022 snapshots. |
| **v2022** | 2022–23 → 2024–25 | 24 | `Student Funding` + `Student Pipeline` | Splits Non-Qatari into **Resident** and **International**. Adds Student Funding. Stable for three years; new uploads will most likely use it. |

Within a template, header **wording** still varies (line breaks, typos, a year inside the header text, extra blocks). The extraction in Phase 2 must therefore **read each column by what its header says, not by its position**.

## 4. What the numbers mean (from the form's own "How to Fill" instructions)

- **Reporting year:** July 1 – June 30.
- **Two collection rounds:** **Fall** (data as of September 30) and **Spring** (as of June 30). Only 13 of 45 file names say which round they are; the inventory's `submission_round` column records it when known.
- **Scope:** degree-seeking students only. No cross-registered, study-abroad, certificate or continuing-education students.

| Measure | Definition |
|---|---|
| **Applied** | Applied during the previous academic year to start in the current one |
| **Admitted** (v2019–20: "Accepted") | Applied and were admitted, same period |
| **Newly enrolled** | New students who started in the current academic year |
| **Registered** | All students (new + continuing) enrolled in the current academic year |
| **Graduated** | Graduates of the current academic year, **requested only in the Spring round** (see P-07) |
| **Pipeline** | Applied / admitted / enrolled / denied by school type: QF schools, independent/public, private, international (outside Qatar), Academic Bridge Program (ABP). "Recommended for ABP" is included in "Denied". |
| **Graduation rate** | For one entering class (*cohort*): first-time enrolled, non-completers, drop-outs, graduated within **100%** and **150%** of normal time |
| **Outcomes after 1 year** | **Previous** academic year's graduates, one year later: employed, self-employed, graduate school, still searching, not seeking, each **in Qatar or abroad** |
| **Internships** | Number of internships by employer type: QF, public, private, abroad, other |
| **Funding** | Students who are self-funded, or on QF scholarship, university scholarship or financial aid, with average amounts in QAR |

### Breakdowns available

| Breakdown | Available |
|---|---|
| Qatari / Non-Qatari | Every template |
| Gender | Registered and graduated: every template. Applied/admitted/enrolled: from v2021 |
| Resident vs international Non-Qatari | v2022 only |
| Nationality (country) | Separate `Student Nationalities` / `Graduate Nationalities` sheets |
| Degree and program | Every template |

**Common level for long-term trends:** university × program × Qatari/Non-Qatari, plus gender where available.

## 5. Sheets used for the story

| Sheet | Templates | Shape | Chapter |
|---|---|---|---|
| Student Data | all | Wide: one row per program, columns for stage × nationality group × gender | Getting in, Studying, Graduating |
| Student Pipeline | v2021, v2022 | Wide: one row per program, columns for school type × stage | Getting in |
| Student Nationalities | all | One row per country: applied/admitted/enrolled/registered by gender | Studying |
| Student Ages | all | One row per age: male/female, and new entrants to first degree | Studying |
| Registered Students Detailed | v2021, v2022 | **Long**: program × nationality × gender × full/part time × scholarship × sponsorship × class year → count | Studying |
| Student Funding | v2022 | Wide: one row per program, funding type × Qatari/Non-Qatari | Studying |
| Internships (v2019–20: Internship - Employers) | all | One row per employer type | Studying |
| Graduation Rate | v2021, v2022 | One row per program × entering class | Graduating |
| Graduate Nationalities | v2021, v2022 | One row per country | Graduating |
| Student Outcomes after 1 Yr | v2021, v2022 | Wide: one row per program, outcome × in/outside Qatar × Qatari/Non-Qatari; sometimes several graduating classes in one sheet | After |
| QF consolidated `Consolidated` | — | Long: year × university × program × nationality × gender → registered | Growth |

Not used for the story (staff, facilities, continuing education, admin): Employee Nationalities, Employee Statistics, Facilities, Continuing Education Data, Academic Support Services, Program and Forecast Data, Data Metrics, Control/helper sheets.

## 6. Processed tables (`data/processed/`)

Generated by the pipeline; never edit them by hand.

### `student_data.csv`: one row per number in every Student Data sheet

Built by `.venv/bin/python -m pipeline.student_data` from the 43 files using templates v2019–v2022.

| Column | Meaning |
|---|---|
| `file_year` | Academic year the file belongs to, after any override in `file_decisions.csv` |
| `university` | Standard code from `universities.csv` |
| `row_type` | `program` (one program) · `all_programs` (the university reported one combined line) · `unnamed_row` (row without a program name among named programs, usually a subtotal: **never add it**) · `sheet_total` (the footer totals under the table) |
| `entity_reported`, `degree`, `program` | Exactly as written in the file (standardised later by the program mapping) |
| `stage` | `applied` · `admitted` · `newly_enrolled` · `registered` · `graduated` |
| `nationality` / `residency` / `gender` | `Qatari`, `Non-Qatari` / `Resident`, `International` / `Male`, `Female`; `All` when not split |
| `breakdown` | Which split the number belongs to: `total`, `nationality`, `gender`, `nationality_gender`. **Only add numbers that share the same breakdown.** |
| `period_label`, `band_label` | Period written in the header (e.g. "May 2025") or above the column block (e.g. "As of Fall 2024") |
| `count` | The number, or blank. **Blank is never zero.** |
| `value_text` | The original cell text when it wasn't a clean number (e.g. "N/A") |
| `remarks` | The row's Remarks cell |
| `source_file`, `source_sheet`, `source_cell` | Exactly where the number came from, e.g. `F8` |

**Check against QF consolidated (registered students):** exact match for 34 of 40 university-years. QF's number for each of the other 6 is reproduced exactly (5) or within 13 (1) by applying QF's blanking rule (P-15).

## 7. Known problems

| ID | Problem | Evidence | Status |
|---|---|---|---|
| **P-01** | **No CMU-Q data for 2021–22.** The file in the `AY21-22` folder is a quality-checked revision of **2020–21**. | Its file name says AY2020-2021, it uses the v2020 template, and its Student Data sheet differs from the 2020–21 file in only 22 cells. QF consolidated also excludes CMU-Q 2021–22. | Accepted: a real gap |
| **P-02** | **CMU-Q 2020–21: Computer Science and Computational Biology are swapped.** In the original file the *registered and graduated* numbers are swapped (Comp. Bio 88 registered, CS 5; the year before was 6 and 85). The revision swapped the *program names on the whole row*, which fixes registered/graduated but swaps *applied/admitted/enrolled* (CS 25 applicants, Comp. Bio 418). The revision also changes graduated counts for four programs. QF consolidated uses the original, wrong registered numbers. | Cell-level comparison of the two CMU-Q files | Decided: D-008 (combine both files) |
| **P-03** | **GU-Q 2022–23 has two files** (`.completed`, `.submitted`). | Every data sheet is identical. `.completed` wrongly says "CMU-Q" in one cell, which `.submitted` fixes. | Decided: D-009 (use `.submitted`) |
| **P-04** | **VCU-Q 2021–22 uses a different form** (v2021-alt): long tables with Fall 2021 and Spring 2022 snapshots, and no Pipeline, Graduation Rate or Outcomes. | Sheet list; QF Issues log | Handle in Phase 2 (separate reader) |
| **P-05** | **VCU-Q registered data missing:** blank in 2022–23; in 2023–24, counts below 10 were blanked by VCU-Q as personally identifiable. | QF Issues log | Accepted: keep blank, never zero |
| **P-06** | **HBKU is different:** reports by **college** (CSE, CIS, CHSS…) not as one university, offers mostly graduate programs, and has files only for 2022–23 and 2023–24. | Entity names inside the files | Decided: D-010 (include, with undergraduate/graduate filter) |
| **P-07** | **"Graduated" doesn't mean the same year everywhere.** The form collects graduates in the Spring round, but Fall-round files report the previous year's graduates (CMU-Q 2023–24: "Graduating Class May 2023"), while others report the current year (VCU-Q 2023–24: "as of September 2024"). CMU-Q 2024–25 reports both May 2024 and May 2025. Several files show 0 graduates because they weren't collected yet (NU-Q 2022–23: "can be confirmed end of August 2023"). | Period labels, remarks, and Outcomes sheets of the following year | Decided: D-011 (date by evidence) |
| **P-08** | **Graduation-rate classes repeat across years** (e.g. WCM-Q's 2016–17 entering class appears in three files) and class labels are inconsistent (e.g. HEC-Q "AY2022/2024"). | Cohort values per file | Decided: D-012 (latest report wins) |
| **P-09** | **Outcomes can repeat across years:** CMU-Q 2024–25 contains both Class of 2023 and Class of 2024. | Period labels | Decided: D-013 (earliest real report wins) |
| **P-10** | **Breakdowns change over time** (no gender for applications before v2021; resident/international only from v2022). | Template comparison | Accepted: trends use the common level (§4) |
| **P-11** | **University names spelled differently** (TAMUQ, WCMC-Q, VCU_Q, HEC-Doha, …). | File names and entity cells | Solved: `universities.csv` |
| **P-12** | **Header wording varies within a template.** | Header comparison across 45 files | Phase 2 reads headers by meaning |
| **P-13** | **Blank is not zero.** Empty program rows contain formula zeros, and footers can show zeros over withheld data. | v2019/v2020 placeholder rows; QF Issues log | Phase 3 check |
| **P-14** | **Helper sheets repeat the data** (`0A. Student Data`, `Student Data Summary`, `ConsolidationControl`). | Sheet contents | Ignore them |
| **P-15** | **QF's consolidated file undercounts** when any demographic part is blank: it blanks the whole Non-Qatari group. NU-Q 2023–24: 260 instead of 474. | QF's numbers reproduced exactly with that rule for 5 of 6 cases | Decided: D-014 (keep every part) |
| **P-16** | **Unnamed subtotal rows among programs.** HEC-Q 2022–23 row 12 adds two cohorts (87) with no program name. | QF Issues log; cell formulas | Solved: `row_type = unnamed_row`, never summed |
| **P-17** | **One line for the whole university.** GU-Q 2023–24 reports no program split. | Its remark: students apply as one major | Solved: `row_type = all_programs` |
| **P-18** | **Degree and program columns swapped:** TAMU-Q 2023–24 puts program names under Degree and "Undergraduate/Graduate" under Program. | QF Issues log | Phase 2: program mapping table |
| **P-19** | **Non-degree rows:** HBKU lists Non-Degree / Conditional Admit rows (24 students in 2022–23). The form says to include degree-seeking students only. | QF Issues log | Phase 2: program mapping table marks them |
