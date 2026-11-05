"""Phase 5: the chart builders. Every chart draws `points` (dashboard/data.py) the same way (D-035):

  complete     solid bar or filled dot
  incomplete   lighter bar or open dot: a university missing that year, or partial data (hover says which)
  missing      a gap, marked with a grey x on the baseline (hover says why)

Colours: the validated categorical slots in their fixed order (never cycled), and one lighter step of slot 1
for 'incomplete'. Lines use at most three; the school-type mix uses five.
"""
import textwrap

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.data import count_text, share_text, year_label

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # blue, orange, aqua, yellow, magenta
BLUE, ORANGE = SERIES[:2]
LIGHT_BLUE = "#86b6ef"
ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # blue steps 250-650: ordered bands (ages)
NOT_GIVEN = "#c3c2b7"  # a neutral grey for 'not given', never a series colour
SEQUENTIAL = [[0, "#f3f8fe"], [0.15, "#cde2fb"], [0.4, "#86b6ef"], [0.7, "#2a78d6"], [1, "#104281"]]
INK, INK_2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
FONT = '"Source Sans 3", "Source Sans Pro", system-ui, sans-serif'
CONFIG = {"displayModeBar": False}
HIDDEN = {"<5": "fewer than 5 students (hidden)", "fewer than 10 students": "fewer than 10 students (hidden)"}


def value_text(value, unit, noun=""):
    if pd.isna(value):
        return ""
    return share_text(value) if unit in ("share", "rate") else f"{count_text(value)} {noun}".strip()


def hover_lines(pts, noun=""):
    """The text under the year in each tooltip: the value, then why it's incomplete or missing, then notes,
    each on its own short line so the tooltip stays narrow."""
    lines = []
    for p in pts.itertuples():
        parts = [value_text(p.value, p.unit, noun) or HIDDEN.get(p.why, p.why[:1].upper() + p.why[1:] or "No data")]
        if p.state != "missing" and p.why:
            parts.append(p.why)
        if p.notes:
            parts.append(p.notes)
        short = [w for part in parts for piece in part.split(" · ") for w in textwrap.wrap(piece, 60)]
        lines.append("<br>".join(short))
    return lines


def style(fig, height=340, percent=False):
    fig.update_layout(
        height=height, margin=dict(l=4, r=4, t=36, b=4), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT, size=13, color=INK_2),
        legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", font=dict(size=12), title_text=""),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, align="left",
                        font=dict(family=FONT, size=13, color=INK)),
        bargap=0.25, barcornerradius=4,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXIS, ticks="", tickfont=dict(color=MUTED), fixedrange=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, showline=False, tickfont=dict(color=MUTED), fixedrange=True,
                     tickformat=".0%" if percent else ",", rangemode="tozero")
    if percent:
        fig.update_yaxes(range=[0, 1.02])
    return fig


def _bars(fig, pts, labels, noun, legend, row=None, col=None):
    """Complete and incomplete bars, and an x for each missing year, on one (sub)plot."""
    x = [year_label(y) for y in pts["year"]]
    hover = hover_lines(pts, noun)
    template = "<b>%{x}</b><br>%{customdata}<extra></extra>"
    for state, colour in (("complete", BLUE), ("incomplete", LIGHT_BLUE)):
        keep = (pts["state"] == state).tolist()
        fig.add_trace(go.Bar(
            x=[v for v, k in zip(x, keep) if k], y=pts.loc[keep, "value"], marker_color=colour,
            customdata=[h for h, k in zip(hover, keep) if k], hovertemplate=template,
            name=labels[state], legendgroup=state, showlegend=legend and any(keep)), row=row, col=col)
    keep = (pts["state"] == "missing").tolist()
    fig.add_trace(go.Scatter(
        x=[v for v, k in zip(x, keep) if k], y=[0] * sum(keep), mode="markers", cliponaxis=False,
        marker=dict(symbol="x-thin", size=9, line=dict(width=2, color=MUTED)),
        customdata=[h for h, k in zip(hover, keep) if k], hovertemplate=template,
        name=labels["missing"], legendgroup="missing", showlegend=legend and any(keep)), row=row, col=col)


LABELS = {"complete": "All data", "incomplete": "Incomplete (hover for why)", "missing": "No usable data"}


