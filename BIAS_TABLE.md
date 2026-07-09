# The Indian Backtest Bias Table

Every number on this page is **measured, not assumed** — on real Indian market data, with the
method stated. This table exists because most claims about backtest bias are vibes with a
percent sign. Cite it, check it, fight it with data.

Maintained by [Ayan Jain](https://www.linkedin.com/in/ayanjain259). Last updated 2026-07-09.
New rows are added as audits publish. The library that checks some of these automatically:
`pip install backtest-bias`.

| # | Bias | Measured effect | Setting & window | Method (one line) |
|---|------|-----------------|------------------|-------------------|
| 1 | **Survivorship (universe hole)** | **23%** of the top-500 (Jan-2015 vintage) no longer resolves on yfinance today — delisted, merged, suspended | Indian equities, 2015 → 2026 | Point-in-time 2015 top-500 mapped through renames to terminal symbols; batch-queried against yfinance; 2 Yahoo symbol quirks classified out |
| 2 | **Survivorship (return inflation)** | **+0.8 pp/yr, ~+7% terminal wealth** (2015 vintage) to **+2.5 pp/yr** (2013 vintage) on equal-weight | Indian top-500, EW monthly, ~10y windows | Same prices both arms; only the universe differs (full PIT universe vs the survivor subset); vintage-dependence is the finding |
| 3 | **How much of a universe *should* be dead** | **~6-8%** by year 3, **11-14%** by 5, **17-21%** by 7, **24-30%** by 10 — stable across six vintages | Indian top-500 vintages 2012-2022 | Fraction of each vintage's names whose data ends >45d before each horizon; a multi-year panel with zero deaths is survivor-only by construction |
| 4 | **Index-membership look-ahead** | **+10%** terminal wealth (cap-weighted) to **+43%** (equal-weight) | NIFTY-50 constituents, 2010-2021, most-used Kaggle NSE dataset | Same 50 names, same prices; only membership *timing* differs (actual inclusion dates vs held-from-start); construction dependence is the finding |
| 5 | **Fundamentals look-ahead (announcement lag)** | Indian quarterly results go public **~42 days** after period end; joining on period-end dates hands the model the future | NSE filings, measured lag distribution | Announcement-date vs period-end-date deltas from exchange filings; PIT joins must use announcement dates |
| 6 | **Look-ahead in a value sort** | **+3.8 pp/yr** (of a +4.0 pp/yr total bias) from fundamentals timing in a 4-way value sort | Indian equities, multi-year panel | Same sort run twice: period-end joins vs announcement-date joins; survivorship contributed the remaining +0.2 pp |
| 7 | **Cost non-stationarity** | Stress-week effective spreads ≈ **3x** calm-week spreads — and momentum-style exits cluster in exactly those weeks | Indian intraday data | Effective spreads estimated from intraday prints, bucketed by volatility regime |
| 8 | **Marking frequency** | Headline CAGR fell from **low-20s to mid-teens** when marked at executable prices with realistic rebalance timing instead of daily closes | One mid-cap momentum system (author's own) | Same strategy, re-marked; the artifact exceeded the entire cost model |

## Reading rules

- Every row states its window and construction; **the same bias measures differently in a
  different setting** (see rows 2 and 4 — vintage and construction change the answer by 3-4x).
  Anyone quoting a single number for "survivorship bias" without a vintage is guessing.
- Directionality: all of these flatter the backtest. Real money runs on the honest side.
- Corrections welcome: open an issue with your own measurement and method. Measured
  disagreements are the good kind.

*Write-ups with charts: the audits publish on Reddit (u/Finance__broski) and
[LinkedIn](https://www.linkedin.com/in/ayanjain259). To have this class of check run on your own
backtest: [Bias Check](https://forms.gle/sAvosfHnitCBm9FD7) — fixed price, 48h, written verdict.*
