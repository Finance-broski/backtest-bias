"""Selection look-ahead: does your screen's accept/reject rule know the year it is judged on?

The other checks in this package ask whether the DATA behind a backtest is honest. This one asks
whether the CHOOSING is. A screen that selects candidates on a window and then reports an
"out-of-sample" result on the last part of that same window has leaked the future into the
selection, even when every hedge ratio and every z-score was computed walk-forward. The leak is in
the labelling, not in the arithmetic, so no data hygiene removes it.

The protocol (measured first on a US pairs screen, 2026-08-25, where it accounted for the entire
apparent edge, 13.9 log points a year):

  1. Walk the history backwards in eras of `hold` sessions. For each era, hand the screen ONLY the
     formation window that ends before the era, let it accept or reject every candidate on that
     window alone, then score both arms forward through the era. Rejected candidates are matched to
     accepted ones on a nuisance key (return correlation, by default) so the comparison is not a
     comparison of relatedness. The per-era gap between the arms is the screen's forward
     information, measured without look-ahead.

  2. Locate the leak. Among candidates accepted IN ERA on formation data alone, split by whether the
     screen run on the WHOLE history also accepts them. Both groups passed the identical test on
     identical evidence; the only difference is information from the future. The difference in
     forward outcome between them is what one bit of future information is worth, and it is the
     number an "out-of-sample" figure computed on full-window acceptance is inflated by.

Adjacent eras share most of their formation data, so gaps across eras are not independent
observations. The honest strength claim is the count of eras in which the sign holds, which is
what the report leads with; a cross-era t is reported for scale and should not be quoted as one.

One rule about the candidate list, learned by getting it wrong: sample candidates from the
POPULATION the screen chooses among, never from the screen's own accept and reject lists. A pool
built from stored accepts plus stored rejects already carries the full-window label, and the clean
gap comes out positive for that reason alone. On the PairDesk vintage, 3,000 pairs drawn from the
population reproduce the published shape: clean gap -0.010 per era, positive in 2 of 6 eras;
hindsight difference +0.153 per era, positive in 6 of 6 (published: -0.021 and +0.139 on a
different 6,000-pair sample).

The default callables implement a pairs screen (Engle-Granger both ways against MacKinnon 2010
finite-sample critical values) and a fixed z-score trading rule, so `check_selection` runs on a
price panel and a list of (y, x) pairs with no other code. Any other screen is audited by passing
its own `select`, `score` and `match_key`; the protocol does not care what is being selected.
"""
from dataclasses import dataclass
from typing import Callable, Hashable, Iterable, Optional, Sequence

import numpy as np
import pandas as pd

from .core import to_wide

# MacKinnon (2010) response-surface coefficients, Engle-Granger residual test, one regressor,
# regression with constant: tau_c(T) = beta_inf + beta_1 / T + beta_2 / T^2.
_MACKINNON_N2_C = {0.01: (-3.9001, -10.534, -30.03),
                   0.05: (-3.3377, -5.967, -8.98),
                   0.10: (-3.0462, -4.069, -5.73)}


def eg_critical_value(n_obs: int, level: float = 0.05) -> float:
    """Finite-sample critical value for the Engle-Granger residual ADF, two variables, constant."""
    b0, b1, b2 = _MACKINNON_N2_C[level]
    return b0 + b1 / n_obs + b2 / n_obs ** 2


def _ols(y: np.ndarray, x: np.ndarray):
    X = np.column_stack([np.ones(len(x)), x])
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    return coef, y - X @ coef


def _adf_t(e: np.ndarray, lags: int = 1) -> float:
    """t-statistic on the level term of an ADF regression on residuals (no constant: the residuals
    of a regression with a constant already have zero mean)."""
    de = np.diff(e)
    lagged = e[lags:-1]
    cols = [lagged] + [de[lags - k - 1: len(de) - k - 1] for k in range(lags)]
    X = np.column_stack(cols)
    target = de[lags:]
    beta, res, *_ = np.linalg.lstsq(X, target, rcond=None)
    resid = target - X @ beta
    dof = max(len(target) - X.shape[1], 1)
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(max(cov[0, 0], 1e-18))
    return float(beta[0] / se)


