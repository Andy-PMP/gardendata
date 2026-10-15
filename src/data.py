"""Load the seed inventory CSV and parse Raleigh planting windows."""
from __future__ import annotations

import calendar
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

log = logging.getLogger(__name__)

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "seeds.csv"
TZ = ZoneInfo("America/New_York")

# Raw CSV header -> clean name. The "(Enriched)" columns hold the populated data;
# the original Days to Maturity / Planting Method columns are empty.
COLUMNS = {
    "Crop Name": "Crop",
    "Variety (if known)": "Variety",
    "Seed Source": "Source",
    "Current Storage Bin": "Bin",
    "Category": "Category",
    "Sun Requirements": "Sun",
    "Planting Method (Enriched)": "Method",
    "Days to Maturity (Enriched)": "Days to Maturity",
    "Spacing (inches)": "Spacing (in)",
    "Seed Depth (inches)": "Depth (in)",
    "Heirloom/Hybrid": "Heirloom/Hybrid",
    "Season Type": "Season",
    "Raleigh Spring Planting": "Spring Window",
    "Raleigh Fall Planting": "Fall Window",
}

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_name) if m})

_RANGE_RE = re.compile(
    r"^([A-Za-z]{3,9})\.?\s*(\d{1,2})\s*[-–—]\s*([A-Za-z]{3,9})\.?\s*(\d{1,2})$"
)


@dataclass(frozen=True)
class Window:
    kind: str  # "range" | "year_round" | "unparsed"
    start: tuple[int, int] | None = None  # (month, day)
    end: tuple[int, int] | None = None
    raw: str = ""


def parse_window(s) -> Window | None:
    """Parse 'Mar 1 - May 1', 'Year-round indoors' or 'N/A'."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    text = str(s).strip()
    if not text or text.lower() in {"n/a", "na", "none", "-"}:
        return None
    if text.lower().startswith("year-round") or text.lower().startswith("year round"):
        return Window("year_round", raw=text)
    m = _RANGE_RE.match(text)
    if m:
        m1, d1 = MONTHS.get(m.group(1).lower()), int(m.group(2))
        m2, d2 = MONTHS.get(m.group(3).lower()), int(m.group(4))
        if m1 and m2:
            return Window("range", (m1, d1), (m2, d2), raw=text)
    log.warning("Unparsed planting window: %r", text)
    return Window("unparsed", raw=text)


def window_contains(w: Window | None, d: date) -> bool:
    """True if the (month, day) of d falls inside w, inclusive. Handles year wrap."""
    if w is None or w.kind == "unparsed":
        return False
    if w.kind == "year_round":
        return True
    md = (d.month, d.day)
    if w.start <= w.end:
        return w.start <= md <= w.end
    return md >= w.start or md <= w.end


def half_month_slot(month: int, day: int) -> int:
    """0..23: (month-1)*2 for days 1-15, +1 for 16-end."""
    return (month - 1) * 2 + (0 if day <= 15 else 1)


def window_half_months(w: Window | None) -> set[int]:
    """Half-month slots (0..23) the window overlaps."""
    if w is None or w.kind == "unparsed":
        return set()
    if w.kind == "year_round":
        return set(range(24))
    a, b = half_month_slot(*w.start), half_month_slot(*w.end)
    if a <= b:
        return set(range(a, b + 1))
    return set(range(a, 24)) | set(range(0, b + 1))


def days_until_start(w: Window | None, d: date) -> int | None:
    """Days from d until the window next opens (0 if it opens today)."""
    if w is None or w.kind != "range":
        return None
    start = date(d.year, *w.start)
    if start < d:
        start = date(d.year + 1, *w.start)
    return (start - d).days


def today_local() -> date:
    return datetime.now(TZ).date()


def _min_days(v) -> float | None:
    """'7-14' -> 7, '90' -> 90; used for numeric sorting."""
    m = re.match(r"\s*(\d+)", str(v))
    return float(m.group(1)) if m else None


_cache: pd.DataFrame | None = None


def load_seeds(path: Path = CSV_PATH) -> pd.DataFrame:
    global _cache
    if _cache is not None and path == CSV_PATH:
        return _cache

    raw = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = [c for c in COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    df = raw[list(COLUMNS)].rename(columns=COLUMNS)
    for c in df.columns:
        df[c] = df[c].str.strip()

    df["Variety"] = df["Variety"].replace("", pd.NA)
    df["Spacing (in)"] = pd.to_numeric(df["Spacing (in)"], errors="coerce")
    df["Depth (in)"] = pd.to_numeric(df["Depth (in)"], errors="coerce")
    df["Days (min)"] = df["Days to Maturity"].map(_min_days)

    # Grouping key: same crop regardless of case ("Garden sage" / "Garden Sage").
    df["Crop Key"] = df["Crop"].str.casefold()

    df["spring_win"] = df["Spring Window"].map(parse_window)
    df["fall_win"] = df["Fall Window"].map(parse_window)
    df["Year-round"] = df.apply(
        lambda r: any(w is not None and w.kind == "year_round" for w in (r.spring_win, r.fall_win)),
        axis=1,
    )

    if path == CSV_PATH:
        _cache = df
    return df


def unparsed_windows(df: pd.DataFrame) -> list[str]:
    out = set()
    for col in ("spring_win", "fall_win"):
        out |= {w.raw for w in df[col] if w is not None and w.kind == "unparsed"}
    return sorted(out)
