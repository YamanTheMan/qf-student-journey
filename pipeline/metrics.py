"""Phase 4: compute the story metrics defined in docs/metrics.md.

Two layers:
  1. bases    plain student counts per stage x university x year x level x program x
              nationality x gender, each with the quality flag of the data it came from
  2. metrics  formulas over bases: a count is a base, a share is part / whole within a base,
              a rate is one base / another

Education City ('All') adds up the bases of the university-years that aren't left out (D-025)
before any share or rate is computed, and records how many universities it covers.
Small numbers are hidden last (D-026).

Writes data/processed/metrics.csv. Run on its own (reads data/processed/):
    .venv/bin/python -m pipeline.metrics
"""
import pandas as pd

from pipeline.inventory import ROOT

PROCESSED = ROOT / "data" / "processed"
QF_CONSOLIDATED = ROOT / "data" / "raw" / "QF_Consolidated_All_Years_AY2011-2025.xlsx"
OUTPUT = PROCESSED / "metrics.csv"
COUNTED_ROWS = ("program", "all_programs")
ALL = "All"
KEYS = ["university", "year", "level", "program_group"]
USE_ORDER = ["leave_out", "show_marked", "show_with_note", "show", "not_applicable"]  # worst first
STATUS_FOR_USE = {"leave_out": "not_comparable", "show_marked": "partial", "show_with_note": "differs", "show": "complete"}
QF_LEVELS = {"Bachelor's": "undergraduate", "Undergraduate": "undergraduate", "Foundation": "foundation",
             "Master's": "graduate", "Doctorate": "graduate", "Diploma": "graduate", "Graduate": "graduate",
             "Professional degree (JD)": "graduate", "Professional degree (MD)": "graduate",
             "Non-degree": "non_degree", "Exchange": "non_degree"}  # D-029
COLUMNS = ["metric", "name", "chapter", "university", "year", "year_kind", "level", "program_group",
           "nationality", "gender", "category", "value", "display", "numerator", "denominator", "unit",
           "source", "quality", "use", "coverage", "report_year", "years_after_graduation", "note"]


# ---------------------------------------------------------------------------------------------
# 1. Bases

def student_rows(tables, stage):
    """Student Data rows of one stage: degree-seeking program rows only (D-016).

    Graduates are dated to their graduating class (D-011), so their `year` is the class and
    `file_year` (kept for the quality flag) the file they came from."""
    sd = tables["student_data"]
    t = sd[(sd["stage"] == stage) & sd["row_type"].isin(COUNTED_ROWS) & sd["level"].notna()
           & (sd["level"] != "non_degree")]
    if stage == "graduated":
        t = t[t["graduates_status"] == "used"]
    t = t.assign(year=t["graduating_year"] if stage == "graduated" else t["file_year"],
                 row_key=t["source_file"] + "|" + t["source_cell"].str.extract(r"(\d+)$")[0]
                 .fillna(t["source_cell"]) + "|" + t["period_label"].fillna("") + "|" + t["band_label"].fillna(""))
    return t


def file_year_of(t, out):
    """The file each (university, year) came from; one file per class (D-011, D-013)."""
    files = t.groupby(["university", "year"])["file_year"].first()
    return [files.get((u, y)) for u, y in zip(out["university"], out["year"])]


def split_parts(t, dim):
    """Counts by nationality (or gender), from the most detailed breakdown each row has.

    A row normally splits nationality x gender. Some rows split one way only (VCU-Q 2023-24's
    applicants: by gender and, separately, by nationality), so a row without nationality x gender
    parts uses its single split instead. Never both, so nothing is counted twice.
    """
    detailed = set(t.loc[t["breakdown"] == "nationality_gender", "row_key"])
    single = "nationality" if dim == "nationality" else "gender"
    parts = pd.concat([t[t["breakdown"] == "nationality_gender"],
                       t[(t["breakdown"] == single) & ~t["row_key"].isin(detailed)]])
    return parts.groupby(KEYS + [dim])["count"].sum(min_count=1).reset_index()


def base_from_student_data(tables, stage):
    """Totals, nationality parts and gender parts of one Student Data stage."""
    t = student_rows(tables, stage)
    totals = t[t["breakdown"] == "total"].groupby(KEYS)["count"].sum(min_count=1).reset_index()
    by_nat = split_parts(t, "nationality")
    by_gender = split_parts(t, "gender")
    out = pd.concat([totals.assign(nationality=ALL, gender=ALL),
                     by_nat.assign(gender=ALL), by_gender.assign(nationality=ALL)], ignore_index=True)
    return out.assign(stage=stage, source="student_data", measure=stage, file_year=file_year_of(t, out))


