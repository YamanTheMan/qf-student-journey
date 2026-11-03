"""Phase 1: build the file inventory.

Scans data/raw/ and writes data/reference/file_inventory.csv with one row per Excel file:
which university and year it belongs to, which template version it uses, and any problems
that can be detected automatically.

Run from the project folder:
    .venv/bin/python -m pipeline.inventory
"""
import hashlib
import re
import warnings
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
REFERENCE_DIR = ROOT / "data" / "reference"
OUTPUT = REFERENCE_DIR / "file_inventory.csv"

# A template version is recognised by the sheets only it has. Checked newest first.
TEMPLATE_SIGNATURES = [
    ("v2022", {"student funding", "student pipeline"}),
    ("v2021", {"student pipeline", "graduation rate"}),
    ("v2021-alt", {"admission", "alumni"}),
    ("v2020", {"control sheet", "student data"}),
    ("v2019", {"dd lists", "student data"}),
]


def normalise_sheet_name(name):
    """'A. Student Data' / '0b. ConsolidationControl' -> 'student data' / 'consolidationcontrol'."""
    name = re.sub(r"^\s*[A-Z0-9]{1,2}[a-z]?\.\s*", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()


def detect_template(sheet_names):
    sheets = {normalise_sheet_name(s) for s in sheet_names}
    for version, required in TEMPLATE_SIGNATURES:
        if required <= sheets:
            return version
    return "unknown"


def load_university_aliases(path=REFERENCE_DIR / "universities.csv"):
    """Map every known spelling (upper case) to its official code, longest spelling first."""
    table = pd.read_csv(path)
    aliases = {}
    for code, alias_list in zip(table["code"], table["aliases"]):
        for alias in alias_list.split("|"):
            aliases[alias.upper()] = code
    return dict(sorted(aliases.items(), key=lambda kv: -len(kv[0])))


def detect_university(filename, aliases):
    """Find a university spelling in the file name, as a whole word (so 'VCU' doesn't match 'VCUarts')."""
    upper = filename.upper()
    for alias, code in aliases.items():
        if re.search(rf"(?<![A-Z]){re.escape(alias)}(?![A-Z])", upper):
            return code
    return None


def folder_year(folder_name):
    """'AY19-20' -> '2019-2020'."""
    m = re.fullmatch(r"AY(\d{2})-(\d{2})", folder_name)
    return f"20{m.group(1)}-20{m.group(2)}" if m else None


def filename_year(filename):
    """Academic year written in the file name, e.g. 'AY2020-2021', 'AY22-23', '2023 - 2024'."""
    m = re.search(r"(?:AY\s?)?(20)?(\d{2})\s?[-–]\s?(20)?(\d{2})(?!\d)", filename)
    if not m:
        return None
    start, end = int(m.group(2)), int(m.group(4))
    if end != start + 1 or not (m.group(1) or filename[m.start():m.start() + 2].upper() == "AY"):
        return None
    return f"20{start:02d}-20{end:02d}"


def submission_round(filename):
    """QF collects data twice a year. 'Graduated' is only requested in the Spring round."""
    m = re.search(r"(?<![a-z])(fall|spring)(?![a-z])", filename.lower())
    return m.group(1) if m else None


def file_kind(filename):
    if filename.startswith("QF_Consolidated_All_Years"):
        return "qf_consolidated_all"
    if filename.startswith("QF_Consolidated_AY"):
        return "qf_consolidated_year"
    return "submission"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_sheet_names(path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # openpyxl warns about data validation it can't read
        wb = openpyxl.load_workbook(path, read_only=True)
        names = wb.sheetnames
        wb.close()
    return names


def build_inventory(raw_dir=RAW_DIR):
    aliases = load_university_aliases()
    rows = []
    for path in sorted(raw_dir.rglob("*")):
        if path.suffix.lower() not in (".xlsx", ".xlsm") or path.name.startswith("~$"):
            continue
        kind = file_kind(path.name)
        sheets = read_sheet_names(path)
        rows.append({
            "path": path.relative_to(raw_dir).as_posix(),
            "file_kind": kind,
            "academic_year": folder_year(path.parent.name) or "all",
            "university": detect_university(path.name, aliases) if kind == "submission" else None,
            "template": detect_template(sheets) if kind == "submission" else None,
            "filename_year": filename_year(path.name),
            "submission_round": submission_round(path.name) if kind == "submission" else None,
            "n_sheets": len(sheets),
            "size_kb": round(path.stat().st_size / 1024),
            "sha256": sha256(path),
            "sheets": " | ".join(sheets),
        })
    inventory = pd.DataFrame(rows)
    inventory.insert(len(inventory.columns) - 1, "flags", flag_problems(inventory))
    return inventory


def flag_problems(inv):
    """Problems a machine can spot. Each needs a human decision, recorded in docs/DECISIONS.md."""
    sub = inv["file_kind"] == "submission"
    dup = sub & inv.duplicated(["academic_year", "university"], keep=False) & inv["university"].notna()
    flags = []
    for i, row in inv.iterrows():
        f = []
        if sub[i] and pd.isna(row["university"]):
            f.append("university_not_detected")
        if sub[i] and row["template"] == "unknown":
            f.append("unknown_template")
        if pd.notna(row["filename_year"]) and row["academic_year"] != "all" and row["filename_year"] != row["academic_year"]:
            f.append("filename_year_mismatch")
        if dup[i]:
            f.append("duplicate_university_year")
        flags.append(";".join(f))
    return flags


def main():
    inventory = build_inventory()
    inventory.to_csv(OUTPUT, index=False)
    sub = inventory[inventory["file_kind"] == "submission"]
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(inventory)} files ({len(sub)} university submissions)\n")
    print("Submissions per year and university:")
    print(pd.crosstab(sub["academic_year"], sub["university"]).to_string(), "\n")
    print("Template versions:", sub["template"].value_counts().to_dict(), "\n")
    flagged = inventory[inventory["flags"] != ""]
    print(f"Flagged files: {len(flagged)}")
    for _, row in flagged.iterrows():
        print(f"  {row['flags']:45} {row['path']}")


if __name__ == "__main__":
    main()
