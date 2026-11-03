"""Phase 3: automatic quality checks on the processed tables.

Each check looks at the tables built by pipeline.build and returns findings: one row per thing
worth knowing, with where it is (table, university, year, program, source cell), how serious it
is, and what was found against what was expected.

  error    impossible data (a negative count): the build stops
  warning  numbers disagree with each other: shown on the dashboard
  info     worth knowing, nothing wrong (a withheld breakdown, text like 'less than 5' in a count cell)

Run on its own (reads data/processed/):
    .venv/bin/python -m pipeline.checks
"""
import pandas as pd

from pipeline.inventory import ROOT

PROCESSED = ROOT / "data" / "processed"
COLUMNS = ["check", "severity", "status", "table", "university", "file_year", "program", "stage",
           "found", "expected", "message", "source_file", "source_cell"]
CHECKS = []


def check(func):
    """Register a check: a function (tables) -> list of finding dicts."""
    CHECKS.append(func)
    return func


def finding(check_id, severity, status, table, row, message, found=None, expected=None, source_cell=None):
    """One finding, located by a representative row of the data it is about."""
    return {
        "check": check_id, "severity": severity, "status": status, "table": table,
        "university": row.get("university"), "file_year": row.get("file_year"),
        "program": row.get("program") if pd.notna(row.get("program", None)) else row.get("program_raw"),
        "stage": row.get("stage"), "found": found, "expected": expected, "message": message,
        "source_file": row.get("source_file"), "source_cell": source_cell or row.get("source_cell"),
    }


def with_row_number(table):
    """Add the Excel row of single-cell numbers ('AB12' -> '12'); computed numbers ('O3+O5') get none."""
    out = table.copy()
    out["excel_row"] = out["source_cell"].str.extract(r"^[A-Z]+(\d+)$")[0]
    return out


# ---------------------------------------------------------------------------------------------
# Every table

COUNT_TABLES = ("student_data", "student_pipeline", "graduation_rate", "outcomes", "nationalities",
                "registered_detailed", "ages", "graduate_nationalities", "internships", "funding")


@check
def negative_counts(tables):
    """C01: a count can never be negative."""
    out = []
    for name in COUNT_TABLES:
        t = tables[name]
        for _, row in t[t["count"].fillna(0) < 0].iterrows():
            out.append(finding("C01 negative count", "error", "negative", name, row,
                               f"Negative count {row['count']}", found=row["count"]))
    return out


@check
def text_in_count_cells(tables):
    """C02: text where a number belongs ('N/A', 'less than 5', '#REF!'), kept as text, never a number."""
    out = []
    for name in COUNT_TABLES:
        t = tables[name]
        if "value_text" not in t.columns:
            continue
        text = t[t["value_text"].notna() & t["count"].isna()]
        if name == "funding":
            text = text[text["measure"] == "students"]
        for (uni, year, value), group in text.groupby(["university", "file_year", "value_text"]):
            row = group.iloc[0]
            out.append(finding("C02 text in a count cell", "info", "text", name, row,
                               f"{len(group)} cell(s) say '{str(value)[:60]}'", found=len(group),
                               source_cell=", ".join(group["source_cell"].head(5))))
    return out


# ---------------------------------------------------------------------------------------------
# Breakdowns add up to their totals

