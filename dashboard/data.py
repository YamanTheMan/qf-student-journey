"""Phase 5: what the dashboard reads from data/processed/metrics.csv, and the one sum it does itself.

Every number is computed and tested by the pipeline (pipeline/metrics.py). The dashboard only picks the rows
a chart needs. The exception is the 'same universities every year' view (D-036): it adds up per-university
values the dashboard shows anyway, so it can never reveal a hidden small number.
"""
import pandas as pd

from pipeline.inventory import REFERENCE_DIR, ROOT

METRICS = ROOT / "data" / "processed" / "metrics.csv"
NUMBERS = ["value", "numerator", "denominator", "coverage", "years_after_graduation"]
ALL = "All"
EDUCATION_CITY = "Education City"
USE_ORDER = ["leave_out", "show_marked", "show_with_note", "show", "not_applicable"]  # worst first, as in the pipeline

# The 'Students' filter: one group at a time, because the files never cross nationality with gender
GROUPS = {"All students": (ALL, ALL), "Qatari": ("Qatari", ALL), "Non-Qatari": ("Non-Qatari", ALL),
          "Female": (ALL, "Female"), "Male": (ALL, "Male")}
LEVELS = {"All levels": ALL, "Undergraduate": "undergraduate", "Graduate": "graduate", "Foundation": "foundation"}
QUALITY = {"not_reported": "not reported", "not_comparable": "not comparable with other years",
           "partial": "partial data", "differs": "differs from another source",
           "breakdown_partial": "split known for too few students"}


def load_metrics(path=METRICS):
    return pd.read_csv(path, keep_default_na=False, na_values={c: [""] for c in NUMBERS})


def universities(path=REFERENCE_DIR / "universities.csv"):
    """{code: full name}, in the reference table's order (also the order of the small charts)."""
    table = pd.read_csv(path)
    return dict(zip(table["code"], table["name"]))


def year_label(year):
    """'2011-2012' -> '2011–12'."""
    return f"{year[:4]}–{year[-2:]}" if isinstance(year, str) and len(year) == 9 else year


def year_span(years):
    """['2019-2020', '2020-2021', '2021-2022', '2024-2025'] -> '2019–20 to 2021–22, 2024–25'."""
    years = sorted(years)
    runs, start = [], None
    for i, y in enumerate(years):
        start = start or y
        nxt = years[i + 1] if i + 1 < len(years) else None
        if nxt is None or int(nxt[:4]) != int(y[:4]) + 1:
            runs.append(year_label(start) if start == y else f"{year_label(start)} to {year_label(y)}")
            start = None
    return ", ".join(runs)


def and_list(items):
    """['GU-Q', 'HBKU', 'NU-Q'] -> 'GU-Q, HBKU and NU-Q'."""
    items = list(items)
    return ", ".join(items[:-1]) + " and " + items[-1] if len(items) > 1 else "".join(items)


def count_text(n):
    return f"{n:,.0f}"


def share_text(x):
    return f"{x:.0%}"


def pick(m, metric, level=ALL, group="All students", name=None, program=ALL, category=""):
    """One slice of a metric, for every university and Education City ('All'), sorted by year."""
    nationality, gender = GROUPS[group]
    rows = m[(m["metric"] == metric) & (m["level"] == level) & (m["program_group"] == program)
             & (m["nationality"] == nationality) & (m["gender"] == gender) & (m["category"] == category)]
    if name is not None:
        rows = rows[rows["name"] == name]
    return rows.sort_values(["year", "university"]).reset_index(drop=True)


def worst_use(uses):
    uses = [u for u in uses if u in USE_ORDER]
    return min(uses, key=USE_ORDER.index) if uses else "show"


def usable(rows):
    """Rows the dashboard can show: not left out (D-025) and not hidden as a small number (D-026)."""
    return rows[(rows["use"] != "leave_out") & rows["value"].notna()]


def headline(m, metric, name=None, category=""):
    """A metric's totals for each university: no level, group or program split. A metric given for one
    level only (M10: undergraduate+foundation) uses that level; a metric split into categories (M09's stages,
    M10's school types) is judged per category."""
    rows = pick(m, metric, name=name, category=category)
    if rows.empty:
        levels = m.loc[m["metric"] == metric, "level"].unique()
        if len(levels) == 1:
            rows = pick(m, metric, levels[0], name=name, category=category)
    return rows


