"""Garden seed inventory dashboard (Raleigh, NC · Zone 7b)."""
import os

import dash_bootstrap_components as dbc
from dash import ClientsideFunction, Dash, Input, Output, dcc, html

from src.data import load_seeds
from src.tabs import calendar, charts, inventory, plant_now
from src.theme import FONTS_URL

load_seeds()  # fail fast on a bad CSV at startup, not on first request

app = Dash(
    __name__,
    title="Garden Seed Inventory",
    external_stylesheets=[dbc.themes.BOOTSTRAP, FONTS_URL],
    suppress_callback_exceptions=True,
)
server = app.server  # gunicorn entry point: gunicorn app:server

# Set the theme before first paint (saved choice, else the OS setting) so dark-mode
# users don't get a flash of the light page. assets/theme.js toggles it later.
app.index_string = app.index_string.replace(
    "{%css%}",
    """{%css%}
        <script>
        (function () {
            var t = null;
            try { t = localStorage.getItem("garden-theme"); } catch (e) {}
            if (t !== "light" && t !== "dark") {
                t = window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
            }
            document.documentElement.setAttribute("data-theme", t);
            document.documentElement.setAttribute("data-bs-theme", t);
        })();
        </script>""",
)


def tab(content, label, value):
    return dcc.Tab(content, label=label, value=value, className="g-tab",
                   selected_className="g-tab--selected")


header = html.Header(
    dbc.Container(
        html.Div(
            [
                html.Div(
                    [
                        html.Img(src=app.get_asset_url("sprout.svg"), className="brand-mark", alt=""),
                        html.Div(
                            [
                                html.H1("Garden Seed Inventory", className="brand-title"),
                                html.P(f"{len(load_seeds())} packets · Raleigh, NC · Zone 7b",
                                       className="brand-sub"),
                            ]
                        ),
                    ],
                    className="brand",
                ),
                html.Button(
                    [
                        html.Img(src=app.get_asset_url("moon.svg"), className="icon-moon", alt=""),
                        html.Img(src=app.get_asset_url("sun.svg"), className="icon-sun", alt=""),
                    ],
                    id="theme-toggle",
                    n_clicks=0,
                    className="theme-toggle",
                    title="Switch light/dark",
                    **{"aria-label": "Switch between light and dark mode"},
                ),
            ],
            className="header-row",
        ),
        fluid="lg",
    ),
    className="site-header",
)

app.layout = html.Div(
    [
        dcc.Store(id="theme"),  # "light" | "dark", the theme currently applied
        header,
        dbc.Container(
            dcc.Tabs(
                [
                    tab(plant_now.layout(), "Plant Now", "now"),
                    tab(inventory.layout(), "Inventory", "inventory"),
                    tab(charts.layout(), "Charts", "charts"),
                    tab(calendar.layout(), "Calendar", "calendar"),
                ],
                value="now",
                className="g-tabs",
                parent_className="g-tabs-parent",
                content_className="g-tab-content",
                mobile_breakpoint=0,  # keep tabs in one row on phones
            ),
            fluid="lg",
            className="pb-5",
        ),
    ]
)

# Runs in the browser: reports the theme on load, flips and saves it on click.
app.clientside_callback(
    ClientsideFunction(namespace="garden", function_name="toggleTheme"),
    Output("theme", "data"),
    Input("theme-toggle", "n_clicks"),
)

for t in (plant_now, inventory, charts, calendar):
    t.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=os.environ.get("DASH_DEBUG") == "1", port=int(os.environ.get("PORT", 8050)))
