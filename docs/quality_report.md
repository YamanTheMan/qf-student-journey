# Data quality report

Written by `.venv/bin/python -m pipeline.build` from the processed tables; don't edit by hand. Every finding, with its exact source cell, is in `data/processed/quality_findings.csv`.

- **error**: impossible data; the build stops until it's fixed
- **warning**: numbers disagree; needs a look, and is shown on the dashboard
- **info**: worth knowing, nothing wrong

## Summary

| Check | Errors | Warnings | Info |
|---|--:|--:|--:|
| C02 text in a count cell | 0 | 0 | 13 |
| C03 breakdown adds up | 0 | 2 | 1959 |
| C04 funnel narrows | 0 | 4 | 0 |
| C05 graduation within class | 0 | 102 | 12 |
| C06 outcomes within class | 0 | 3 | 0 |
| C07 registered vs QF | 0 | 0 | 6 |
| C08 ages vs Student Data | 0 | 4 | 6 |
| C08 nationalities vs Student Data | 0 | 2 | 4 |
| C08 registered_detailed vs Student Data | 0 | 2 | 3 |
| C09 pipeline vs Student Data | 0 | 8 | 24 |
| C10 graduate_nationalities vs dated graduates | 0 | 5 | 1 |
| C10 outcomes vs dated graduates | 0 | 2 | 2 |
| C12 funding sponsor rows | 0 | 0 | 3 |

## Coverage and quality by measure

✓ complete · ◑ breakdown partial (totals fine, some nationality/gender parts withheld) · ≈ differs (from a reference, plausibly) · ◐ partial (fewer than a reference, or a key part missing) · ≠ not comparable · ✗ not reported (sheet left empty) · – not in that year's form · blank: no file from that university that year

Every flag, with the findings behind it, is in `data/processed/quality_flags.csv`.

**Getting in: applied**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VCU-Q | ✓ | ✓ | ✓ | ✓ | ◑ | ◑ |
| WCM-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Getting in: admitted**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VCU-Q | ✓ | ✓ | ✓ | ✓ | ◑ | ◑ |
| WCM-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Getting in: newly enrolled**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VCU-Q | ✓ | ✓ | ✗ | ✗ | ◑ | ◑ |
| WCM-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Getting in: applicants by school type**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | – | – |  | ✓ | ✓ | ✓ |
| GU-Q | – | – | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | – | – | ✗ | ✗ | ✗ | ✗ |
| NU-Q | – | – | ◐ | ✓ | ◐ | ◐ |
| TAMU-Q | – | – | ≠ | ✓ | ✓ | ✗ |
| VCU-Q | – | – | – | ◐ | ≈ | ✓ |
| WCM-Q | – | – | ✓ | ✓ | ✓ | ✓ |

**Studying: registered students**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VCU-Q | ✓ | ✓ | ✓ | ✗ | ◑ | ◑ |
| WCM-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Studying: nationalities**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✓ | ✓ | ◐ | ✓ |
| VCU-Q | ✓ | ✓ | ✓ | ✓ | ◐ | ✓ |
| WCM-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Studying: registered students in detail**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | – | – |  | ✓ | ✓ | ✓ |
| GU-Q | – | – | ✓ | ✗ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | – | – | ✓ | ✗ | ✓ | ✓ |
| NU-Q | – | – | ✗ | ✓ | ✓ | ✓ |
| TAMU-Q | – | – | ✗ | ✓ | ◐ | ✓ |
| VCU-Q | – | – | ✓ | ✓ | ✓ | ◐ |
| WCM-Q | – | – | ✓ | ✓ | ✓ | ✓ |

**Studying: ages**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ◐ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✓ | ✓ | ◐ | ✓ |
| VCU-Q | ✓ | ✗ | ✓ | ✓ | ✓ | ◐ |
| WCM-Q | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

**Studying: funding**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | – | – |  | ✓ | ✓ | ✓ |
| GU-Q | – | – | – | ✗ | ◐ | ✓ |
| HBKU |  |  |  | ✓ | ✗ |  |
| HEC-Q | – | – | – | ≈ | ✓ | ✓ |
| NU-Q | – | – | – | ✓ | ✓ | ✓ |
| TAMU-Q | – | – | – | ✓ | ✓ | ✓ |
| VCU-Q | – | – | – | ✗ | ◐ | ✓ |
| WCM-Q | – | – | – | ✓ | ✓ | ✓ |

