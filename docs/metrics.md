# Metric catalogue

Every number the dashboard shows, defined once: what it measures, how it's computed, where it comes from and how its quality is judged. Computed by `pipeline/metrics.py` into `data/processed/metrics.csv`.

## Rules that apply to every metric

| Rule | |
|---|---|
| **Who counts** | Degree-seeking students only. `non_degree` rows are left out (D-016). Only `program` and `all_programs` rows are used; subtotals, footers and sponsor rows never are. |
| **Year** | The submission's academic year, except **graduates and outcomes** (by graduating class, D-011, D-013) and **graduation rates** (by entering class, D-012). |
| **Levels** | Every metric is given for all levels together and for `undergraduate`, `graduate` and `foundation` separately (D-010). |
| **Headcounts** | Always from Student Data. The other sheets give **shares** only (D-020, D-022). |
| **Quality** | Each value carries the quality flag of the data it's built from (the worst flag of its numerator and denominator), and that flag's `use`: show, show with a note, show marked "partial", or leave out (D-025). |
| **Education City totals** | "All universities" adds up only university-years that aren't left out, and records how many universities it covers (`coverage`). A year missing a university is marked. |
| **Small numbers** | In any breakdown, counts of 1–4 show as "<5"; shares and rates on fewer than 10 students aren't shown. Totals always show (D-026). |

## The metrics

`count` = number of students; `share` = part ÷ whole of the same group; `rate` = how many of a group reached a stage.

### 1. Growth: how Education City grew

| ID | Metric | Formula | Unit | Source |
|---|---|---|---|---|
| M01 | Registered students | registered | count | QF consolidated before 2019–20, Student Data after (D-029) |
| M02 | Qatari share of students | Qatari registered ÷ registered | share | same |
| M03 | Female share of students | female registered ÷ registered (where gender is reported) | share | same |

### 2. Getting in

| ID | Metric | Formula | Unit | Source |
|---|---|---|---|---|
| M04 | Applicants | applied | count | Student Data |
| M05 | Admitted | admitted | count | Student Data |
| M06 | New students | newly enrolled | count | Student Data |
| M07 | Acceptance rate | admitted ÷ applied | rate | Student Data |
| M08 | Yield | newly enrolled ÷ admitted | rate | Student Data |
| M09 | Qatari share of applicants / admitted / new students | Qatari ÷ all, per stage | share | Student Data |
| M10 | School-type mix | a school type's applicants (admitted, enrolled) ÷ the Pipeline's own total for that stage | share | Student Pipeline (D-020) |

### 3. Studying

| ID | Metric | Formula | Unit | Source |
|---|---|---|---|---|
| M11 | Nationality mix | students of a country (or region) ÷ students in the sheet | share | Nationalities (D-022) |
| M12 | Age mix | students of an age band ÷ students in the sheet | share | Ages (D-022) |
| M13 | Full-time share, scholarship share, class-year mix | group ÷ students in the sheet | share | Registered Students Detailed (D-022) |
| M14 | Funding by type | students with a funding type ÷ registered students. Types overlap, so they're **never stacked** (P-35). | share | Funding + Student Data |
| M15 | Internships by employer type | internships of a type ÷ all internships | share and count | Internships |

### 4. Graduating

| ID | Metric | Formula | Unit | Source |
|---|---|---|---|---|
| M16 | Graduates | graduates of a graduating class | count | Student Data (dated, D-011); gaps filled per D-028 |
| M17 | Qatari share of graduates | Qatari graduates ÷ graduates | share | Student Data |
| M18 | On-time graduation rate | graduated within 100% of normal time ÷ entered | rate | Graduation Rate (by entering class) |
| M19 | Graduation rate within 150% | graduated within 150% ÷ entered, made comparable per D-027 | rate | Graduation Rate |
| M20 | Drop-out rate | drop-outs ÷ entered | rate | Graduation Rate |
| M21 | Graduate nationality mix | graduates of a country ÷ graduates in the sheet | share | Graduate Nationalities (D-022, D-024) |

Entering classes with graduates but no entrants (P-25) give counts but no rates.

### 5. After graduation

| ID | Metric | Formula | Unit | Source |
|---|---|---|---|---|
| M22 | Employment rate | (employed + self-employed) ÷ class size | rate | Outcomes; class size per D-021 |
| M23 | Further study rate | in graduate school ÷ class size | rate | Outcomes |
| M24 | Still searching | still searching ÷ class size | rate | Outcomes |
| M25 | Working in Qatar | employed in Qatar ÷ employed (incl. self-employed) | share | Outcomes |

Each is also given for Qatari and Non-Qatari graduates separately. `years_after_graduation` is kept with each value.
