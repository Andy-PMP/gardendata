"""Inventory: full filterable/searchable table with CSV download."""
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

from src.data import load_seeds
from src.tabs.common import filter_collapse, filter_toggle, make_table, register_toggle

COLS = [
    "Crop", "Variety", "Category", "Source", "Bin", "Method", "Season", "Heirloom/Hybrid",
    "Sun", "Days to Maturity", "Spacing (in)", "Depth (in)", "Spring Window", "Fall Window",
]
FILTERS = [
    ("inv-category", "Category"),
    ("inv-season", "Season"),
    ("inv-method", "Method"),
    ("inv-heirloom", "Heirloom/Hybrid"),
]
SEARCH_COLS = ["Crop", "Variety", "Source", "Bin"]


def _dropdown(id_, col, df):
    return dbc.Col(
        dcc.Dropdown(
            id=id_,
            options=sorted(df[col].dropna().unique()),
            multi=True,
            placeholder=col,
        ),
        md=3,
        sm=6,
        className="mb-2",
    )


def layout():
    df = load_seeds()
    return html.Div(
        [
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(
                                    id="inv-search",
                                    type="search",
                                    placeholder="Search crop, variety, source, bin…",
                                    debounce=True,
                                ),
                                md=6,
                                className="mb-2",
                            ),
                            dbc.Col(
                                [filter_toggle("inv-filter-btn"),
                                 html.Span(id="inv-count", className="text-secondary")],
                                xs=8,
                                md=4,
                                className="d-flex align-items-center gap-2 mb-2",
                            ),
                            dbc.Col(
                                dbc.Button("Download CSV", id="inv-dl-btn", size="sm",
                                           className="btn-garden-outline"),
                                xs=4,
                                md=2,
                                className="text-end mb-2",
                            ),
                        ],
                        className="align-items-center",
                    ),
                    filter_collapse(
                        "inv-filters", dbc.Row([_dropdown(i, c, df) for i, c in FILTERS])
                    ),
                ],
                className="panel filter-panel",
            ),
            dcc.Download(id="inv-dl"),
            html.Div(make_table("inv-table", COLS, nowrap=True, page_size=25),
                     className="panel table-panel"),
        ]
    )


def filter_df(category, season, method, heirloom, search):
    df = load_seeds()
    for col, vals in zip([c for _, c in FILTERS], [category, season, method, heirloom]):
        if vals:
            df = df[df[col].isin(vals)]
    if search:
        q = search.strip().casefold()
        hay = df[SEARCH_COLS].fillna("").agg(" ".join, axis=1).str.casefold()
        df = df[hay.str.contains(q, regex=False)]
    return df.sort_values("Crop Key")


def register_callbacks(app):
    inputs = [Input(i, "value") for i, _ in FILTERS] + [Input("inv-search", "value")]

    @app.callback(
        Output("inv-table", "data"),
        Output("inv-count", "children"),
        Output("inv-filter-btn", "children"),
        *inputs,
    )
    def update(*args):
        df = filter_df(*args)
        total = len(load_seeds())
        active = sum(1 for v in args[: len(FILTERS)] if v)
        label = f"Filters · {active}" if active else "Filters"
        return df[COLS].to_dict("records"), f"Showing {len(df)} of {total}", label

    register_toggle(app, "inv-filter-btn", "inv-filters")

    @app.callback(
        Output("inv-dl", "data"),
        Input("inv-dl-btn", "n_clicks"),
        *[State(i.component_id, "value") for i in inputs],
        prevent_initial_call=True,
    )
    def download(_, *args):
        return dcc.send_data_frame(filter_df(*args)[COLS].to_csv, "seed_inventory.csv", index=False)
