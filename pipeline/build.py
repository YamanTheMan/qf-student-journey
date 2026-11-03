"""Build every processed table with one command.

    .venv/bin/python -m pipeline.build              # build, check, write, then run the tests
    .venv/bin/python -m pipeline.build --no-tests

1. Refresh the file inventory. A new file with a flag that no decision covers (an unknown
   template, a second file for the same university and year, ...) needs a person.
2. Build every table in memory, in order (Graduate Nationalities is dated from Student Data).
3. Run the quality checks (pipeline.checks). An error (impossible data, e.g. a negative count)
   needs a person too.
4. If anything needs a person (an unreadable file, an unknown program spelling, numbers
   without a name, a quality error, ...), print it all and stop WITHOUT writing:
   data/processed/ never holds a half-built mix of old and new tables.
5. Otherwise write every table, the findings, the quality flags and docs/quality_report.md,
   then run the tests.

This is the command GitHub will run on every upload (Phase 6).
"""
import subprocess
import sys

import pandas as pd

from pipeline import (checks, graduation_rate, inventory, nationalities, outcomes, registered_detailed,
                      student_data, student_life, student_pipeline)
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

    findings = None
    if not problems:  # with problems the tables may be incomplete, so checking them would mislead
        print("3. Quality checks")
        findings = checks.run_checks(tables)
        errors = findings[findings["severity"] == "error"]
        problems += [f"{e['check']}: {e['message']} ({e['source_file']} {e['source_cell']})" for _, e in errors.iterrows()]
        print("   " + ", ".join(f"{n} {s}" for s, n in findings["severity"].value_counts().items()))

    if problems:
        print(f"\nStopped: {len(problems)} problem(s) need a person. Nothing was written.")
        for p in problems:
            print("  ", p)
        sys.exit(1)

    print("4. Writing data/processed/ and docs/quality_report.md")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(PROCESSED / f"{name}.csv", index=False)
        print(f"   {name + '.csv':28} {len(table):>7,} numbers from {table['source_file'].nunique():>2} files")
    checks.write_outputs(tables, findings)

    if "--no-tests" not in sys.argv:
        print("5. Tests")
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
