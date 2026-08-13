# 0.2.0 (2026-08-14)

- New: `check_identity` - reanimation detector (wild months + penny prints inside one
  series) and late-first-bar detector, with an `IdentityReport`. Advisory by design:
  verify suspects against corporate-action records; real +1,625% months exist.
- New: `check_universe` - the look-ahead signature (coverage rising after the start date)
  and the missing-deaths signature (start-alive members dying far below the measured
  curve), with a `UniverseReport`.
- New: `REFERENCES["US"]` - measured S&P 500 vintage constants: bias +0.4 to +1.0 pp/yr,
  yearly gap range -7.5 to +3.5, identity error 1.7 pp/yr.
- Exposed `expected_death_range` in the public API.
- Fixed: `__version__` drift between the package and pyproject.

# Changelog

## 0.1.2 (2026-08-01): docs-only

No code changes. The README on PyPI was frozen at the 0.1.0-era text; this release ships the
current one: numbers aligned to the published paper (24% invisibility, +0.8 to +3.2 pp/yr
survivorship range, measured death-rate curve), Bias Table and Kaggle replication links, and
typography cleanup. Library behavior is identical to 0.1.1.

## 0.1.1 (2026-07-09): same-day hostile audit

Ran an adversarial input suite against v0.1 a few hours after release. Findings, fixed and
locked in as regression tests:

- **Calendar-padding masking bug (the bad one):** death was measured against the calendar's end,
  so a panel reindexed onto a padded/future calendar made every name look dead, which could
  have let a survivor-only panel read as clean. Death is now measured against the DATA's end
  (latest observation across symbols).
- **YYYYMMDD integer dates** (common in exchange dumps) parsed silently as epoch-nanoseconds,
  collapsing a 9-year panel to a 0.0y window. Now detected and parsed correctly.
- Single-symbol wide panels are accepted; empty frames raise a clear error; `Adj Close` and
  similar column names are sniffed in long format; yfinance-style MultiIndex columns are
  flattened; the min_obs error now hints at weekly/monthly data.
- **Benchmarks upgraded from range to measured curve:** the "how much should be dead" reference
  is now a horizon curve measured across six top-500 vintages (2012-2022): ~6-8% by 3y,
  11-14% by 5y, 17-21% by 7y, 24-30% by 10y, and verdicts quote the range matched to your
  window length instead of one flat number.

Test count: 6 to 13.

## 0.1.0 (2026-07-09)

Initial release: `check_survivorship`, `dead_name_ratio`, `assert_integrity`.
