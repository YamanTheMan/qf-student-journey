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
           "source", "quality", "use", "coverage", "note"]


# ---------------------------------------------------------------------------------------------
# 1. Bases

def student_rows(tables, stage):
    """Student Data rows of one stage: degree-seeking program rows only (D-016)."""
    sd = tables["student_data"]
    t = sd[(sd["stage"] == stage) & sd["row_type"].isin(COUNTED_ROWS) & sd["level"].notna()
           & (sd["level"] != "non_degree")]
    t = t.assign(year=t["file_year"], row_key=t["source_file"] + "|" + t["source_cell"].str.extract(r"(\d+)$")[0]
                 .fillna(t["source_cell"]) + "|" + t["period_label"].fillna("") + "|" + t["band_label"].fillna(""))
    return t


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
    return out.assign(stage=stage, source="student_data", measure=stage)


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
    return out.assign(stage="registered", source="qf_consolidated", measure=None)


def roll_up(base):
    """Add level = All and program_group = All rows (sums of the detailed ones)."""
    dims = ["stage", "source", "measure", "nationality", "gender"]
    detail = base[base["program_group"] != ALL]
    by_level = detail.groupby(["university", "year", "level"] + dims, dropna=False)["count"].sum(min_count=1) \
        .reset_index().assign(program_group=ALL)
    already = base[base["program_group"] == ALL]  # QF history comes at level x All programs
    per_level = pd.concat([by_level, already], ignore_index=True)
    all_levels = per_level.groupby(["university", "year", "program_group"] + dims, dropna=False)["count"] \
        .sum(min_count=1).reset_index().assign(level=ALL)
    return pd.concat([detail, per_level, all_levels], ignore_index=True)


def with_quality(base, flags):
    """Attach each base row's flag (Student Data stages) or 'complete' (QF history)."""
    f = flags.set_index(["measure", "university", "file_year"])[["status", "use"]]
    keys = list(zip(base["measure"], base["university"], base["year"]))
    found = f.reindex(pd.MultiIndex.from_tuples(keys)).reset_index(drop=True)
    out = base.reset_index(drop=True).assign(quality=found["status"].fillna("complete"), use=found["use"].fillna("show"))
    return out


def education_city(base):
    """'All' universities: sum of the university-years that aren't left out, with coverage."""
    kept = base[(base["use"] != "leave_out") & (base["program_group"] == ALL)]
    dims = ["year", "level", "program_group", "stage", "source", "nationality", "gender"]
    agg = kept.groupby(dims, dropna=False).agg(
        count=("count", lambda s: s.sum(min_count=1)),
        coverage=("university", "nunique"),
        use=("use", lambda s: min(s, key=USE_ORDER.index)),
    ).reset_index()
    agg["quality"] = agg["use"].map(STATUS_FOR_USE)
    return agg.assign(university=ALL, measure=None)


def build_bases(tables, flags):
    stages = ["registered", "applied", "admitted", "newly_enrolled"]
    sd = pd.concat([base_from_student_data(tables, s) for s in stages], ignore_index=True)
    history = base_from_qf_history()
    base = with_quality(roll_up(pd.concat([sd, history], ignore_index=True)), flags)
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
    metrics = pd.concat(growth_and_getting_in(base, tables, flags) + studying(tables, flags, base), ignore_index=True)
    metrics["year_kind"] = "academic"
    if "note" not in metrics:
        metrics["note"] = None
    metrics.loc[metrics["source"] == "qf_consolidated", "note"] = "From QF's consolidated file (D-029)"
    metrics = hide_small_numbers(metrics)
    return metrics.reindex(columns=COLUMNS)


def load():
    read = dict(keep_default_na=False, na_values={c: [""] for c in ("count", "level", "program", "program_group",
                                                                   "period_label", "band_label", "graduating_year")},
                dtype={"degree_raw": str, "program_raw": str})
    names = ("student_data", "student_pipeline", "nationalities", "ages", "registered_detailed", "funding", "internships")
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
