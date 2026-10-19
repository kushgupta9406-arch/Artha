# ARTHA — Sector Intelligence & Ranking Desk

ARTHA is a Streamlit equity-research application built from Capitaline financial data.

## Model structure

- **Full model:** 351 companies have the multi-year dataset used by the full methodology.
  346 currently satisfy the historical criterion-coverage gate and receive an official
  sector TOPSIS rank.
- **ARTHA Snapshot:** companies in the wider universe that lack sufficient multi-year
  history can receive a separate 0–100 sector-relative current assessment. Snapshot is
  deliberately **not** an official TOPSIS rank.
- **Historical mode:** uses the supplied Capitaline year-end data.
- **Live mode:** fetches current NSE prices **and the latest Yahoo Finance statements** (TTM where
  available), chain-links them to the Capitaline history, recomputes every ratio and reruns the
  full model (weights, TOPSIS, 70:30 blend, WSM, robustness). See `LIVE_MARKET_SETUP.md`.
- **Ask ARTHA:** an assistant on the server (free offline mode by default, free Groq AI or Claude optional), answering from ARTHA's own rankings, weights,
  methodology and validation results through lookup tools. Visitors need no API key. See `DEPLOY.md`.
- **Performance validation:** Karl Pearson correlation between ARTHA percentiles and realised
  returns — point-in-time backtests (FY25→1Y, FY23→3Y, FY21→5Y) and descriptive trailing tests
  (1/3/5/10Y), with confidence intervals, quintile spreads and top-10 tables. See `VALIDATION.md`.

See `SNAPSHOT_MODEL.md`, `SNAPSHOT_VALIDATION.md`, `LIVE_MARKET_SETUP.md`, `VALIDATION.md` and `DEPLOY.md`.

## Run the application

Python 3.10+ is required.

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux, activate/use the equivalent `.venv/bin/python`.

Streamlit normally opens:

`http://localhost:8501`

Historical mode works immediately from the supplied processed files.

## Live market mode

Live mode requires an internet connection.

1. Open the app.
2. Select **Live** under Market data.
3. Keep **Include latest fundamentals** on and click **Refresh live data & rerank**
   (or run `python pipeline/live_refresh.py`). The first run downloads statements for ~350
   companies and takes about 10–15 minutes; repeat runs within 20 hours reuse the cache.
4. Wait for the refresh and complete reranking to finish.

## Ask ARTHA

Works with no key in free **offline mode**. For free-form AI answers at no cost, create a free key at
<https://console.groq.com/keys> and put `GROQ_API_KEY = "gsk_..."` in `.streamlit/secrets.toml`
(copy `secrets.toml.example`). `ANTHROPIC_API_KEY` (paid) also works.

## Performance validation

`python pipeline/validation.py`, or the button on the **Performance validation** page.

The submitted package intentionally does not include an old saved live ranking. This
ensures that anyone using Live mode creates a fresh market snapshot using the audited
ticker map. Companies without a safely mapped/current NSE quote retain their historical
Capitaline valuation rather than being assigned a guessed security.

## Rebuild from Capitaline exports

The source spreadsheets are included under `data/raw/`. To rebuild the historical model:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py
```

Or use the **Rebuild data** page inside ARTHA.

## Main folders

- `app.py` — Streamlit user interface
- `pipeline/` — data preparation, TOPSIS, live-price, export and Snapshot logic
  - `features_core.py` — the single feature engine used by historical, live and backtest runs
  - `live_fundamentals.py` — Yahoo statements, chain-linking, reconciliation
  - `ask_artha.py` — server-side Claude assistant and its lookup tools
  - `validation.py` — Pearson performance validation
- `data/raw/` — supplied Capitaline source spreadsheets
- `data/work/` — processed historical model outputs
- `data/live/ticker_map.csv` — audited NSE mapping layer
- `web/` — generated historical dashboard and browser engine
- `tests/check_parity.js` — optional JS/Python TOPSIS parity test

## Notes

- Live data is obtained through `yfinance` for this local academic/research build.
- Historical mode uses Capitaline only; Live mode adds Yahoo's latest periods on top.
- ARTHA outputs are model-based research views, not personalised investment advice.
