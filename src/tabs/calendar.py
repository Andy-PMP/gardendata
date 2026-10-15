"""Planting calendar: one row per crop across 24 half-months, spring/fall/year-round.

The grid is rendered as one static HTML document in an iframe rather than as Dash
components: ~330 rows as individual html.Div cells is thousands of React components
and freezes the browser. Each row draws one bar per contiguous window instead of
24 cells, which keeps the DOM small too.
"""
import calendar as cal
from html import escape

import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from src.data import half_month_slot, load_seeds, today_local, window_half_months
from src.tabs.common import filter_collapse, filter_toggle, register_toggle
from src.theme import FONTS_URL, SANS, palette


def _crop_rows(categories, seasons, sort_by):
    df = load_seeds()
    if categories:
        df = df[df["Category"].isin(categories)]
    if seasons:
        df = df[df["Season"].isin(seasons)]

    rows = []
    for _, g in df.groupby("Crop Key", sort=False):
        spring, fall, yr = set(), set(), False
        for w in g["spring_win"]:
            if w is not None and w.kind == "year_round":
                yr = True
            else:
                spring |= window_half_months(w)
        for w in g["fall_win"]:
            if w is not None and w.kind == "year_round":
                yr = True
            else:
                fall |= window_half_months(w)
        first = 99 if yr else min(spring | fall, default=99)  # sprouts sort last
        rows.append(
            dict(
                name=g["Crop"].iloc[0],
                n=len(g),
                category=g["Category"].iloc[0],
                spring=spring,
                fall=fall,
                year_round=yr,
                first=first,
                tip=f"Spring: {', '.join(sorted(set(g['Spring Window'])))}"
                f" · Fall: {', '.join(sorted(set(g['Fall Window'])))}",
            )
        )
    key = (lambda r: (r["first"], r["name"].casefold())) if sort_by == "date" else (
        lambda r: r["name"].casefold()
    )
    return sorted(rows, key=key)


def _runs(slots):
    """{4,5,6,20,21} -> [(4, 6), (20, 21)]: contiguous half-month runs."""
    runs, start, prev = [], None, None
    for s in sorted(slots):
        if start is None:
            start = prev = s
        elif s == prev + 1:
            prev = s
        else:
            runs.append((start, prev))
            start = prev = s
    if start is not None:
        runs.append((start, prev))
    return runs


def _bars(row):
    if row["year_round"]:
        return '<i class="yr" style="grid-column:1/25"></i>'
    out = []
    for cls in ("spring", "fall"):
        for a, b in _runs(row[cls]):
            out.append(f'<i class="{cls}" style="grid-column:{a + 1}/{b + 2}"></i>')
    return "".join(out)


# Colors come from _theme_vars(); this sheet only references the variables.
GRID_CSS = f"""
* {{ box-sizing: border-box; }}
html, body {{ margin:0; background:var(--surface); color:var(--ink);
             font:13px {SANS}; }}
.r {{ display:grid; grid-template-columns:minmax(140px, 220px) 1fr; min-width:520px; }}
.r:not(.h):hover {{ background:var(--hover); }}
.h {{ position:sticky; top:0; z-index:3; background:var(--surface);
     border-bottom:1px solid var(--baseline); font-size:12px; font-weight:600; color:var(--ink-2); }}
.n {{ position:sticky; left:0; z-index:2; background:inherit; padding:3px 8px;
     white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.r:not(.h) .n {{ background:var(--surface); }}
.r:not(.h):hover .n {{ background:var(--hover); }}
.m {{ display:grid; grid-template-columns:repeat(12, 1fr); }}
.m span {{ text-align:center; padding:6px 0; border-left:1px solid var(--grid); }}
.m span.now {{ color:var(--ink); text-decoration:underline; }}
.t {{ position:relative; display:grid; grid-template-columns:repeat(24, 1fr);
     align-self:center; height:14px; margin:4px 0; background-color:var(--empty);
     background-image:repeating-linear-gradient(to right, var(--grid) 0 1px, transparent 1px calc(100% / 12)); }}
.t i {{ display:block; height:100%; border-radius:3px; }}
.t i.spring {{ background:var(--spring); }}
.t i.fall {{ background:var(--fall); }}
.t i.yr {{ background:var(--yr); }}
.t::after {{ content:""; position:absolute; top:-4px; bottom:-4px; width:2px;
            left:calc(var(--today) - 1px); background:var(--ink); z-index:1; }}
"""