def breakdown_findings(table_name, t, key):
    """Compare each reported total with the sum of its parts, for every breakdown on the same row.

    key: the columns that identify one total and its parts (file, Excel row, stage, ...).
    """
    t = with_row_number(t)
    t = t[t["excel_row"].notna()]
    out = []
    for _, group in t.groupby(key, dropna=False):
        totals = group[group["breakdown"] == "total"]
        if totals.empty or totals["count"].isna().all():
            continue
        total = int(totals["count"].sum())
        row = totals.iloc[0]
        for breakdown, parts in group[group["breakdown"] != "total"].groupby("breakdown"):
            filled, blank = parts["count"].dropna(), parts["count"].isna().sum()
            found = int(filled.sum()) if len(filled) else None
            where = f"{breakdown.replace('_', ' x ')} parts"
            if found is None:
                if total == 0:
                    # The usual sign of a section not filled in: blank parts under a formula total.
                    out.append(finding("C03 breakdown adds up", "info", "formula_zero", table_name, row,
                                       f"Total is 0 but every {where} is blank: a formula over missing data, "
                                       f"so unknown rather than zero students (P-13)", found=None, expected=0))
                else:
                    out.append(finding("C03 breakdown adds up", "info", "withheld", table_name, row,
                                       f"Total {total} given but all {where} are blank (breakdown withheld)",
                                       expected=total))
            elif found == 0 and total > 0:
                # e.g. VCU-Q 2023-24's footer: parts are formulas over cells withheld for privacy
                out.append(finding("C03 breakdown adds up", "info", "withheld", table_name, row,
                                   f"Total {total} but every {where} is 0: formulas over withheld numbers",
                                   found=0, expected=total))
            elif found == total:
                if blank:
                    out.append(finding("C03 breakdown adds up", "info", "blanks_are_zero", table_name, row,
                                       f"{blank} blank {where}; the rest add up to the total {total}, "
                                       f"so the blanks are effectively zero", found=found, expected=total))
            elif blank and found < total:
                out.append(finding("C03 breakdown adds up", "info", "partly_withheld", table_name, row,
                                   f"{blank} blank {where}; the filled ones add up to {found} of {total}",
                                   found=found, expected=total))
            else:
                out.append(finding("C03 breakdown adds up", "warning", "mismatch", table_name, row,
                                   f"{where.capitalize()} add up to {found}, but the reported total is {total}",
                                   found=found, expected=total))
    return out


@check
def breakdowns_add_up(tables):
    """C03: every reported total equals the sum of its nationality / gender / location parts."""
    out = []
    sd = tables["student_data"]
    out += breakdown_findings("student_data", sd, ["source_file", "excel_row", "stage", "period_label", "band_label"])
    out += breakdown_findings("graduation_rate", tables["graduation_rate"], ["source_file", "excel_row", "stage", "cohort"])
    out += breakdown_findings("outcomes", tables["outcomes"], ["source_file", "excel_row", "stage"])
    fu = tables["funding"]
    out += breakdown_findings("funding", fu[fu["measure"] == "students"], ["source_file", "excel_row", "stage"])
    out += breakdown_findings("nationalities", tables["nationalities"], ["source_file", "excel_row", "stage"])
    return out


# ---------------------------------------------------------------------------------------------
# The admissions funnel narrows: applied >= admitted >= enrolled

def funnel_findings(table_name, t, key, steps):
    """Checked per university and year, not per program: NU-Q and GU-Q admit students to the university
    (often as 'Undeclared') and count enrollment by major, so a single program's funnel can widen."""
    out = []
    t = t[t["row_type"].isin(["program", "all_programs"]) & (t["level"] != "non_degree")]
    if "breakdown" in t.columns:
        t = t[t["breakdown"] == "total"]
    wide = t.pivot_table(index=key, columns="stage", values="count", aggfunc="sum")
    first = t.drop_duplicates(key).set_index(key)
    for (earlier, later) in steps:
        if earlier not in wide or later not in wide:
            continue
        bad = wide[(wide[later] > wide[earlier]) & (wide[earlier] > 0)]  # an earlier stage of 0 = not reported
        for idx, values in bad.iterrows():
            row = first.loc[idx].to_dict() | dict(zip(key, idx)) | {"program": None, "source_cell": None, "stage": later}
            where = f" from {row['school_type']}" if "school_type" in row else ""
            out.append(finding("C04 funnel narrows", "warning", f"{later}_above_{earlier}", table_name, row,
                               f"{int(values[later])} {later.replace('_', ' ')} but only {int(values[earlier])} "
                               f"{earlier.replace('_', ' ')}{where}", found=int(values[later]), expected=int(values[earlier])))
    return out


