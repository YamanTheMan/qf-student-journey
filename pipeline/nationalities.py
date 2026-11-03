"""Phase 2: extract the Student Nationalities sheet: students by country of nationality.

Writes data/processed/nationalities.csv with one row per number: country (as written and
standardised), stage, gender, and the exact source cell. 2019-22 files give registered students
only; from 2022-23 the sheet also gives applied, admitted and newly enrolled students.

Country names are standardised by ignoring capitals ('QATAR' = 'Qatar') and by the alias table
data/reference/country_aliases.csv ('Viet Nam' -> 'Vietnam'). A country listed twice in one file
with identical numbers is used once; with different numbers it stops the build.

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


def standardise_countries(table, aliases=None):
    """Add 'country': alias table first, otherwise the spelling most often used for that name."""
    if aliases is None:
        aliases = pd.read_csv(REFERENCE_DIR / "country_aliases.csv", keep_default_na=False)
    by_alias = dict(zip(aliases["alias"].str.lower(), aliases["country"]))
    lower = table["country_raw"].str.strip().str.lower()
    usual = table["country_raw"].groupby(lower).agg(lambda s: s.value_counts().index[0])
    out = table.copy()
    out.insert(out.columns.get_loc("country_raw") + 1, "country", lower.map(by_alias).fillna(lower.map(usual)))
    return out


def mark_duplicates(table, extra_keys=()):
    """A country listed twice in one file: identical numbers -> one copy is a 'duplicate';
    different numbers -> a problem for a person (returned as text). extra_keys separates
    lists that legitimately repeat countries, e.g. two graduating classes in one sheet."""
    out = table.copy()
    key = ["source_file", "country", "stage", *[c for c in ("gender",) if c in out.columns], *extra_keys]
    groups = out.groupby(key)["count"]
    conflicting = groups.transform(lambda s: s.nunique(dropna=False) > 1)
    out["row_status"] = "used"
    out.loc[out.duplicated(key, keep="first") & ~conflicting, "row_status"] = "duplicate"
    problems = [f"{f}: '{c}' is listed twice with different numbers"
                for f, c in out.loc[conflicting, ["source_file", "country"]].drop_duplicates().values]
    return out, problems


def extract_all():
    table, problems = extract_list_sheet("student nationalities", KEYS, nationalities_header, TEMPLATES)
    table = pd.concat([table, pd.DataFrame(vcu_2021_22.nationality_records())], ignore_index=True)
    table["count"] = table["count"].astype("Int64")
    table, duplicate_problems = mark_duplicates(standardise_countries(table))
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