**Studying: internships**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✗ | ✗ |  | ✗ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✗ |  |
| HEC-Q | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| NU-Q | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| TAMU-Q | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ |
| VCU-Q | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| WCM-Q | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Graduating: graduates**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| GU-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| NU-Q | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| TAMU-Q | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| VCU-Q | ✓ | ✗ | ✓ | ✗ | ◑ | ✓ |
| WCM-Q | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

**Graduating: graduation rate by entering class**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | – | – |  | ✓ | ✓ | ✓ |
| GU-Q | – | – | – | ✗ | ◐ | ✗ |
| HBKU |  |  |  | ◐ | ◐ |  |
| HEC-Q | – | – | – | ✓ | ✓ | ✓ |
| NU-Q | – | – | – | ✗ | ✗ | ◐ |
| TAMU-Q | – | – | – | ✓ | ✓ | ✓ |
| VCU-Q | – | – | – | ✗ | ✗ | ✗ |
| WCM-Q | – | – | – | ✓ | ✓ | ✓ |

**Graduating: graduate nationalities**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | – | – |  | ✓ | ✓ | ✓ |
| GU-Q | – | – | ✓ | ✗ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | – | – | ≠ | ✗ | ≈ | ✓ |
| NU-Q | – | – | ✗ | ✗ | ≠ | ✓ |
| TAMU-Q | – | – | ✗ | ✓ | ◐ | ✓ |
| VCU-Q | – | – | – | ✗ | ◐ | ✗ |
| WCM-Q | – | – | ✓ | ✓ | ✓ | ✓ |

**After: outcomes one year on**

| University | 19–20 | 20–21 | 21–22 | 22–23 | 23–24 | 24–25 |
|---|---|---|---|---|---|---|
| CMU-Q | – | – |  | ✓ | ◐ | ✓ |
| GU-Q | – | – | ✓ | ✗ | ✓ | ✓ |
| HBKU |  |  |  | ✓ | ✓ |  |
| HEC-Q | – | – | ✓ | ✗ | ✗ | ✗ |
| NU-Q | – | – | ✗ | ✓ | ✓ | ✓ |
| TAMU-Q | – | – | ✗ | ✓ | ✓ | ≈ |
| VCU-Q | – | – | – | ✓ | ◐ | ◐ |
| WCM-Q | – | – | ✓ | ✓ | ✓ | ✓ |

## Warnings

### C03 breakdown adds up: mismatch (2)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
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

### C08 ages vs Student Data: lower (4)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| CMU-Q | 2024-2025 | ages | 335 vs 454 in Student Data's registered students: only 74% | nan |
| HEC-Q | 2019-2020 | ages | 63 vs 187 in Student Data's registered students: only 34% | nan |
| TAMU-Q | 2023-2024 | ages | 645 vs 672 in Student Data's registered students: only 96% | nan |
| VCU-Q | 2024-2025 | ages | 296 vs 323 in Student Data's registered students: only 92% | nan |

### C08 nationalities vs Student Data: lower (2)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| TAMU-Q | 2023-2024 | nationalities | 609 vs 672 in Student Data's registered students: only 91% | nan |
| VCU-Q | 2023-2024 | nationalities | 197 vs 311 in Student Data's registered students: only 63% | nan |

### C08 registered_detailed vs Student Data: lower (2)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| TAMU-Q | 2023-2024 | registered_detailed | 556 vs 672 in Student Data's registered students: only 83% | nan |
| VCU-Q | 2024-2025 | registered_detailed | 279 vs 323 in Student Data's registered students: only 86% | nan |

### C09 pipeline vs Student Data: higher (4)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| VCU-Q | 2023-2024 | student_pipeline | 175 vs 157 in Student Data (admitted): 1.1x | nan |
| NU-Q | 2024-2025 | student_pipeline | 123 vs 97 in Student Data (newly enrolled): 1.3x | nan |
| TAMU-Q | 2021-2022 | student_pipeline | 495 vs 140 in Student Data (newly enrolled): 3.5x | nan |
| VCU-Q | 2023-2024 | student_pipeline | 120 vs 91 in Student Data (newly enrolled): 1.3x | nan |

### C09 pipeline vs Student Data: lower (4)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| NU-Q | 2023-2024 | student_pipeline | 268 vs 409 in Student Data (admitted): only 66% | nan |
| NU-Q | 2024-2025 | student_pipeline | 307 vs 354 in Student Data (admitted): only 87% | nan |
| VCU-Q | 2022-2023 | student_pipeline | 143 vs 165 in Student Data (admitted): only 87% | nan |
| NU-Q | 2021-2022 | student_pipeline | 110 vs 131 in Student Data (newly enrolled): only 84% | nan |