@check
def funnel_narrows(tables):
    """C04: per university and year, no more students admitted than applied, or enrolled than admitted."""
    steps = [("applied", "admitted"), ("admitted", "newly_enrolled")]
    out = funnel_findings("student_data", tables["student_data"], ["university", "file_year"], steps)
    out += funnel_findings("student_pipeline", tables["student_pipeline"], ["university", "file_year", "school_type"],
                           steps + [("applied", "denied"), ("denied", "recommended_abp")])
    return out


# ---------------------------------------------------------------------------------------------
# Graduation and outcomes stay within their class

@check
def graduation_within_class(tables):
    """C05: graduates and leavers of an entering class can't outnumber the class."""
    out = []
    t = with_row_number(tables["graduation_rate"])
    t = t[(t["report_status"] == "used") & (t["breakdown"] == "total")]
    key = ["source_file", "excel_row", "cohort"]
    wide = t.pivot_table(index=key, columns="stage", values="count", aggfunc="sum").fillna(0)
    first = t.drop_duplicates(key).set_index(key)
    for idx, v in wide.iterrows():
        row = first.loc[idx].to_dict() | dict(zip(key, idx))
        graduates = v.get("graduated_100", 0) + v.get("graduated_150", 0)
        entered = v.get("entered", 0)
        if entered == 0 and graduates > 0:
            out.append(finding("C05 graduation within class", "warning", "no_entrants", "graduation_rate", row,
                               f"Class {row['cohort']}: {int(graduates)} graduates but no entrants reported, so no "
                               f"rate can be computed (P-25)", found=int(graduates), expected=0))
        elif graduates > entered and v.get("graduated_150", 0) <= entered and v.get("graduated_150", 0) >= v.get("graduated_100", 0):
            out.append(finding("C05 graduation within class", "info", "150_includes_100", "graduation_rate", row,
                               f"Class {row['cohort']}: within-100% + within-150% exceed the {int(entered)} entrants, "
                               f"so '150%' includes the 100% graduates here (P-24)", found=int(graduates), expected=int(entered)))
        elif graduates > entered:
            out.append(finding("C05 graduation within class", "warning", "more_graduates_than_entrants", "graduation_rate", row,
                               f"Class {row['cohort']}: {int(graduates)} graduates from {int(entered)} entrants",
                               found=int(graduates), expected=int(entered)))
    return out


OUTCOMES = ("employed", "self_employed", "grad_school", "still_searching", "not_seeking")


@check
def outcomes_within_class(tables):
    """C06: outcomes of a graduating class can't outnumber the class."""
    out = []
    t = tables["outcomes"]
    t = t[(t["report_status"] == "used") & (t["breakdown"] == "total") & t["row_type"].isin(["program", "all_programs"])]
    for (uni, year, source), group in t.groupby(["university", "graduating_year", "source_file"]):
        size = group[group["stage"] == "graduates"]["count"].sum()
        outcomes = group[group["stage"].isin(OUTCOMES)]["count"].sum()
        row = group.iloc[0].to_dict()
        if outcomes > 0 and size == 0:
            out.append(finding("C06 outcomes within class", "warning", "class_size_missing", "outcomes", row,
                               f"Class {year}: {int(outcomes)} outcomes reported but the class size is 0 or blank (P-27)",
                               found=int(outcomes), expected=None))
        elif outcomes > size:
            out.append(finding("C06 outcomes within class", "warning", "more_outcomes_than_graduates", "outcomes", row,
                               f"Class {year}: {int(outcomes)} outcomes for {int(size)} graduates (P-27)",
                               found=int(outcomes), expected=int(size)))
    return out


# ---------------------------------------------------------------------------------------------
# Across tables and sources

QF_CONSOLIDATED = ROOT / "data" / "raw" / "QF_Consolidated_All_Years_AY2011-2025.xlsx"
COUNTED_ROWS = ("program", "all_programs")


