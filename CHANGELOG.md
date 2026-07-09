# Changelog

## 0.1.1 (2026-07-09) — same-day hostile audit

Ran an adversarial input suite against v0.1 a few hours after release. Findings, fixed and
locked in as regression tests:

- **Calendar-padding masking bug (the bad one):** death was measured against the calendar's end,
  so a panel reindexed onto a padded/future calendar made every name look dead — which could
  have let a survivor-only panel read as clean. Death is now measured against the DATA's end
  (latest observation across symbols).
- **YYYYMMDD integer dates** (common in exchange dumps) parsed silently as epoch-nanoseconds,
  collapsing a 9-year panel to a 0.0y window. Now detected and parsed correctly.
- Single-symbol wide panels are accepted; empty frames raise a clear error; `Adj Close` and
  similar column names are sniffed in long format; yfinance-style MultiIndex columns are
  flattened; the min_obs error now hints at weekly/monthly data.
- **Benchmarks upgraded from range to measured curve:** the "how much should be dead" reference
  is now a horizon curve measured across six top-500 vintages (2012-2022) — ~6-8% by 3y,
  11-14% by 5y, 17-21% by 7y, 24-30% by 10y — and verdicts quote the range matched to your
  window length instead of one flat number.

Test count: 6 → 13.

## 0.1.0 (2026-07-09)

Initial release: `check_survivorship`, `dead_name_ratio`, `assert_integrity`.