def bars(pts, noun="students", labels=LABELS, height=340):
    fig = go.Figure()
    _bars(fig, pts, labels, noun, legend=True)
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(categoryorder="array", categoryarray=[year_label(y) for y in pts["year"]])
    return style(fig, height)


def small_multiples(per_university, noun="students", cols=3, labels=LABELS, shared=True):
    """One small bar chart per university (or per stage), years in the same slots. shared: all on one scale;
    otherwise each chart has its own scale and its own axis labels (applicants outnumber new students tenfold)."""
    names = list(per_university)
    rows = -(-len(names) // cols)
    fig = make_subplots(rows=rows, cols=cols, shared_yaxes=shared, subplot_titles=names,
                        horizontal_spacing=0.07 if shared else 0.09, vertical_spacing=0.12)
    seen = set()
    for i, (uni, pts) in enumerate(per_university.items()):
        states = set(pts["state"])
        _bars(fig, pts, {s: labels[s] for s in labels}, noun, legend=False, row=i // cols + 1, col=i % cols + 1)
        for trace in fig.data[-3:]:  # one legend entry per state across all the small charts
            if trace.legendgroup in states and trace.legendgroup not in seen and len(trace.x):
                trace.showlegend = True
                seen.add(trace.legendgroup)
    years = [year_label(y) for y in next(iter(per_university.values()))["year"]]
    top = max(pts["value"].max() for pts in per_university.values())
    fig.update_layout(barmode="overlay")
    fig.update_annotations(font=dict(size=13, color=INK))
    style(fig, height=190 * rows + 60)
    if shared:
        fig.update_yaxes(range=[0, top * 1.08])  # one scale for every small chart, not just within a row
    # first and last year under the first chart of each row only, so neighbouring labels never collide
    fig.update_xaxes(categoryorder="array", categoryarray=years, tickvals=[years[0], years[-1]],
                     tickfont=dict(size=11), showticklabels=False)
    for r in range(1, rows + 1):
        fig.update_xaxes(showticklabels=True, row=r, col=1)
    fig.update_layout(bargap=0.15, margin=dict(t=70), legend=dict(y=1.0, yanchor="top", yref="container"))
    if not shared:
        fig.update_layout(height=260 * rows + 40)
    return fig


def lines(series, height=320, percent=True, noun=""):
    """One line per series (at most three colours), labelled at its last point; gaps stay gaps.
    Incomplete points are open dots; missing years get an x on the baseline."""
    fig = go.Figure()
    colours = SERIES[:3]
    years = None
    gap_traces = []  # added after the lines, so the legend lists the lines first
    for (name, pts), colour in zip(series.items(), colours):
        x = [year_label(y) for y in pts["year"]]
        years = years or x
        hover = hover_lines(pts, noun)
        symbols = ["circle-open" if s == "incomplete" else "circle" for s in pts["state"]]
        fig.add_trace(go.Scatter(
            x=x, y=pts["value"], mode="lines+markers", name=name, connectgaps=False,
            line=dict(color=colour, width=2),
            marker=dict(size=8, color=colour, symbol=symbols, line=dict(width=2, color=colour)),
            customdata=hover, hovertemplate=f"{name}: %{{customdata}}<extra></extra>"))
        gaps = (pts["state"] == "missing").tolist()
        if any(gaps):
            gap_traces.append(go.Scatter(
                x=[v for v, g in zip(x, gaps) if g], y=[0] * sum(gaps), mode="markers", cliponaxis=False,
                marker=dict(symbol="x-thin", size=9, line=dict(width=2, color=MUTED)),
                customdata=[h for h, g in zip(hover, gaps) if g], name=LABELS["missing"], legendgroup="missing",
                showlegend=not gap_traces, hovertemplate=f"{name}: %{{customdata}}<extra></extra>"))
        last = pts[pts["value"].notna()].tail(1)
        if len(last):
            fig.add_annotation(x=year_label(last["year"].iloc[0]), y=last["value"].iloc[0], text=name,
                               xanchor="left", xshift=10, showarrow=False, font=dict(color=INK_2, size=12))
    fig.add_traces(gap_traces)
    if any((pts["state"] == "incomplete").any() for pts in series.values()):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=LABELS["incomplete"],
                                 marker=dict(size=8, symbol="circle-open", color=MUTED, line=dict(width=2))))
    fig.update_layout(hovermode="x unified")
    # the labels at the line ends take room, so label every other year (always the latest) to keep them level
    ticks = years[::-1][::2][::-1] if len(years) > 10 else years
    fig.update_xaxes(categoryorder="array", categoryarray=years, tickvals=ticks, tickangle=0, showspikes=True,
                     spikecolor=AXIS, spikethickness=1, spikedash="solid", spikemode="across")
    style(fig, height, percent)
    fig.update_layout(margin=dict(r=90))
    return fig


