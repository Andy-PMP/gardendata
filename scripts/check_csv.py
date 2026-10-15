"""Print the CSV schema, categorical value counts, and any unparsed planting windows.

Usage: python scripts/check_csv.py [path/to/seeds.csv]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from src.data import COLUMNS, CSV_PATH, load_seeds, unparsed_windows  # noqa: E402

path = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PATH

raw = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
print(f"{path}: {len(raw)} rows, {len(raw.columns)} columns\n")
for c in raw.columns:
    blank = (raw[c].str.strip() == "").sum()
    used = "->  " + COLUMNS[c] if c in COLUMNS else "(ignored)"
    print(f"  {c!r:50} blank={blank:<4} {used}")

df = load_seeds(path)
for c in ["Category", "Season", "Method", "Heirloom/Hybrid", "Sun", "Source", "Bin"]:
    print(f"\n== {c}")
    print(df[c].value_counts().to_string())

for c in ["Spring Window", "Fall Window"]:
    print(f"\n== {c}")
    print(df[c].value_counts().to_string())

bad = unparsed_windows(df)
print(f"\nUnparsed windows: {len(bad)}")
for s in bad:
    print("  ", repr(s))
sys.exit(1 if bad else 0)
