# ARTHA Snapshot methodology

ARTHA Snapshot is a **current assessment, not a ranking**. It exists for companies in the widened ARTHA universe that do not have enough multi-year history for the full TOPSIS model.

## What remains unchanged

The original full-model universe, TOPSIS ranks, Entropy/CRITIC weighting, robustness simulations, ratings and sector model are untouched. Snapshot never writes into the full-model `rank`, `score`, `Q` or `V` fields.

## Scoring logic

Snapshot converts each usable metric into a 0–100 peer percentile. The reference group is the company's sector when at least 8 observations exist for that metric; otherwise it falls back to the same company family, and finally to the broad universe. This prevents a bank from being judged on the same raw profitability scale as a manufacturer while still handling small or unclassified groups.

The final score preserves ARTHA's **70% quality / 30% valuation** philosophy. Industrial companies use current profitability, growth, leverage/coverage, cash conversion and valuation multiples. Banks, NBFCs, capital-market companies and insurance/holding companies use family-specific profiles so structurally inappropriate industrial ratios are not applied.

Missing company values are **not imputed**. Available metrics are combined inside their pillar, then the pillar score is shrunk towards a neutral 50 in proportion to data coverage. This prevents a company with only a handful of available metrics from receiving an unjustifiably extreme score. An overall Snapshot requires at least three quality metrics with at least 50% of intended quality weight and at least one valuation metric with at least one-third of intended valuation weight. If the quality hurdle is met but valuation is not, ARTHA shows a **Quality-only Snapshot** and deliberately withholds the overall score rather than silently changing the 70/30 model.

Non-positive P/E, P/B and EV/EBITDA are excluded instead of being interpreted as cheap. Debt/equity is excluded where net worth is non-positive.

## Labels

- **Strong:** score >= 70
- **Favourable:** 60–69.9
- **Balanced:** 45–59.9
- **Cautious:** 35–44.9
- **Weak:** < 35

These are Snapshot views, not investment recommendations and not TOPSIS ratings.

Data confidence is displayed separately: High at >=85% intended metric weight, Medium at 65–84.9%, and Limited below 65%.