def student_totals(tables, stage, levels=None):
    """Student Data's reported totals of one stage, per university and year."""
    sd = tables["student_data"]
    t = sd[(sd["stage"] == stage) & (sd["breakdown"] == "total") & sd["row_type"].isin(COUNTED_ROWS)]
    if levels:
        t = t[t["level"].isin(levels)]
    return t.groupby(["university", "file_year"])["count"].sum(min_count=1)


def compare(check_id, table, ours, reference, label, close=0.02, explain=None, stage=None):
    """Findings for every university-year where `ours` differs from `reference`.

    Equal: nothing. Within `close`: info. Otherwise a warning, unless `explain` returns a reason.
    """
    out = []
    both = pd.DataFrame({"ours": ours, "reference": reference}).dropna()
    for (uni, year), v in both.iterrows():
        found, expected = int(v["ours"]), int(v["reference"])
        if found == expected:
            continue
        row = {"university": uni, "file_year": year, "stage": stage}
        gap = abs(found - expected) / expected if expected else float("inf")
        reason = explain(uni, year, found, expected) if explain else None
        if reason:
            status, severity, message = reason
        elif expected == 0:
            status, severity, message = ("fills_gap", "info", f"{found} here, but {label} shows 0 "
                                         f"(a formula over missing data): this sheet fills the gap")
        elif gap <= close:
            status, severity, message = "close", "info", f"{found} vs {expected} in {label} (within {close:.0%})"
        elif found < expected:
            status, severity, message = "lower", "warning", f"{found} vs {expected} in {label}: only {found / expected:.0%}"
        else:
            status, severity, message = "higher", "warning", f"{found} vs {expected} in {label}: {found / expected:.1f}x"
        out.append(finding(check_id, severity, status, table, row, message, found=found, expected=expected))
    return out


def qf_registered():
    qf = pd.read_excel(QF_CONSOLIDATED, sheet_name="Consolidated")
    qf = qf[qf["Year"] >= "2019-2020"]
    return qf.groupby(["University", "Year"])["Registered"].sum(min_count=1).rename_axis(["university", "file_year"])


@check
def registered_vs_qf(tables):
    """C07: registered students equal QF's consolidated file, or the gap is QF's blanking rule (P-15)."""
    sd = tables["student_data"]
    parts = sd[(sd["stage"] == "registered") & (sd["breakdown"] == "nationality_gender") & sd["row_type"].isin(COUNTED_ROWS)]
    # QF's rule: a nationality x gender group counts only if every part of it is filled
    groups = parts.groupby(["university", "file_year", "source_file", "program_raw", "degree_raw", "nationality", "gender"],
                           dropna=False)["count"]
    qf_rule = groups.apply(lambda s: s.sum() if s.notna().all() else None).dropna() \
        .groupby(["university", "file_year"]).sum()
    reference = qf_registered()

    def explain(uni, year, found, expected):
        rebuilt = qf_rule.get((uni, year))
        if rebuilt is not None and abs(rebuilt - expected) <= max(15, 0.02 * expected):
            return ("qf_leaves_out_blank_groups", "info",
                    f"{found} (ours) vs {expected} (QF): QF leaves out any group with a blank part; "
                    f"applying that rule to our numbers gives {int(rebuilt)} (P-15)")
        return None
    return compare("C07 registered vs QF", "student_data", student_totals(tables, "registered"), reference,
                   "QF's consolidated file", close=0, explain=explain, stage="registered")


@check
def secondary_sheets_vs_student_data(tables):
    """C08: sheets that list registered students another way add up to Student Data's registered total."""
    registered = student_totals(tables, "registered")
    nat = tables["nationalities"]
    nat = nat[(nat["stage"] == "registered") & (nat["breakdown"] == "total") & (nat["row_status"] == "used")]
    ages = tables["ages"]
    ages = ages[(ages["stage"] == "registered") & (ages["breakdown"] == "gender")]
    out = []
    for table, t in (("nationalities", nat), ("registered_detailed", tables["registered_detailed"]), ("ages", ages)):
        ours = t.groupby(["university", "file_year"])["count"].sum()
        out += compare(f"C08 {table} vs Student Data", table, ours[ours > 0], registered,
                       "Student Data's registered students", stage="registered")
    return out


