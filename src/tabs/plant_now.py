"""Plant Now: varieties whose Raleigh window contains today, plus what opens soon.

Rendered as cards (they read well on a phone). Cards are capped and paged with a
"Show more" button: hundreds of Dash components at once is slow to mount.
"""
from datetime import timedelta

import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from src.data import days_until_start, load_seeds, today_local, window_contains

SOON_DAYS = 30
PAGE = 48
SOON_CAP = 24

FRACTIONS = {0.125: "⅛", 0.25: "¼", 0.375: "⅜", 0.5: "½", 0.75: "¾"}


def fmt_depth(x):
    """0.25 -> '¼″', 1.5 -> '1½″', 2 -> '2″'."""
    if x is None or x != x:
        return None
    whole, frac = int(x), round(x - int(x), 3)
    s = (str(whole) if whole else "") + FRACTIONS.get(frac, "" if not frac else f"{frac:g}"[1:])
    return f"{s or '0'}″"


def layout():
    return html.Div(
        [
            dcc.Interval(id="pn-tick", interval=60 * 60 * 1000),
            html.Div(id="pn-hero", className="hero"),
            dbc.Switch(
                id="pn-indoor",
                label="Include year-round indoor sprouts",
                value=False,
                className="mb-3",
            ),
            html.Div(id="pn-cards", className="seed-grid"),
            html.Div(
                dbc.Button("Show more", id="pn-more", n_clicks=0, className="btn-garden-outline"),
                id="pn-more-wrap",
                className="text-center mt-3",
            ),
            html.H2(f"Opening in the next {SOON_DAYS} days", className="section-title"),
            html.P(id="pn-soon-note", className="text-secondary"),
            html.Div(id="pn-soon", className="seed-grid"),
        ]
    )


def _next_opening(df, today):
    """(days, date, crops) for the next window opening after today."""
    best = {}
    for r in df.to_dict("records"):
        for w in (r["spring_win"], r["fall_win"]):
            n = days_until_start(w, today)
            if n:
                best.setdefault(n, set()).add(r["Crop"])
    if not best:
        return None
    n = min(best)
    return n, (today + timedelta(days=n)), sorted(best[n], key=str.casefold)


def _rows_for(df, today, include_indoor):
    now, soon = [], []
    for r in df.to_dict("records"):
        for label, w, raw in (
            ("Spring", r["spring_win"], r["Spring Window"]),
            ("Fall", r["fall_win"], r["Fall Window"]),
        ):
            if w is None:
                continue
            if w.kind == "year_round":
                if include_indoor and label == "Spring":  # one row, not two
                    now.append(_row(r, "Year-round", "Indoors, any time"))
                continue
            base = _row(r, label, raw)
            if window_contains(w, today):
                now.append(base)
            else:
                n = days_until_start(w, today)
                if n is not None and 0 < n <= SOON_DAYS:
                    soon.append({**base, "Opens in": n})
    now.sort(key=lambda x: x["Crop"].casefold())
    soon.sort(key=lambda x: (x["Opens in"], x["Crop"].casefold()))
    return now, soon


def _row(r, label, raw):
    return {
        **{c: r[c] for c in ("Crop", "Method", "Category", "Days to Maturity", "Bin", "Depth (in)")},
        "Window": label,
        "Dates": raw.replace(" - ", " – "),
    }


def seed_card(x):
    method = "Direct sow" if x["Method"] == "Direct" else x["Method"]
    meta = [method, f"{x['Days to Maturity']} days"]
    depth = fmt_depth(x["Depth (in)"])
    if depth:
        meta.append(f"{depth} deep")
    when = x["Dates"] if "Opens in" not in x else f"Opens in {x['Opens in']} days · {x['Dates']}"
    return html.Div(
        [
            html.Div(
                [
                    html.Span([html.Span(className=f"dot dot-{x['Window'].lower()}"), when],
                              className="window-chip"),
                    html.Span(x["Category"], className="cat-chip"),
                ],
                className="seed-card-top",
            ),
            html.H3(x["Crop"], className="seed-name"),
            html.Div(" · ".join(meta), className="seed-meta"),
            html.Div(["Bin ", html.B(x["Bin"])], className="seed-bin"),
        ],
        className="seed-card",
    )


def _hero(today, now, soon, nxt):
    spring = sum(1 for x in now if x["Window"] == "Spring")
    fall = sum(1 for x in now if x["Window"] == "Fall")
    indoor = len(now) - spring - fall
    parts = [f"{n} {lbl}" for n, lbl in ((spring, "spring"), (fall, "fall"), (indoor, "indoor")) if n]
    if now:
        big, unit = str(len(now)), "packet ready to sow" if len(now) == 1 else "packets ready to sow"
        detail = " · ".join(parts)
    else:
        big, unit, detail = "0", "packets in an outdoor window today", ""

    side = None
    if soon:
        side = [html.Span("Next 30 days", className="hero-side-label"),
                html.Span(f"{len(soon)} windows open", className="hero-side-value")]
    elif nxt:
        n, d, crops = nxt
        side = [html.Span("Next window opens", className="hero-side-label"),
                html.Span(f"{d:%b} {d.day}", className="hero-side-value"),
                html.Span(f"in {n} days · {len(crops)} crops", className="hero-side-sub")]

    return [
        html.Div(
            [
                html.Div(f"{today:%A}, {today:%B} {today.day}", className="hero-eyebrow"),
                html.Div([html.Span(big, className="hero-num"), html.Span(unit, className="hero-unit")],
                         className="hero-line"),
                html.Div(detail, className="hero-detail") if detail else None,
            ],
            className="hero-main",
        ),
        html.Div(side, className="hero-side") if side else None,
    ]


def register_callbacks(app):
    @app.callback(
        Output("pn-hero", "children"),
        Output("pn-cards", "children"),
        Output("pn-more-wrap", "style"),
        Output("pn-more", "children"),
        Output("pn-soon", "children"),
        Output("pn-soon-note", "children"),
        Input("pn-tick", "n_intervals"),
        Input("pn-indoor", "value"),
        Input("pn-more", "n_clicks"),
    )
    def update(_, indoor, more):
        df = load_seeds()
        today = today_local()
        now, soon = _rows_for(df, today, bool(indoor))
        nxt = None if soon else _next_opening(df, today)

        limit = PAGE * (1 + (more or 0))
        cards = [seed_card(x) for x in now[:limit]]
        if not now:
            cards = [html.P("Nothing is in an outdoor planting window today.", className="empty")]
        remaining = len(now) - limit
        more_style = {"display": "block" if remaining > 0 else "none"}
        more_label = f"Show {min(PAGE, remaining)} more of {remaining}" if remaining > 0 else ""

        if soon:
            note = "" if len(soon) <= SOON_CAP else (
                f"Showing the first {SOON_CAP} of {len(soon)}. The Calendar tab has the full picture.")
        elif nxt:
            n, d, crops = nxt
            note = (f"Nothing opens in the next {SOON_DAYS} days. Next up on {d:%b} {d.day}: "
                    f"{', '.join(crops[:3])}{' and more' if len(crops) > 3 else ''}.")
        else:
            note = ""

        return (_hero(today, now, soon, nxt), cards, more_style, more_label,
                [seed_card(x) for x in soon[:SOON_CAP]], note)
