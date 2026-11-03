"""Build every processed table with one command.

    .venv/bin/python -m pipeline.build              # build, check, write, then run the tests
    .venv/bin/python -m pipeline.build --no-tests

1. Refresh the file inventory. A new file with a flag that no decision covers (an unknown
   template, a second file for the same university and year, ...) needs a person.
2. Build every table in memory, in order (Graduate Nationalities is dated from Student Data).
3. If anything needs a person (an unreadable file, an unknown program spelling, numbers
   without a name, ...), print it all and stop WITHOUT writing: data/processed/ never holds
   a half-built mix of old and new tables.
4. Otherwise write every table to data/processed/ and run the tests.

This is the command GitHub will run on every upload (Phase 6).
"""
import subprocess
import sys

import pandas as pd

from pipeline import (graduation_rate, inventory, nationalities, outcomes, registered_detailed, student_data,
                      student_life, student_pipeline)
from pipeline.inventory import REFERENCE_DIR, ROOT

PROCESSED = ROOT / "data" / "processed"


def unresolved_flags(inv):
    """Inventory flags not covered by a decision in file_decisions.csv."""
    decided = set(pd.read_csv(REFERENCE_DIR / "file_decisions.csv")["path"])
    problems = []
    for row in inv[inv["flags"].fillna("") != ""].itertuples():
        for flag in row.flags.split(";"):
            if flag == "duplicate_university_year":
                same = inv[(inv["academic_year"] == row.academic_year) & (inv["university"] == row.university)]
                covered = bool(set(same["path"]) & decided)
            else:
                covered = row.path in decided
            if not covered:
                problems.append(f"{row.path}: inventory flag '{flag}' needs a decision in file_decisions.csv")
    return problems


def build_tables():
    """Every table, built in memory: ({name: table}, problems)."""
    tables, problems = {}, []

    def add(name, result):
        tables[name], table_problems = result
        problems.extend(table_problems)

    add("student_data", student_data.extract_all())
    add("student_pipeline", student_pipeline.extract_all())
    add("graduation_rate", graduation_rate.extract_all())
    add("outcomes", outcomes.extract_all())
    add("nationalities", nationalities.extract_all())
    add("registered_detailed", registered_detailed.extract_all())
    add("ages", student_life.ages())
    add("graduate_nationalities", student_life.graduate_nationalities(tables["student_data"]))
    add("internships", student_life.internships())
    add("funding", student_life.funding())
    return tables, problems


def main():
    print("1. File inventory")
    inv = inventory.build_inventory()
    inv.to_csv(inventory.OUTPUT, index=False)
    print(f"   {len(inv)} files, {(inv['file_kind'] == 'submission').sum()} university submissions")
    problems = unresolved_flags(inv)

    print("2. Building tables")
    tables, table_problems = build_tables()
    problems += table_problems

    if problems:
        print(f"\nStopped: {len(problems)} problem(s) need a person. Nothing was written.")
        for p in problems:
            print("  ", p)
        sys.exit(1)

    print("3. Writing data/processed/")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(PROCESSED / f"{name}.csv", index=False)
        print(f"   {name + '.csv':28} {len(table):>7,} numbers from {table['source_file'].nunique():>2} files")

    if "--no-tests" not in sys.argv:
        print("4. Tests")
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
