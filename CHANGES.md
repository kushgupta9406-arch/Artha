# What changed in this version

## 1. Fully live ARTHA ranking
- `pipeline/features_core.py`: the per-company feature formulas were moved out of `build.py` into one
  function. Historical build, Live mode and the backtest all call it. Rebuilding the historical model
  reproduces the submitted `features.pkl`, `rank.pkl` and `data.json` exactly.
- `pipeline/live_fundamentals.py` (new): downloads Yahoo annual / quarterly / TTM statements for the
  full-model companies, chain-links the newest period onto the Capitaline history, rejects companies
  whose Yahoo figures don't reconcile with Capitaline for the same year, and writes provenance and a
  reconciliation report.
- `pipeline/live_refresh.py`: the refresh now runs prices + fundamentals, recomputes every ratio,
  and reruns the full method (blended weights, Q/V TOPSIS, 70:30, WSM, 400 draws, LOPO, ratings,
  Level-2, AlphaPct). `--prices-only` keeps the old behaviour.
- Company pages show which period and source each company's live fundamentals came from.

## 2. Ask ARTHA on the server
- `pipeline/ask_artha.py` (new): Claude with eight lookup tools over ARTHA's own data (sectors,
  companies, comparisons, screens, methodology and weights, data status, validation results).
- New **Ask ARTHA** page in the app. The key is read from Streamlit secrets or an environment
  variable on the server; visitors never see or enter it. Per-session and per-day question caps.
- Admin password (`ARTHA_ADMIN_PASSWORD`) gates refresh, rebuild and validation on a public deployment.
- `DEPLOY.md`: step-by-step Streamlit Community Cloud deployment.

## 3. Performance validation (Karl Pearson)
- `pipeline/validation.py` (new) + **Performance validation** page: point-in-time backtests
  (FY25→1Y, FY23→3Y, FY21→5Y) and descriptive trailing tests (1/3/5/10Y). Pearson r with p-value
  and 95% CI, Spearman, quintile spreads with permutation tests, top-10 picks and top-10 returners,
  per-sector r. See `VALIDATION.md`.

## Other
- `requirements.txt`: adds `anthropic`.
- `.streamlit/config.toml`: hides the developer toolbar for visitors.
- The dashboard's built-in Ask tab now points visitors to the Ask ARTHA page.
