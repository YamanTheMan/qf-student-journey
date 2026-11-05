# Data dictionary

What is in `data/raw/`, what each number means, and what's wrong with it. This is the reference for building the pipeline (Phase 2) and its checks (Phase 3).

- **File-by-file list:** [`data/reference/file_inventory.csv`](../data/reference/file_inventory.csv), regenerated with `.venv/bin/python -m pipeline.inventory`.
- **University names:** [`data/reference/universities.csv`](../data/reference/universities.csv) maps every spelling found in the files to one code.
- **Which files to use:** [`data/reference/file_decisions.csv`](../data/reference/file_decisions.csv) lists the exceptions. Every other file is used as-is. `use` is one of: `no` (skip the file), `only` (use only the listed `programs` × `stages`), `except` (use everything but the listed `programs` × `stages`), or `yes`. `academic_year` overrides the year implied by the folder.
- **Program names:** [`data/reference/programs.csv`](../data/reference/programs.csv) has one row per program spelling found in the files (145 so far), giving its standard name, stable group, level, qualification and field (D-015). A new spelling in a future upload stops the build until a row is added.
- **Sheets to skip:** [`data/reference/sheet_exclusions.csv`](../data/reference/sheet_exclusions.csv) lists single sheets that aren't read, each with its decision (D-018).
- **Country names:** [`data/reference/countries.csv`](../data/reference/countries.csv) gives every country spelling seen in the files (252 so far, including typos like "Palisrine") one standard country (209) and one of 12 regions (D-030). A new spelling stops the build until a row is added.
- **Internship employers:** [`data/reference/employers.csv`](../data/reference/employers.csv) gives each employer that the 2019–21 forms name (180 spellings) a standard name and one of the form's five types: QF, Public, Private, Abroad, Other (D-034). `basis` says whether the type is clear from the `name`, `known`, or a `guess`, with the reason in `note`. A new name stops the build until a row is added.
- **When graduates graduated:** [`data/reference/graduate_timing.csv`](../data/reference/graduate_timing.csv) lists, per university and file, which class its graduates belong to when a remark or the Outcomes sheet shows it, each with its evidence (D-011). Files without an entry use labels in the sheet, or else the form's definition.

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

Generated by the pipeline; never edit them by hand. **Rebuild them all with one command:** `.venv/bin/python -m pipeline.build`. It refreshes the inventory, builds every table, stops without writing anything if a problem needs a person, and runs the tests.

VCU-Q 2021–22 used a different form (template `v2021-alt`). Its rows are added to Student Data, Registered Students Detailed, Nationalities and Ages by `pipeline/vcu_2021_22.py` (D-019). Its program totals are computed from their parts: `remarks` says so, and `source_cell` lists every cell added (e.g. `O3+O5+O9`).

> **Reading these files:** read text columns exactly as written, for example `pd.read_csv(path, keep_default_na=False)` plus explicit missing values for number columns. Otherwise pandas silently turns text like "N/A" (a real degree value in some files) into "missing".

### `student_data.csv`: one row per number in every Student Data sheet

Built by `.venv/bin/python -m pipeline.student_data` from the 43 files using templates v2019–v2022.

