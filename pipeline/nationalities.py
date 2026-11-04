"""Phase 2: extract the Student Nationalities sheet: students by country of nationality.

Writes data/processed/nationalities.csv with one row per number: country (as written and
standardised), stage, gender, and the exact source cell. 2019-22 files give registered students
only; from 2022-23 the sheet also gives applied, admitted and newly enrolled students.

Country names are standardised with data/reference/countries.csv, which gives every spelling
seen ('Burma', 'Myanmar (Burma)', 'QATAR', a typo like 'Palisrine') one standard country and a
region (D-030). A spelling not in it stops the build. A country listed twice in one file with
identical numbers is used once; with different numbers it stops the build.

Run from the project folder:
    .venv/bin/python -m pipeline.nationalities
"""
import pandas as pd

from pipeline import vcu_2021_22
from pipeline.headers import nationalities_header
from pipeline.inventory import REFERENCE_DIR, ROOT
from pipeline.lists import extract_list_sheet
from pipeline.tables import report_problems

OUTPUT = ROOT / "data" / "processed" / "nationalities.csv"
TEMPLATES = ("v2019", "v2020", "v2021", "v2022")
KEYS = {"country_raw": lambda text: text == "nationality"}


def load_countries(path=REFERENCE_DIR / "countries.csv"):
    return pd.read_csv(path, keep_default_na=False)


def standardise_countries(table, countries=None):
    """Add 'country' and 'region' from countries.csv, matching spellings ignoring capitals and spaces.

    Returns (table, problems): an unknown spelling is a problem for a person.
    """
    countries = load_countries() if countries is None else countries
    key = countries["spelling"].str.strip().str.lower()
    country, region = dict(zip(key, countries["country"])), dict(zip(key, countries["region"]))
    lower = table["country_raw"].str.strip().str.lower()
    out = table.copy()
    at = out.columns.get_loc("country_raw") + 1
    out.insert(at, "country", lower.map(country))
    out.insert(at + 1, "region", lower.map(region))
    unknown = sorted(out.loc[out["country"].isna(), "country_raw"].unique())
    problems = [f"country spelling not in data/reference/countries.csv: '{u}'" for u in unknown]
    return out, problems


def mark_duplicates(table, extra_keys=()):
    """A country listed twice in one file (after standardising its name):
      - at most one row has students: the form lists the country under two names ('Burma' and
        'Myanmar'); both rows are used, which adds nothing but the real number
      - identical non-zero numbers: a repeated summary row (NU-Q 2019-20); one copy is a 'duplicate'
      - different non-zero numbers: a problem for a person (returned as text)
    extra_keys separates lists that legitimately repeat countries, e.g. two graduating classes."""
    out = table.copy()
    key = ["source_file", "country", "stage", *[c for c in ("gender",) if c in out.columns], *extra_keys]
    nonzero = out["count"].fillna(0) > 0
    with_students = nonzero.groupby([out[k] for k in key]).transform("sum")
    distinct = out["count"].groupby([out[k] for k in key]).transform(lambda s: s.nunique(dropna=False))
    repeated_summary = (with_students > 1) & (distinct == 1)
    conflicting = (with_students > 1) & (distinct > 1)
    out["row_status"] = "used"
    out.loc[repeated_summary & out.duplicated(key, keep="first"), "row_status"] = "duplicate"
    problems = [f"{f}: '{c}' is listed twice with different numbers"
                for f, c in out.loc[conflicting, ["source_file", "country"]].drop_duplicates().values]
    return out, problems


def extract_all():
    table, problems = extract_list_sheet("student nationalities", KEYS, nationalities_header, TEMPLATES)
    table = pd.concat([table, pd.DataFrame(vcu_2021_22.nationality_records())], ignore_index=True)
    table["count"] = table["count"].astype("Int64")
    table, country_problems = standardise_countries(table)
    problems += country_problems
    table, duplicate_problems = mark_duplicates(table)
    return table, problems + duplicate_problems


def main():
    table, problems = extract_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(table):,} numbers from {table['source_file'].nunique()} files")
    print("Row status:", table["row_status"].value_counts().to_dict(), "\n")
    reg = table[(table["stage"] == "registered") & (table["breakdown"] == "total") & (table["row_status"] == "used")]
    latest = reg[reg["file_year"] == reg["file_year"].max()]
    print(f"Countries with registered students in {latest['file_year'].iloc[0]}: {(latest.groupby('country')['count'].sum() > 0).sum()}")
    print("Top 10:", latest.groupby("country")["count"].sum().nlargest(10).to_dict())
    report_problems(problems)


if __name__ == "__main__":
    main()
