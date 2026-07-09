"""backtest-bias core: survivorship checks for financial price panels.

Design rules:
- The library checks YOUR data. It ships no market data of its own.
- The packaged benchmarks are published, measured numbers (sources in REFERENCES) so a finding
  can be quantified, not just flagged.
- Anything the library cannot judge honestly, it says so instead of guessing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Published, measured benchmarks that motivated this library (see README for the write-ups).
# These quantify what a survivor-only panel typically does to a backtest.
REFERENCES = {
    "IN": {
        "death_rate_range": (0.10, 0.30),   # fraction of a mid/large-cap universe that stops
                                            # trading over a multi-year window (measured 2013 &
                                            # 2015 vintages, Indian top-500)
        "bias_pp_per_year": (0.8, 2.5),     # measured EW return inflation from survivor-only
                                            # universes, vintage-dependent
        "construction_dependence": "+10% terminal wealth (cap-weighted) to +43% (equal-weight) "
                                   "measured on one widely used dataset, 2010-2021",
    },
}


def to_wide(prices: pd.DataFrame,
            date_col: str = None, symbol_col: str = None, value_col: str = None) -> pd.DataFrame:
    """Accept a wide panel (DatetimeIndex x symbols) or a long frame (date/symbol/price columns)
    and return wide. Column names are sniffed case-insensitively when not given."""
    if isinstance(prices.index, pd.DatetimeIndex) and prices.shape[1] > 1 and \
            not any(str(c).lower() in ("symbol", "ticker") for c in prices.columns):
        return prices.sort_index()
    df = prices.copy()
    cols = {str(c).lower(): c for c in df.columns}
    date_col = date_col or next((cols[k] for k in ("date", "dt", "day", "time") if k in cols), None)
    symbol_col = symbol_col or next((cols[k] for k in ("symbol", "ticker", "scrip", "name") if k in cols), None)
    value_col = value_col or next((cols[k] for k in ("close", "adj_close", "price", "px", "nav") if k in cols), None)
    if not (date_col and symbol_col and value_col):
        raise ValueError("could not sniff long-format columns; pass date_col/symbol_col/value_col")
    df[date_col] = pd.to_datetime(df[date_col])
    return df.pivot_table(index=date_col, columns=symbol_col, values=value_col, aggfunc="last").sort_index()


def dead_name_ratio(prices: pd.DataFrame, gap_days: int = 45, min_obs: int = 60,
                    as_of=None, **to_wide_kw) -> float:
    """Fraction of symbols whose data ENDS well before the panel does (i.e. names that died and
    were kept — the thing survivor-only panels don't have). 0.0 = your panel only contains
    the living."""
    w = to_wide(prices, **to_wide_kw)
    end = pd.Timestamp(as_of) if as_of is not None else w.index.max()
    counted = dead = 0
    for c in w.columns:
        s = w[c].dropna()
        if len(s) < min_obs:
            continue
        counted += 1
        if s.index.max() < end - pd.Timedelta(days=gap_days):
            dead += 1
    if counted == 0:
        raise ValueError(f"no symbol has >= {min_obs} observations; nothing to judge")
    return dead / counted


@dataclass
class SurvivorshipReport:
    n_symbols: int
    n_dead_in_window: int
    dead_ratio: float
    window_years: float
    survivor_only_suspected: bool
    severity: str                      # "clean" | "warn" | "severe"
    detail: str
    market: str = "IN"
    dead_symbols: list = field(default_factory=list)

    def estimated_bias_pp_per_year(self):
        """Published measured band for what a survivor-only panel adds to EW returns."""
        ref = REFERENCES.get(self.market)
        return ref["bias_pp_per_year"] if (ref and self.survivor_only_suspected) else (0.0, 0.0)

    def summary(self) -> str:
        lines = [f"survivorship check: {self.n_symbols} symbols over {self.window_years:.1f}y, "
                 f"{self.n_dead_in_window} died in-window ({self.dead_ratio:.0%})",
                 f"verdict: {self.severity.upper()} - {self.detail}"]
        lo, hi = self.estimated_bias_pp_per_year()
        if hi > 0:
            lines.append(f"expect EW returns inflated roughly +{lo}-{hi} pp/yr vs an honest "
                         f"universe (measured, vintage-dependent; see backtest_bias.REFERENCES)")
        return "\n".join(lines)

    def __repr__(self):
        return f"<SurvivorshipReport {self.severity}: {self.n_dead_in_window}/{self.n_symbols} dead, {self.window_years:.1f}y>"


def check_survivorship(prices: pd.DataFrame, gap_days: int = 45, min_obs: int = 60,
                       min_names: int = 20, min_years: float = 3.0, market: str = "IN",
                       **to_wide_kw) -> SurvivorshipReport:
    """THE core question: does your universe contain names that died inside your test window?

    A multi-year panel of 20+ names with ZERO deaths carries the survivor-only signature:
    every stock in it is a stock that made it to the end, and your backtest literally cannot
    buy the ones that didn't. Reference universes lose 10-30% of names over such windows."""
    w = to_wide(prices, **to_wide_kw)
    end = w.index.max()
    years = max((end - w.index.min()).days / 365.25, 0.01)
    firsts, lasts, dead = {}, {}, []
    for c in w.columns:
        s = w[c].dropna()
        if len(s) < min_obs:
            continue
        firsts[c], lasts[c] = s.index.min(), s.index.max()
        if lasts[c] < end - pd.Timedelta(days=gap_days):
            dead.append(c)
    n = len(firsts)
    if n == 0:
        raise ValueError(f"no symbol has >= {min_obs} observations; nothing to judge")
    ratio = len(dead) / n

    if ratio == 0 and n >= min_names and years >= min_years:
        sev, suspect = "severe", True
        detail = (f"{n} names over {years:.1f}y with zero deaths is the survivor-only signature; "
                  f"comparable universes lose "
                  f"{REFERENCES[market]['death_rate_range'][0]:.0%}-{REFERENCES[market]['death_rate_range'][1]:.0%} "
                  f"of names over such windows" if market in REFERENCES else
                  f"{n} names over {years:.1f}y with zero deaths is the survivor-only signature")
    elif ratio == 0 and n >= min_names:
        sev, suspect = "warn", False
        detail = f"zero deaths but only {years:.1f}y of window - re-run on your full research span"
    elif ratio < 0.05 and years >= 5:
        sev, suspect = "warn", False
        detail = f"suspiciously few deaths ({ratio:.1%}) for a {years:.1f}y window - check how the universe was built"
    else:
        sev, suspect = "clean", False
        detail = "dead names present in the panel; survivor-only construction not indicated"

    return SurvivorshipReport(n_symbols=n, n_dead_in_window=len(dead), dead_ratio=ratio,
                              window_years=years, survivor_only_suspected=suspect,
                              severity=sev, detail=detail, market=market,
                              dead_symbols=sorted(dead)[:50])


def assert_integrity(prices: pd.DataFrame, min_dead_ratio: float = 0.05,
                     gap_days: int = 45, min_obs: int = 60, **to_wide_kw) -> None:
    """CI gate: raise if the panel smells survivor-only. Wire it into your data pipeline so a
    silent re-download of survivor-only data fails the build instead of flattering the backtest."""
    r = dead_name_ratio(prices, gap_days=gap_days, min_obs=min_obs, **to_wide_kw)
    if r < min_dead_ratio:
        raise AssertionError(
            f"survivorship gate failed: dead-name ratio {r:.1%} < required {min_dead_ratio:.0%}. "
            f"This panel likely only contains stocks that survived to the end; backtests on it "
            f"will overstate returns (measured +0.8-2.5 pp/yr EW on Indian data).")