| Column | Meaning |
|---|---|
| `file_year` | Academic year the file belongs to, after any override in `file_decisions.csv` |
| `university` | Standard code from `universities.csv` |
| `row_type` | `program` (one program) · `all_programs` (the university reported one combined line) · `unnamed_row` (row without a program name among named programs, usually a subtotal: **never add it**) · `sheet_total` (the footer totals under the table) |
| `entity_reported`, `degree_raw`, `program_raw` | Exactly as written in the file |
| `program`, `program_group` | Standard program name, and a group name that stays the same across all years (from `programs.csv`). Use `program_group` for trends. |
| `level` | `foundation` · `undergraduate` · `graduate` · `non_degree` (leave `non_degree` out of totals, D-016) |
| `qualification`, `field` | Standard qualification (Bachelor's, Master's, Doctorate, MD, JD, …) and one of 13 broad fields (Engineering, Art & Design, …) |
| `stage` | `applied` · `admitted` · `newly_enrolled` · `registered` · `graduated` |
| `nationality` / `residency` / `gender` | `Qatari`, `Non-Qatari` / `Resident`, `International` / `Male`, `Female`; `All` when not split |
| `breakdown` | Which split the number belongs to: `total`, `nationality`, `gender`, `nationality_gender`. **Only add numbers that share the same breakdown.** |
| `period_label`, `band_label` | Period written in the header (e.g. "May 2025") or above the column block (e.g. "As of Fall 2024") |
| `count` | The number, or blank. **Blank is never zero.** |
| `value_text` | The original cell text when it wasn't a clean number (e.g. "N/A") |
| `remarks` | The row's Remarks cell |
| `source_file`, `source_sheet`, `source_cell` | Exactly where the number came from, e.g. `F8` |
| `graduating_year` | *Graduated rows only.* The class these graduates belong to (D-011) |
| `timing_evidence` | *Graduated rows only.* How the class was dated: `label` (a date in or above the header), `remark` or `outcomes` (an entry in `graduate_timing.csv`), or `form_default` (the file's own year, as the form defines it) |
| `timing_note` | *Graduated rows only.* The label text or the evidence sentence |
| `graduates_status` | *Graduated rows only.* `used` · `not_reported` (the file gave no graduates for that class: not collected yet) · `superseded` (a later file reports the same class). **Use only `used` rows.** |

**Graduates check:** each class size agrees with the number of that class's graduates tracked in the following year's Outcomes sheet. CMU-Q: 87 = 87, 103 = 103, 120 = 120. NU-Q: 112 = 112. WCM-Q: 41 = 41, 42 = 42, 50 = 50. GU-Q: 97 vs 96, 120 vs 119.

**Check against QF consolidated (registered students):** exact match for 34 of 40 university-years. QF's number for each of the other 6 is reproduced exactly (5) or within 13 (1) by applying QF's blanking rule (P-15).

### `student_pipeline.csv`: where applicants come from

Built by `.venv/bin/python -m pipeline.student_pipeline` from the 28 files with a Student Pipeline sheet (2021–22 onwards). Same columns as `student_data.csv`, except that `nationality`, `residency`, `gender`, `breakdown` and the graduate timing columns are replaced by:

| Column | Meaning |
|---|---|
| `stage` | `applied` · `admitted` · `newly_enrolled` · `denied` · `recommended_abp` (recommended for the Academic Bridge Program; **already included in `denied`**) |
| `school_type` | `QF schools` · `Independent/public schools` · `Private schools` · `International schools` (outside Qatar) · `Academic Bridge Program` |

**Scope:** students entering from school, so **undergraduate and foundation entry only**. HBKU's pipeline covers only its one undergraduate program, and graduate-only HEC-Q has none.

**Check against Student Data** (undergraduate and foundation programs; WCM-Q admitted excluded because Student Data includes internal promotions, per its remark): exact match in 37 of 65 university-year-stage comparisons, within 5% in 51, within 10% in 56. The 9 larger differences are listed in P-22 for Phase 3.

### `graduation_rate.csv`: each entering class followed to completion

Built by `.venv/bin/python -m pipeline.graduation_rate` from the 2022–23 to 2024–25 files (template v2022). 2021–22 is not read (P-23). Same columns as `student_data.csv`, except that `residency`, `period_label` and the graduate timing columns are replaced by:

| Column | Meaning |
|---|---|
| `cohort_raw` / `cohort` | Entering class as written (`AY2018/2019`, `2005-2006`, `2019-20`, `AY2022/2024`, …) / the academic year it started, e.g. `2018-2019` |
| `normal_years` | Normal time to completion in years, as reported |
| `stage` | `entered` (first-time degree-seeking students in the class) · `non_completers` · `dropouts` · `graduated_100` (within normal time) · `graduated_150` (within 150% of normal time, **see P-24**) |
| `report_status` | `used` · `superseded` (a later file reports the same class, D-012) · `empty` (the class is listed with no numbers). **Use only `used` rows.** |

**Coverage (used reports):** WCM-Q 2016–2021, TAMU-Q 2017–2021, CMU-Q 2018–2020, HEC-Q 2020–2024 and NU-Q 2019–2022 report entering classes with their size, so graduation *rates* can be computed. **GU-Q 2005–2020 (16 classes, university-wide), HBKU 2015–2022 and NU-Q's 2024–25 report give graduates per class but no entrants**, so they show how many graduated, not what share (P-25; corrected in Phase 3). VCU-Q's sheets contain only `#REF!` errors.

**Check against Student Data:** each class is never larger than the newly enrolled students of its starting year. That's expected, since first-time students exclude transfers and foundation students. CMU-Q matches exactly (112 vs 113, 124 vs 124); WCM-Q 0.77–1.00; TAMU-Q 0.74–0.86; HEC-Q 0.31–0.47 (executive cohorts start mid-year).

### `outcomes.csv`: where graduates are a year later

Built by `.venv/bin/python -m pipeline.outcomes` from the 28 files with a Student Outcomes after 1 Yr sheet (2021–22 onwards). Same identity and source columns as `student_data.csv`, plus:

| Column | Meaning |
|---|---|
| `stage` | `graduates` (the class size) · `employed` · `self_employed` · `grad_school` · `still_searching` · `not_seeking` |
| `nationality` / `location` | `Qatari`, `Non-Qatari` / `In Qatar`, `Outside Qatar`; `All` when not split |
| `breakdown` | `total`, `nationality`, `location`, `nationality_location`. Only add numbers that share the same breakdown. |
| `period_label` | The class written inside the header (VCU-Q: "AY 2021-22") |
| `graduating_year`, `class_evidence` | The class these graduates belong to: from the header or a block label like "Class of 2023" (`label`), otherwise the form's definition, the previous academic year (`form_default`) |
| `years_after_graduation` | When the outcomes were measured, e.g. 1 for the class of 2022–23 in the 2023–24 file |
| `report_status` | `used` · `later_report` (the same class at the same university was reported earlier, D-013) · `empty` (no non-zero outcome: not collected yet). **Use only `used` rows.** |

**Checks:** each class is used from exactly one file. Class sizes match our dated graduates (`student_data.csv`) wherever both exist: CMU-Q 87 = 87, 120 = 120; NU-Q 112 = 112; WCM-Q 41 = 41, 42 = 42, 50 = 50. The small gaps are explained (P-27). Outcomes fill the class size for classes Student Data doesn't report (e.g. TAMU-Q 2021–22: 110, NU-Q 2021–22: 108).

### `nationalities.csv`: students by country of nationality

Built by `.venv/bin/python -m pipeline.nationalities` from 42 files (all years from 2019–20). Columns: `country_raw` (as written), `country` (standardised), `stage`, `gender`, `breakdown`, `count`, `row_status`, plus year, university, template and source columns. 2019–22 files give registered students only; from 2022–23 also applied, admitted and newly enrolled.

- **Country names:** `country` and `region` come from `data/reference/countries.csv` (capitals and spaces ignored; "Burma" = "Myanmar", "Palisrine" = "Palestine"). "Non-Qatari" is not a country: it becomes "Non-Qatari (country not given)", region "Not given" (P-30).
- **`row_status`:** `used` or `duplicate` (the same country listed twice in one file with identical numbers, P-31). Different numbers for the same country stop the build.
- **Blank cells are left out:** every country is printed in the template, so a blank says nothing a missing row doesn't.
- **Check:** registered totals equal Student Data in 34 of 41 university-years (38 within 2%), and the "Qatar" row equals Qatari students in 32 of 39. Gaps: P-33.

### `registered_detailed.csv`: registered students in detail

Built by `.venv/bin/python -m pipeline.registered_detailed` from 24 files (2021–22 onwards; two 2021–22 files don't have the sheet, and GU-Q 2022–23 is skipped by D-018). One count per program × `nationality` × `gender` × `attendance` × `scholarship` × `sponsorship` × `language` × `year_class`, plus `attendance_std`, `scholarship_std`, `sponsorship_std` (Full-time / Part-time / Yes / No / Mixed) and the standard program columns.

**Check:** totals equal Student Data's registered students in 19 of 24 university-years (21 within 2%). VCU-Q 2022–23 gives 294 students where Student Data left registered blank (P-05). Gaps: P-33.

### `ages.csv`, `graduate_nationalities.csv`, `internships.csv`, `funding.csv`

Built together by `.venv/bin/python -m pipeline.student_life`. Run `pipeline.student_data` first: graduate nationalities are dated from it.

| Table | Files | Contents | Check |
|---|---|---|---|
| `ages.csv` | 40 (all years) | `age` (as written: `<15`, `17`, `35-39`, `Age unknown`), `stage` = `registered` or `new_entrants` (students entering their *first* university degree), `gender` | Registered students equal Student Data in 29 of 39 university-years (35 within 5%). New entrants are smaller than newly enrolled by definition: no graduate students or transfers. |
| `graduate_nationalities.csv` | 21 (2021–22 on) | `country_raw` / `country` (standardised as in nationalities.csv), `graduating_year` and `timing_evidence`: dated **exactly like the same file's graduate counts** (D-011), or by a graduation date in the row's remarks; `row_status` | Equal to our dated graduates in 14 of 20 classes. Gaps: P-36. "Less than 5" is kept as text, never a number. |
| `internships.csv` | 22 (all years) | `employer_raw`, `employer` (standard name, older files only), `employer_type` (`QF`, `Public`, `Private`, `Abroad`, `Other`: the form's own type from 2021–22, and from `data/reference/employers.csv` for the employers older files name, D-034), `count` | No independent source |
| `funding.csv` | 23 (2022–23 on) | `stage` = funding type (`self_funded`, `qf_scholarship`, `university_scholarship`, `financial_aid`, `government_sponsored`, `company_sponsored`, `multiple_sources`), `measure` = `students` (in `count`) or `average_amount_qar` (in `amount_qar`), `nationality`, the three sponsor-detail text columns, standard program columns | Funding types overlap (P-35): never add them up. `row_type = sponsor_detail` rows (P-34) are never added to totals. |

### `quality_findings.csv` and `docs/quality_report.md`: automatic quality checks

Written by every build (`pipeline/checks.py`). Each finding has `check`, `severity` (`error` stops the build, `warning` needs a look and will be shown on the dashboard, `info` is worth knowing), `status`, the table, university, year, program and stage it's about, `found` vs `expected`, a plain-language `message`, and the exact `source_file` and `source_cell`. [`docs/quality_report.md`](quality_report.md) is the readable summary.

| Check | What it tests |
|---|---|
| C01 negative count | No count is below zero (error) |
| C02 text in a count cell | 'N/A', 'less than 5', '#REF!' are kept as text (info) |
| C03 breakdown adds up | Every reported total equals its nationality / gender / location parts. A total of 0 over blank parts is a formula over missing data, so **unknown, not zero** (P-13). |
| C04 funnel narrows | Per university and year (not per program: some universities admit to "Undeclared"): admitted ≤ applied, newly enrolled ≤ admitted, also per school type |
| C05 graduation within class | Graduates ≤ entrants, for the totals and for the Qatari / Non-Qatari parts (a part that fails flags its split ◑, P-38); flags classes with graduates but no entrants (P-25) and the "150% includes 100%" convention (P-24) |
| C06 outcomes within class | Outcomes ≤ class size; flags outcomes with a class size of 0 (P-27) |
| C07 registered vs QF | Registered students equal QF's consolidated file; a gap that QF's blanking rule reproduces is info (P-15) |
| C08 … vs Student Data | Nationalities, Registered Students Detailed and Ages add up to Student Data's registered students (P-33) |
| C09 pipeline vs Student Data | Applied / admitted / enrolled by school type, at undergraduate + foundation entry, within 10% (P-22); WCM-Q's internal promotions are info |
| C10 … vs dated graduates | A class's size in Outcomes and Graduate Nationalities equals its dated graduates (for a Graduate Nationalities list, the Outcomes class size where Student Data has none, D-028); more than double means "not one class" (P-36) |
| C11 class size vs newly enrolled | An entering class is never larger than that year's newly enrolled |
| C12 funding sponsor rows | Funding split into sponsor rows that are never added (D-023): that university-year's Funding is ◐ partial |

A reference of 0 (a formula over missing data) gives an info finding "fills_gap": the other sheet supplies the missing number (e.g. VCU-Q 2022–23).

### `quality_flags.csv`: one quality flag per measure × university × year

Written with the findings (`pipeline/flags.py`). A **measure** is one thing the dashboard shows: a Student Data stage (`applied`, `admitted`, `newly_enrolled`, `registered`, `graduated`) or another table. The year is the submission's academic year. Columns: `measure`, `university`, `file_year`, `status`, `symbol`, `use` (what the dashboard does with it, D-025: `show`, `show_with_note`, `show_marked`, `leave_out`, `not_applicable`), `notes` (the findings behind the flag).

| Status | Symbol | Meaning |
|---|:-:|---|
| `complete` | ✓ | numbers present and consistent |
| `breakdown_partial` | ◑ | totals fine, some nationality / gender parts withheld or blank |
| `differs` | ≈ | higher than a reference, or parts that don't add up, but plausibly so |
| `partial` | ◐ | fewer than a reference, or a key part missing (e.g. entrants for a rate) |
| `not_comparable` | ≠ | means something else (a cumulative list, a funnel that widens, 1.5× off) |
| `not_reported` | ✗ | the form had the sheet, but no numbers (or only formula zeros) |
| `not_in_form` | – | that year's form didn't have the sheet |

The report shows each measure as a university × year grid of these symbols.

### `metrics.csv`: the story numbers

Written by every build (`pipeline/metrics.py`); every metric is defined in [docs/metrics.md](metrics.md). One row per value: `metric` (M01…), `name`, `chapter`, `university` (`All` = Education City), `year`, `year_kind`, `level`, `program_group`, `nationality`, `gender`, `category` (e.g. a school type), `value`, `display` ("<5" or "fewer than 10 students" when hidden, D-026), `numerator`, `denominator`, `unit` (count / share / rate), `source`, `quality` and `use` (D-025), `coverage` (universities included in an Education City value), `report_year` (the report a by-class value came from), `years_after_graduation` (outcomes), `note`. `year_kind` is `academic`, `graduating_class` (M16, M17, M21–M25) or `entering_class` (M18–M20).

**Check:** Education City's registered students equal QF's own totals for every year 2011–12 to 2018–19, minus the non-degree students we leave out (D-016). HBKU's 2015–16 "QFIS | All Programs" line has no degree category in QF's file, so it's counted at level `unknown` (in the all-levels total only).

## 7. Known problems

| ID | Problem | Evidence | Status |
|---|---|---|---|
| **P-01** | **No CMU-Q data for 2021–22.** The file in the `AY21-22` folder is a quality-checked revision of **2020–21**. | Its file name says AY2020-2021, it uses the v2020 template, and its Student Data sheet differs from the 2020–21 file in only 22 cells. QF consolidated also excludes CMU-Q 2021–22. | Accepted: a real gap |
| **P-02** | **CMU-Q 2020–21: Computer Science and Computational Biology are swapped.** In the original file the *registered and graduated* numbers are swapped (Comp. Bio 88 registered, CS 5; the year before was 6 and 85). The revision swapped the *program names on the whole row*, which fixes registered/graduated but swaps *applied/admitted/enrolled* (CS 25 applicants, Comp. Bio 418). The revision also changes graduated counts for four programs. QF consolidated uses the original, wrong registered numbers. | Cell-level comparison of the two CMU-Q files | Decided: D-008 (combine both files) |
| **P-03** | **GU-Q 2022–23 has two files** (`.completed`, `.submitted`). | Every data sheet is identical. `.completed` wrongly says "CMU-Q" in one cell, which `.submitted` fixes. | Decided: D-009 (use `.submitted`) |
| **P-04** | **VCU-Q 2021–22 uses a different form** (v2021-alt): long tables with Fall 2021 and Spring 2022 snapshots, and no Pipeline, Graduation Rate or Outcomes. | Sheet list; QF Issues log | Solved: `pipeline/vcu_2021_22.py` feeds the standard tables (D-019); registered matches QF exactly |
| **P-05** | **VCU-Q registered data missing:** blank in 2022–23; in 2023–24, counts below 10 were blanked by VCU-Q as personally identifiable. | QF Issues log | Accepted: keep blank, never zero |
| **P-06** | **HBKU is different:** reports by **college** (CSE, CIS, CHSS…) not as one university, offers mostly graduate programs, and has files only for 2022–23 and 2023–24. | Entity names inside the files | Decided: D-010 (include, with undergraduate/graduate filter) |
| **P-07** | **"Graduated" doesn't mean the same year everywhere.** The form collects graduates in the Spring round, but Fall-round files report the previous year's graduates (CMU-Q 2023–24: "Graduating Class May 2023"), while others report the current year (VCU-Q 2023–24: "as of September 2024"). CMU-Q 2024–25 reports both May 2024 and May 2025. Several files show 0 graduates because they weren't collected yet (NU-Q 2022–23: "can be confirmed end of August 2023"). | Period labels, remarks, and Outcomes sheets of the following year | Solved: D-011, applied in `pipeline/graduates.py`. TAMU-Q 2022–23 (8 graduates, next year's Outcomes tracks 113) is marked not reported. |
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
| **P-18** | **Degree and program columns swapped:** TAMU-Q 2023–24 puts program names under Degree and "Undergraduate/Graduate" under Program. | QF Issues log | Solved: corrected in `programs.csv` (D-015) |
| **P-19** | **Non-degree rows:** HBKU lists Non-Degree / Conditional Admit rows (24 students in 2022–23). The form says to include degree-seeking students only. | QF Issues log | Solved: `level = non_degree`, left out of totals (D-016) |
| **P-20** | **`#REF!` instead of program names.** The Pipeline sheet copies names from the Student Data tab by formula; in GU-Q, HEC-Q, TAMU-Q and VCU-Q files those formulas broke. All such rows are empty. | 96 `#REF!` cells | Solved: Excel errors are never treated as names. A row without a name that holds non-zero numbers stops the build. |
| **P-21** | **VCU-Q 2022–23 Pipeline: degree and program columns don't line up.** | VCU-Q's remark on admission routes; numbers compared with Student Data | Solved: mapped by degree (D-017) |
| **P-22** | **Pipeline and Student Data disagree by more than 10% in 9 cases.** TAMU-Q 2021–22 newly enrolled 495 vs 140; NU-Q admitted 2023–24 268 vs 409 and 2024–25 307 vs 354; NU-Q newly enrolled 2021–22 110 vs 131 and 2024–25 123 vs 97; VCU-Q 2022–23 admitted 143 vs 165 and newly enrolled 73 vs 0 (Student Data's 0 is a formula over missing data); VCU-Q 2023–24 admitted 175 vs 157 and newly enrolled 120 vs 91. | Comparison in §6; quality check C04 confirms TAMU-Q 2021–22's Pipeline "enrolled" exceeds its admitted by school type (317 vs 183, …) | Decided: D-020. Totals from Student Data; Pipeline used for the school-type mix only |
| **P-23** | **2021–22 Graduation Rate is percentages only** ("% Overall Graduation Rate (AY20/21)"), with no class sizes and no clear entering class. | Header survey: 5 files | Not read. Rates come from class counts in the 2022–25 files. |
| **P-24** | **"Graduated within 150%" means different things.** TAMU-Q counts *all* graduates within 150% (including the 100% ones); WCM-Q and HEC-Q count only the *extra* graduates after normal time. | Which way each class adds up to its entrants: TAMU-Q 12 of 12 classes one way, WCM-Q 5 of 5 and HEC-Q 3 of 6 the other | Phase 4: decide how to compute a comparable 150% rate |
| **P-25** | **Graduates reported without entrants:** HBKU (79 class reports), GU-Q's 2005–2020 history (16) and NU-Q 2024–25 (7) give graduates per entering class but 0 or no entrants, so no graduation *rate* can be computed for them. | Quality check C05 | Phase 4: show their graduate counts without a rate |
| **P-26** | **HBKU 2022–23 Graduation Rate swaps the program names of its BS and PhD rows.** | Degree and normal time vs the 2023–24 sheet | Solved: mapped by degree in `programs.csv` |
| **P-27** | **Outcomes and class sizes don't always fit.** CMU-Q 2022–23 and VCU-Q 2022–23 report outcomes with a class size of 0 (left blank or a formula zero); TAMU-Q 2023–24 reports 157 outcomes for 156 graduates. Class size vs dated graduates: TAMU-Q 2023–24 156 vs 143 (the 143 was provisional), VCU-Q 2023–24 65 vs 72, GU-Q 2023–24 119 vs 120. | Outcomes check in §6 | Decided: D-021. Fallback class size for outcome rates |
| **P-28** | **Outcomes not collected for some classes.** GU-Q 2020–21 and 2022–23, HBKU 2022–23 and HEC-Q 2020–21 give a class size but every outcome is 0. | Outcomes sheets | Marked `empty`; the dashboard shows "not reported" |
| **P-29** | **CMU-Q's 2023–24 Outcomes sheet lists its programs without names**, and the 2024–25 sheet repeats the same class with names. | Same five numbers in both sheets | Solved: D-013 compares a whole class at a university, so the class is counted once |
| **P-30** | **"Non-Qatari" used as a country.** NU-Q reports most non-Qatari students as one lump (430–534 a year), so NU-Q has no country detail for them; HBKU, CMU-Q and VCU-Q have small lumps. | Nationalities sheets | Solved: standardised to "Non-Qatari (country not given)" |
| **P-31** | **NU-Q 2019–20 lists Qatar and Non-Qatari twice:** summary rows at the top repeat the alphabetical rows. | Identical numbers (174, 205) | Solved: identical duplicates are used once |
| **P-32** | **GU-Q 2022–23 Registered Students Detailed holds summary tables, not the detailed list.** | GU-Q's remark; columns don't line up with the headers | Solved: sheet skipped (D-018) |
| **P-33** | **Secondary sheets don't always add up to Student Data.** HEC-Q 2022–23 Nationalities is empty (0 vs 238); TAMU-Q 2023–24 Nationalities 609 and Detailed 556 vs 672; VCU-Q 2023–24 Nationalities 197 vs 311 and 2024–25 Detailed 279 vs 323 (small numbers redacted). | Checks in §6 | Decided: D-022. Shown as shares, never headcounts; partial years marked ◐ |
| **P-34** | **Funding broken down by sponsor in unnamed rows.** GU-Q 2023–24 ("GU-Q Grant" 256, "QF Scholarship" 12, company sponsors…) and VCU-Q 2022–24 ("Qatar Airways", "Qatar Armed Forces"…) add rows with the sponsor's name and no program. For GU-Q they appear to extend the main line, for VCU-Q they don't add up to it (11 vs 126). | Funding sheets | Decided: D-023. Never summed; Funding for those years flagged ◐ (check C12) |
| **P-35** | **Funding types overlap.** Adding them up gives more students than are registered (e.g. TAMU-Q 2023–24: 797 vs 672), even though a "multiple funding sources" type exists. | Funding check in §6 | Phase 4: show each funding type separately, never stacked |
| **P-36** | **Some graduate-nationality lists are not one class.** NU-Q 2023–24 has 720 (Qatar 332 + Non-Qatari 388) against 112 graduates, likely cumulative. HEC-Q graduates by cohort, so its lists don't match academic years (2021–22: 128 vs 53). | Check in §6 | Decided: D-024. Left out (flagged ≠ by check C10) |
| **P-37** | **Older internship lists name the employer** (Qatar Museums, QAPCO, Brookings Doha Center, …) instead of its type: 390 internships in 2019–21. | Internship sheets | Decided: D-034. Sorted into the five types by `data/reference/employers.csv` (180 names; each says whether its type is clear from the name, known, or a guess) |
| **P-38** | **Some nationality splits of a graduation-rate class are impossible:** HEC-Q's class of 2021–22 has 32 Non-Qatari graduates from 6 Non-Qatari entrants in one program, its class of 2022–23 62 Qatari graduates from 7; WCM-Q's class of 2018–19 34 Non-Qatari graduates from 33. The totals add up. | Quality check C05 | Decided: D-032. Totals used, split not (flagged ◑) |
| **P-39** | **TAMU-Q reports 0 drop-outs in every class** while counting 11–21 non-completers, who together with its graduates make up the class. The form doesn't define the two terms. | Graduation Rate sheets | Decided: D-032. No drop-out rate from a report without any drop-outs |
| **P-40** | **A blank part of a split makes a share look complete.** VCU-Q 2024–25 gives 270 female students and a blank male count against 323 registered, so its female share came out as 100% (and its Qatari share as 67% of those 270). Education City 2023–24 has the same gap on a larger scale: VCU-Q gave no split at all, so the split covers 3,590 of 3,901 students. Found while checking the Growth chapter. | Metrics M02, M03, M09, M17 | Decided: D-037. A share is marked below 95% coverage and left out below 90%, with its possible range in the note |