def mark_change(fig, years, at, before, after):
    """A hairline between two years where the source changes, labelled on both sides."""
    labels = [year_label(y) for y in years]
    if at not in years or years.index(at) == 0:
        return fig
    x = years.index(at) - 0.5
    fig.add_shape(type="line", x0=x, x1=x, xref="x", y0=0, y1=1, yref="paper", line=dict(color=AXIS, width=1))
    for text, anchor in ((f"{before} ", "right"), (f" {after}", "left")):
        fig.add_annotation(x=x, y=1, xref="x", yref="paper", text=text, xanchor=anchor, yanchor="top",
                           showarrow=False, font=dict(size=11, color=MUTED))
    fig.update_xaxes(categoryarray=labels)
    return fig


def table(series, noun=""):
    """The numbers behind a chart (every chart has one): one column per series, then what's missing."""
    out = None
    for name, pts in series.items():
        col = pd.DataFrame({"Year": [year_label(y) for y in pts["year"]],
                            name: [value_text(v, u, noun) or HIDDEN.get(w, "–") for v, u, w
                                   in zip(pts["value"], pts["unit"], pts["why"])]})
        out = col if out is None else out.merge(col, on="Year")
    notes = list(series.values())[0]
    out["Notes"] = [" · ".join(x for x in (w if s != "missing" else "", n) if x)
                    for s, w, n in zip(notes["state"], notes["why"], notes["notes"])]
    return out


