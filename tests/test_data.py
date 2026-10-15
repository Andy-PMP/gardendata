from datetime import date

import pytest

from src.data import (
    days_until_start,
    load_seeds,
    parse_window,
    unparsed_windows,
    window_contains,
    window_half_months,
)


def test_parse_range():
    w = parse_window("Mar 1 - May 1")
    assert w.kind == "range" and w.start == (3, 1) and w.end == (5, 1)


@pytest.mark.parametrize("s", ["Mar 1-May 1", "  Mar 1 – May 1 ", "March 1 - May 1", "Mar. 1 - May 1"])
def test_parse_range_variants(s):
    w = parse_window(s)
    assert w.kind == "range" and w.start == (3, 1) and w.end == (5, 1)


@pytest.mark.parametrize("s", ["N/A", "", "  ", None, float("nan")])
def test_parse_none(s):
    assert parse_window(s) is None


def test_parse_year_round():
    assert parse_window("Year-round indoors").kind == "year_round"


def test_parse_garbage():
    assert parse_window("whenever").kind == "unparsed"


def test_contains_boundaries():
    w = parse_window("Aug 15 - Oct 1")
    assert window_contains(w, date(2026, 8, 15))
    assert window_contains(w, date(2026, 10, 1))
    assert not window_contains(w, date(2026, 8, 14))
    assert not window_contains(w, date(2026, 10, 2))


def test_contains_wrap():
    w = parse_window("Nov 15 - Feb 1")
    assert window_contains(w, date(2026, 12, 25))
    assert window_contains(w, date(2026, 1, 10))
    assert not window_contains(w, date(2026, 3, 1))


def test_contains_none_and_year_round():
    assert not window_contains(None, date(2026, 5, 1))
    assert window_contains(parse_window("Year-round indoors"), date(2026, 5, 1))


def test_half_months():
    # Mar 1 (slot 4) through May 1 (slot 8)
    assert window_half_months(parse_window("Mar 1 - May 1")) == {4, 5, 6, 7, 8}
    # Apr 15 is early April (slot 6); May 31 late May (slot 9)
    assert window_half_months(parse_window("Apr 15 - May 31")) == {6, 7, 8, 9}
    assert window_half_months(parse_window("Nov 16 - Jan 10")) == {21, 22, 23, 0}
    assert window_half_months(parse_window("Year-round indoors")) == set(range(24))
    assert window_half_months(None) == set()


def test_days_until_start():
    w = parse_window("Nov 1 - Dec 1")
    assert days_until_start(w, date(2026, 10, 15)) == 17
    assert days_until_start(w, date(2026, 11, 1)) == 0
    assert days_until_start(parse_window("Mar 1 - May 1"), date(2026, 10, 15)) == 137


def test_real_csv_loads_cleanly():
    df = load_seeds()
    assert len(df) == 377
    assert unparsed_windows(df) == []
    assert set(df["Method"]) <= {"Direct", "Transplant"}
    assert not df["Crop"].str.endswith(" ").any()
