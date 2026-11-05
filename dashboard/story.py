"""Phase 5: the sentences at the top of each chapter, written from the numbers so they never go stale.

Comparisons over time always use the same universities in both years (D-036), whatever the chart shows.
"""
import pandas as pd

from dashboard import data as d


def _who(university, level, group):
    level_word = {v: k.lower() for k, v in d.LEVELS.items() if v != d.ALL}.get(level, "")
    group_word = {"All students": "", "Female": "female", "Male": "male"}.get(group, group)
    students = " ".join(w for w in (group_word, level_word, "students") if w)
    return students


def growth(m, university=d.EDUCATION_CITY, level=d.ALL, group="All students"):
    """Markdown: latest size, then like-for-like change since the first year with data."""
    years = d.years_of(m, "M01")
    pts = d.points(m, "M01", years, university, False, level, group)
    have = pts[pts["value"].notna()]
    if have.empty:
        return "No data for this selection."
    last = have.iloc[-1]
    students = _who(university, level, group)
    text = f"In {d.year_label(last.year)}, {d.EDUCATION_CITY if university == d.EDUCATION_CITY else university} " \
           f"had **{d.count_text(last.value)}** {students}"
    if university == d.EDUCATION_CITY:
        h = d.headline(m, "M01")
        n = int(h.loc[(h["university"] == d.ALL) & (h["year"] == last.year), "coverage"].iloc[0])
        text += f" ({n} universities reported)"
    if group == "All students":
        shares = []
        for metric, word in (("M02", "Qatari"), ("M03", "female")):
            p = d.points(m, metric, [last.year], university, False, level)
            if p["value"].notna().all():
                shares.append(f"{d.share_text(p['value'].iloc[0])} {word}")
        text += ": " + " and ".join(shares) if shares else ""
    text += "."
    # change over time, like for like
    if university == d.EDUCATION_CITY:
        keep, same = d.same_universities(m, "M01", years, level, group)
        same = same[same["value"].notna()]
        if len(keep) > 1 and len(same) > 1 and same["value"].iloc[0] > 0 and _apart(same["year"]) >= MIN_YEARS:
            first, end = same.iloc[0], same.iloc[-1]
            text += (f" Counting only the {len(keep)} universities with data in every year "
                     f"({', '.join(keep)}), {students} went from {d.count_text(first.value)} in "
                     f"{d.year_label(first.year)} to {d.count_text(end.value)} in {d.year_label(end.year)} "
                     f"({_change(first.value, end.value)}).")
    elif len(have) > 1 and have["value"].iloc[0] > 0 and _apart(have["year"]) >= MIN_YEARS:
        first = have.iloc[0]
        text += (f" That's {_change(first.value, last.value)} since {d.year_label(first.year)} "
                 f"({d.count_text(first.value)}).")
    return text


MIN_YEARS = 3  # a change over fewer years isn't a trend worth a sentence


def _apart(years):
    return int(years.iloc[-1][:4]) - int(years.iloc[0][:4])


def _change(before, after):
    change = after / before - 1
    if abs(change) < 0.005:
        return "about the same"
    return f"{'up' if change > 0 else 'down'} {abs(change):.0%}"


ADMISSIONS = [("M04", None, ""), ("M05", None, ""), ("M06", None, "")]