def base_from_outcomes(tables, have):
    """D-028: a graduating class Student Data lacks takes its class size from the next year's
    Outcomes sheet (total and Qatari / Non-Qatari; no gender)."""
    oc = tables["outcomes"]
    oc = oc[(oc["report_status"] == "used") & (oc["stage"] == "graduates") & oc["row_type"].isin(COUNTED_ROWS)
            & oc["level"].notna() & (oc["level"] != "non_degree")].assign(year=lambda d: d["graduating_year"])
    size = oc[oc["breakdown"] == "total"].groupby(["university", "year"])["count"].sum()
    missing = size[size > 0].index.difference(have)
    oc = oc[oc.set_index(["university", "year"]).index.isin(missing)]
    totals = oc[oc["breakdown"] == "total"].groupby(KEYS)["count"].sum(min_count=1).reset_index()
    by_nat = oc[oc["breakdown"] == "nationality"].groupby(KEYS + ["nationality"])["count"].sum(min_count=1).reset_index()
    out = pd.concat([totals.assign(nationality=ALL, gender=ALL), by_nat.assign(gender=ALL)], ignore_index=True)
    return out.assign(stage="graduated", source="outcomes", measure="outcomes", file_year=file_year_of(oc, out))


def base_from_qf_history():
    """Registered students 2011-12 to 2018-19 from QF's consolidated file (D-029)."""
    qf = pd.read_excel(QF_CONSOLIDATED, sheet_name="Consolidated")
    # No degree category (HBKU 2015-16 'QFIS | All Programs', 237 students): level 'unknown', so they
    # count in the all-levels total but in no level of their own
    qf = qf[qf["Year"] < "2019-2020"].assign(level=lambda d: d["Degree Category"].map(QF_LEVELS).fillna("unknown"))
    qf = qf[qf["level"] != "non_degree"]
    qf = qf.rename(columns={"University": "university", "Year": "year", "Registered": "count",
                            "Nationality": "nationality", "Gender": "gender"}).assign(program_group=ALL)
    totals = qf.groupby(KEYS)["count"].sum(min_count=1).reset_index().assign(nationality=ALL, gender=ALL)
    by_nat = qf.groupby(KEYS + ["nationality"])["count"].sum(min_count=1).reset_index().assign(gender=ALL)
    gendered = qf[qf["gender"].notna()]
    by_gender = gendered.groupby(KEYS + ["gender"])["count"].sum(min_count=1).reset_index().assign(nationality=ALL)
    # gender shares only where QF gives every row a gender for that university-year
    full = qf.groupby(["university", "year"])["gender"].apply(lambda s: s.notna().all())
    by_gender = by_gender[by_gender.set_index(["university", "year"]).index.map(full.get).fillna(False).astype(bool)]
    out = pd.concat([totals, by_nat, by_gender], ignore_index=True)
    return out.assign(stage="registered", source="qf_consolidated", measure=None, file_year=out["year"])


def roll_up(base):
    """Add level = All and program_group = All rows (sums of the detailed ones)."""
    dims = ["stage", "source", "measure", "file_year", "nationality", "gender"]
    detail = base[base["program_group"] != ALL]
    by_level = detail.groupby(["university", "year", "level"] + dims, dropna=False)["count"].sum(min_count=1) \
        .reset_index().assign(program_group=ALL)
    already = base[base["program_group"] == ALL]  # QF history comes at level x All programs
    per_level = pd.concat([by_level, already], ignore_index=True)
    all_levels = per_level.groupby(["university", "year", "program_group"] + dims, dropna=False)["count"] \
        .sum(min_count=1).reset_index().assign(level=ALL)
    return pd.concat([detail, per_level, all_levels], ignore_index=True)


def with_quality(base, flags):
    """Attach each base row's flag (Student Data stages, Outcomes) or 'complete' (QF history)."""
    f = flags.set_index(["measure", "university", "file_year"])[["status", "use"]]
    keys = list(zip(base["measure"], base["university"], base["file_year"]))
    found = f.reindex(pd.MultiIndex.from_tuples(keys)).reset_index(drop=True)
    out = base.reset_index(drop=True).assign(quality=found["status"].fillna("complete"), use=found["use"].fillna("show"))
    return out


def education_city(base):
    """'All' universities: sum of the university-years that aren't left out, with coverage.
    A class can mix sources (graduates from Student Data and, where it lacks one, Outcomes)."""
    kept = base[(base["use"] != "leave_out") & (base["program_group"] == ALL)]
    dims = ["year", "level", "program_group", "stage", "nationality", "gender"]
    agg = kept.groupby(dims, dropna=False).agg(
        count=("count", lambda s: s.sum(min_count=1)),
        coverage=("university", "nunique"),
        use=("use", lambda s: min(s, key=USE_ORDER.index)),
        source=("source", lambda s: "+".join(sorted(set(s)))),
    ).reset_index()
    agg["quality"] = agg["use"].map(STATUS_FOR_USE)
    return agg.assign(university=ALL, measure=None, file_year=None)


