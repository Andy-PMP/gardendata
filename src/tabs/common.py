"""Shared table styling, column definitions and phone filter toggles.

Colors are CSS variables (assets/style.css) so tables follow the light/dark theme.
"""
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table


TABLE_STYLE = dict(
    style_table={"overflowX": "auto"},
    style_cell={
        "fontFamily": "var(--sans)",
        "fontSize": "14px",
        "color": "var(--ink)",
        "backgroundColor": "var(--surface)",
        "padding": "8px 12px",
        "textAlign": "left",
        "whiteSpace": "normal",
        "height": "auto",
        "border": "none",
        "borderBottom": "1px solid var(--line)",
    },
    style_header={
        "fontWeight": "600",
        "fontSize": "13px",
        "backgroundColor": "var(--forest-soft)",
        "borderBottom": "1px solid var(--line)",
    },
    style_data_conditional=[
        {"if": {"state": "active"}, "backgroundColor": "var(--forest-soft)", "border": "none"},
        {"if": {"column_id": "Crop"}, "fontWeight": "500"},
    ],
)

NUMERIC = {"Spacing (in)", "Depth (in)"}


def columns(names):
    return [
        {"name": n, "id": n, "type": "numeric" if n in NUMERIC else "text"} for n in names
    ]


def make_table(id_, cols, nowrap=False, **kw):
    style = dict(TABLE_STYLE)
    if nowrap:  # one line per row; wide tables scroll horizontally
        style["style_cell"] = {**style["style_cell"], "whiteSpace": "nowrap"}
    return dash_table.DataTable(
        id=id_, columns=columns(cols), data=[], sort_action="native", **style, **kw
    )


def filter_toggle(btn_id, label="Filters"):
    """Phone-only button that opens/closes a filter_collapse (hidden at md and up)."""
    return dbc.Button(label, id=btn_id, n_clicks=0, size="sm",
                      className="btn-garden-outline d-md-none filter-toggle")


def filter_collapse(collapse_id, children):
    """Collapsed on phones until toggled; always shown at md and up (see .filter-collapse CSS)."""
    return dbc.Collapse(children, id=collapse_id, is_open=False, className="filter-collapse")


def register_toggle(app, btn_id, collapse_id):
    @app.callback(
        Output(collapse_id, "is_open"),
        Input(btn_id, "n_clicks"),
        State(collapse_id, "is_open"),
        prevent_initial_call=True,
    )
    def _toggle(_, is_open):
        return not is_open