def getting_in(m, university=d.EDUCATION_CITY, level=d.ALL, group="All students"):
    """Markdown: the latest year's funnel, then like-for-like change in applicants and new students."""
    years = d.years_of(m, "M04")
    apps = d.points(m, "M04", years, university, False, level, group)
    have = apps[apps["value"].notna()]
    if have.empty:
        return "No data for this selection."
    year = have["year"].iloc[-1]
    who = d.EDUCATION_CITY if university == d.EDUCATION_CITY else university
    one = {metric: d.points(m, metric, [year], university, False, level, group).iloc[0]
           for metric in ("M04", "M05", "M06", "M07", "M08")}
    students = _who(university, level, group).replace("students", "applicants")
    text = f"In {d.year_label(year)}, {who} had **{d.count_text(one['M04'].value)}** {students}"
    if university == d.EDUCATION_CITY:
        h = d.headline(m, "M04")
        n = int(h.loc[(h["university"] == d.ALL) & (h["year"] == year), "coverage"].iloc[0])
        text += f" ({n} universities reported)"
    rates = group == "All students"
    if pd.notna(one["M05"].value):
        text += f" and admitted **{d.count_text(one['M05'].value)}**"
        text += f" ({d.share_text(one['M07'].value)})" if rates and pd.notna(one["M07"].value) else ""
    text += "."
    if pd.notna(one["M06"].value):
        text += f" **{d.count_text(one['M06'].value)}** enrolled"
        text += f", {d.share_text(one['M08'].value)} of those admitted" if rates and pd.notna(one["M08"].value) else ""
        text += "."
    if university == d.EDUCATION_CITY:
        keep = d.every_year_of_all(m, ADMISSIONS, years)
        series = {metric: d.same_universities(m, metric, years, level, group, among=keep)[1]
                  for metric in ("M04", "M06")}
        a, n = (series[k][series[k]["value"].notna()] for k in ("M04", "M06"))
        if len(keep) > 1 and len(a) > 1 and a["value"].iloc[0] > 0 and _apart(a["year"]) >= MIN_YEARS:
            text += (f" Counting only the {len(keep)} universities with data in every year ({', '.join(keep)}), "
                     f"applicants went from {d.count_text(a['value'].iloc[0])} in {d.year_label(a['year'].iloc[0])} "
                     f"to {d.count_text(a['value'].iloc[-1])} in {d.year_label(a['year'].iloc[-1])} "
                     f"({_change(a['value'].iloc[0], a['value'].iloc[-1])})")
            if len(n) > 1 and n["value"].iloc[0] > 0:
                text += (f", and new students from {d.count_text(n['value'].iloc[0])} to "
                         f"{d.count_text(n['value'].iloc[-1])} ({_change(n['value'].iloc[0], n['value'].iloc[-1])})")
            text += "."
    elif len(have) > 1 and _apart(have["year"]) >= MIN_YEARS and have["value"].iloc[0] > 0:
        text += (f" Applicants are {_change(have['value'].iloc[0], have['value'].iloc[-1])} since "
                 f"{d.year_label(have['year'].iloc[0])} ({d.count_text(have['value'].iloc[0])}).")
    return text


REGION_PHRASES = {
    "Qatar": "from Qatar", "Other Arab countries": "from other Arab countries", "South Asia": "from South Asia",
    "North America": "from North America", "Other GCC": "from other GCC countries", "Europe": "from Europe",
    "East & Southeast Asia & Pacific": "from East and Southeast Asia and the Pacific",
    "Iran, Turkey, Caucasus & Central Asia": "from Iran, Turkey, the Caucasus and Central Asia",
    "Sub-Saharan Africa": "from Sub-Saharan Africa", "Latin America & Caribbean": "from Latin America and the Caribbean",
}


def countries(m, university, year):
    """How many countries students came from: every country with students, including those hidden as '<5'."""
    who = d.ALL if university == d.EDUCATION_CITY else university
    rows = m[(m["metric"] == "M11") & (m["university"] == who) & (m["year"] == year)
             & m["category"].str.startswith("country: ") & ~m["category"].str.lower().str.contains("not given")]
    return int(((rows["value"] > 0) | (rows["display"] == "<5")).sum())


def studying(m, university=d.EDUCATION_CITY, level=d.ALL):
    """Markdown: where students come from (latest year), how many study full-time, and the like-for-like
    change in the share from Qatar."""
    years = d.years_of(m, "M11", category="region: Qatar")
    who = d.EDUCATION_CITY if university == d.EDUCATION_CITY else university
    text = ""
    if level == d.ALL:
        regions = {r: d.points(m, "M11", years, university, category=f"region: {r}")
                   for r in d.categories(m, "M11", "region: ") if r in REGION_PHRASES}
        have = regions["Qatar"][regions["Qatar"]["value"].notna()]
        if have.empty:
            return "No data for this selection."
        year = have["year"].iloc[-1]
        latest = {r: pts.set_index("year").loc[year, "value"] for r, pts in regions.items()}
        top = sorted((r for r in latest if pd.notna(latest[r])), key=lambda r: -latest[r])[:3]
        parts = [f"{d.share_text(latest[r])} {REGION_PHRASES[r]}" for r in top]
        text = (f"In {d.year_label(year)}, {who}'s students came from **{countries(m, university, year)}** countries: "
                f"{', '.join(parts[:-1])} and {parts[-1]}.")
    full = d.points(m, "M13", d.years_of(m, "M13", "Attendance mix", "attendance: Full-time"), university,
                    level=level, name="Attendance mix", category="attendance: Full-time")
    full = full[full["value"].notna()]
    if len(full):
        year = full["year"].iloc[-1]
        unknown = d.points(m, "M13", [year], university, level=level, name="Attendance mix",
                           category="attendance: Not given")["value"].iloc[0]
        students = _who(university, level, "All students")
        text += (f" {d.share_text(full['value'].iloc[-1])} of {students} studied full-time in {d.year_label(year)}"
                 + (f" ({d.share_text(unknown)} not given)." if pd.notna(unknown) and unknown >= 0.05 else "."))
    if university == d.EDUCATION_CITY and level == d.ALL:
        keep = d.every_year_in(m, "M11", years, "region: ")
        _, same = d.same_universities(m, "M11", years, category="region: Qatar", among=keep)
        same = same[same["value"].notna()]
        if len(keep) > 1 and len(same) > 1 and _apart(same["year"]) >= MIN_YEARS:
            text += (f" Among the {len(keep)} universities with nationality data in every year ({', '.join(keep)}), "
                     f"the share from Qatar went from {d.share_text(same['value'].iloc[0])} in "
                     f"{d.year_label(same['year'].iloc[0])} to {d.share_text(same['value'].iloc[-1])} in "
                     f"{d.year_label(same['year'].iloc[-1])}.")
    return text.strip() or "No data for this selection."