def build_bases(tables, flags):
    stages = ["registered", "applied", "admitted", "newly_enrolled", "graduated"]
    sd = pd.concat([base_from_student_data(tables, s) for s in stages], ignore_index=True)
    graduated = sd[sd["stage"] == "graduated"]
    filled = base_from_outcomes(tables, pd.MultiIndex.from_frame(graduated[["university", "year"]].drop_duplicates()))
    history = base_from_qf_history()
    base = with_quality(roll_up(pd.concat([sd, filled, history], ignore_index=True)), flags)
    base["coverage"] = 1
    return pd.concat([base, education_city(base)], ignore_index=True)


# ---------------------------------------------------------------------------------------------
# 2. Metrics

def worst_use(*uses):
    present = [u for u in uses if isinstance(u, str)]
    return min(present, key=USE_ORDER.index) if present else "show"


def counts(base, metric, name, chapter, stage):
    b = base[base["stage"] == stage]
    return b.assign(metric=metric, name=name, chapter=chapter, value=b["count"], numerator=None, denominator=None,
                    unit="count", category=None)


def share(base, metric, name, chapter, stage, dim, part):
    """part's share of a stage, within the students whose `dim` is known (Qatari / female)."""
    b = base[(base["stage"] == stage)]
    other_dim = "gender" if dim == "nationality" else "nationality"
    b = b[(b[dim] != ALL) & (b[other_dim] == ALL)]
    keys = KEYS + ["source", "quality", "use", "coverage"]
    whole = b.groupby(keys, dropna=False)["count"].sum(min_count=1).rename("denominator")
    num = b[b[dim] == part].set_index(keys)["count"].rename("numerator")
    out = pd.concat([num, whole], axis=1).reset_index()
    return out.assign(metric=metric, name=name, chapter=chapter, value=out["numerator"] / out["denominator"],
                      unit="share", nationality=ALL, gender=ALL, category=None)


def rate(base, metric, name, chapter, top, bottom):
    """top stage / bottom stage (e.g. admitted / applied), totals only."""
    t = base[(base["nationality"] == ALL) & (base["gender"] == ALL)]
    a = t[t["stage"] == top][KEYS + ["count", "use", "coverage", "source"]]
    b = t[t["stage"] == bottom][KEYS + ["count", "use", "coverage"]]
    joined = a.merge(b, on=KEYS, suffixes=("_top", "_bottom"))
    joined["use"] = [worst_use(x, y) for x, y in zip(joined["use_top"], joined["use_bottom"])]
    return joined.assign(metric=metric, name=name, chapter=chapter, numerator=joined["count_top"],
                         denominator=joined["count_bottom"], value=joined["count_top"] / joined["count_bottom"],
                         unit="rate", nationality=ALL, gender=ALL, category=None,
                         coverage=joined[["coverage_top", "coverage_bottom"]].min(axis=1),
                         quality=joined["use"].map(STATUS_FOR_USE))


def school_type_mix(tables, flags):
    """M10: each school type's share of the Pipeline's own total for a stage (D-020)."""
    pl = tables["student_pipeline"]
    pl = pl[pl["row_type"].isin(COUNTED_ROWS) & pl["level"].isin(["undergraduate", "foundation"])
            & pl["stage"].isin(["applied", "admitted", "newly_enrolled"])].rename(columns={"file_year": "year"})
    f = flags[flags["measure"] == "student_pipeline"].set_index(["university", "file_year"])["use"]
    pl = pl.assign(use=[f.get((u, y), "show") for u, y in zip(pl["university"], pl["year"])])
    rows = []
    for scope, data in (("university", pl), ("All", pl[pl["use"] != "leave_out"].assign(university=ALL))):
        g = data.groupby(["university", "year", "stage", "school_type"]).agg(
            n=("count", lambda s: s.sum(min_count=1)), use=("use", lambda s: min(s, key=USE_ORDER.index)),
            coverage=("university", "size"))
        whole = g.groupby(["university", "year", "stage"])["n"].transform("sum")
        g = g.assign(denominator=whole).reset_index()
        if scope == "All":
            g["coverage"] = data.groupby(["year"])["source_file"].nunique().reindex(g["year"]).values
        else:
            g["coverage"] = 1
        rows.append(g)
    m = pd.concat(rows, ignore_index=True)
    return m.assign(metric="M10", name="School-type mix", chapter="Getting in", numerator=m["n"],
                    value=m["n"] / m["denominator"], unit="share", level="undergraduate+foundation",
                    program_group=ALL, nationality=ALL, gender=ALL,
                    category=m["stage"] + ": " + m["school_type"], source="student_pipeline",
                    quality=m["use"].map(STATUS_FOR_USE))


