"""backtest-bias core: survivorship checks for financial price panels.

Design rules:
- The library checks YOUR data. It ships no market data of its own.
- The packaged benchmarks are published, measured numbers (sources in REFERENCES) so a finding
  can be quantified, not just flagged.
- Anything the library cannot judge honestly, it says so instead of guessing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Published, measured benchmarks (see README for the write-ups).
# death_curve: fraction of a top-500 universe that stops trading within N years of the vintage
# date. Measured on Indian equities across six vintages (2012-2022); remarkably stable.
REFERENCES = {
    "IN": {
        "death_curve": {3: (0.05, 0.08), 5: (0.11, 0.14), 7: (0.17, 0.21), 10: (0.24, 0.30)},
        "bias_pp_per_year": (0.8, 2.5),     # measured EW return inflation from survivor-only
                                            # universes, vintage-dependent
        "construction_dependence": "+10% terminal wealth (cap-weighted) to +43% (equal-weight) "
                                   "measured on one widely used dataset, 2010-2021",
    },
    "US": {
        # Measured on point-in-time S&P 500 vintages (2010, 2015) against the same free
        # source, exits priced at last close; write-ups on the site.
        "bias_pp_per_year": (0.4, 1.0),
        "yearly_gap_range_pp": (-7.5, 3.5),  # survivor-minus-true by year: small on average,
                                             # large always
        "identity_pp_per_year": 1.7,         # four recycled tickers (dead company, new listing
                                             # on the same symbol) moved a measured result by
                                             # this much - more than the bias itself
    },
}


def expected_death_range(years: float, market: str = "IN"):
    """Interpolated measured range for how much of a universe should have died in `years`."""
    curve = REFERENCES.get(market, {}).get("death_curve")
    if not curve or years <= 0:
        return None
    xs = sorted(curve)
    if years <= xs[0]:
        lo, hi = curve[xs[0]]
        f = years / xs[0]
        return (lo * f, hi * f)
    if years >= xs[-1]:
        return curve[xs[-1]]
    for a, b in zip(xs, xs[1:]):
        if a <= years <= b:
            f = (years - a) / (b - a)
            return (curve[a][0] + f * (curve[b][0] - curve[a][0]),
                    curve[a][1] + f * (curve[b][1] - curve[a][1]))
    return curve[xs[-1]]


def _parse_dates(col: pd.Series) -> pd.Series:
    """Robust date parsing incl. the YYYYMMDD-integer style common in exchange dumps."""
    if pd.api.types.is_integer_dtype(col) or (
            col.dtype == object and col.astype(str).str.fullmatch(r"\d{8}").all()):
        as_int = pd.to_numeric(col, errors="coerce")
        if as_int.between(18000101, 21991231).all():
            return pd.to_datetime(as_int.astype("Int64").astype(str), format="%Y%m%d")
    return pd.to_datetime(col)


def to_wide(prices: pd.DataFrame,
            date_col: str = None, symbol_col: str = None, value_col: str = None) -> pd.DataFrame:
    """Accept a wide panel (DatetimeIndex x symbols) or a long frame (date/symbol/price columns)
    and return wide. Column names are sniffed case-insensitively when not given."""
    if prices is None or len(prices) == 0:
        raise ValueError("empty frame - nothing to judge")
    if isinstance(prices.index, pd.DatetimeIndex) and \
            not any(str(c).lower().strip() in ("symbol", "ticker") for c in prices.columns):
        w = prices.sort_index()
        if isinstance(w.columns, pd.MultiIndex):                 # yfinance multi-field download
            const = [i for i in range(w.columns.nlevels) if w.columns.get_level_values(i).nunique() == 1]
            w = w.droplevel(const, axis=1) if const else w.set_axis(
                ["_".join(map(str, t)) for t in w.columns], axis=1)
        return w
    df = prices.copy()
    cols = {str(c).lower().strip(): c for c in df.columns}
    date_col = date_col or next((cols[k] for k in ("date", "dt", "day", "time", "bar_date") if k in cols), None)
    symbol_col = symbol_col or next((cols[k] for k in ("symbol", "ticker", "scrip", "name", "instrument") if k in cols), None)
    value_col = value_col or next((cols[k] for k in ("close", "adj close", "adj_close", "adjclose",
                                                     "price", "px", "nav", "last", "ltp", "settle") if k in cols), None)
    if not (date_col and symbol_col and value_col):
        raise ValueError("could not sniff long-format columns; pass date_col/symbol_col/value_col")
    df[date_col] = _parse_dates(df[date_col])
    return df.pivot_table(index=date_col, columns=symbol_col, values=value_col, aggfunc="last").sort_index()


def _lifespans(w: pd.DataFrame, min_obs: int):
    firsts, lasts = {}, {}
    for c in w.columns:
        s = w[c].dropna()
        if len(s) < min_obs:
            continue
        firsts[c], lasts[c] = s.index.min(), s.index.max()
    if not lasts:
        raise ValueError(f"no symbol has >= {min_obs} observations; nothing to judge "
                         f"(if your data is weekly/monthly, lower min_obs)")
    return firsts, lasts


def dead_name_ratio(prices: pd.DataFrame, gap_days: int = 45, min_obs: int = 60,
                    as_of=None, **to_wide_kw) -> float:
    """Fraction of symbols whose data ENDS well before the panel's DATA does (names that died and
    were kept - the thing survivor-only panels don't have). 0.0 = your panel only contains
    the living. The reference end is the latest observation across symbols, so calendar padding
    (empty future rows) cannot distort the answer."""
    w = to_wide(prices, **to_wide_kw)
    _, lasts = _lifespans(w, min_obs)
    end = pd.Timestamp(as_of) if as_of is not None else max(lasts.values())
    dead = sum(1 for t in lasts.values() if t < end - pd.Timedelta(days=gap_days))
    return dead / len(lasts)


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
                       as_of=None, **to_wide_kw) -> SurvivorshipReport:
    """THE core question: does your universe contain names that died inside your test window?

    A multi-year panel of 20+ names with ZERO deaths carries the survivor-only signature:
    every stock in it is a stock that made it to the end, and your backtest literally cannot
    buy the ones that didn't. The verdict quotes the measured death-rate range for your window
    length (Indian top-500, six vintages 2012-2022)."""
    w = to_wide(prices, **to_wide_kw)
    firsts, lasts = _lifespans(w, min_obs)
    end = pd.Timestamp(as_of) if as_of is not None else max(lasts.values())
    start = min(firsts.values())
    years = max((end - start).days / 365.25, 0.01)
    dead = sorted(c for c, t in lasts.items() if t < end - pd.Timedelta(days=gap_days))
    n = len(lasts)
    ratio = len(dead) / n

    exp = expected_death_range(years, market)
    exp_txt = (f"comparable universes lose {exp[0]:.0%}-{exp[1]:.0%} of names over "
               f"{years:.0f}y (measured)") if exp else "no measured reference for this market"

    if ratio == 0 and n >= min_names and years >= min_years:
        sev, suspect = "severe", True
        detail = (f"{n} names over {years:.1f}y with zero deaths is the survivor-only signature; "
                  + exp_txt)
    elif ratio == 0 and n >= min_names:
        sev, suspect = "warn", False
        detail = f"zero deaths but only {years:.1f}y of window - re-run on your full research span"
    elif exp and ratio < 0.5 * exp[0] and years >= min_years:
        sev, suspect = "warn", False
        detail = (f"only {ratio:.1%} of names died where {exp_txt.replace('comparable universes lose ', '')} "
                  f"- check how the universe was built")
    else:
        sev, suspect = "clean", False
        detail = "dead names present in the panel; survivor-only construction not indicated"

    return SurvivorshipReport(n_symbols=n, n_dead_in_window=len(dead), dead_ratio=ratio,
                              window_years=years, survivor_only_suspected=suspect,
                              severity=sev, detail=detail, market=market,
                              dead_symbols=[str(c) for c in dead[:50]])


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


@dataclass
class IdentityReport:
    n_symbols: int
    reanimation_suspects: list
    late_first_bars: list
    severity: str                      # "clean" | "warn" | "severe"
    detail: str

    def summary(self) -> str:
        lines = [f"identity check: {self.n_symbols} symbols, "
                 f"{len(self.reanimation_suspects)} reanimation suspects, "
                 f"{len(self.late_first_bars)} late first bars",
                 f"verdict: {self.severity.upper()} - {self.detail}"]
        if self.reanimation_suspects:
            lines.append("suspects: " + ", ".join(
                f"{s['symbol']} (wild_months={s['wild_months']}, min_px={s['min_px']:.2f})"
                for s in self.reanimation_suspects[:10]))
            lines.append("verify each against corporate-action records before use. Four "
                         "recycled tickers moved a measured US result by 1.7 pp/yr, more "
                         "than the survivorship bias itself (see backtest_bias.REFERENCES).")
        return "\n".join(lines)

    def __repr__(self):
        return (f"<IdentityReport {self.severity}: {len(self.reanimation_suspects)} suspects, "
                f"{len(self.late_first_bars)} late first bars>")


def check_identity(prices: pd.DataFrame, wild_ret: float = 1.5, min_wild: int = 2,
                   penny_px: float = 2.0, grace_days: int = 120, min_obs: int = 60,
                   **to_wide_kw) -> IdentityReport:
    """Is each ticker the same company all the way through its series?

    Free sources silently stitch a new listing onto a dead company's history when a ticker
    is reused (Compuware died 2014; CPWR later printed a +4,567% month when the replacement
    was spliced on). Two cheap detectors catch most of it:

    - reanimation: two or more months with |return| > wild_ret combined with penny-level
      prints inside one series means two companies are stitched together;
    - late first bar: a series that starts well after the panel does is a later listing or
      a recycled symbol - it cannot have been bought at the panel's start.

    Both are advisory: verify flagged names against corporate-action records rather than
    dropping them blindly (a real +1,625% month exists; filters must kill fake returns
    without killing embarrassing true ones)."""
    w = to_wide(prices, **to_wide_kw)
    firsts, _ = _lifespans(w, min_obs)
    panel_start = w.index.min()
    monthly = w.resample("ME").last()
    rets = monthly.pct_change(fill_method=None)

    suspects, late = [], []
    for c in w.columns:
        s = monthly[c].dropna() if c in monthly.columns else pd.Series(dtype=float)
        if s.empty:
            continue
        wild = int((rets[c].abs() > wild_ret).sum())
        pmin = float(s.min())
        if wild >= min_wild and pmin < penny_px:
            suspects.append({"symbol": str(c), "wild_months": wild, "min_px": pmin})
        fv = firsts.get(c)
        if fv is not None and fv > panel_start + pd.Timedelta(days=grace_days):
            late.append({"symbol": str(c), "first_bar": str(pd.Timestamp(fv).date())})

    if suspects:
        sev = "severe"
        detail = (f"{len(suspects)} series carry the reanimation signature (wild months + "
                  f"penny prints): likely two companies stitched onto one ticker")
    elif late:
        sev = "warn"
        detail = (f"{len(late)} series start well after the panel does: later listings or "
                  f"recycled symbols; exclude them from any window that begins before their "
                  f"first bar")
    else:
        sev = "clean"
        detail = "no reanimation signatures; every series spans the panel it claims"
    return IdentityReport(n_symbols=len(w.columns), reanimation_suspects=suspects,
                          late_first_bars=late, severity=sev, detail=detail)


@dataclass
class UniverseReport:
    n_universe: int
    n_present: int
    coverage_at_start: float
    coverage_ever: float
    lookahead_suspected: bool
    n_alive_at_start: int
    n_died_in_window: int
    died_ratio: float
    window_years: float
    survivor_only_suspected: bool
    severity: str                      # "clean" | "warn" | "severe"
    detail: str
    market: str = "IN"

    def summary(self) -> str:
        lines = [f"universe check: {self.n_universe} names, {self.n_present} present in panel; "
                 f"coverage {self.coverage_at_start:.0%} at start vs {self.coverage_ever:.0%} ever",
                 f"deaths: {self.n_died_in_window}/{self.n_alive_at_start} start-alive names "
                 f"stopped printing over {self.window_years:.1f}y ({self.died_ratio:.0%})",
                 f"verdict: {self.severity.upper()} - {self.detail}"]
        return "\n".join(lines)

    def __repr__(self):
        return f"<UniverseReport {self.severity}: coverage {self.coverage_at_start:.0%}->{self.coverage_ever:.0%}, deaths {self.died_ratio:.0%}>"


def check_universe(prices: pd.DataFrame, universe, start, gap_days: int = 60,
                   min_obs: int = 60, market: str = "IN", **to_wide_kw) -> UniverseReport:
    """Was this universe knowable on its start date, and does it die like a real one?

    Two signatures of a today's-list-backfilled universe (a look-ahead in universe
    construction, the most common survivorship mechanism in practice):

    - rising coverage: members whose data begins after the start date were added to the
      index later - the list is today's, applied backwards;
    - missing deaths: a real universe loses names to delisting and merger at a measured
      rate; a universe whose start-alive members almost never stop printing was filtered
      through hindsight, whatever its coverage profile looks like.

    `universe` is the member list you backtest on; `start` is the date the backtest begins."""
    w = to_wide(prices, **to_wide_kw)
    uni = [str(x).strip() for x in pd.Series(universe).astype(str) if str(x).strip()]
    start = pd.Timestamp(start)
    have = [c for c in w.columns if str(c) in set(uni)]
    end = w.index.max()
    years = max((end - start).days / 365.25, 0.01)

    at_start = [c for c in have if w[c].loc[:start].notna().any()]
    cov0 = len(at_start) / max(len(uni), 1)
    cov1 = len(have) / max(len(uni), 1)
    lookahead = (cov1 - cov0) > 0.10

    died = [c for c in at_start
            if w[c].last_valid_index() is not None
            and w[c].last_valid_index() < end - pd.Timedelta(days=gap_days)]
    died_ratio = len(died) / max(len(at_start), 1)
    exp = expected_death_range(years, market)

    survivor_only = bool(exp and died_ratio < 0.5 * exp[0] and years >= 3.0)
    if lookahead:
        sev = "severe"
        detail = (f"coverage rises {cov0:.0%} -> {cov1:.0%}: members enter the data after the "
                  f"start date, the signature of today's list applied backwards")
    elif survivor_only:
        sev = "severe"
        detail = (f"only {died_ratio:.0%} of start-alive names die over {years:.1f}y where "
                  f"comparable universes lose {exp[0]:.0%}-{exp[1]:.0%} (measured): the "
                  f"corpses are missing, likely a survivor-filtered source")
    elif exp and died_ratio < exp[0] and years >= 3.0:
        sev = "warn"
        detail = (f"death share {died_ratio:.0%} sits below the measured "
                  f"{exp[0]:.0%}-{exp[1]:.0%} band: ask where the delisted names went")
    else:
        sev = "clean"
        detail = ("coverage flat and death share plausible; still confirm the universe "
                  "file's as-of date in writing")
    return UniverseReport(n_universe=len(uni), n_present=len(have), coverage_at_start=cov0,
                          coverage_ever=cov1, lookahead_suspected=lookahead,
                          n_alive_at_start=len(at_start), n_died_in_window=len(died),
                          died_ratio=died_ratio, window_years=years,
                          survivor_only_suspected=survivor_only, severity=sev,
                          detail=detail, market=market)