@check
def pipeline_vs_student_data(tables):
    """C09: applicants, admitted and enrolled by school type add up to Student Data's (school-leaver entry only)."""
    pl = tables["student_pipeline"]
    entry = ["undergraduate", "foundation"]
    pl = pl[pl["row_type"].isin(COUNTED_ROWS) & pl["level"].isin(entry)]
    out = []
    for stage in ("applied", "admitted", "newly_enrolled"):
        ours = pl[pl["stage"] == stage].groupby(["university", "file_year"])["count"].sum(min_count=1)

        def explain(uni, year, found, expected, stage=stage):
            if uni == "WCM-Q" and stage == "admitted":
                return ("internal_promotions", "info", f"{found} vs {expected}: WCM-Q's Student Data counts students "
                        "promoted from Foundation and pre-medical years as admitted")
            return None
        out += compare("C09 pipeline vs Student Data", "student_pipeline", ours[ours > 0],
                       student_totals(tables, stage, entry), f"Student Data ({stage.replace('_', ' ')})",
                       close=0.10, explain=explain, stage=stage)
    return out


def dated_graduates(tables):
    sd = tables["student_data"]
    g = sd[(sd["stage"] == "graduated") & (sd["graduates_status"] == "used") & (sd["breakdown"] == "total")
           & sd["row_type"].isin(COUNTED_ROWS)]
    return g.groupby(["university", "graduating_year"])["count"].sum(min_count=1)


@check
def classes_vs_dated_graduates(tables):
    """C10: a graduating class's size in Outcomes and Graduate Nationalities equals the graduates dated in Student Data."""
    graduates = dated_graduates(tables)
    oc = tables["outcomes"]
    oc = oc[(oc["report_status"] == "used") & (oc["stage"] == "graduates") & (oc["breakdown"] == "total")
            & oc["row_type"].isin(COUNTED_ROWS)]
    gn = tables["graduate_nationalities"]
    gn = gn[gn["row_status"] == "used"]
    out = []
    for table, t in (("outcomes", oc), ("graduate_nationalities", gn)):
        sizes = t.groupby(["university", "graduating_year"])["count"].sum()
        sizes = sizes[sizes > 0]
        file_year = t.groupby(["university", "graduating_year"])["file_year"].max()

        def explain(uni, year, found, expected, table=table):
            if found > 2 * expected:
                return ("not_one_class", "warning", f"{found} vs {expected} graduates in the class of {year}: "
                        f"more than double, so this list is not one class (P-36)")
            return None
        for f in compare(f"C10 {table} vs dated graduates", table, sizes, graduates,
                         "the graduates dated in Student Data", close=0.05, explain=explain, stage="graduated"):
            f["message"] = f"Class {f['file_year']}: " + f["message"]
            f["file_year"] = file_year.get((f["university"], f["file_year"]))  # report the submission year
            out.append(f)
    return out


@check
def class_size_vs_newly_enrolled(tables):
    """C11: an entering class (first-time students) can't be larger than that year's newly enrolled students."""
    gr = tables["graduation_rate"]
    gr = gr[(gr["report_status"] == "used") & (gr["stage"] == "entered") & (gr["breakdown"] == "total")]
    sizes = gr.groupby(["university", "cohort"])["count"].sum().rename_axis(["university", "file_year"])
    sizes = sizes[sizes > 0]
    newly = student_totals(tables, "newly_enrolled")
    both = pd.DataFrame({"class": sizes, "newly": newly}).dropna()
    return [finding("C11 class size vs newly enrolled", "warning", "class_larger", "graduation_rate",
                    {"university": u, "file_year": y, "stage": "entered"},
                    f"Entering class {y}: {int(v['class'])} first-time students but only {int(v['newly'])} newly enrolled",
                    found=int(v["class"]), expected=int(v["newly"]))
            for (u, y), v in both[both["class"] > both["newly"]].iterrows()]