def years_of(m, metric, name=None, category=""):
    """Every year in which Education City has a value for this metric."""
    h = headline(m, metric, name, category)
    return sorted(h.loc[h["university"] == ALL, "year"].unique())


def present(m, metric, name=None, category=""):
    """{year: universities with usable data that year}, judged on the metric's totals."""
    h = usable(headline(m, metric, name, category))
    h = h[h["university"] != ALL]
    return h.groupby("year")["university"].agg(set).to_dict()


def every_year(m, metric, years, name=None, category=""):
    """The universities with usable data in every one of `years` in which the metric exists at all
    (gender starts in 2014-15: the years before don't narrow the set), in reference order."""
    seen = present(m, metric, name, category)
    exists = set(years_of(m, metric, name, category))
    years = [y for y in years if y in exists]
    keep = set.intersection(*[seen.get(y, set()) for y in years]) if years else set()
    return [u for u in universities() if u in keep]


def every_year_of_all(m, measures, years):
    """The universities with data in every year for each of several measures, so that charts shown side by side
    (applicants, admitted, new students) compare the same universities. measures: [(metric, name, category)]."""
    keep = set.intersection(*[set(every_year(m, metric, years, name, category))
                              for metric, name, category in measures])
    return [u for u in universities() if u in keep]


def every_year_in(m, metric, years, family, name=None):
    """every_year for a mix: a university counts in a year if it has usable data for any category of `family`
    ('region: '). A university with no students from one region simply has no row for it, so a single category
    can't be the test."""
    rows = m[(m["metric"] == metric) & m["category"].str.startswith(family) & (m["program_group"] == ALL)
             & (m["nationality"] == ALL) & (m["gender"] == ALL)]
    if name is not None:
        rows = rows[rows["name"] == name]
    levels = set(rows["level"])
    rows = rows[rows["level"] == (ALL if ALL in levels or not levels else next(iter(levels)))]
    exists = set(rows.loc[rows["university"] == ALL, "year"])
    seen = usable(rows[rows["university"] != ALL]).groupby("year")["university"].agg(set)
    years = [y for y in years if y in exists]
    keep = set.intersection(*[seen.get(y, set()) for y in years]) if years else set()
    return [u for u in universities() if u in keep]


def categories(m, metric, family, name=None):
    """The categories of a mix without their family prefix: 'region: Qatar' -> 'Qatar'."""
    rows = m[(m["metric"] == metric) & m["category"].str.startswith(family)]
    if name is not None:
        rows = rows[rows["name"] == name]
    return sorted(c[len(family):] for c in rows["category"].unique())


def no_split(m, metric, year, level, group, name=None, category=""):
    """Universities with a total that year but no row for this nationality or gender group: they gave no split
    (the graduating classes filled from the Outcomes sheet have no gender, D-028). Unlike a level a university
    simply doesn't teach, a missing group isn't zero students. Empty for 'All students'."""
    if group == "All students":
        return set()
    h = headline(m, metric, name, category)
    h = h[(h["university"] != ALL) & (h["year"] == year) & (h["use"] != "leave_out") & h["value"].notna()]
    if level != ALL:  # judged on the same level's total
        h = pick(m, metric, level, name=name, category=category)
        h = h[(h["university"] != ALL) & (h["year"] == year) & h["value"].notna()]
    split = pick(m, metric, level, group, name, category=category)
    return set(h["university"]) - set(split.loc[split["year"] == year, "university"])


def absent(m, metric, years, level=ALL, group="All students", name=None, category=""):
    """{year: [(university, why)]}: universities that have this slice in some year but no usable data in this
    one. Judged on the metric's totals, so a university that simply has no students at a level isn't absent;
    one that has a total but no split for the chosen group is (no_split)."""
    h = headline(m, metric, name, category)
    h = h[h["university"] != ALL]
    in_slice = set(pick(m, metric, level, group, name, category=category)["university"])
    order = [u for u in universities() if u in in_slice]
    out = {}
    for year in years:
        rows = h[h["year"] == year].set_index("university")
        unsplit = no_split(m, metric, year, level, group, name, category)
        missing = []
        for u in order:
            if u not in rows.index:
                missing.append((u, "no data"))
            elif rows.loc[[u], "use"].eq("leave_out").any():
                quality = rows.loc[[u], "quality"].iloc[0]
                missing.append((u, QUALITY.get(quality, quality.replace("_", " "))))
            elif rows.loc[[u], "value"].isna().all() and not rows.loc[[u], "display"].any():
                missing.append((u, "no data"))  # a row without numbers (VCU-Q 2023-24 gave no nationality split)
            elif u in unsplit:
                missing.append((u, f"no {'gender' if group in ('Female', 'Male') else 'nationality'} split"))
        out[year] = missing
    return out


