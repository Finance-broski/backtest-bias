# backtest-bias

**Checks whether your backtest data is lying to you.**

Most backtests don't fail loudly. They flatter you quietly, because the data underneath them is
missing the stocks that died. This library tests your price panel for that, in one line, and
tells you roughly what it costs when it finds it.

## The measured numbers this library is built on

These are not estimates. I measured them on real Indian market data and published the write-ups:

- **24%** of the top-500 Indian stocks (as of 2015) are invisible to yfinance today: delisted,
  merged, or renamed with no public mapping. A universe built by fetching current listings runs
  on survivors only.
- Survivor-only universes inflated equal-weight returns by **+0.8 to +3.2 pp/yr** depending on
  the universe vintage and the survivor definition. Same market, same method, a factor of four
  apart. Anyone quoting one number is guessing. (Working paper under review at SSRN.)
- On the most widely used Kaggle NSE dataset, index-membership look-ahead added **+10%** terminal
  wealth cap-weighted and **+43%** equal-weighted over 2010-2021. The bias depends on construction.
- How much of a universe *should* be dead? Measured across six top-500 vintages (2012-2022,
  Indian equities), the curve is stable: **~5-8% by 3 years, 11-14% by 5, 17-21% by 7, 24-30% by
  10.** Verdicts quote the range matched to your window length. If your panel lost zero names,
  your panel is the problem.

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
expect EW returns inflated roughly +0.8-3.2 pp/yr vs an honest universe (measured,
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

- **v0.2**: look-ahead / point-in-time violations: fundamentals dated by period instead of
  announcement, index membership applied backwards, same-bar signal fills
- **v0.3**: rename-continuity and corporate-action gap detection

## Who, and how to get this run on your own data

I'm [Ayan Jain](https://www.linkedin.com/in/ayanjain259). I build point-in-time Indian equity
data and audit backtests and datasets for the biases that inflate them. The measured numbers
above come from those audits.

If you want this class of check run on your own backtest or dataset by a person instead of a
library, that's my **Bias Check**: you send the backtest or data, and within 48 hours you get a
written verdict on survivorship, look-ahead / point-in-time integrity, cost realism, and marking,
with what's wrong and roughly what it costs in return terms. Fixed price, Rs 7,500. Start it
through the [intake form](https://forms.gle/sAvosfHnitCBm9FD7) or email ayanjain259@gmail.com.
Larger or ongoing work is scoped separately, tell me the problem and I'll send a quote.

**Public data and replication:** a survivorship-free Indian equity dataset (NSE/BSE) and a
runnable notebook that visualizes the bias on a sample are on Kaggle under
[financebroski](https://www.kaggle.com/financebroski) (the
[dataset](https://www.kaggle.com/datasets/financebroski/survivorship-free-indian-equity-data-nsebse)
and the [notebook](https://www.kaggle.com/code/financebroski/survivorship-bias-visualized-indian-equity-sample)).

**The Bias Table:** every measured number behind this library, one page, citable:
[BIAS_TABLE.md](BIAS_TABLE.md). New rows land by email at
[The Bias Ledger](https://financebroski.substack.com).

MIT licensed. Issues and war stories welcome, especially datasets that fooled you.
