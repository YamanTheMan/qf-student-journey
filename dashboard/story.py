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