SOURCES = {"qf_consolidated": "QF's consolidated file", "student_data": "the universities' Student Data sheets"}


def points(m, metric, years, university=EDUCATION_CITY, same=False, level=ALL, group="All students", name=None,
           category="", among=None):
    """What one chart series draws: per year a value and a state (D-035).

    state: 'complete'; 'incomplete' (drawn lighter: a university is missing that year, or the data is partial);
    'missing' (a gap, with the reason on hover). `why` holds that reason, `notes` anything else to say.
    among: for the 'same universities' view, a set shared with other charts (every_year_of_all).
    """
    if university == EDUCATION_CITY and same:
        _, rows = same_universities(m, metric, years, level, group, name, category, among)
        rows = rows.assign(source="", note="")
        gone = {y: [] for y in years}
    else:
        who = ALL if university == EDUCATION_CITY else university
        rows = pick(m, metric, level, group, name, category=category)
        rows = rows[rows["university"] == who]
        everyone = absent(m, metric, years, level, group, name, category)
        gone = everyone if who == ALL else {y: [g for g in everyone[y] if g[0] == who] for y in years}
    out = []
    for year in years:
        r = rows[rows["year"] == year]
        row = dict(year=year, value=float("nan"), unit=None, numerator=float("nan"), denominator=float("nan"),
                   state="missing", why="", notes="")
        if r.empty or r["value"].isna().all() or r["use"].eq("leave_out").all():
            reasons = [why for _, why in gone.get(year, [])] if university != EDUCATION_CITY else []
            own = ""  # the row's own reason: a hidden small number, or why it's left out
            if len(r):
                first = r.iloc[0]
                own = first["display"] or (first.get("note") or QUALITY.get(first.get("quality"), "")
                                           if first["use"] == "leave_out" else "")
            row["why"] = own or (reasons[0] if reasons else "no data")
            out.append(row)
            continue
        r = r.iloc[0]
        row.update(value=r["value"], unit=r["unit"], numerator=r["numerator"], denominator=r["denominator"])
        partial = r["use"] in ("show_marked", "show_with_note")
        missing_unis = gone.get(year, []) if university == EDUCATION_CITY else []
        row["state"] = "incomplete" if partial or missing_unis else "complete"
        why = []
        if missing_unis:
            why.append("Not included: " + ", ".join(f"{u} ({w})" for u, w in missing_unis))
        if partial:
            reason = QUALITY.get(r.get("quality", ""), "partial data")
            why.append(reason[:1].upper() + reason[1:])
        row["why"] = " · ".join(why)
        report = r.get("report_year", "")
        notes = [f"Source: {SOURCES[r['source']]}" if r.get("source") in SOURCES else "",
                 f"From the {year_label(report)} report" if isinstance(report, str) and report and
                 r.get("year_kind") == "entering_class" else "",
                 *str(r.get("note", "")).split(" · ")]
        row["notes"] = " · ".join(n for n in notes if n and not n.startswith("From QF"))
        out.append(row)
    return pd.DataFrame(out)


def _family_denominators(m, metric, level, group, name, category, keep):
    """For a share of one category in a mix ('region: Qatar'), each university's whole: the denominator its other
    rows of the same family ('region: ...') carry. A university with no students in a category has no row for it,
    but its students still count in the whole. None for metrics whose rows each carry their own denominator."""
    if ": " not in category:
        return None
    family = category.split(": ")[0] + ": "
    nationality, gender = GROUPS[group]
    rows = m[(m["metric"] == metric) & (m["level"] == level) & (m["program_group"] == ALL)
             & (m["nationality"] == nationality) & (m["gender"] == gender) & m["category"].str.startswith(family)
             & m["university"].isin(keep)]
    if name is not None:
        rows = rows[rows["name"] == name]
    return rows.groupby(["university", "year"])["denominator"].max().to_dict()


