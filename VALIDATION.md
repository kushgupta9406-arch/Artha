# ARTHA performance validation (Karl Pearson correlation)

Code: `pipeline/validation.py` · App page: **Performance validation** · Output: `data/validation/`

## The question

Do companies that ARTHA ranks higher go on to deliver higher stock returns than their sector peers?

## Two tests, kept separate

**A. Point-in-time backtest — predictive (the test that counts).**
ARTHA is rebuilt exactly as it would have looked at an earlier fiscal year-end. The Capitaline
ten-year arrays are sliced so FY25, FY23 or FY21 becomes the "latest year", and every step is
recomputed from that data only: features, the 60% criterion-coverage rule, winsorisation,
subjective + Entropy + CRITIC weights, Quality and Valuation TOPSIS, the 70:30 blend, ratings,
the Level-2 sector model and AlphaPct. The ranking is formed on 1 July after the year-end
(annual results are public by then) and forward total returns are measured:

| As-of data | Formed | Forward window |
|---|---|---|
| FY25 | 1 Jul 2025 | 1 year |
| FY23 | 1 Jul 2023 | 3 years |
| FY21 | 1 Jul 2021 | 5 years |

A 10-year point-in-time test is not possible: the Capitaline file holds ten years and the
five-year criteria need history before the start date.

**B. Current ranking vs trailing 1/3/5/10-year returns — descriptive only.**
Today's ranking (live if available) against past returns. This does not show predictive power:
growth and price-to-52-week-high criteria partly reflect the same history, and the valuation
pillar penalises stocks that have already rallied.

## The statistic

For each company, *x* = ARTHA percentile inside its sector and *y* = return percentile inside the
same sector. Pearson's r = cov(x, y) / (σx σy). Using percentiles keeps a few multi-baggers from
dominating r (it is then close to Spearman's ρ, which is also reported). The cross-sector
version uses AlphaPct against the raw return percentile.

Reported for every window: r, p-value, Fisher-z 95% confidence interval, n; average return by
ARTHA quintile and the Q1−Q5 spread with a 1,000-shuffle permutation p-value; equal-weight
return of the top 5/10/20 picks vs the universe and the Nifty 50; the top 10 ARTHA picks with
their returns; the 10 best-returning stocks with their ARTHA percentile; r inside each sector.

Returns are annualised total returns from Yahoo Finance prices adjusted for dividends and splits.

## How to read the result honestly

- In published equity research, the correlation between a fundamental score and next-period
  returns (the information coefficient) is usually 0.02–0.15. A stable 0.05–0.10 is useful.
- A stock-level r above 0.7 with *future* returns does not occur in genuine out-of-sample tests.
  If you ever see one, look for look-ahead bias first. ARTHA does not tune anything to raise r.
- The "5-bucket r" (correlation across the five quintile averages) can reach ±0.7 by chance
  with only five points. During testing on randomly generated prices it came out at 0.72 for one
  window. That is why it is shown with a permutation p-value and is not used as the headline.
- What would count as good evidence: a positive sector-neutral r whose confidence interval
  excludes zero, a positive Q1−Q5 spread with permutation p < 0.05, and the same sign across the
  1/3/5-year windows.

## Limitations

- Survivorship bias: the universe is today's Capitaline company set.
- Promoter-holding change is not available point-in-time, so the coverage rule drops it in the backtests.
- Yahoo prices can miss corporate actions for a few names; NSE-unmapped companies are excluded.
- Small sectors give unstable per-sector r; read those as colour, not evidence.
