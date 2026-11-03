# Data quality report

Written by `.venv/bin/python -m pipeline.build` from the processed tables; don't edit by hand. Every finding, with its exact source cell, is in `data/processed/quality_findings.csv`.

- **error**: impossible data; the build stops until it's fixed
- **warning**: numbers disagree; needs a look, and is shown on the dashboard
- **info**: worth knowing, nothing wrong

## Summary

| Check | Errors | Warnings | Info |
|---|--:|--:|--:|
| C02 text in a count cell | 0 | 0 | 13 |
| C03 breakdown adds up | 0 | 4 | 1957 |
| C04 funnel narrows | 0 | 4 | 0 |
| C05 graduation within class | 0 | 102 | 12 |
| C06 outcomes within class | 0 | 3 | 0 |

## Warnings

### C03 breakdown adds up: mismatch (4)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| VCU-Q | 2023-2024 | student_data | Nationality x gender parts add up to 0, but the reported total is 98 | VCU_Q Fall Student Data Collection AY202 AB13 |
| VCU-Q | 2023-2024 | student_data | Nationality x gender parts add up to 0, but the reported total is 311 | VCU_Q Fall Student Data Collection AY202 AJ13 |
| HEC-Q | 2022-2023 | funding | Nationality parts add up to 43, but the reported total is 52 | AY22-23 HEC-Q Student Data Collection.xl H11 |
| HEC-Q | 2022-2023 | funding | Nationality parts add up to 130, but the reported total is 139 | AY22-23 HEC-Q Student Data Collection.xl H50 |

### C04 funnel narrows: newly enrolled above admitted (4)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| TAMU-Q | 2021-2022 | student_pipeline | 122 newly enrolled but only 56 admitted from Independent/public schools | TAMU-Q Fall Student Data Collection AY20 |
| TAMU-Q | 2021-2022 | student_pipeline | 40 newly enrolled but only 21 admitted from International schools | TAMU-Q Fall Student Data Collection AY20 |
| TAMU-Q | 2021-2022 | student_pipeline | 317 newly enrolled but only 183 admitted from Private schools | TAMU-Q Fall Student Data Collection AY20 |
| TAMU-Q | 2021-2022 | student_pipeline | 16 newly enrolled but only 13 admitted from QF schools | TAMU-Q Fall Student Data Collection AY20 |

### C05 graduation within class: no entrants (102)

| University | Year | Findings |
|---|---|--:|
| GU-Q | 2023-2024 | 16 |
| HBKU | 2022-2023 | 23 |
| HBKU | 2023-2024 | 56 |
| NU-Q | 2024-2025 | 7 |

Example: Class 2017-2018: 1 graduates but no entrants reported, so no rate can be computed (P-25)

### C06 outcomes within class: class size missing (2)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| CMU-Q | 2023-2024 | outcomes | Class 2022-2023: 103 outcomes reported but the class size is 0 or blank (P-27) | AY23-24 Fall Student Data Collection Fin H8 |
| VCU-Q | 2023-2024 | outcomes | Class 2022-2023: 48 outcomes reported but the class size is 0 or blank (P-27) | VCU_Q Fall Student Data Collection AY202 H8 |

### C06 outcomes within class: more outcomes than graduates (1)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| TAMU-Q | 2024-2025 | outcomes | Class 2023-2024: 157 outcomes for 156 graduates (P-27) | AY24-25 TAMU-Q Student Data Template - S H8 |

## Information

| Check | Status | Meaning | Findings | Universities |
|---|---|---|--:|---|
| C02 text in a count cell | text | a count cell holds text ('N/A', 'less than 5', '#REF!'); kept as text, never a number | 13 | GU-Q, VCU-Q |
| C03 breakdown adds up | blanks_are_zero | some parts blank, but the rest add up to the total, so the blanks are zeros | 484 | CMU-Q, GU-Q, HBKU, NU-Q, TAMU-Q, VCU-Q |
| C03 breakdown adds up | formula_zero | a total of 0 over blank parts: the section wasn't filled in, so unknown rather than zero | 1433 | CMU-Q, GU-Q, HBKU, HEC-Q, NU-Q, TAMU-Q, VCU-Q, WCM-Q |
| C03 breakdown adds up | partly_withheld | some parts blank and the filled ones add up to less than the total | 6 | VCU-Q |
| C03 breakdown adds up | withheld | a total is given but its breakdown is blank (often small numbers withheld for privacy) | 34 | VCU-Q |
| C05 graduation within class | 150_includes_100 | 'graduated within 150%' includes the within-100% graduates at this university (P-24) | 12 | TAMU-Q |
