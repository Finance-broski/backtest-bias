# Selection Look-Ahead Is Not a Data Problem: Measuring the Leak in a Screening Rule's Labels

**Ayan Jain**, Independent Researcher.
*Working paper. This version: September 6, 2026. Comments welcome.*

## Abstract

A screen chooses candidates on a window of history. When it then reports an "out-of-sample" result on the last part of that same window, the future has leaked into the choosing, even if every statistic inside the screen was computed walk-forward. We measure this leak on a weekly pairs screen that tests about 1.7 million combinations of liquid US stocks and ETFs. When every accept-or-reject decision is recomputed inside each test year, so that no decision can see the year it is judged on, the screen's apparent edge disappears: the gap between accepted pairs and correlation-matched rejected pairs falls from about eleven log points a year to slightly below zero. Splitting the pairs accepted in-era by one bit of future information, whether the full-window rule would also have accepted them, isolates the leak: that bit is worth about fourteen log points a year, more than the edge that had been measured. A positive control shows the same code recovering a planted edge, and a prevalence sweep bounds what the clean test could have missed. The protocol is released as a check in an open-source package, with a within-era permutation test in place of sign counts, and placebo labels are shown to read clean. The finding concerns a rule's labels, not pairs trading; the commercial screens examined share the construction that produces it.

**Keywords:** look-ahead bias; selection bias; backtesting; pairs trading; cointegration; permutation tests
**JEL codes:** C12, C52, C58, G11, G14

## 1. Introduction

Look-ahead in backtesting is usually discussed as a data problem: a fundamental dated by its fiscal period rather than its announcement, an index membership applied backwards, a hedge ratio fitted on the whole window and used from day one. These are computational look-aheads. They live in the arithmetic, and the remedy is well known: compute each quantity from data available at the time, walk the estimate forward, and hold a period back.

A second look-ahead survives all of that. A screen is a rule that decides which candidates to look at. When the rule is run on a full window of history and the candidates it accepts are then evaluated on the last year of that window, the evaluation year was inside the data that chose them. Every hedge ratio can be walk-forward and every z-score honest, and the accepted set still knows the year it is judged on, because a relationship that failed during that year was less likely to have been accepted in the first place. The leak is in the label, not in the arithmetic, and no amount of data hygiene removes it.

The construction is not unusual. It is how the two commercial pairs screens examined for this work describe their own outputs, and it is how the screen studied here worked until 25 August 2026, when the measurement below was made.

The multiple-testing literature on backtests treats the number of trials as the quantity that inflates a reported result: Bailey, Borwein, López de Prado and Zhu (2017) on the probability of backtest overfitting, Bailey and López de Prado (2014) and López de Prado and Porcu (2026) on the deflated Sharpe ratio, and Harvey, Liu and Zhu (2016) on the cross-section of expected returns. Selection look-ahead is a different inflation: a single trial whose selection step saw its own evaluation period. The pairs-trading literature from Gatev, Goetzmann and Rouwenhorst (2006) through the survey of Krauss (2017) forms pairs on a formation period and trades them on a subsequent one, which is the honest construction; the leak enters when a screen is re-run on a window that contains the trading period and its output is then described as out of sample.

This paper's contribution is to measure that leak on one screen and to release the measurement as an instrument. We show that the screen's apparent edge, a gap of about eleven log points a year between accepted and correlation-matched rejected pairs, disappears when the label is recomputed inside each test year (Section 4.2); that one bit of future information, whether the full-window rule also accepts a pair the in-era rule accepted, is worth about fourteen log points a year, more than the edge it was inflating (Section 4.3); that the same code recovers a planted edge, and that the clean test would have detected genuine cointegration in as little as half a percent of tested pairs (Section 4.4); and that the check, released in version 0.3.0 of the backtest-bias package, reproduces the result on a fresh sample and reads clean on placebo labels (Section 4.5).

## 2. The screen and the data

The screen tests every pair among roughly 1,900 liquid US names on 2,500-session windows, 1.7 million combinations a week. Acceptance requires the Engle and Granger (1987) residual test to clear the MacKinnon (1991) finite-sample critical value in both orientations, with a false-discovery q-value beside every statistic. Hedge ratios are estimated by total least squares and re-fitted walk-forward for standings; half-lives carry the small-sample correction; capacity is measured from dollar volume with the binding leg identified; the price source's survivorship gaps are measured and printed, following the companion paper (Jain, 2026).