RATE_METRICS = ("M18", "M19", "M20")


def rates_only(m):
    """Graduation-rate rows that are rates: classes with graduates but no entrants give counts instead (P-25)."""
    return m[~(m["metric"].isin(RATE_METRICS) & (m["unit"] == "count"))]


def latest_rate(m, metric, university, level, group):
    """(value, entering class) of a university's latest usable rate, or None."""
    years = sorted(set(m.loc[m["metric"] == metric, "year"]))
    pts = d.points(rates_only(m), metric, years, university, level=level, group=group)
    pts = pts[pts["value"].notna()]
    return (pts["value"].iloc[-1], pts["year"].iloc[-1]) if len(pts) else None


def graduating(m, university=d.EDUCATION_CITY, level=d.ALL, group="All students"):
    """Markdown: the latest graduating class, the like-for-like change, then on-time graduation rates."""
    years = d.years_of(m, "M16")
    pts = d.points(m, "M16", years, university, False, level, group)
    have = pts[pts["value"].notna()]
    if have.empty:
        return "No data for this selection."
    last = have.iloc[-1]
    who = d.EDUCATION_CITY if university == d.EDUCATION_CITY else university
    level_word = {"undergraduate": "undergraduate", "graduate": "graduate-level", "foundation": "foundation"}.get(level, "")
    group_word = {"All students": "", "Female": "female", "Male": "male"}.get(group, group)
    graduates = " ".join(w for w in (group_word, level_word, "graduates") if w)
    text = f"{who}'s class of {d.year_label(last.year)} had **{d.count_text(last.value)}** {graduates}"
    if university == d.EDUCATION_CITY:
        h = d.headline(m, "M16")
        n = int(h.loc[(h["university"] == d.ALL) & (h["year"] == last.year), "coverage"].iloc[0])
        text += f" ({n} universities reported)"
    if group == "All students":
        q = d.points(m, "M17", [last.year], university, level=level).iloc[0]
        text += f", {d.share_text(q['value'])} of them Qatari" if pd.notna(q["value"]) else ""
    text += "."
    if university == d.EDUCATION_CITY:
        keep, same = d.same_universities(m, "M16", years, level, group)
        same = same[same["value"].notna()]
        if len(keep) > 1 and len(same) > 1 and same["value"].iloc[0] > 0 and _apart(same["year"]) >= MIN_YEARS:
            text += (f" Counting only the {len(keep)} universities with graduates in every class "
                     f"({', '.join(keep)}), {graduates} went from {d.count_text(same['value'].iloc[0])} in "
                     f"{d.year_label(same['year'].iloc[0])} to {d.count_text(same['value'].iloc[-1])} in "
                     f"{d.year_label(same['year'].iloc[-1])} ({_change(same['value'].iloc[0], same['value'].iloc[-1])}).")
    if group in ("Female", "Male"):
        return text  # graduation rates aren't split by gender
    if university == d.EDUCATION_CITY:
        latest = {u: latest_rate(m, "M18", u, level, group) for u in d.universities()}
        latest = {u: r for u, r in latest.items() if r}
        if len(latest) > 1:
            low, high = (min(latest.items(), key=lambda kv: kv[1][0]), max(latest.items(), key=lambda kv: kv[1][0]))
            text += (f" Where universities report graduation rates, the share of their latest entering class that "
                     f"graduated on time ranges from {d.share_text(low[1][0])} ({low[0]}, entered "
                     f"{d.year_label(low[1][1])}) to {d.share_text(high[1][0])} ({high[0]}, entered "
                     f"{d.year_label(high[1][1])}).")
    else:
        on_time, by_150 = latest_rate(m, "M18", university, level, group), latest_rate(m, "M19", university, level, group)
        if on_time:
            text += (f" Of the students who entered in {d.year_label(on_time[1])}, {d.share_text(on_time[0])} "
                     "graduated on time")
            text += (f"; of those who entered in {d.year_label(by_150[1])}, {d.share_text(by_150[0])} graduated "
                     "within 150% of normal time." if by_150 else ".")
    return text