def growth_and_getting_in(base, tables, flags):
    parts = [
        counts(base, "M01", "Registered students", "Growth", "registered"),
        share(base, "M02", "Qatari share of students", "Growth", "registered", "nationality", "Qatari"),
        share(base, "M03", "Female share of students", "Growth", "registered", "gender", "Female"),
        counts(base, "M04", "Applicants", "Getting in", "applied"),
        counts(base, "M05", "Admitted", "Getting in", "admitted"),
        counts(base, "M06", "New students", "Getting in", "newly_enrolled"),
        rate(base, "M07", "Acceptance rate", "Getting in", "admitted", "applied"),
        rate(base, "M08", "Yield", "Getting in", "newly_enrolled", "admitted"),
    ]
    for stage in ("applied", "admitted", "newly_enrolled"):
        parts.append(share(base, "M09", "Qatari share", "Getting in", stage, "nationality", "Qatari")
                     .assign(category=stage))
    parts.append(school_type_mix(tables, flags))
    return parts


# ---------------------------------------------------------------------------------------------
# 3. Studying (shares within the sheet that holds them, D-022)

def flag_use(flags, measure):
    f = flags[flags["measure"] == measure].set_index(["university", "file_year"])["use"]
    return lambda universities, years: [f.get((u, y), "show") for u, y in zip(universities, years)]


def mix(rows, metric, name, chapter, use_of, denominators=None):
    """Shares of each category within (university, year, level), for each university and Education City.

    rows: university, year, level, category, count. denominators (optional): a Series indexed by
    (university, year, level) to divide by instead of the categories' own total.
    """
    rows = rows[rows["count"].notna()].copy()
    if use_of is not None:  # otherwise the rows bring their own `use`
        rows["use"] = use_of(rows["university"], rows["year"])
    group = ["university", "year", "level"]
    per_uni = rows.groupby(group + ["category"]).agg(numerator=("count", "sum"), use=("use", "first")).reset_index()
    if denominators is None:
        per_uni["denominator"] = per_uni.groupby(group)["numerator"].transform("sum")
    else:
        per_uni = per_uni.merge(denominators.rename("denominator").reset_index(), on=group, how="left")
    per_uni["coverage"] = 1
    kept = per_uni[per_uni["use"] != "leave_out"]
    ec = kept.groupby(["year", "level", "category"]).agg(
        numerator=("numerator", "sum"), use=("use", lambda s: min(s, key=USE_ORDER.index)),
        coverage=("university", "nunique")).reset_index()
    ec_den = kept.drop_duplicates(group).groupby(["year", "level"])["denominator"].sum()
    ec["denominator"] = [ec_den.get((y, lv)) for y, lv in zip(ec["year"], ec["level"])] if denominators is not None \
        else ec.groupby(["year", "level"])["numerator"].transform("sum")
    out = pd.concat([per_uni, ec.assign(university=ALL)], ignore_index=True)
    out = out[out["denominator"].fillna(0) > 0]
    return out.assign(metric=metric, name=name, chapter=chapter, value=out["numerator"] / out["denominator"],
                      unit="share", program_group=ALL, nationality=ALL, gender=ALL,
                      quality=out["use"].map(STATUS_FOR_USE), source=None)


def with_all_levels(rows):
    """Add level = All (sum over levels) to rows that have a level."""
    all_levels = rows.groupby([c for c in rows.columns if c not in ("level", "count")], dropna=False)["count"] \
        .sum().reset_index().assign(level=ALL)
    return pd.concat([rows, all_levels], ignore_index=True)


AGE_BANDS = [(17, "under 18"), (20, "18-20"), (23, "21-23"), (29, "24-29")]


def age_band(age):
    text = str(age).strip().lower()
    if text.startswith("<"):
        return "under 18"
    if text.startswith(">") or "-" in text:
        return "30 and over"
    if text.isdigit():
        return next((band for top, band in AGE_BANDS if int(text) <= top), "30 and over")
    return "not given"


