"""Charts: inventory counts by category, source, season type, heirloom status."""
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from src.data import load_seeds
from src.theme import SANS, palette

TOP_SOURCES = 15
ROW_PX = 26
CHARTS = [  # (id, title, column, top-N)
    ("ch-category", "By category", "Category", None),
    ("ch-source", "By seed source", "Source", TOP_SOURCES),
    ("ch-season", "By season type", "Season", None),
    ("ch-heirloom", "Heirloom vs hybrid", "Heirloom/Hybrid", None),
]


def _counts(col, top=None):
    vc = load_seeds()[col].value_counts()
    if top and len(vc) > top:
        vc = pd.concat([vc.head(top), pd.Series({"Other": vc.iloc[top:].sum()})])
    return vc


def bar(vc, theme="light"):
    # Single series: one color, no legend; the card title names it.
    p = palette(theme)
    vc = vc.iloc[::-1]  # largest on top in a horizontal chart
    fig = go.Figure(
        go.Bar(
            x=vc.values,
            y=vc.index,
            orientation="h",
            marker=dict(color=p["bar"], cornerradius=4, line=dict(width=0)),
            text=vc.values,
            textposition="outside",
            textfont=dict(color=p["ink_2"], size=12),
            cliponaxis=False,
            hovertemplate="%{y}: %{x} packets<extra></extra>",
        )
    )
    fig.update_layout(
        height=max(140, 30 + len(vc) * ROW_PX),
        margin=dict(l=4, r=36, t=4, b=24),
        bargap=max(0.15, 1 - 18 / ROW_PX),  # ~18px bars, leftover is air
        plot_bgcolor=p["surface"],
        paper_bgcolor=p["surface"],
        font=dict(family=SANS, color=p["ink_2"], size=12),
        xaxis=dict(showgrid=True, gridcolor=p["line"], gridwidth=1, zeroline=True,
                   zerolinecolor=p["baseline"], tickfont=dict(color=p["muted"]), title=None,
                   fixedrange=True),
        yaxis=dict(showgrid=False, ticks="", automargin=True, title=None, fixedrange=True),
        hoverlabel=dict(bgcolor=p["surface"], bordercolor=p["line"],
                        font=dict(family=SANS, color=p["ink"])),
        showlegend=False,
    )
    return fig


def _card(id_, title, subtitle):
    return dbc.Col(
        html.Div(
            [
                html.H3(title, className="panel-title"),
                html.P(subtitle, className="panel-sub"),
                dcc.Graph(id=id_, config={"displayModeBar": False, "responsive": True}),
            ],
            className="panel",
        ),
        lg=6,
        className="mb-4",
    )


def layout():
    df = load_seeds()
    heirloom_pct = round(100 * (df["Heirloom/Hybrid"] == "Heirloom").mean())
    subtitles = [
        f"{df['Category'].nunique()} categories",
        f"{df['Source'].nunique()} suppliers",
        "Cool- and warm-season annuals, plus perennials",
        f"{heirloom_pct}% heirloom",
    ]
    return dbc.Row(
        [_card(id_, title, sub) for (id_, title, _, _), sub in zip(CHARTS, subtitles)],
        className="pt-2",
    )


def register_callbacks(app):
    @app.callback([Output(id_, "figure") for id_, *_ in CHARTS], Input("theme", "data"))
    def update(theme):
        return [bar(_counts(col, top), theme) for _, _, col, top in CHARTS]
