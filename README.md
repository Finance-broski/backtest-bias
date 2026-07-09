# backtest-bias

**Checks whether your backtest data is lying to you.**

Most backtests don't fail loudly. They flatter you quietly, because the data underneath them is
missing the stocks that died. This library tests your price panel for that — in one line — and
tells you roughly what it costs when it finds it.

## The measured numbers this library is built on

These are not estimates. I measured them on real Indian market data and published the write-ups:

- **23%** of the top-500 Indian stocks (as of 2015) are invisible to yfinance today — delisted,
  merged, suspended. Any backtest built on it runs on survivors only.
- Survivor-only universes inflated equal-weight returns by **+0.8 to +2.5 pp/yr** depending on
  universe vintage — same market, same method, 3x difference. Anyone quoting one number is guessing.
- On the most widely used Kaggle NSE dataset, index-membership look-ahead added **+10%** terminal
  wealth cap-weighted and **+43%** equal-weighted over 2010-2021. The bias depends on construction.
- How much of a universe *should* be dead? Measured across six top-500 vintages (2012-2022,
  Indian equities), the curve is remarkably stable: **~6-8% by 3 years, 11-14% by 5, 17-21% by 7,
  24-30% by 10.** Verdicts quote the range matched to your window length. If your panel lost
  zero names, your panel is the problem.

## Install

```
pip install backtest-bias
```

## 30 seconds to a verdict

```python
import pandas as pd
from backtest_bias import check_survivorship

prices = pd.read_csv("my_panel.csv")   # wide (date x symbols) or long (date/symbol/close)
report = check_survivorship(prices)
print(report.summary())
```

```
survivorship check: 412 symbols over 9.2y, 0 died in-window (0%)
verdict: SEVERE - 412 names over 9.2y with zero deaths is the survivor-only signature;
comparable universes lose 22%-28% of names over 9y (measured)
expect EW returns inflated roughly +0.8-2.5 pp/yr vs an honest universe (measured,
vintage-dependent; see backtest_bias.REFERENCES)
```

## What v0.1 ships

| function | what it answers |
|---|---|
| `check_survivorship(prices)` | does my universe contain the stocks that died, or only the winners? Full report with severity and a measured bias estimate |
| `dead_name_ratio(prices)` | one number: what fraction of my names end before the panel does. `0.0` = pure survivor panel |
| `assert_integrity(prices)` | CI gate: raise if the panel smells survivor-only, so a silent re-download of bad data fails your pipeline instead of flattering your backtest |

Input handling is forgiving: wide panels, long frames, sniffed column names, NaN-padded
histories. Anything the library cannot judge honestly, it raises instead of guessing.

## Roadmap

- **v0.2** — look-ahead / point-in-time violations: fundamentals dated by period instead of
  announcement, index membership applied backwards, same-bar signal fills
- **v0.3** — rename-continuity and corporate-action gap detection

## Who

I'm [Ayan Jain](https://www.linkedin.com/in/ayanjain259). I build point-in-time Indian
equity data and audit backtests and datasets for bias — the measured numbers above come from
those audits. If you want this class of check run on your own backtest by a person instead of a
library, that's my [Bias Check](https://forms.gle/sAvosfHnitCBm9FD7): fixed price, 48h, written
verdict.

MIT licensed. Issues and war stories welcome — especially datasets that fooled you.
