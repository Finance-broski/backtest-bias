"""backtest-bias v0.3: the selection look-ahead check on synthetic panels with known truth.

Three facts the check must reproduce:
  1. On pure noise, an honest in-era screen has no forward information (clean gap about zero), yet
     the full-history label still "knows the future": among pairs accepted in era, the ones the
     full-window screen also accepts do better forward. That is the leak, and it appears on noise.
  2. With planted cointegrated pairs among the noise, the honest in-era screen finds them and the
     clean gap turns positive: the instrument can see a real edge when one exists.
  3. A user-supplied screen and score run through the same protocol.
Run: python -m pytest tests/test_selection.py -q"""
import sys, os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backtest_bias import check_selection, eg_both_ways, eg_critical_value, SelectionReport


def eg10(form, cands):
    return eg_both_ways(form, cands, level=0.10)

HOLD, MIN_FORM, N_ERAS = 120, 500, 3
T = MIN_FORM + HOLD * N_ERAS + 40
DAYS = pd.bdate_range("2016-01-01", periods=T)


def _noise_panel(n_pairs, rng):
    cols, cands = {}, []
    for i in range(n_pairs):
        x = np.cumsum(rng.normal(0, 0.015, T))
        y = np.cumsum(rng.normal(0, 0.015, T))
        cols[f"X{i:03d}"], cols[f"Y{i:03d}"] = x, y
        cands.append((f"Y{i:03d}", f"X{i:03d}"))
    return pd.DataFrame(cols, index=DAYS), cands


def _planted_panel(n_true, n_noise, rng, half_life=12.0):
    """True pairs: y = x + a stationary AR(1) spread, so y and x cointegrate by construction."""
    cols, cands = {}, []
    phi = 0.5 ** (1.0 / half_life)
    for i in range(n_true):
        x = np.cumsum(rng.normal(0, 0.015, T))
        s = np.zeros(T)
        for t in range(1, T):
            s[t] = phi * s[t - 1] + rng.normal(0, 0.012)
        cols[f"X{i:03d}"], cols[f"Y{i:03d}"] = x, x + s
        cands.append((f"Y{i:03d}", f"X{i:03d}"))
    noise, ncands = _noise_panel(n_noise, rng)
    noise.columns = [c.replace("X", "NX").replace("Y", "NY") for c in noise.columns]
    df = pd.concat([pd.DataFrame(cols, index=DAYS), noise], axis=1)
    return df, cands + [(y.replace("Y", "NY"), x.replace("X", "NX")) for y, x in ncands]


def test_critical_values_match_mackinnon_shape():
    # finite-sample values sit below the asymptotic ones and converge upward with T
    assert eg_critical_value(100) < eg_critical_value(1000) < -3.33
    assert eg_critical_value(10 ** 6) == pytest.approx(-3.3377, abs=1e-3)


def test_noise_has_no_forward_information_but_full_label_knows_the_future():
    rng = np.random.default_rng(3)
    panel, cands = _noise_panel(300, rng)
    rep = check_selection(np.exp(panel), cands, select=eg10, hold=HOLD, n_eras=N_ERAS,
                          min_form=MIN_FORM, min_arm=3, seed=1)
    assert isinstance(rep, SelectionReport)
    assert rep.n_eras >= 2
    # the honest rule cannot rank noise: the clean gap is small either way
    assert abs(rep.clean_gap_mean) < 0.05
    # the leak: full-window acceptance is worth something forward even on noise
    assert len(rep.hindsight) >= 2
    assert rep.hindsight_mean > 0
    assert 0 < rep.full_window_inflation_mean <= rep.hindsight_mean + 1e-12
    assert rep.severity in ("warn", "severe")
    assert "future" in rep.summary() or "inflated" in rep.summary() or "label" in rep.summary()


def test_planted_pairs_give_the_honest_screen_a_positive_gap():
    rng = np.random.default_rng(11)
    panel, cands = _planted_panel(25, 60, rng)
    rep = check_selection(np.exp(panel), cands, hold=HOLD, n_eras=N_ERAS, min_form=MIN_FORM,
                          min_arm=3, seed=2)
    # the in-era screen accepts mostly the true pairs and they revert forward
    assert rep.eras.accept_rate.mean() > 0.10
    assert rep.clean_gap_mean > 0
    assert rep.clean_gap_positive_eras >= rep.n_eras - 1


def test_user_supplied_screen_and_score_run_through_the_protocol():
    rng = np.random.default_rng(5)
    panel, cands = _noise_panel(40, rng)

    def select_first_half(form, candidates):          # a rule that ignores the data entirely
        return set(candidates[: len(candidates) // 2])

    def score_last_return(form, hold, pair):          # forward outcome: the y leg's era return
        y, _ = pair
        s = hold[y].dropna()
        return float(s.iloc[-1] - s.iloc[0]) if len(s) > 1 else None

    def key_zero(form, pair):
        return 0.0

    rep = check_selection(np.exp(panel), cands, select=select_first_half, score=score_last_return,
                          match_key=key_zero, hold=HOLD, n_eras=N_ERAS, min_form=MIN_FORM, min_arm=3)
    # a data-blind rule has identical in-era and full-window labels: no bit to measure, and that
    # is clean, not a warning
    assert rep.n_eras >= 2
    assert len(rep.hindsight) == 0
    assert np.isnan(rep.hindsight_mean)
    assert rep.identical_label_eras == rep.n_eras
    assert rep.severity == "clean"


def test_full_accepted_can_be_supplied_from_a_stored_vintage():
    rng = np.random.default_rng(9)
    panel, cands = _noise_panel(300, rng)
    stored = eg10(panel, cands)
    rep = check_selection(np.exp(panel), cands, select=eg10, hold=HOLD, n_eras=N_ERAS,
                          min_form=MIN_FORM, min_arm=3, full_accepted=stored)
    rep2 = check_selection(np.exp(panel), cands, select=eg10, hold=HOLD, n_eras=N_ERAS,
                           min_form=MIN_FORM, min_arm=3)
    assert rep.hindsight_mean == pytest.approx(rep2.hindsight_mean)


def test_in_era_labels_make_the_hindsight_number_informational():
    rng = np.random.default_rng(3)
    panel, cands = _noise_panel(300, rng)
    rep = check_selection(np.exp(panel), cands, select=eg10, hold=HOLD, n_eras=N_ERAS,
                          min_form=MIN_FORM, min_arm=3, seed=1, labels_reported_in_era=True)
    assert rep.hindsight_mean > 0                 # the number is still measured
    assert rep.severity == "clean"                # but it does not condemn in-era reporting
    assert "in-era labels" in rep.detail


def test_match_balance_is_reported_and_small_when_matching_works():
    rng = np.random.default_rng(11)
    panel, cands = _planted_panel(25, 60, rng)
    rep = check_selection(np.exp(panel), cands, hold=HOLD, n_eras=N_ERAS, min_form=MIN_FORM,
                          min_arm=3, seed=2)
    assert "match_key_accepted" in rep.eras.columns and "match_key_rejected" in rep.eras.columns
    assert rep.match_balance == rep.match_balance          # not NaN


def test_wide_frame_without_a_datetime_index_is_accepted():
    rng = np.random.default_rng(21)
    panel, cands = _noise_panel(120, rng)
    plain = np.exp(panel).reset_index(drop=True)          # integer index, wide
    rep = check_selection(plain, cands, select=eg10, hold=HOLD, n_eras=N_ERAS, min_form=MIN_FORM,
                          min_arm=3)
    assert rep.n_eras >= 2