@check
def funding_sponsor_rows(tables):
    """C12: funding split into sponsor rows that are never added to totals (D-023), so that
    university-year's funding is partial."""
    fu = tables["funding"]
    sponsors = fu[(fu["row_type"] == "sponsor_detail") & (fu["measure"] == "students")]
    detail_cols = [c for c in fu.columns if c.endswith("_details")]
    out = []
    for (uni, year), group in sponsors.groupby(["university", "file_year"]):
        names = pd.unique(group[detail_cols].stack().dropna())
        rows = group["source_cell"].str.extract(r"(\d+)$")[0].nunique()
        out.append(finding("C12 funding sponsor rows", "info", "sponsor_rows", "funding", group.iloc[0].to_dict(),
                           f"{rows} sponsor row(s) kept out of funding totals (D-023), e.g. "
                           + "; ".join(str(n)[:40] for n in names[:3]), found=int(group["count"].sum())))
    return out


# ---------------------------------------------------------------------------------------------

def run_checks(tables):
    findings = [f for check_func in CHECKS for f in check_func(tables)]
    return pd.DataFrame(findings, columns=COLUMNS)


STATUS_MEANING = {
    "formula_zero": "a total of 0 over blank parts: the section wasn't filled in, so unknown rather than zero",
    "blanks_are_zero": "some parts blank, but the rest add up to the total, so the blanks are zeros",
    "withheld": "a total is given but its breakdown is blank (often small numbers withheld for privacy)",
    "partly_withheld": "some parts blank and the filled ones add up to less than the total",
    "text": "a count cell holds text ('N/A', 'less than 5', '#REF!'); kept as text, never a number",
    "150_includes_100": "'graduated within 150%' includes the within-100% graduates at this university (P-24)",
    "close": "differs from its reference by less than the tolerance",
    "fills_gap": "the reference is 0 (a formula over missing data); this sheet supplies the number",
    "qf_leaves_out_blank_groups": "differs from QF only because QF leaves out groups with a blank part (P-15)",
    "internal_promotions": "WCM-Q counts promoted students as admitted; the Pipeline doesn't",
    "sponsor_rows": "funding split into sponsor rows kept out of totals (D-023); funding flagged partial",
}


MEASURE_NAMES = {  # story order
    "applied": "Getting in: applied", "admitted": "Getting in: admitted", "newly_enrolled": "Getting in: newly enrolled",
    "student_pipeline": "Getting in: applicants by school type", "registered": "Studying: registered students",
    "nationalities": "Studying: nationalities", "registered_detailed": "Studying: registered students in detail",
    "ages": "Studying: ages", "funding": "Studying: funding", "internships": "Studying: internships",
    "graduated": "Graduating: graduates", "graduation_rate": "Graduating: graduation rate by entering class",
    "graduate_nationalities": "Graduating: graduate nationalities", "outcomes": "After: outcomes one year on",
}
LEGEND = ("✓ complete · ◑ breakdown partial (totals fine, some nationality/gender parts withheld) · "
          "≈ differs (from a reference, plausibly) · ◐ partial (fewer than a reference, or a key part missing) · "
          "≠ not comparable · ✗ not reported (sheet left empty) · – not in that year's form · "
          "blank: no file from that university that year")


def coverage_section(flags):
    from pipeline.flags import matrix
    lines = ["## Coverage and quality by measure", "", LEGEND, "",
             "Every flag, with the findings behind it, is in `data/processed/quality_flags.csv`.", ""]
    years = sorted(flags["file_year"].unique())
    universities = sorted(flags["university"].unique())
    for measure, name in MEASURE_NAMES.items():
        grid = matrix(flags, measure).reindex(index=universities, columns=years).astype(object).fillna("")
        lines += [f"**{name}**", "", "| University | " + " | ".join(y[2:4] + "–" + y[7:] for y in years) + " |",
                  "|---|" + "---|" * len(years),
                  *[f"| {u} | " + " | ".join(grid.loc[u]) + " |" for u in universities], ""]
    return lines