### C10 graduate_nationalities vs dated graduates: higher (1)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| HEC-Q | 2023-2024 | graduate_nationalities | Class 2023-2024: 96 vs 82 in the graduates dated in Student Data: 1.2x | nan |

### C10 graduate_nationalities vs dated graduates: lower (2)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| TAMU-Q | 2023-2024 | graduate_nationalities | Class 2023-2024: 109 vs 143 in the graduates dated in Student Data: only 76% | nan |
| VCU-Q | 2023-2024 | graduate_nationalities | Class 2023-2024: 46 vs 72 in the graduates dated in Student Data: only 64% | nan |

### C10 graduate_nationalities vs dated graduates: not one class (2)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| HEC-Q | 2021-2022 | graduate_nationalities | Class 2021-2022: 128 vs 53 graduates in the class of 2021-2022: more than double, so this list is not one class (P-36) | nan |
| NU-Q | 2023-2024 | graduate_nationalities | Class 2022-2023: 720 vs 112 graduates in the class of 2022-2023: more than double, so this list is not one class (P-36) | nan |

### C10 outcomes vs dated graduates: higher (1)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| TAMU-Q | 2024-2025 | outcomes | Class 2023-2024: 156 vs 143 in the graduates dated in Student Data: 1.1x | nan |

### C10 outcomes vs dated graduates: lower (1)

| University | Year | Table | Finding | Source |
|---|---|---|---|---|
| VCU-Q | 2024-2025 | outcomes | Class 2023-2024: 65 vs 72 in the graduates dated in Student Data: only 90% | nan |

## Information

| Check | Status | Meaning | Findings | Universities |
|---|---|---|--:|---|
| C02 text in a count cell | text | a count cell holds text ('N/A', 'less than 5', '#REF!'); kept as text, never a number | 13 | GU-Q, VCU-Q |
| C03 breakdown adds up | blanks_are_zero | some parts blank, but the rest add up to the total, so the blanks are zeros | 484 | CMU-Q, GU-Q, HBKU, NU-Q, TAMU-Q, VCU-Q |
| C03 breakdown adds up | formula_zero | a total of 0 over blank parts: the section wasn't filled in, so unknown rather than zero | 1433 | CMU-Q, GU-Q, HBKU, HEC-Q, NU-Q, TAMU-Q, VCU-Q, WCM-Q |
| C03 breakdown adds up | partly_withheld | some parts blank and the filled ones add up to less than the total | 6 | VCU-Q |
| C03 breakdown adds up | withheld | a total is given but its breakdown is blank (often small numbers withheld for privacy) | 36 | VCU-Q |
| C05 graduation within class | 150_includes_100 | 'graduated within 150%' includes the within-100% graduates at this university (P-24) | 12 | TAMU-Q |
| C07 registered vs QF | qf_leaves_out_blank_groups | differs from QF only because QF leaves out groups with a blank part (P-15) | 6 | HBKU, NU-Q, TAMU-Q, VCU-Q |
| C08 ages vs Student Data | close | differs from its reference by less than the tolerance | 5 | GU-Q, NU-Q, TAMU-Q |
| C08 ages vs Student Data | fills_gap | the reference is 0 (a formula over missing data); this sheet supplies the number | 1 | VCU-Q |
| C08 nationalities vs Student Data | close | differs from its reference by less than the tolerance | 4 | GU-Q, NU-Q |
| C08 registered_detailed vs Student Data | close | differs from its reference by less than the tolerance | 2 | GU-Q, TAMU-Q |
| C08 registered_detailed vs Student Data | fills_gap | the reference is 0 (a formula over missing data); this sheet supplies the number | 1 | VCU-Q |
| C09 pipeline vs Student Data | close | differs from its reference by less than the tolerance | 19 | CMU-Q, NU-Q, TAMU-Q, VCU-Q |
| C09 pipeline vs Student Data | fills_gap | the reference is 0 (a formula over missing data); this sheet supplies the number | 1 | VCU-Q |
| C09 pipeline vs Student Data | internal_promotions | WCM-Q counts promoted students as admitted; the Pipeline doesn't | 4 | WCM-Q |
| C10 graduate_nationalities vs dated graduates | close | differs from its reference by less than the tolerance | 1 | HEC-Q |
| C10 outcomes vs dated graduates | close | differs from its reference by less than the tolerance | 2 | GU-Q, VCU-Q |
| C12 funding sponsor rows | sponsor_rows | funding split into sponsor rows kept out of totals (D-023); funding flagged partial | 3 | GU-Q, VCU-Q |