def _theme_vars(theme):
    p = palette(theme)
    return (
        f":root{{color-scheme:{'dark' if theme == 'dark' else 'light'};"
        f"--surface:{p['surface']};--ink:{p['ink']};--ink-2:{p['ink_2']};--grid:{p['line']};"
        f"--baseline:{p['baseline']};--empty:{p['empty']};--hover:{p['hover']};"
        f"--spring:{p['spring']};--fall:{p['fall']};--yr:{p['year_round']}}}"
    )


def grid_html(rows, today_slot, theme="light"):
    today_month = today_slot // 2 + 1
    today_pct = (today_slot + 0.5) / 24 * 100
    months = "".join(
        f'<span class="{"now" if m == today_month else ""}">{cal.month_abbr[m]}</span>'
        for m in range(1, 13)
    )
    body = []
    for r in rows:
        label = escape(r["name"]) + (f" ×{r['n']}" if r["n"] > 1 else "")
        tip = escape(f"{r['name']} ({r['category']}) · {r['tip']}", quote=True)
        body.append(f'<div class="r" title="{tip}"><div class="n">{label}</div>'
                    f'<div class="t">{_bars(r)}</div></div>')
    return (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f'<link rel="stylesheet" href="{FONTS_URL}"><style>{_theme_vars(theme)}{GRID_CSS}'
        f".t{{--today:{today_pct:.3f}%}}</style></head><body>"
        f'<div class="r h"><div class="n">Crop</div><div class="m">{months}</div></div>'
        + "".join(body)
        + "</body></html>"
    )


def _legend():
    def item(cls, text):
        return html.Span([html.Span(className=f"cal-swatch {cls}"), text], className="me-3")

    return html.Div(
        [item("spring", "Spring window"), item("fall", "Fall window"),
         item("yr", "Year-round indoors"),
         html.Span([html.Span(className="cal-swatch today-key"), "Today"])],
        className="cal-legend",
    )


def layout():
    df = load_seeds()
    return html.Div(
        [
            html.Div(
                [
                    filter_toggle("cal-filter-btn", "Filters & sort"),
                    filter_collapse(
                        "cal-filters",
                        dbc.Row(
                            [
                                dbc.Col(dcc.Dropdown(id="cal-category",
                                                     options=sorted(df["Category"].unique()),
                                                     multi=True, placeholder="Category"),
                                        md=4, className="mb-2"),
                                dbc.Col(dcc.Dropdown(id="cal-season",
                                                     options=sorted(df["Season"].unique()),
                                                     multi=True, placeholder="Season type"),
                                        md=3, className="mb-2"),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="cal-sort",
                                        options=[{"label": "Sort A–Z", "value": "name"},
                                                 {"label": "Sort by first sowing", "value": "date"}],
                                        value="date",
                                        inline=True,
                                    ),
                                    md=5,
                                    className="d-flex align-items-center mb-2",
                                ),
                            ],
                        ),
                    ),
                    _legend(),
                    html.P(id="cal-count", className="text-secondary small mb-0"),
                ],
                className="panel filter-panel",
            ),
            html.Iframe(id="cal-grid", className="cal-frame"),
        ]
    )


def register_callbacks(app):
    @app.callback(
        Output("cal-grid", "srcDoc"),
        Output("cal-count", "children"),
        Input("cal-category", "value"),
        Input("cal-season", "value"),
        Input("cal-sort", "value"),
        Input("theme", "data"),
    )
    def update(categories, seasons, sort_by, theme):
        today = today_local()
        rows = _crop_rows(categories, seasons, sort_by)
        note = f"{len(rows)} crops. ×N means N packets of that crop; hover a row for exact dates."
        return grid_html(rows, half_month_slot(today.month, today.day), theme), note

    register_toggle(app, "cal-filter-btn", "cal-filters")