def studying(tables, flags, base):
    out = []
    # M11 nationality mix: regions and countries, registered students
    nat = tables["nationalities"]
    nat = nat[(nat["stage"] == "registered") & (nat["breakdown"] == "total") & (nat["row_status"] == "used")]
    nat = nat.rename(columns={"file_year": "year"}).assign(level=ALL)
    use_nat = flag_use(flags, "nationalities")
    out.append(mix(nat.assign(category="region: " + nat["region"]), "M11", "Nationality mix", "Studying", use_nat))
    countries = nat[nat["count"] > 0]
    out.append(mix(countries.assign(category="country: " + countries["country"]), "M11", "Nationality mix",
                   "Studying", use_nat))

    # M12 age mix, all students and new entrants
    ages = tables["ages"]
    ages = ages[ages["breakdown"] == "gender"].rename(columns={"file_year": "year"}).assign(level=ALL)
    ages = ages.assign(category=ages["stage"].str.replace("_", " ") + ": " + ages["age"].map(age_band))
    for stage in ("registered", "new_entrants"):
        part = ages[ages["stage"] == stage]
        out.append(mix(part, "M12", "Age mix", "Studying", flag_use(flags, "ages")))

    # M13 attendance, scholarship and class year, by level
    rd = tables["registered_detailed"]
    rd = rd[rd["row_type"].isin(COUNTED_ROWS) & rd["level"].notna() & (rd["level"] != "non_degree")]
    rd = rd.rename(columns={"file_year": "year"})
    use_rd = flag_use(flags, "registered_detailed")
    for column, label, name in (("attendance_std", "attendance", "Attendance mix"),
                                ("scholarship_std", "scholarship", "Scholarship share"),
                                ("year_class", "class year", "Class-year mix")):
        values = rd[column].replace("", pd.NA).fillna("not given").astype(str).str.strip().str.capitalize()
        rows = with_all_levels(rd.assign(category=label + ": " + values)[["university", "year", "level", "category", "count"]])
        out.append(mix(rows, "M13", name, "Studying", use_rd))

    # M14 funding types, each against registered students (types overlap, never stacked: P-35)
    fu = tables["funding"]
    fu = fu[fu["row_type"].isin(COUNTED_ROWS) & (fu["measure"] == "students") & (fu["breakdown"] == "total")
            & fu["level"].notna() & (fu["level"] != "non_degree")].rename(columns={"file_year": "year"})
    rows = with_all_levels(fu.assign(category="funding: " + fu["stage"].str.replace("_", " "))
                           [["university", "year", "level", "category", "count"]])
    reg = base[(base["stage"] == "registered") & (base["nationality"] == ALL) & (base["gender"] == ALL)
               & (base["program_group"] == ALL) & (base["university"] != ALL)]
    denominators = reg.set_index(["university", "year", "level"])["count"]
    funding = mix(rows, "M14", "Funding by type", "Studying", flag_use(flags, "funding"), denominators)
    reg_use = reg.set_index(["university", "year"])["use"].to_dict()
    funding["use"] = [worst_use(u, reg_use.get((uni, y))) if uni != ALL else u
                      for u, uni, y in zip(funding["use"], funding["university"], funding["year"])]
    # Every university reports 0 QF-scholarship students in every year: QF records those itself
    # ('to be provided by QF financial services'), so this sheet can't measure them (D-031)
    qf = funding["category"] == "funding: qf scholarship"
    funding.loc[qf, "use"] = "leave_out"
    funding.loc[qf, "note"] = "Not measured here: universities leave QF scholarships to QF Financial Services (D-031)"
    funding["quality"] = funding["use"].map(STATUS_FOR_USE)
    out.append(funding)

    # M15 internships by employer type: counts and shares of all internships
    it = tables["internships"].rename(columns={"file_year": "year"}).assign(level=ALL)
    it = it.assign(category="employer: " + it["employer_type"])
    internships = mix(it, "M15", "Internships by employer type", "Studying", flag_use(flags, "internships"))
    counts_ = internships.assign(value=internships["numerator"], unit="count", denominator=None,
                                 name="Internships by employer type (count)")
    out += [internships, counts_]
    return out


# ---------------------------------------------------------------------------------------------
# 4. Graduating and after: by graduating class, or by entering class for graduation rates

BACHELOR_YEARS = 4  # the form's default normal time to completion; used for every undergraduate class (D-032)


def window_closed(cohort, file_year, years):
    """True when a class that entered in `cohort` has had `years` academic years by the end of `file_year`."""
    return int(cohort[:4]) + years - 1 <= int(file_year[:4])