def _hbar_states(fig, labels, values, states, hover, text):
    """Horizontal bars coloured by state, with an x at zero for a missing one."""
    for state, colour in (("complete", BLUE), ("incomplete", LIGHT_BLUE)):
        keep = [st == state for st in states]
        fig.add_trace(go.Bar(
            y=[l for l, k in zip(labels, keep) if k], x=[v for v, k in zip(values, keep) if k], orientation="h",
            marker_color=colour, text=[t for t, k in zip(text, keep) if k], textposition="outside", cliponaxis=False,
            textfont=dict(color=INK_2), customdata=[h for h, k in zip(hover, keep) if k],
            hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>", name=LABELS[state], showlegend=False))
    keep = [st == "missing" for st in states]
    fig.add_trace(go.Scatter(
        y=[l for l, k in zip(labels, keep) if k], x=[0] * sum(keep), mode="markers", cliponaxis=False,
        marker=dict(symbol="x-thin", size=9, line=dict(width=2, color=MUTED)),
        customdata=[h for h, k in zip(hover, keep) if k], hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
        name=LABELS["missing"], showlegend=False))


def _hbar_layout(fig, labels, height, percent=False, top=None):
    style(fig, height=height, percent=percent)
    fig.update_layout(barmode="overlay", bargap=0.3, margin=dict(l=4, r=60, t=8, b=4))
    fig.update_yaxes(categoryorder="array", categoryarray=labels[::-1], range=None, gridcolor="rgba(0,0,0,0)",
                     tickfont=dict(color=INK, size=13))
    fig.update_xaxes(showgrid=False, showticklabels=False, linecolor="rgba(0,0,0,0)",
                     range=[0, top * 1.18] if top else None)  # every bar carries its own number
    return fig


def funnel(stages, noun="students"):
    """One year's funnel: a horizontal bar per stage, widest first. stages: {label: one points row}."""
    labels, rows = list(stages), list(stages.values())
    fig = go.Figure()
    _hbar_states(fig, labels, [r["value"] for r in rows], [r["state"] for r in rows],
                 hover_lines(pd.DataFrame(rows), noun), [value_text(r["value"], r["unit"]) for r in rows])
    return _hbar_layout(fig, labels, height=60 * len(labels) + 30)


def ranked(per_university, noun="", last=("Not given",)):
    """One measure for each university (or region, country, funding type) in one year, highest first; those
    without data, and 'Not given', at the bottom."""
    rows = sorted(per_university.items(),
                  key=lambda kv: (kv[0] in last, pd.isna(kv[1]["value"]), -(kv[1]["value"] or 0)))
    labels = [u for u, _ in rows]
    pts = pd.DataFrame([r for _, r in rows])
    percent = bool(pts["unit"].isin(["share", "rate"]).any())
    fig = go.Figure()
    _hbar_states(fig, labels, pts["value"].tolist(), pts["state"].tolist(), hover_lines(pts, noun),
                 [value_text(v, u, noun) for v, u in zip(pts["value"], pts["unit"])])
    top = pts["value"].max()
    return _hbar_layout(fig, labels, height=34 * len(labels) + 20, percent=percent,
                        top=top if pd.notna(top) and top > 0 else None)


def stacked_shares(groups, categories, colours=None):
    """100% bars, one per group (a stage, a year), split into categories in a fixed order and colour.
    groups: {label: {category: one points row}}. A segment is labelled only where its number fits.
    colours: one per category (default: the categorical slots in order)."""
    fig = go.Figure()
    labels = list(groups)
    colours = colours or SERIES[:len(categories)]
    for i, category in enumerate(categories):
        rows = [groups[g].get(category) for g in labels]
        values = [r["value"] if r is not None else None for r in rows]
        hover = [hover_lines(pd.DataFrame([r]))[0] if r is not None else "No data" for r in rows]
        fig.add_trace(go.Bar(
            y=labels, x=values, orientation="h", name=category, customdata=hover,
            marker=dict(color=colours[i], line=dict(color="white", width=2)),
            text=[share_text(v) if v is not None and pd.notna(v) and v >= 0.08 else "" for v in values],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color="white" if colours[i] in ORDINAL[2:] else INK, size=12),
            hovertemplate=f"<b>%{{y}}</b> · {category}<br>%{{customdata}}<extra></extra>"))
    style(fig, height=64 * len(labels) + 70, percent=True)
    fig.update_layout(barmode="stack", bargap=0.35, legend=dict(traceorder="normal"))
    fig.update_yaxes(categoryorder="array", categoryarray=labels[::-1], range=None, gridcolor="rgba(0,0,0,0)",
                     tickfont=dict(color=INK, size=13))
    fig.update_xaxes(tickformat=".0%", range=[0, 1.001], showgrid=True, gridcolor=GRID)
    return fig


def ranked_table(per_university, name, noun="", label="University"):
    """The numbers behind a ranking or a one-year mix: one row per university (or category)."""
    rows = per_university.items()
    return pd.DataFrame({
        label: [u for u, _ in rows],
        name: [value_text(r["value"], r["unit"], noun) or HIDDEN.get(r["why"], "–") for _, r in rows],
        "Notes": [" · ".join(x for x in ((r["why"]), r["notes"]) if x) for _, r in rows]})

def heatmap(rows, noun=""):
    """A table of shares coloured by size (one blue, light to dark): one row per category, one column per year.
    rows: {label: points over years}. Hidden or missing cells stay white with a dash; hover says why."""
    labels = list(rows)
    years = [year_label(y) for y in next(iter(rows.values()))["year"]]
    z = [[v if pd.notna(v) else None for v in pts["value"]] for pts in rows.values()]
    hover = [hover_lines(pts, noun) for pts in rows.values()]
    top = max((v for row in z for v in row if v is not None), default=1) or 1
    fig = go.Figure(go.Heatmap(
        z=z, x=years, y=labels, colorscale=SEQUENTIAL, zmin=0, zmax=top, showscale=False, xgap=2, ygap=2,
        customdata=hover, hovertemplate="<b>%{y}</b> · %{x}<br>%{customdata}<extra></extra>"))
    for i, row in enumerate(z):
        for j, v in enumerate(row):
            fig.add_annotation(x=years[j], y=labels[i], showarrow=False, font=dict(
                size=12, color="white" if v is not None and v > 0.55 * top else INK),
                text=share_text(v) if v is not None else "–")
    style(fig, height=30 * len(labels) + 50)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", tickfont=dict(color=INK, size=13),
                     tickformat="", rangemode=None)
    fig.update_xaxes(side="top", linecolor="rgba(0,0,0,0)")
    fig.update_layout(margin=dict(l=4, r=4, t=30, b=4), plot_bgcolor="white")
    return fig