The rule's true size was measured rather than assumed. Against a null built from real series rotated out of alignment, and against a joint bootstrap that resamples the two legs' daily returns as pairs, so that correlation is preserved to three decimals while every long-run tie is destroyed, the two-orientation rule at a nominal 5% accepts 2.0 to 2.7% of pairs that are false by construction. On independent random walks of 1,000 observations the released code gives 4.95% for one orientation and 1.95% for both, the same number by a different route.

## 3. Method

**The contaminated test.** Take the accepted set as the stored screen labelled it, on the full 2,500-session window. Hold back the last 250 sessions. Trade both arms through the same fixed rule: enter at two standard deviations of the formation spread, exit at half, stop at twenty sessions, twenty basis points a round trip. Match the rejected arm to the accepted arm on return correlation, in ten quantile bins, so the comparison is not a comparison of relatedness. Outcomes are in log points over the held-back year.

**The clean test.** Recompute the label inside each era. End the formation window before the year being traded, test both orientations on that window alone, take the finite-sample critical value for that window's own length, and only then trade forward. A pair may be accepted in one year and rejected in the next, which is the point. Six thousand pairs, six eras of 250 sessions.

**Locating the leak.** Take only the pairs accepted in era, on pre-split data alone, and split them by whether the stored full-window screen also accepted them. Both groups passed the identical test on identical evidence. The only difference between them is information from the future.

**Positive control.** Synthetic pairs are built with a stated fraction whose spread is a genuine Ornstein-Uhlenbeck process of known half-life, the rest independent random walks sharing a market factor so that both groups carry similar correlation. The identical accept-and-trade code is run with the same split, the same critical value and the same rule, first with the tie strong enough that every planted pair is accepted, then weakened until acceptance rates match the real screen's.

**Strength claims.** A cross-era t is reported for scale only: adjacent formation windows share most of a decade of data and most of their names, so six era gaps are not six independent observations. The claims rest on the count of eras in which the sign holds and, in the released instrument, on a one-sided permutation p-value from shuffling group membership within each era, which keeps every era's sizes and distribution and assumes nothing across eras.

**Code and data.** Every number in Section 4 is produced by public code: the protocol document SELECTION_LOOKAHEAD.md and the free 21 August 2026 build in the PairDesk repository (github.com/Finance-broski/pairdesk), and version 0.3.0 of the backtest-bias package (PyPI; GitHub tag v0.3.0; Zenodo 10.5281/zenodo.22373468). The vintage is us_2026-08-21_lb2500_n1845_3f61ab. Prices are survivorship-blind, with the cost measured.

## 4. Results

### 4.1 The contaminated test (Table 1)

| arm | n | mean, log points | positive | return correlation |
|---|---|---|---|---|
| accepted | 3,000 | +0.1030 | 53.4% | 0.365 |
| rejected | 3,000 | +0.0004 | 31.2% | 0.306 |
| rejected, correlation matched | 3,000 | -0.0099 | 30.9% | 0.373 |

A gap of eleven log points in the held-back year, not explained by correlation. Repeated era by era it was positive in six years of six with a mean of +0.055, and the accepted arm alone was positive in six of six. A vendor with this table has a product.

### 4.2 The clean test (Table 2)

| era | accept rate | accepted | rejected, matched | gap |
|---|---|---|---|---|
| year 1 back | 4.00% | -0.0010 | -0.0026 | +0.0016 |
| year 2 back | 4.05% | -0.0227 | +0.0041 | -0.0268 |
| year 3 back | 4.43% | -0.0094 | +0.0036 | -0.0130 |
| year 4 back | 4.47% | +0.0190 | +0.0466 | -0.0276 |
| year 5 back | 3.95% | -0.0023 | +0.0325 | -0.0348 |
| year 6 back | 4.28% | -0.0488 | -0.0228 | -0.0259 |

Mean gap -0.0211, positive in one year of six. The accepted arm loses money in five of six years. Correlation matching is identical between this and the contaminated run; the only thing that changed is where the label came from. A cross-era t computes to -3.92 and should not be quoted as one, for the reason given in Section 3.

### 4.3 Locating the leak (Table 3)

| group | mean, log points | positive eras |
|---|---|---|
| the full window also accepted it | +0.0884 | 6 of 6 |
| it did not | -0.0504 | 1 of 6 |
| difference | +0.1388 | 6 of 6 |

One bit of future information, whether the relationship still looked cointegrated once the test year was folded in, is worth fourteen log points a year. That is larger than the edge that was being measured. The gap is not partly look-ahead. The gap is the look-ahead.

