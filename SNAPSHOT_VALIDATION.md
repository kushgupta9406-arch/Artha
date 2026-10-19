# ARTHA Snapshot validation note

Validation was run on a rebuilt copy of the supplied Capitaline model so the working historical/live outputs were not altered.

## Coverage

Broad non-TOPSIS universe: **3,603** companies.

Historical valuation mode:
- **2,197** receive a full ARTHA Snapshot (quality + valuation).
- **971** receive a quality-only Snapshot because valuation evidence is insufficient.
- **435** remain data-limited and show raw available metrics only.
- Total broad companies receiving at least a current quality assessment: **3,168 / 3,603 = 87.9%**.

Using the saved live-price overlay, **2,245** receive a full Snapshot and **923** a quality-only Snapshot; the total assessed population remains 3,168.

## Cross-check against the existing full model

The Snapshot is deliberately not fitted to reproduce TOPSIS. The existing full-model companies were used only as a validation set.

Among 339 rankable companies with enough Snapshot inputs:
- Spearman correlation, Snapshot vs full TOPSIS score: **0.581**.
- Spearman correlation, Snapshot quality vs full-model Q: **0.625**.
- Spearman correlation, Snapshot valuation vs full-model V: **0.613**.

This is a useful positive relationship without making the lightweight model a disguised copy of TOPSIS.

## Skew checks

- Spearman correlation of Snapshot score with log market cap: **0.068** — very low, so the Snapshot is not materially a size score.
- Mean Snapshot scores by sector ranged from **50.87 to 56.64**, a spread of **5.77 points**, supporting the sector-relative design rather than a large systematic sector tilt.
- Missing values are not median-imputed. Pillar scores are shrunk toward neutral 50 as coverage falls, and data coverage is shown separately.
- Non-positive P/E, P/B and EV/EBITDA are excluded rather than rewarded as “cheap”. Negative-net-worth D/E is excluded.

## Example: Balu Forge

On the supplied historical universe, Balu Forge receives:
- Snapshot: **71.6 / 100 (Strong)**
- Quality: **81.9**
- Valuation: **47.6**
- Data coverage: **100%**

Using the supplied saved live-price snapshot, its valuation changes and the Snapshot becomes about **72.2**, while the frozen quality score remains unchanged. This confirms that Live mode changes the market-sensitive Snapshot component without rewriting fundamentals.

## Separation from TOPSIS

No original full-model ranking output is modified by Snapshot. TOPSIS rank, Q/V, ratings, robustness tests and sector-level rankings continue to come from the original full model. Snapshot is computed in memory from the currently selected Historical/Live broad universe and produces no rank.
