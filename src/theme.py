"""Shared colors and fonts, light and dark.

Keep in sync with the :root / [data-theme="dark"] tokens in assets/style.css.
Python-rendered pieces (Plotly charts, the calendar iframe) take a theme name and
look their colors up here; everything else is styled by CSS variables.
"""

FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,500;9..144,600&"
    "family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap"
)
SANS = "'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
SERIF = "Fraunces, Georgia, serif"

PALETTES = {
    "light": dict(
        bg="#f6f2e8",        # linen page
        surface="#fffdf8",   # cards, tables, chart plot area
        ink="#22301f",       # deep green-black text
        ink_2="#5b5a4e",
        muted="#8a877b",
        line="#e6e0d0",
        baseline="#cfc8b4",
        empty="#efeadd",     # empty calendar track
        hover="#f3efe3",
        bar="#2f5d3a",       # single-series chart bars (forest)
        # Window colors, validated against surface, all pairs:
        # CVD ΔE ≥ 9.1, normal-vision ΔE ≥ 20.8, contrast ≥ 3:1.
        spring="#009488",    # teal: new growth
        fall="#cc6235",      # terracotta
        year_round="#8a5fb0",  # plum
    ),
    "dark": dict(
        bg="#141a14",
        surface="#1d241d",
        ink="#ece6d6",
        ink_2="#b9b4a3",
        muted="#8c8878",
        line="#2f382e",
        baseline="#46503f",
        empty="#283028",
        hover="#252e25",
        bar="#7fb28a",       # sage
        # Stepped for the dark surface, all pairs: normal-vision ΔE ≥ 19.9,
        # contrast ≥ 3:1. Teal↔plum CVD ΔE 7.9 sits in the 6–8 band, which is
        # allowed because position also separates them on the calendar
        # (year-round bars span the whole row; spring bars sit Feb–Jun).
        spring="#16a092",
        fall="#d86c40",
        year_round="#a07bc8",
    ),
}


def palette(theme):
    return PALETTES["dark" if theme == "dark" else "light"]