The mechanism is visible in synthetic controls. A relationship that reverted for years and then died still passes the full-window test 78 to 88% of the time, because a decade of history outvotes the dead stretch. The test finds relationships that existed. It does not know whether they still do, and the full-window label is therefore, in part, knowledge of whether the relationship survived the year it is about to be judged on.

Two consequences follow for anyone reporting figures from a screen of this kind. A full-window "out-of-sample" figure is the first row of Table 3 alone. Its inflation over the honest in-era figure is the difference times the share of in-era accepts the full window drops; on the sample of Section 4.5 that inflation is +0.112 log points per era. And no ranking computed on the full window survives either: the screen's own Sharpe column ranked the held-back year at a rank correlation of 0.150, monotone across deciles; recomputed before the split across five eras and 30,000 pair-years, none of seven formation columns reaches two standard errors, the Sharpe column sits at 0.28 standard errors and the ADF statistic at 0.14, and the best formation-Sharpe quintile finishes below the worst.

### 4.4 Positive control and the prevalence bound (Tables 4 and 5)

A negative result is worth what the instrument that produced it is worth. Table 4 reports the planted-edge control; purity is the share of accepted pairs that are genuine.

| planted half-life | accept, genuine | accept, independent | purity | gap |
|---|---|---|---|---|
| 15 sessions | 100.0% | 2.1% | 89.5% | +0.120 |
| 25 sessions | 100.0% | 2.1% | 89.5% | +0.092 |
| 40 sessions | 99.8% | 2.1% | 89.4% | +0.081 |

The instrument recovers a planted edge. The 2.1% acceptance on independent pairs confirms the bootstrap's estimate of the rule's size by a different route, and the gap it recovers, +0.08 to +0.12, is the size of the contaminated result on real data. The look-ahead was worth about as much as a real relationship would have been.

Weakening the planted tie until acceptance rates are realistic bounds what the clean test could have missed (Table 5).

| prevalence of genuine ties | accept rate | purity | gap |
|---|---|---|---|
| 15% | 16.9% | 89.0% | +0.046 |
| 8% | 10.0% | 79.9% | +0.044 |
| 4% | 6.1% | 65.4% | +0.041 |
| 2% | 4.2% | 48.0% | +0.032 |
| 1% | 3.2% | 31.4% | +0.027 |
| 0.5% | 2.7% | 18.6% | +0.023 |

The real screen accepts 4.2% of what it tests, which sits on the 2% row, where the gap would be +0.032. Measured, it is -0.021, and the six era gaps have a standard deviation of 0.013 around it, so even the best era, +0.002, sits below +0.032. Genuine cointegration in even half a percent of tested pairs, at a strength that clears twenty basis points of cost, would have produced a visibly positive gap. The bound is conditional on that strength: a real tie whose spread cannot cover costs is invisible here, and untradeable, which is the same conclusion.

### 4.5 The instrument, released, and its reproduction (Table 6)

The protocol is a check in version 0.3.0 of backtest-bias, check_selection. It takes a price panel, a list of candidates, and three callables: select, which accepts or rejects candidates given a formation window and nothing else; score, which returns a forward outcome for a candidate over a held-out window; and match_key, a nuisance value on which rejected candidates are matched to accepted ones. Reference callables implement the pairs screen above, so the check runs on a panel and a list of pairs with no other code; any other screen is audited by passing its own. The check walks the history backwards in eras, recomputes the label inside each, scores both arms, and reports three numbers: the clean gap, the hindsight difference, and the full-window inflation.

Four properties of the instrument were established during a sequence of audits, each a way the instrument could have lied. First, strength claims are permutation p-values, not sign counts: a fair coin lands five eras of six 11% of the time, so a verdict resting on "positive in five of six" condemns by chance at that rate. Under the null the p is uniform: across 400 draws of no-difference groups on era scales from 1 to 100,000, 6.0% fall below 0.05, 11.3% below 0.10 and 21.5% below 0.20. Second, the hindsight split needs adequate groups: a placebo label with no information about the future, run on the real sample, read as a severe leak in one draw of three when it overlapped the in-era accepts in a handful of pairs per era, since a difference between two five-pair means runs to five positive eras in six by chance. An era's split now counts only when both groups have at least ten members, and such placebos read "too thin to say". Third, placebo labels with large groups read clean: random labels covering half the candidates give p-values of 0.84, 0.24 and 0.39 on the real sample. Fourth, the candidate pool must come from the population: a pool assembled from the screen's own stored accept and reject lists already carries the full-window label, and the clean gap comes out positive for that reason alone. This error was made in the first version of the measurement, and the package documentation records it.

