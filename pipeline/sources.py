"""Which raw files the pipeline reads, for which academic year, and with which exceptions.

Combines the automatic inventory (data/reference/file_inventory.csv, from pipeline.inventory)
with the hand-made decisions (data/reference/file_decisions.csv, see docs/DECISIONS.md).
"""
from dataclasses import dataclass

import pandas as pd

from pipeline.inventory import REFERENCE_DIR


@dataclass(frozen=True)
class SourceFile:
    path: str              # relative to data/raw
    university: str
    academic_year: str     # after any override in file_decisions.csv
    template: str
    use: str = "yes"       # yes / only / except
    programs: frozenset = frozenset()
    stages: frozenset = frozenset()
    skip_sheets: frozenset = frozenset()  # from sheet_exclusions.csv

    def keeps(self, program, stage):
        """Apply this file's decision to one number."""
        listed = program in self.programs and stage in self.stages
        if self.use == "only":
            return listed
        if self.use == "except":
            return not listed
        return True


def _split(value):
    return frozenset(value.split("|")) if isinstance(value, str) else frozenset()


def submissions(templates=None):
    """University submission files to extract, skipping those marked 'no'."""
    inventory = pd.read_csv(REFERENCE_DIR / "file_inventory.csv")
    decisions = pd.read_csv(REFERENCE_DIR / "file_decisions.csv").set_index("path")
    exclusions = pd.read_csv(REFERENCE_DIR / "sheet_exclusions.csv").groupby("path")["sheet"].agg(frozenset)
    files = []
    for row in inventory[inventory["file_kind"] == "submission"].itertuples():
        if templates and row.template not in templates:
            continue
        decision = decisions.loc[row.path] if row.path in decisions.index else None
        use = decision["use"] if decision is not None else "yes"
        if use == "no":
            continue
        year = row.academic_year
        if decision is not None and isinstance(decision["academic_year"], str):
            year = decision["academic_year"]
        files.append(SourceFile(
            path=row.path,
            university=row.university,
            academic_year=year,
            template=row.template,
            use=use,
            programs=_split(decision["programs"]) if decision is not None else frozenset(),
            stages=_split(decision["stages"]) if decision is not None else frozenset(),
            skip_sheets=exclusions.get(row.path, frozenset()),
        ))
    return files