def same_universities(m, metric, years, level=ALL, group="All students", name=None, category="", among=None):
    """Education City recomputed from only the universities with usable data in every one of `years` (D-036).

    Counts are added; shares and rates add their numerators and denominators. A university without a row in
    this slice adds nothing (it has no students at that level). If any part is hidden as a small number or
    left out, that year's sum isn't shown either, so the sum never reveals what D-026 hides.
    Years in which Education City has no value for this metric at all (e.g. gender before 2014-15) don't
    narrow the set; they stay gaps. `among` gives the set instead (shared by charts shown together).
    Returns (universities, rows with year, value, numerator, denominator, unit, use, display, coverage).
    """
    keep = list(among) if among is not None else every_year(m, metric, years, name, category)
    rows = pick(m, metric, level, group, name, category=category)
    rows = rows[rows["university"].isin(keep)]
    whole = _family_denominators(m, metric, level, group, name, category, keep)
    out = []
    for year in years:
        r = rows[rows["year"] == year]
        unit = r["unit"].iloc[0] if len(r) else None
        hidden = r["value"].isna() | (r["use"] == "leave_out")
        row = dict(year=year, unit=unit, use=worst_use(r["use"]), coverage=len(keep), display="",
                   value=float("nan"), numerator=float("nan"), denominator=float("nan"))
        if not keep or r.empty:
            row["display"] = "no data"
        elif hidden.any() or no_split(m, metric, year, level, group, name, category) & set(keep):
            row["display"] = "not shown: includes a small or missing number"
        elif unit == "count":
            row["value"] = r["value"].sum()
        else:
            row["numerator"] = r["numerator"].sum()
            if whole is None:
                row["denominator"] = r["denominator"].sum()
            else:  # every university's whole, including those with no row in this category
                parts = [whole.get((u, year)) for u in keep]
                row["denominator"] = sum(parts) if all(pd.notna(p) for p in parts) else float("nan")
            row["value"] = row["numerator"] / row["denominator"] if row["denominator"] else float("nan")
            if pd.isna(row["value"]):
                row["display"] = "not shown: includes a small or missing number"
        out.append(row)
    return keep, pd.DataFrame(out, columns=["year", "value", "numerator", "denominator", "unit", "use", "display",
                                            "coverage"])


def mix_year(m, metric, family, year, university=EDUCATION_CITY, same=False, level=ALL, name=None, among=()):
    """One year of a mix (every category of `family`, e.g. all countries) in one pass:
    {category: row with value, unit, state, why, notes}, the same fields points() gives a chart.

    For the 'same universities' view (D-036) each category adds the universities' numerators over the sum of
    their wholes; a hidden part hides that category's sum, as in same_universities."""
    rows = m[(m["metric"] == metric) & (m["year"] == year) & (m["level"] == level) & (m["program_group"] == ALL)
             & (m["nationality"] == ALL) & (m["gender"] == ALL) & m["category"].str.startswith(family)]
    if name is not None:
        rows = rows[rows["name"] == name]
    out = {}
    if university == EDUCATION_CITY and same:
        rows = rows[rows["university"].isin(among)]
        whole = rows.groupby("university")["denominator"].max()
        total = whole.sum() if len(whole) == len(among) and len(among) else float("nan")
        for category, r in rows.groupby("category"):
            hidden = r["value"].isna().any() or r["use"].eq("leave_out").any()
            counts = r["unit"].eq("count").all()
            value = float("nan") if hidden or not (total or counts) else \
                (r["value"].sum() if counts else r["numerator"].sum() / total)
            use = worst_use(r["use"])
            out[category[len(family):]] = dict(
                value=value, unit="count" if counts else "share", state="missing" if pd.isna(value) else
                ("incomplete" if use in ("show_marked", "show_with_note") else "complete"),
                why="not shown: includes a small or missing number" if pd.isna(value) else "", notes="")
        return out
    who = ALL if university == EDUCATION_CITY else university
    for _, r in rows[rows["university"] == who].iterrows():
        left_out = r["use"] == "leave_out"
        missing = left_out or pd.isna(r["value"])
        partial = r["use"] in ("show_marked", "show_with_note")
        why = (r["display"] or (r["note"] or QUALITY.get(r["quality"], "")) if missing
               else (QUALITY.get(r["quality"], "partial data") if partial else ""))
        out[r["category"][len(family):]] = dict(
            value=float("nan") if left_out else r["value"], unit=r["unit"],
            state="missing" if missing else ("incomplete" if partial else "complete"),
            why=why[:1].upper() + why[1:] if why and why not in ("<5", "fewer than 10 students") else why,
            notes="" if missing else r["note"])
    return out
