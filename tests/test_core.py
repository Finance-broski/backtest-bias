"""backtest-bias v0.1 regression: synthetic panels with known truth; every verdict must match.
Run: python -m pytest tests/ -q   (or python tests/test_core.py)"""
import sys, os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtest_bias import (assert_integrity, check_survivorship, dead_name_ratio, to_wide)

RNG = np.random.default_rng(7)
DAYS = pd.bdate_range("2015-01-01", "2024-12-31")


def _walk(n):
    return 100 * np.exp(np.cumsum(RNG.normal(0.0003, 0.02, n)))


def survivor_panel(n_names=30):
    """Everyone lives to the end: the survivor-only signature."""
    return pd.DataFrame({f"S{i:03d}": _walk(len(DAYS)) for i in range(n_names)}, index=DAYS)


def honest_panel(n_names=30, death_frac=0.3):
    """30% of names die somewhere in the middle: what real history looks like."""
    df = survivor_panel(n_names)
    dead = list(df.columns[: int(n_names * death_frac)])
    for i, c in enumerate(dead):
        cut = DAYS[len(DAYS) // 3 + i * 40]
        df.loc[df.index > cut, c] = np.nan
    return df, dead


def test_survivor_only_flagged_severe():
    rep = check_survivorship(survivor_panel())
    assert rep.severity == "severe" and rep.survivor_only_suspected
    assert rep.n_dead_in_window == 0
    lo, hi = rep.estimated_bias_pp_per_year()
    assert hi == 2.5 and lo == 0.8
    assert "survivor-only signature" in rep.summary()


def test_honest_panel_clean():
    df, dead = honest_panel()
    rep = check_survivorship(df)
    assert rep.severity == "clean" and not rep.survivor_only_suspected
    assert rep.n_dead_in_window == len(dead)
    assert set(rep.dead_symbols) == set(dead)
    assert rep.estimated_bias_pp_per_year() == (0.0, 0.0)


def test_dead_name_ratio_numbers():
    df, dead = honest_panel(30, 0.3)
    r = dead_name_ratio(df)
    assert abs(r - len(dead) / 30) < 1e-9
    assert dead_name_ratio(survivor_panel()) == 0.0


def test_assert_integrity_gate():
    with pytest.raises(AssertionError, match="survivorship gate failed"):
        assert_integrity(survivor_panel())
    df, _ = honest_panel()
    assert_integrity(df)  # should not raise


def test_long_format_sniffing():
    df, dead = honest_panel(25)
    long = df.stack().rename("close").reset_index()
    long.columns = ["Date", "Ticker", "Close"]
    rep = check_survivorship(long)
    assert rep.n_symbols == 25 and rep.n_dead_in_window == len(dead)
    w = to_wide(long)
    assert w.shape[1] == 25 and isinstance(w.index, pd.DatetimeIndex)


def test_short_window_only_warns():
    short = survivor_panel().iloc[:300]
    rep = check_survivorship(short)
    assert rep.severity == "warn" and not rep.survivor_only_suspected


if __name__ == "__main__":
    for fn in [test_survivor_only_flagged_severe, test_honest_panel_clean,
               test_dead_name_ratio_numbers, test_assert_integrity_gate,
               test_long_format_sniffing, test_short_window_only_warns]:
        fn()
        print(f"  PASS {fn.__name__}")
    print("backtest-bias v0.1: GREEN")


# ---- v0.1.1 hostile-audit regressions (2026-07-09): every attack that landed, kept forever ----

def test_calendar_padding_cannot_mask():
    """THE masking bug: padded future calendar made everyone look dead -> survivor panels
    could read clean. Death is now measured against the DATA's end, not the calendar's."""
    df, dead = honest_panel()
    padded = df.reindex(pd.bdate_range(DAYS[0], DAYS[-1] + pd.Timedelta(days=180)))
    assert abs(dead_name_ratio(padded) - dead_name_ratio(df)) < 1e-9
    surv_padded = survivor_panel().reindex(pd.bdate_range(DAYS[0], DAYS[-1] + pd.Timedelta(days=180)))
    assert check_survivorship(surv_padded).severity == "severe"   # still caught


def test_yyyymmdd_integer_dates():
    df, dead = honest_panel(10)
    long = df.stack().rename("close").reset_index()
    long.columns = ["date", "symbol", "close"]
    long["date"] = long["date"].dt.strftime("%Y%m%d").astype(int)
    rep = check_survivorship(long)
    assert 8 < rep.window_years < 11
    assert rep.n_dead_in_window == len(dead)


def test_single_column_wide():
    one = pd.DataFrame({"RELIANCE": _walk(len(DAYS))}, index=DAYS)
    assert dead_name_ratio(one) == 0.0


def test_empty_frame_friendly():
    with pytest.raises(ValueError, match="empty frame"):
        check_survivorship(pd.DataFrame())


def test_adj_close_sniffed():
    df, dead = honest_panel(8)
    long = df.stack().rename("x").reset_index()
    long.columns = ["Date", "Symbol", "Adj Close"]
    assert check_survivorship(long).n_symbols == 8


def test_multiindex_columns_flatten():
    df = survivor_panel(6)
    df.columns = pd.MultiIndex.from_product([["Close"], list(df.columns)])
    rep = check_survivorship(df)
    assert rep.n_symbols == 6


def test_horizon_matched_expectation_in_detail():
    rep = check_survivorship(survivor_panel())          # ~10y window
    assert "measured" in rep.detail and "%" in rep.detail
