# ARTHA — Live Market & Fundamentals Layer

## Why ~3,950 companies are not all full-TOPSIS ranked
The widened universe combines the multi-year Capitaline set with one-year/latest exports. Full ARTHA ranking needs enough observations for growth, cash conversion, consistency, historical valuation percentiles and other multi-year criteria. Only the full-history subset can satisfy the model's criterion/coverage gates without inventing data. The rest remain useful in the broad screener and sector views.

Live prices do **not** fix missing historical fundamentals, so Live mode intentionally keeps this distinction.

## Refresh flow
1. ARTHA downloads/caches the official NSE equity security list.
2. Capitaline Code + Company Name is matched to an NSE symbol using audited manual, direct-symbol and exact-name matches and saved in `data/live/ticker_map.csv`.
3. Yahoo Finance / `yfinance` requests recent 15-minute NSE prices for every mapped company, plus annual / quarterly / TTM statements for the ~350 full-model companies.
4. The heavier 2-year daily history is requested only for full-model companies, where ARTHA needs a 52-week high and a more corporate-action-tolerant historical price base.
5. Latest Yahoo statements are chain-linked onto the Capitaline history for the full-model companies (see below); broad-universe companies get the price overlay only.
6. The full model is rerun from scratch: blended weights, Q/V TOPSIS, 70:30 final score, WSM, 400 robustness draws, leave-one-pillar-out, ratings, Level-2 sector TOPSIS and AlphaPct.
7. The snapshot is written to `data/live/` and `web/artha_live.html`.
8. The app can switch back to Historical at any time.

## Live fundamentals (new)
Live mode no longer freezes fundamentals. For every full-model company with an audited NSE
ticker, `pipeline/live_fundamentals.py` downloads Yahoo Finance's annual, quarterly and
trailing-twelve-month (TTM) income statement, balance sheet and cash-flow statement.

**Joining Yahoo to Capitaline — chain-linking.** Yahoo and Capitaline define some lines
differently (EBITDA with or without other income, bank revenue, cash vs cash-and-bank).
Replacing one source with the other inside a series would show fake growth, so ARTHA uses the
standard index-splicing rule for each line item and ratio:

    latest value = Capitaline value at the last Capitaline year-end × (Yahoo latest ÷ Yahoo at that same year-end)

Capitaline keeps the definition and level; Yahoo contributes only the change since then (e.g.
TTM to June 2026 vs FY26). If a ratio is not meaningful (sign change or more than a 5× move) the
change is added instead. Items with no newer Yahoo period (Indian quarterly cash flow is usually
missing) keep their Capitaline value.

**Sanity gate.** Yahoo's figure for the same fiscal year is compared with Capitaline's (sales
for industrials, net worth for lenders). If they differ by more than 2× (1.67× for lenders) the
Yahoo statements are rejected for that company — usually a wrong ticker or units — and only the
price overlay is applied. Each company's tear sheet says which source was used.

**Recomputation.** The live arrays go through `features_core.compute_features`, the same function
the historical build uses, so every ratio (ROCE, ROE, margins, CAGRs, D/E, interest cover,
cash quality, P/E, EV/EBITDA, P/B, FCF yield, valuation vs own history, Piotroski and the flags)
is recomputed. When period 0 is a TTM window ending after the fiscal year-end, CAGRs use the
true elapsed time (e.g. 3.25 years). The full method then reruns unchanged.

**Outputs** in `data/live/`: `provenance.csv` (source, latest period and link method per company
and item), `reconciliation.json` / `reconciliation_detail.csv` (Yahoo vs Capitaline for the same
year: median ratio, share within 5% and 20%), and `status.json`.

**Not on Yahoo for Indian companies:** promoter holding (Capitaline File 11 values are kept) and
bank asset quality (not in either source).

Command line: `python pipeline/live_refresh.py` (add `--prices-only` for the old behaviour,
`--force` to ignore the 20-hour statements cache).

## Valuation update logic (prices-only mode)
- Current market cap: historical market cap scaled by the change in market price. For full-model names the Yahoo historical adjusted price is used as the fiscal-year-end scaling base where available; otherwise the Capitaline year-end NSE price is the fallback.
- P/E and P/B: historical model multiple × current market-cap factor (equivalent to holding the latest model earnings/net worth fixed).
- EV/EBITDA: historical EV plus the change in equity market cap, with net debt and EBITDA held fixed.
- FCF yield: historical FCF yield divided by the market-cap factor.
- Price/high: current price ÷ current 52-week high.
- Historical valuation percentiles: current multiple is re-compared with the company's historical multiple series.

## NSE-only consequence
Not every company in the broad Capitaline universe is currently NSE-listed. Because this build is deliberately NSE-only, those names do not get a substituted BSE quote. Their saved Capitaline valuation remains in place and the model marks the quote state as stale internally.

## Manual symbol correction
Open `data/live/ticker_map.csv` after the first refresh. For any mapping you want to override:

1. Find the Capitaline `code` / `capitaline_name` row.
2. Put the correct NSE symbol in `nse_symbol` (for example `TCS`, not `TCS.NS`).
3. Set `manual` to `1`.
4. Save and refresh Live mode.

Manual rows are preserved on future automatic map rebuilds.

## Provider note
`yfinance` is suitable for this local research/education build. If ARTHA is later published commercially or needs SLA-grade data, replace `pipeline/live_prices.py` with an appropriately licensed market-data provider; the ranking code does not need to change.


## Mapping safety

The submission build disables automatic fuzzy ticker assignment by default. Ambiguous names remain unmatched/stale until explicitly mapped; this prevents a similar company name from silently receiving another security's live price.