Table 6 reports the reproduction with the released code: three thousand pairs drawn from the population of the 21 August 2026 vintage, six eras of 250 sessions, the stored vintage's labels as the full-window set, 999 shuffles.

| number | value | eras positive | permutation p |
|---|---|---|---|
| clean gap | -0.0103 per era | 2 of 6 | 0.777 |
| hindsight difference | +0.1531 per era | 6 of 6 | 0.001 |
| full-window inflation | +0.1121 per era | | |

Different sample, same shape as Tables 2 and 3. The verdict line reads severe, with the reason printed, and the clean-gap line says what it should: the rule itself shows no forward information, which is a finding about the rule, not a fault in the data. The matching held: the mean return correlation of the two arms differed by 0.010 across the six eras.

## 5. Implications

1. **An "out-of-sample" figure from a screen is only as honest as the screen's labels.** If the acceptance decision was made on a window containing the evaluation period, the figure is contaminated regardless of how the statistics inside the screen were computed. The remedy is to recompute the label inside each era, which is a change to the protocol, not to the arithmetic.
2. **The leak is measurable and can exceed the edge.** On this screen one bit of future information was worth fourteen log points a year against a measured edge of eleven. A screen that has not measured its own leak cannot say what fraction of its reported edge is real.
3. **Strength claims across eras need a test that assumes nothing across eras.** Formation windows overlap, so a cross-era t overstates; a sign count condemns a fair coin one time in nine. A within-era permutation test does neither.
4. **Rankings computed on the full window inherit the same leak.** A formation-period column that ranks the held-back year at a rank correlation of 0.150 ranks nothing once the label is recomputed before the split.

## 6. Limitations

This paper does not say that pairs trading does not work. It says that this screen's labels, on this universe, under one fixed rule, carry no forward information that survives honest labelling, and that the full-window label carries a great deal, all of it from the future. One trading rule was tested. Six eras of 250 sessions overlap heavily in formation data. Around 250 pairs pass in each era and they overlap in names. The honest reading of the clean gap is that it is not detectably positive rather than that it is reliably negative, and Section 4.4 says what "not detectably" means in prevalence terms. Findings measured independently of the acceptance label are unaffected: capacity, survivorship, transaction costs, market neutrality and the borrow distribution.

## References

- Bailey, D. H., Borwein, J. M., López de Prado, M., and Zhu, Q. J. (2017). The probability of backtest overfitting. *Journal of Computational Finance*, 20(4), 39-69.
- Bailey, D. H., and López de Prado, M. (2014). The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. *Journal of Portfolio Management*, 40(5), 94-107.
- Engle, R. F., and Granger, C. W. J. (1987). Co-integration and error correction: Representation, estimation, and testing. *Econometrica*, 55(2), 251-276.
- Gatev, E., Goetzmann, W. N., and Rouwenhorst, K. G. (2006). Pairs trading: Performance of a relative-value arbitrage rule. *Review of Financial Studies*, 19(3), 797-827.
- Harvey, C. R., Liu, Y., and Zhu, H. (2016). ... and the cross-section of expected returns. *Review of Financial Studies*, 29(1), 5-68.
- Jain, A. (2026). Survivorship bias in Indian equities is not a number: Vintage- and filter-dependence in point-in-time universes. Working paper, SSRN 7099378.
- Krauss, C. (2017). Statistical arbitrage pairs trading strategies: Review and outlook. *Journal of Economic Surveys*, 31(2), 513-545.
- López de Prado, M., and Porcu, E. (2026). The deflated Sharpe ratio: A unified framework for search-adjusted performance inference. Working paper, SSRN 7198158.
- MacKinnon, J. G. (1991). Critical values for cointegration tests. In R. F. Engle and C. W. J. Granger (Eds.), *Long-Run Economic Relationships: Readings in Cointegration* (pp. 267-276). Oxford University Press.

## Acknowledgments

The author thanks Heather Dempsey, whose memo of 5 September 2026 argued that the protocol should be released as an instrument rather than as a document.

## Declaration: Generative AI in the writing and analysis process

During the preparation of this work the author used Claude (Anthropic) to assist with drafting and with the implementation of the analyses. The measurements follow the public protocol document, and the analysis code is released; the author reviewed, verified, and edited all content and takes full responsibility for the content of this publication.

## Conflict of interest

The author sells the screen studied in this paper as a subscription product and operates a commercial backtest-audit practice. The result reported here is printed on the product's own page.
