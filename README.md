# backtest-bias

[![DOI](https://zenodo.org/badge/1294836988.svg)](https://doi.org/10.5281/zenodo.21770386)

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

## Citing this

If you use the library or the measured constants in [BIAS_TABLE.md](BIAS_TABLE.md), cite it as:

> Jain, A. (2026). *backtest-bias: survivorship and integrity checks for financial price panels*.
> Zenodo. https://doi.org/10.5281/zenodo.22373468

That DOI is the concept DOI: it always resolves to the latest version. GitHub also reads
`CITATION.cff` in this repo, so the "Cite this repository" button in the sidebar produces BibTeX
and APA directly.

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

## What v0.3 adds: is the choosing honest?

The checks above ask whether the data is lying. `check_selection` asks whether the screen is.

A screen selects candidates on a window of history. If it then reports an "out-of-sample" result
on the last part of that same window, the future has leaked into the selection, even when every
hedge ratio and z-score was computed walk-forward. The leak is in the choosing, not in the
arithmetic, so no data hygiene removes it. Measured first on a US pairs screen, where the answer
to one question, would this pair also have been accepted with the test year included, was worth
13.9 log points a year and accounted for the entire apparent edge.

**How the check works.** It walks your history backwards in eras (250 sessions by default). In
each era the screen sees only the data before it, the formation window, and accepts or rejects
every candidate on that alone. Both groups are then scored forward through the era, with the
rejected group matched to the accepted one on return correlation so the comparison is not a
comparison of relatedness. Three numbers come back:

- **the clean gap**: accepted minus matched rejected, with labels recomputed inside each era.
  This is what the rule knows about the forward period when it cannot see it.
- **the hindsight difference**: among candidates accepted in era, the forward outcome of those
  the full-history screen also accepts, minus those it does not. Both groups passed the same test
  on the same evidence; the only difference is information from the future. This is what one bit
  of the future is worth, and it is the number that condemns a screen.
- **the full-window inflation**: how much an "out-of-sample" figure computed on full-history
  acceptance overstates the honest in-era figure.

```python
from backtest_bias import check_selection

# prices: long (date, symbol, close) or wide (dates x symbols) on a datetime index
# candidates: a few thousand drawn from the population the screen chooses among
candidates = [("KO", "PEP"), ("XOM", "CVX"), ("V", "MA")]     # (y, x) pairs for the built-in screen
rep = check_selection(prices, candidates, hold=250, n_eras=6)
print(rep.summary())
```

On a 3,000-pair sample of the PairDesk vintage, the summary reads:

```
selection look-ahead check: 3000 candidates, 6 eras of 250 sessions, labels recomputed inside each era
forward information of the rule: gap -0.0103 log points per era, positive in 2 of 6 eras, permutation p 0.777
worth of one bit of future information: +0.1531 log points per era, positive in 6 of 6 eras, within-era permutation p 0.001 (cross-era t +4.90 for scale only; eras overlap)
a full-window 'out-of-sample' figure overstates the honest one by +0.1121 log points per era
verdict: SEVERE - the full-history label carries forward information worth +0.1531 per era, positive in 6 of 6 eras, permutation p 0.001; ...
```

`rep.eras` holds the per-era table (accept rate, both arms, the gap, the match balance) and
`rep.hindsight` the per-era split. The p-values come from shuffling group membership within each
era, which assumes nothing across eras; a label with no information about the future reads clean
under them, which was checked with placebo labels on the same sample. The published protocol found -0.021 and +0.139 on a different
6,000-pair sample; same shape.

Two rules for reading it. Draw the candidates from the population the screen chooses among, never
from its stored accept and reject lists: a pool built from the screen's own labels already carries
the future, and the clean gap comes out positive and meaningless. And a negative clean gap on
noise is not a fault: a pair accepted on its formation window has a formation deviation that
understates its forward deviation, so a fixed rule trades it more and pays more cost.

Any screen is audited the same way by passing its own callables: `select(formation_window,
candidates)`, `score(formation_window, hold_window, candidate)` and `match_key(formation_window,
candidate)`, with `unit` naming what the score returns. If you already hold the screen's acceptance
on the full history, pass it as `full_accepted`. If the figures you have reported were computed with
labels recomputed inside each era already, say so with `labels_reported_in_era=True`; the hindsight
number is then informational and the verdict does not condemn them. The protocol and the
measurements behind it are written up in the
[PairDesk repository](https://github.com/Finance-broski/pairdesk/blob/main/SELECTION_LOOKAHEAD.md).

## What v0.2 adds

```python
from backtest_bias import check_identity, check_universe

# is each ticker the same company all the way through its series?
print(check_identity(prices).summary())

# was your member list knowable on the backtest's start date, and does it die like a real one?
print(check_universe(prices, universe=my_symbols, start="2015-01-01").summary())
```

| call | question it answers |
|---|---|
| `check_identity(prices)` | recycled tickers: a dead company's history silently stitched to a new listing on the same symbol. Four such tickers moved a measured US result by 1.7 pp/yr, more than the survivorship bias itself |
| `check_universe(prices, universe, start)` | the two signatures of today's list applied backwards: members whose data begins after the start date, and a universe whose start-alive names almost never die (measured death curves say they should) |

`REFERENCES` now carries the measured US constants alongside the Indian ones: survivor-filter effect +0.4 to +1.0 pp/yr by vintage, yearly gaps swinging -7.5 to +3.5, and the 1.7 pp/yr identity error.

## What v0.1 ships

| function | what it answers |
|---|---|
| `check_survivorship(prices)` | does my universe contain the stocks that died, or only the winners? Full report with severity and a measured bias estimate |
| `dead_name_ratio(prices)` | one number: what fraction of my names end before the panel does. `0.0` = pure survivor panel |
| `assert_integrity(prices)` | CI gate: raise if the panel smells survivor-only, so a silent re-download of bad data fails your pipeline instead of flattering your backtest |

Input handling is forgiving: wide panels, long frames, sniffed column names, NaN-padded
histories. Anything the library cannot judge honestly, it raises instead of guessing.

## Roadmap

- **v0.4**: price-level look-ahead and timestamp checks: fundamentals dated by period instead of
  announcement, same-bar signal fills
- **v0.5**: corporate-action gap detection

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

## The practice behind this

I audit backtests and datasets professionally. The public record, 155 strategies tested and 143 killed, lives at [financebroski.com/graveyard.html](https://financebroski.com/graveyard.html); the audit practice is at [financebroski.com](https://financebroski.com).
