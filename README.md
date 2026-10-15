# Garden Seed Inventory

A Plotly Dash dashboard for a 377-packet seed collection, tuned to Raleigh, NC (USDA Zone 7b).

| Tab | What it shows |
|---|---|
| **Plant Now** | Cards for every packet whose spring or fall window includes today (Eastern time), with sowing method, depth and storage bin, plus windows opening in the next 30 days. A toggle adds the year-round indoor sprouts. |
| **Inventory** | The full table, filterable by category, season type, planting method and heirloom status, with text search over crop, variety, source and bin. Download the filtered rows as CSV. |
| **Charts** | Packet counts by category, seed source, season type, and heirloom vs hybrid. |
| **Calendar** | One row per crop, 12 months split into early/late halves, with spring, fall and year-round windows and a marker for today. |

The header's sun/moon button switches light and dark mode. It defaults to the device's setting and remembers your choice in the browser. On phones, the Inventory and Calendar filters fold behind a **Filters** button.

## Project layout

```
app.py               Dash app; exposes `server` for gunicorn
src/data.py          CSV loading, column mapping, planting-window parsing
src/tabs/*.py        One module per tab: layout() + register_callbacks(app)
src/theme.py         Colors and fonts shared by the Python side (charts, tables, calendar)
assets/style.css     Site styling; its :root and dark tokens mirror src/theme.py (auto-loaded by Dash)
assets/theme.js      Light/dark toggle (clientside callback)
data/seeds.csv       The inventory
scripts/check_csv.py Schema report + list of unparseable planting windows
tests/               Parser tests and a smoke test against the real CSV
```

## Data notes

`src/data.py` maps the raw CSV headers to short names (`COLUMNS`). A few things worth knowing:

- Planting method and days to maturity come from the **`(Enriched)`** columns. The original `Planting Method (Direct/Transplant)` and `Days to Maturity` columns are empty, as are `New Storage Bin`, `Planting season` and `Notes`. Those are ignored.
- Planting windows must look like `Mar 1 - May 1`, `N/A`, or `Year-round indoors`. Full month names, en dashes and missing spaces are also accepted, and so are windows that wrap the new year (`Nov 15 - Feb 1`).
- After editing the CSV, run `python scripts/check_csv.py`. It exits non-zero and lists any window text it couldn't parse. Rows with an unparsed window don't show on Plant Now or the calendar.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt pytest
python app.py                   # http://127.0.0.1:8050
pytest
```

Set `DASH_DEBUG=1` for hot reload and the Dash dev tools. gunicorn doesn't run on Windows, but `python app.py` is all you need locally.

## Deploy to Render (free tier)

1. Push this folder to a GitHub (or GitLab) repo, including `data/seeds.csv`. Leave out `.venv/`, which `.gitignore` already does.
2. In the Render dashboard choose **New → Blueprint**, connect the repo, and Render reads `render.yaml`:
   - build: `pip install -r requirements.txt`
   - start: `gunicorn app:server --workers 2 --bind 0.0.0.0:$PORT`
   - Python 3.12.7, free plan
3. Click **Apply**. The first build takes a few minutes, and the URL looks like `https://garden-seeds.onrender.com`.

Without Blueprints, use **New → Web Service** with the same build and start commands and set the env var `PYTHON_VERSION=3.12.7`. The `Procfile` holds the same start command for Heroku-style hosts.

**Free-tier behavior:** the service sleeps after about 15 minutes without traffic, and the next visit takes about 30–60 seconds to wake it. To update the data, commit a new `data/seeds.csv` and push. Render redeploys automatically.