def graduation_classes(tables, flags):
    """Graduation Rate reports (latest per class, D-012) as one row per university x class x level x nationality.

    'Graduated by 150%' counts everyone who graduated by 150% of normal time (D-027): where a program
    row's 150% number already includes the on-time graduates (C05's test) it's used as is, otherwise
    the on-time and extra graduates are added. Each window (normal time, 150%) only counts once it has
    closed by the end of the report's year (D-032)."""
    gr = tables["graduation_rate"]
    gr = gr[(gr["report_status"] == "used") & gr["row_type"].isin(COUNTED_ROWS) & gr["level"].notna()
            & (gr["level"] != "non_degree")]
    gr = gr.assign(row_key=gr["source_file"] + "|" + gr["source_cell"].str.extract(r"(\d+)$")[0],
                   normal_years=gr["normal_years"].astype("string").fillna(""))  # a blank key would drop the row
    keys = ["row_key", "university", "file_year", "cohort", "level", "normal_years"]
    wide = gr.pivot_table(index=keys + ["nationality"], columns="stage", values="count", aggfunc="sum").fillna(0)
    wide = wide.reset_index()
    total = wide[wide["nationality"] == ALL].set_index("row_key")
    cumulative = (total["graduated_100"] + total["graduated_150"] > total["entered"]) \
        & (total["graduated_150"] <= total["entered"]) & (total["graduated_150"] >= total["graduated_100"])
    wide["cumulative"] = wide["row_key"].map(cumulative).fillna(False).astype(bool)
    wide["by_150"] = wide["graduated_150"].where(wide["cumulative"], wide["graduated_100"] + wide["graduated_150"])
    years = pd.to_numeric(wide["normal_years"], errors="coerce").astype(float) \
        .where(wide["level"] != "undergraduate", BACHELOR_YEARS)
    wide["closed_100"] = [y == y and window_closed(c, f, int(y)) for c, f, y in zip(wide["cohort"], wide["file_year"], years)]
    wide["closed_150"] = [y == y and window_closed(c, f, -(-int(y) * 3 // 2))
                          for c, f, y in zip(wide["cohort"], wide["file_year"], years)]
    # A report with 0 drop-outs in every class hasn't reported them (TAMU-Q counts its leavers as non-completers)
    reported = wide[wide["nationality"] == ALL].groupby(["university", "file_year"])["dropouts"].sum() > 0
    wide["dropouts_known"] = wide["closed_100"] & pd.Series(
        [bool(reported.get(k, False)) for k in zip(wide["university"], wide["file_year"])], index=wide.index)
    wide["use"] = flag_use(flags, "graduation_rate")(wide["university"], wide["file_year"])
    wide = wide.assign(year=wide["cohort"])
    agg = dict(entered=("entered", "sum"), graduated_100=("graduated_100", "sum"), by_150=("by_150", "sum"),
               dropouts=("dropouts", "sum"), closed_100=("closed_100", "all"), closed_150=("closed_150", "all"),
               dropouts_known=("dropouts_known", "all"),
               cumulative=("cumulative", "any"), report_year=("file_year", "max"),
               use=("use", lambda s: min(s, key=USE_ORDER.index)))
    per_level = wide.groupby(["university", "year", "level", "nationality"]).agg(**agg).reset_index()
    all_levels = wide.groupby(["university", "year", "nationality"]).agg(**agg).reset_index().assign(level=ALL)
    classes = pd.concat([per_level, all_levels], ignore_index=True)
    # More Qatari (or Non-Qatari) graduates than entrants in a program row (C05): the class keeps its
    # totals but not its nationality split
    entered = wide["row_key"].map(total["entered"])
    impossible = (wide["nationality"] != ALL) & (entered > 0) \
        & ((wide["graduated_100"] > wide["entered"]) | (wide["by_150"] > wide["entered"]))
    bad = set(zip(wide.loc[impossible, "university"], wide.loc[impossible, "year"]))
    split = classes["nationality"] != ALL
    return classes[~(split & pd.Series([k in bad for k in zip(classes["university"], classes["year"])], index=classes.index))]


def class_rate(classes, metric, name, top, closed):
    """top / entered for each class whose window has closed. Classes with entrants get a rate and
    count towards Education City; classes with graduates but no entrants get a count only (P-25)."""
    c = classes[classes[closed]]
    rated = c[c["entered"] > 0].assign(numerator=lambda d: d[top], denominator=lambda d: d["entered"], coverage=1)
    kept = rated[rated["use"] != "leave_out"]
    ec = kept.groupby(["year", "level", "nationality"]).agg(
        numerator=("numerator", "sum"), denominator=("denominator", "sum"), coverage=("university", "nunique"),
        cumulative=("cumulative", "any"), report_year=("report_year", "max"),
        use=("use", lambda s: min(s, key=USE_ORDER.index))).reset_index().assign(university=ALL)
    rates = pd.concat([rated, ec], ignore_index=True)
    rates = rates.assign(value=rates["numerator"] / rates["denominator"], unit="rate")
    unrated = c[(c["entered"] == 0) & (c[top] > 0)]
    unrated = unrated.assign(value=unrated[top], numerator=None, denominator=None, unit="count", coverage=1,
                             note="Graduates of this class without its entrants, so no rate (P-25)")
    out = pd.concat([rates, unrated], ignore_index=True)
    if top == "by_150":
        converted = out["cumulative"].fillna(False).astype(bool) & (out["unit"] == "rate") & (out["university"] != ALL)
        out.loc[converted, "note"] = "This report's '150%' number already included the on-time graduates (D-027)"
    return out.assign(metric=metric, name=name, chapter="Graduating", year_kind="entering_class",
                      program_group=ALL, gender=ALL, category=None, source="graduation_rate",
                      quality=out["use"].map(STATUS_FOR_USE))


OUTCOMES = ["employed", "self_employed", "grad_school", "still_searching", "not_seeking"]


def outcome_classes(tables, flags, base):
    """Outcomes reports (earliest real report per class, D-013) as one row per university x class x
    level x nationality, with the class size chosen per D-021."""
    oc = tables["outcomes"]
    oc = oc[(oc["report_status"] == "used") & oc["row_type"].isin(COUNTED_ROWS) & oc["level"].notna()
            & (oc["level"] != "non_degree")].assign(year=lambda d: d["graduating_year"])
    keys = ["university", "year", "file_year", "years_after_graduation", "level", "nationality"]
    total = oc[oc["breakdown"] == "total"]
    parts = oc[oc["breakdown"].isin(["nationality", "nationality_location"])]
    located = oc[(oc["breakdown"] == "nationality_location") & oc["stage"].isin(["employed", "self_employed"])]
    in_qatar = located[located["location"] == "In Qatar"]
    frames = [total.pivot_table(index=keys, columns="stage", values="count", aggfunc="sum"),
              parts.pivot_table(index=keys, columns="stage", values="count", aggfunc="sum")]
    wide = pd.concat(frames).fillna(0)
    for name, rows in (("employed_located", located), ("employed_in_qatar", in_qatar)):
        by_nat = rows.groupby(keys)["count"].sum()
        whole = rows.assign(nationality=ALL).groupby(keys)["count"].sum()
        wide[name] = pd.concat([by_nat, whole]).reindex(wide.index).fillna(0)
    wide = wide.reset_index()
    sums = ["graduates"] + OUTCOMES + ["employed_located", "employed_in_qatar"]
    all_levels = wide.groupby([k for k in keys if k != "level"])[sums].sum().reset_index().assign(level=ALL)
    c = pd.concat([wide, all_levels], ignore_index=True)

    # Class size (D-021): Outcomes' own -> graduates dated in Student Data -> sum of the outcomes (partial)
    graduated = base[(base["stage"] == "graduated") & (base["source"] == "student_data") & (base["gender"] == ALL)
                     & (base["program_group"] == ALL)].set_index(["university", "year", "level", "nationality"])["count"]
    found = (graduated.get(k) for k in zip(c["university"], c["year"], c["level"], c["nationality"]))
    dated = pd.Series([float(n) if pd.notna(n) else 0.0 for n in found], index=c.index)
    reported = c[OUTCOMES].sum(axis=1)
    c["class_size"] = c["graduates"].where(c["graduates"] > 0, dated.where(dated > 0, reported))
    c["note"] = None
    c.loc[c["graduates"] <= 0, "note"] = "Class size from the graduates dated in Student Data (D-021)"
    c.loc[(c["graduates"] <= 0) & (dated <= 0), "note"] = "Class size unknown: the reported outcomes are used (D-021)"
    c["use"] = flag_use(flags, "outcomes")(c["university"], c["file_year"])
    partial = (c["graduates"] <= 0) & (dated <= 0)
    c.loc[partial, "use"] = [worst_use(u, "show_marked") for u in c.loc[partial, "use"]]
    return c.assign(employed_total=c["employed"] + c["self_employed"]).rename(columns={"file_year": "report_year"})


def outcome_rate(classes, metric, name, top, bottom, unit):
    keys = ["year", "level", "nationality", "years_after_graduation"]
    c = classes.assign(numerator=classes[top], denominator=classes[bottom], coverage=1)
    c = c[c["denominator"] > 0]
    kept = c[c["use"] != "leave_out"]
    ec = kept.groupby(keys).agg(numerator=("numerator", "sum"), denominator=("denominator", "sum"),
                                coverage=("university", "nunique"), report_year=("report_year", "max"),
                                use=("use", lambda s: min(s, key=USE_ORDER.index))).reset_index()
    out = pd.concat([c, ec.assign(university=ALL)], ignore_index=True)
    if bottom != "class_size":
        out["note"] = None  # the class-size note doesn't apply to a share of the employed
    return out.assign(metric=metric, name=name, chapter="After graduation", year_kind="graduating_class",
                      value=out["numerator"] / out["denominator"], unit=unit, program_group=ALL, gender=ALL,
                      category=None, source="outcomes", quality=out["use"].map(STATUS_FOR_USE))


def graduating_and_after(tables, flags, base):
    by_class = dict(year_kind="graduating_class")
    graduates = counts(base, "M16", "Graduates", "Graduating", "graduated")
    out = [graduates.assign(report_year=graduates["file_year"], **by_class),
           share(base, "M17", "Qatari share of graduates", "Graduating", "graduated", "nationality", "Qatari")
           .assign(**by_class)]
    out[0].loc[out[0]["source"].str.contains("outcomes"), "note"] = \
        "Class size from the next year's Outcomes sheet where Student Data has none (D-028)"

    classes = graduation_classes(tables, flags)
    out += [class_rate(classes, "M18", "On-time graduation rate", "graduated_100", "closed_100"),
            class_rate(classes, "M19", "Graduation rate within 150%", "by_150", "closed_150"),
            class_rate(classes, "M20", "Drop-out rate", "dropouts", "dropouts_known")]
    out[-1] = out[-1][out[-1]["unit"] == "rate"]  # a drop-out count without its class says nothing

    # M21 graduate nationality mix by region and country; lists that aren't one class are left out (D-024)
    gn = tables["graduate_nationalities"]
    gn = gn[gn["row_status"] == "used"].assign(year=lambda d: d["graduating_year"], level=ALL)
    gn = gn.assign(use=flag_use(flags, "graduate_nationalities")(gn["university"], gn["file_year"]))
    countries = gn[gn["count"] > 0]
    for rows in (gn.assign(category="region: " + gn["region"]), countries.assign(category="country: " + countries["country"])):
        out.append(mix(rows, "M21", "Graduate nationality mix", "Graduating", None)
                   .assign(source="graduate_nationalities", **by_class))

    outcomes = outcome_classes(tables, flags, base)
    out += [outcome_rate(outcomes, "M22", "Employment rate", "employed_total", "class_size", "rate"),
            outcome_rate(outcomes, "M23", "Further study rate", "grad_school", "class_size", "rate"),
            outcome_rate(outcomes, "M24", "Still searching", "still_searching", "class_size", "rate"),
            outcome_rate(outcomes, "M25", "Working in Qatar", "employed_in_qatar", "employed_located", "share")]
    return out


# ---------------------------------------------------------------------------------------------
# Small numbers (D-026)

def hide_small_numbers(m):
    """Counts of 1-4 in any breakdown become '<5'; shares and rates on fewer than 10 aren't shown.
    Totals (no nationality, gender, program or category split) are always shown."""
    m = m.copy()
    split = (m["nationality"] != ALL) | (m["gender"] != ALL) | (m["program_group"] != ALL) | m["category"].notna()
    # a share of 1-4 students in a breakdown would reveal the count (share x total), so it's hidden too
    small_count = split & (((m["unit"] == "count") & m["value"].between(1, 4))
                           | (m["unit"].isin(["share", "rate"]) & m["numerator"].between(1, 4)))
    small_base = m["unit"].isin(["share", "rate"]) & (m["denominator"] < 10) & ~small_count
    m["display"] = None
    m.loc[small_count, "display"] = "<5"
    m.loc[small_base, "display"] = "fewer than 10 students"
    hidden = small_count | small_base
    m.loc[hidden, ["value", "numerator", "denominator"]] = None
    return m


def compute(tables, flags):
    base = build_bases(tables, flags)
    metrics = pd.concat(growth_and_getting_in(base, tables, flags) + studying(tables, flags, base)
                        + graduating_and_after(tables, flags, base), ignore_index=True)
    metrics["year_kind"] = metrics["year_kind"].fillna("academic")
    metrics["years_after_graduation"] = metrics["years_after_graduation"].astype("Int64")
    metrics.loc[metrics["source"] == "qf_consolidated", "note"] = "From QF's consolidated file (D-029)"
    metrics = hide_small_numbers(metrics)
    return metrics.reindex(columns=COLUMNS)


def load():
    read = dict(keep_default_na=False, na_values={c: [""] for c in ("count", "level", "program", "program_group",
                                                                   "period_label", "band_label", "graduating_year")},
                dtype={"degree_raw": str, "program_raw": str})
    names = ("student_data", "student_pipeline", "nationalities", "ages", "registered_detailed", "funding", "internships",
             "graduation_rate", "outcomes", "graduate_nationalities")
    read["dtype"] |= {"age": str, "year_class": str}
    tables = {n: pd.read_csv(PROCESSED / f"{n}.csv", **read) for n in names}
    flags = pd.read_csv(PROCESSED / "quality_flags.csv", keep_default_na=False)
    return tables, flags


def main():
    tables, flags = load()
    metrics = compute(tables, flags)
    metrics.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(metrics):,} values")
    print(metrics.groupby(["metric", "name"]).size().to_string())


if __name__ == "__main__":
    main()