def report(findings, flags=None):
    """The readable quality report (markdown), regenerated by every build."""
    counts = findings.groupby(["check", "severity"]).size().unstack(fill_value=0)
    for severity in ("error", "warning", "info"):
        if severity not in counts:
            counts[severity] = 0
    lines = [
        "# Data quality report",
        "",
        "Written by `.venv/bin/python -m pipeline.build` from the processed tables; don't edit by hand. "
        "Every finding, with its exact source cell, is in `data/processed/quality_findings.csv`.",
        "",
        "- **error**: impossible data; the build stops until it's fixed",
        "- **warning**: numbers disagree; needs a look, and is shown on the dashboard",
        "- **info**: worth knowing, nothing wrong",
        "",
        "## Summary",
        "",
        "| Check | Errors | Warnings | Info |",
        "|---|--:|--:|--:|",
        *[f"| {c} | {r['error']} | {r['warning']} | {r['info']} |" for c, r in counts.iterrows()],
        "",
        *(coverage_section(flags) if flags is not None else []),
        "## Warnings",
        "",
    ]
    warnings_ = findings[findings["severity"].isin(["error", "warning"])]
    for (check_name, status), group in warnings_.groupby(["check", "status"]):
        lines += [f"### {check_name}: {status.replace('_', ' ')} ({len(group)})", ""]
        if len(group) > 12:
            by = group.groupby(["university", "file_year"]).size()
            lines += ["| University | Year | Findings |", "|---|---|--:|",
                      *[f"| {u} | {y} | {n} |" for (u, y), n in by.items()], ""]
            lines += [f"Example: {group.iloc[0]['message']}", ""]
        else:
            lines += ["| University | Year | Table | Finding | Source |", "|---|---|---|---|---|"]
            for _, f in group.iterrows():
                cell_ref = f["source_cell"] if pd.notna(f["source_cell"]) else ""
                source = f"{str(f['source_file']).split('/')[-1][:40]} {cell_ref}".strip()
                lines.append(f"| {f['university']} | {f['file_year']} | {f['table']} | {f['message']} | {source} |")
            lines.append("")
    lines += ["## Information", "",
              "| Check | Status | Meaning | Findings | Universities |", "|---|---|---|--:|---|"]
    info = findings[findings["severity"] == "info"]
    for (check_name, status), group in info.groupby(["check", "status"]):
        unis = ", ".join(sorted(group["university"].dropna().unique()))
        lines.append(f"| {check_name} | {status} | {STATUS_MEANING.get(status, '')} | {len(group)} | {unis} |")
    return "\n".join(lines) + "\n"


def load_tables():
    read = dict(keep_default_na=False, na_values={c: [""] for c in ("count", "level", "program", "amount_qar",
                                                                   "graduating_year", "cohort", "value_text",
                                                                   "period_label", "band_label")},
                dtype={"degree_raw": str, "program_raw": str, "age": str, "remarks": str})
    return {name: pd.read_csv(PROCESSED / f"{name}.csv", **read) for name in COUNT_TABLES}


REPORT = ROOT / "docs" / "quality_report.md"
FINDINGS = PROCESSED / "quality_findings.csv"
FLAGS = PROCESSED / "quality_flags.csv"


def write_outputs(tables, findings):
    """Findings, flags and the readable report, written together by every build."""
    from pipeline.flags import quality_flags
    flags = quality_flags(tables, findings)
    findings.to_csv(FINDINGS, index=False)
    flags.to_csv(FLAGS, index=False)
    REPORT.write_text(report(findings, flags))
    return flags


def main():
    tables = load_tables()
    findings = run_checks(tables)
    write_outputs(tables, findings)
    print(findings.groupby(["check", "severity", "status"]).size().to_string())
    print(f"\nWrote {FINDINGS.relative_to(ROOT)}, {FLAGS.relative_to(ROOT)} and {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