def eg_both_ways(form: pd.DataFrame, candidates: Sequence[tuple], level: float = 0.05,
                 lags: int = 1) -> set:
    """Default screen: accept a pair only if the Engle-Granger residual test clears the
    finite-sample critical value in BOTH orientations on the formation window alone."""
    accepted = set()
    for pair in candidates:
        y, x = pair
        if y not in form.columns or x not in form.columns:
            continue
        s = form[[y, x]].dropna()
        if len(s) < 100:
            continue
        cv = eg_critical_value(len(s), level)
        a, b = s[y].values, s[x].values
        _, e1 = _ols(a, b)
        if _adf_t(e1, lags) > cv:
            continue
        _, e2 = _ols(b, a)
        if _adf_t(e2, lags) > cv:
            continue
        accepted.add(pair)
    return accepted


def zscore_rule_pnl(form: pd.DataFrame, hold: pd.DataFrame, pair: tuple, entry: float = 2.0,
                    exit_z: float = 0.5, stop: int = 20, cost: float = 0.002) -> Optional[float]:
    """Default forward score: fit the spread on the formation window, trade the era with a fixed
    z-score rule, return the era's PnL in log points net of a round-trip cost."""
    y, x = pair
    if y not in form.columns or x not in form.columns:
        return None
    f = form[[y, x]].dropna()
    h = hold[[y, x]].dropna()
    if len(f) < 100 or len(h) < 20:
        return None
    coef, sf = _ols(f[y].values, f[x].values)
    sd = sf.std()
    if sd <= 0:
        return None
    sh = h[y].values - (coef[0] + coef[1] * h[x].values)
    z = (sh - sf.mean()) / sd
    pos, ent, pnl = 0, 0, 0.0
    for i in range(1, len(z)):
        if pos == 0:
            if z[i] > entry:
                pos, ent = -1, i
            elif z[i] < -entry:
                pos, ent = 1, i
        elif abs(z[i]) <= exit_z or i - ent >= stop or i == len(z) - 1:
            pnl += pos * (sh[i] - sh[ent]) - cost
            pos = 0
    return float(pnl)


def return_correlation(form: pd.DataFrame, pair: tuple) -> Optional[float]:
    """Default matching key: correlation of the two legs' returns over the formation window."""
    y, x = pair
    if y not in form.columns or x not in form.columns:
        return None
    r = form[[y, x]].dropna().diff().dropna()
    if len(r) < 30:
        return None
    return float(r[y].corr(r[x]))


def _match(keys_acc: pd.Series, keys_rej: pd.Series, bins: int, rng: np.random.Generator) -> list:
    """Quantile-match the rejected pool to the accepted arm on the nuisance key."""
    if keys_acc.empty or keys_rej.empty:
        return []
    edges = np.unique(np.quantile(keys_acc.values, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        # a degenerate key (a tiny arm, or a constant): nothing to match on, so draw the same
        # number of rejects at random and say so by construction rather than fail
        pool = list(keys_rej.index)
        take = min(len(keys_acc), len(pool))
        idx = rng.choice(len(pool), size=take, replace=False)
        return [pool[i] for i in idx]
    edges[0], edges[-1] = -np.inf, np.inf
    picked = []
    acc_bins = pd.cut(keys_acc, edges, include_lowest=True)
    rej_bins = pd.cut(keys_rej, edges, include_lowest=True)
    for b, k in acc_bins.value_counts().items():
        pool = list(keys_rej[rej_bins == b].index)
        if pool:
            take = min(int(k), len(pool))
            idx = rng.choice(len(pool), size=take, replace=False)
            picked.extend(pool[i] for i in idx)
    return picked


@dataclass
class SelectionReport:
    n_candidates: int
    n_eras: int
    hold: int
    eras: pd.DataFrame                 # per era: accept_rate, accepted, rejected_matched, gap, n
    clean_gap_mean: float              # accepted minus matched rejected, labels recomputed in era
    clean_gap_positive_eras: int
    hindsight: pd.DataFrame            # per era: also_accepted_full, not_accepted_full, difference
    hindsight_mean: float              # the worth of one bit of future information
    hindsight_positive_eras: int
    hindsight_t: float                 # cross-era t, for scale only; eras are not independent
    severity: str                      # "clean" | "warn" | "severe"
    detail: str
    unit: str = "log points per era"

    def summary(self) -> str:
        lines = [f"selection look-ahead check: {self.n_candidates} candidates, {self.n_eras} eras "
                 f"of {self.hold} sessions, labels recomputed inside each era",
                 f"forward information of the rule: gap {self.clean_gap_mean:+.4f} {self.unit}, "
                 f"positive in {self.clean_gap_positive_eras} of {self.n_eras} eras",
                 f"worth of one bit of future information: {self.hindsight_mean:+.4f} {self.unit}, "
                 f"positive in {self.hindsight_positive_eras} of {self.n_eras} eras "
                 f"(cross-era t {self.hindsight_t:+.2f}, eras overlap, do not quote it as one)",
                 f"verdict: {self.severity.upper()} - {self.detail}"]
        return "\n".join(lines)

    def __repr__(self):
        return (f"<SelectionReport {self.severity}: clean gap {self.clean_gap_mean:+.4f}, "
                f"hindsight {self.hindsight_mean:+.4f} over {self.n_eras} eras>")


def check_selection(prices: pd.DataFrame, candidates: Sequence[Hashable],
                    select: Callable = eg_both_ways, score: Callable = zscore_rule_pnl,
                    match_key: Callable = return_correlation, hold: int = 250, n_eras: int = 6,
                    min_form: int = 750, match_bins: int = 10, min_arm: int = 5,
                    full_accepted: Optional[Iterable[Hashable]] = None, log_prices: bool = True,
                    seed: int = 41, **to_wide_kw) -> SelectionReport:
    """Audit a screen for selection look-ahead.

    prices        wide (dates x symbols) or long; passed through `to_wide`. Log-transformed unless
                  `log_prices=False`.
    candidates    the things the screen chooses among; (y, x) tuples for the default pairs screen.
                  Draw them from the population, not from the screen's stored accept/reject lists.
    select        select(formation_window, candidates) -> accepted candidates, using the window ONLY.
    score         score(formation_window, hold_window, candidate) -> forward outcome or None.
    match_key     match_key(formation_window, candidate) -> nuisance value to match rejects on.
    full_accepted the screen's acceptance on the whole history, if you already have it (the stored
                  vintage); otherwise `select` is run on the full panel to obtain it.

    Two numbers come back. The clean gap is what the rule knows about the forward period when it
    cannot see it. The hindsight difference is how much a full-history label inflates an
    "out-of-sample" figure, and it is the one that condemns a screen."""
    w = to_wide(prices, **to_wide_kw)
    panel = np.log(w) if log_prices else w.copy()
    panel = panel.sort_index()
    cands = list(candidates)
    rng = np.random.default_rng(seed)
    full = set(full_accepted) if full_accepted is not None else set(select(panel, cands))

    era_rows, hind_rows = [], []
    T = len(panel)
    for e in range(n_eras):
        end = T - e * hold
        start_hold = end - hold
        if start_hold < min_form:
            break
        form, held = panel.iloc[:start_hold], panel.iloc[start_hold:end]
        accepted = set(select(form, cands))
        rejected = [c for c in cands if c not in accepted]
        keys_acc = pd.Series({c: match_key(form, c) for c in accepted}).dropna()
        keys_rej = pd.Series({c: match_key(form, c) for c in rejected}).dropna()
        matched = _match(keys_acc, keys_rej, match_bins, rng)
        sc_acc = pd.Series({c: score(form, held, c) for c in accepted}).dropna()
        sc_rej = pd.Series({c: score(form, held, c) for c in matched}).dropna()
        if len(sc_acc) < min_arm or len(sc_rej) < min_arm:
            continue
        era_rows.append(dict(era=f"era {e + 1} back", accept_rate=len(accepted) / max(len(cands), 1),
                             n_accepted=len(sc_acc), n_rejected_matched=len(sc_rej),
                             accepted=float(sc_acc.mean()), rejected_matched=float(sc_rej.mean()),
                             gap=float(sc_acc.mean() - sc_rej.mean()),
                             accepted_positive=float((sc_acc > 0).mean())))
        also = sc_acc[[c in full for c in sc_acc.index]]
        notf = sc_acc[[c not in full for c in sc_acc.index]]
        if len(also) and len(notf):
            hind_rows.append(dict(era=f"era {e + 1} back", n_also=len(also), n_not=len(notf),
                                  also_accepted_full=float(also.mean()),
                                  not_accepted_full=float(notf.mean()),
                                  difference=float(also.mean() - notf.mean())))

    eras = pd.DataFrame(era_rows)
    hind = pd.DataFrame(hind_rows)
    n_eras_done = len(eras)
    if n_eras_done == 0:
        raise ValueError("not enough history for one era: need min_form + hold rows and at least "
                         f"{min_arm} scored candidates per arm")
    gap_mean = float(eras.gap.mean())
    gap_pos = int((eras.gap > 0).sum())
    if len(hind):
        h_mean = float(hind.difference.mean())
        h_pos = int((hind.difference > 0).sum())
        h_t = float(h_mean / (hind.difference.std(ddof=1) / np.sqrt(len(hind)))) if len(hind) > 1 and hind.difference.std(ddof=1) > 0 else float("nan")
    else:
        h_mean, h_pos, h_t = float("nan"), 0, float("nan")

    # Verdict. The condemning signature is a hindsight difference that is positive in nearly every
    # era: the full-history label knows the future. The clean gap is reported as a finding about
    # the rule, not as a fault: a rule with no forward information is honest, it is just not an edge.
    if len(hind) >= 3 and h_pos >= max(3, int(np.ceil(0.8 * len(hind)))) and h_mean > 0:
        sev = "severe"
        detail = (f"the full-history label carries forward information worth {h_mean:+.4f} per era, "
                  f"positive in {h_pos} of {len(hind)} eras; any 'out-of-sample' figure computed on "
                  f"candidates selected on the full window is inflated by it")
    elif len(hind) >= 3 and h_mean > 0 and h_pos > len(hind) / 2:
        sev = "warn"
        detail = (f"the full-history label adds {h_mean:+.4f} per era in {h_pos} of {len(hind)} eras; "
                  f"report only figures computed with labels recomputed inside each era")
    elif len(hind) < 3:
        sev = "warn"
        detail = (f"only {len(hind)} era(s) had both split groups; extend the history or the "
                  f"candidate list before reading the hindsight number")
    else:
        sev = "clean"
        detail = "full-history and in-era labels lead to the same forward outcomes"
    if gap_pos <= n_eras_done / 2 or gap_mean <= 0:
        detail += (f"; the rule itself shows no forward information (gap {gap_mean:+.4f}, positive in "
                   f"{gap_pos} of {n_eras_done} eras), which is a finding about the rule, not a fault "
                   f"in the data")
    return SelectionReport(n_candidates=len(cands), n_eras=n_eras_done, hold=hold, eras=eras,
                           clean_gap_mean=gap_mean, clean_gap_positive_eras=gap_pos, hindsight=hind,
                           hindsight_mean=h_mean, hindsight_positive_eras=h_pos, hindsight_t=h_t,
                           severity=sev, detail=detail)
