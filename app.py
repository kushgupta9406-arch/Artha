"""ARTHA — Streamlit app.

Run:  streamlit run app.py
Data: Capitaline exports in data/raw/  ->  python run_pipeline.py  ->  data/work/ + web/artha.html
"""
import html, json, os, subprocess, sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
WORK, WEB, RAW, LIVE = ROOT / 'data' / 'work', ROOT / 'web', ROOT / 'data' / 'raw', ROOT / 'data' / 'live'
sys.path.insert(0, str(ROOT / 'pipeline'))
from paths import FILES  # noqa: E402
from snapshot import build_snapshot_scores, profile_for_family, LABELS as SNAP_LABELS  # noqa: E402

st.set_page_config(
    page_title='ARTHA — Sector Intelligence & Ranking Desk',
    page_icon='◈',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Theme-adaptive styling (works in light and dark mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .block-container { padding-top: 2.2rem; }

    .artha-hero {
        border-radius: 14px; padding: 22px 26px; margin-bottom: 18px;
        background: linear-gradient(135deg, rgba(59,130,246,0.14), rgba(16,185,129,0.08));
        border: 1px solid rgba(59,130,246,0.25);
    }
    .artha-hero h1 { margin: 0; font-size: 30px; font-weight: 800; letter-spacing: -0.02em; }
    .artha-hero p { margin: 6px 0 0 0; font-size: 14px; opacity: 0.8; }

    .page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
    .page-head h2 { margin: 0; font-weight: 800; letter-spacing: -0.02em; }
    .page-head .sub { font-size: 13.5px; color: #64748b; margin-top: 3px; }

    .artha-card {
        background: rgba(128,128,128,0.04); border: 1px solid rgba(128,128,128,0.18);
        border-radius: 12px; padding: 18px 22px; margin-bottom: 18px; transition: border-color 0.2s ease;
    }
    .artha-card:hover { border-color: rgba(59,130,246,0.35); }

    .kpi-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 10px 0 18px 0; }
    .kpi-card { background: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.15); border-radius: 10px; padding: 14px 16px; }
    .kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #8892b0; font-weight: 600; margin-bottom: 4px; }
    .kpi-val { font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
    .kpi-sub { font-size: 11.5px; color: #64748b; margin-top: 2px; }

    .badge { display: inline-block; padding: 3px 9px; border-radius: 6px; font-size: 12px; font-weight: 600; letter-spacing: 0.02em; }
    .badge-accumulate { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
    .badge-corehold   { background: rgba(59,130,246,0.15); color: #3b82f6; border: 1px solid rgba(59,130,246,0.3); }
    .badge-watchlist  { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
    .badge-avoid      { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
    .badge-neutral    { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }

    .flag-chip { display: flex; align-items: flex-start; gap: 10px; padding: 9px 13px; border-radius: 8px; font-size: 12.5px; margin-bottom: 7px; border: 1px solid transparent; }
    .flag-high { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.25); color: #ef4444; }
    .flag-warn { background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.25); color: #d97706; }
    .flag-info { background: rgba(100,116,139,0.08); border-color: rgba(100,116,139,0.2); color: #64748b; }
    .flag-ok   { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.2); color: #10b981; }

    .artha-divider { margin: 22px 0 16px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.15); }
    .artha-foot { margin-top: 28px; padding-top: 10px; border-top: 1px solid rgba(128,128,128,0.15); font-size: 12px; color: #8892b0; }
    pre, code { font-family: 'JetBrains Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATA + HISTORICAL / LIVE MARKET MODE
# ==========================================
@st.cache_data(show_spinner=False)
def load():
    f = pd.read_pickle(WORK / 'features.pkl'); r = pd.read_pickle(WORK / 'rank.pkl')
    lite = pd.read_pickle(WORK / 'lite.pkl'); meta = json.load(open(WORK / 'meta.json'))
    full = r.join(f, rsuffix='_f')
    uni = pd.read_pickle(WORK / 'universe.pkl')
    dj = json.load(open(WORK / 'data.json', encoding='utf-8'))
    comps = {int(k): v for k, v in dj['companies'].items()}
    full['alpha'] = pd.Series({c: v.get('alpha') for c, v in comps.items()}, dtype=float).reindex(full.index)
    sectors = pd.DataFrame(dj['sectors']).T
    lser = pd.read_pickle(WORK / 'lite_series.pkl')
    return full, lite, meta, uni, comps, sectors, lser

@st.cache_data(show_spinner=False)
def load_live():
    f = pd.read_pickle(LIVE / 'features.pkl'); r = pd.read_pickle(LIVE / 'rank.pkl')
    lite = pd.read_pickle(WORK / 'lite.pkl')
    meta = json.load(open(LIVE / 'meta.json'))
    full = r.join(f, rsuffix='_f')
    uni = pd.read_pickle(LIVE / 'universe.pkl')
    dj = json.load(open(LIVE / 'data.json', encoding='utf-8'))
    comps = {int(k): v for k, v in dj['companies'].items()}
    full['alpha'] = pd.Series({c: v.get('alpha') for c, v in comps.items()}, dtype=float).reindex(full.index)
    sectors = pd.DataFrame(dj['sectors']).T
    lser = pd.read_pickle(WORK / 'lite_series.pkl')
    return full, lite, meta, uni, comps, sectors, lser

@st.cache_data(show_spinner=False)
def dashboard_html(live=False):
    p = WEB / ('artha_live.html' if live else 'artha.html')
    return p.read_text(encoding='utf-8')

def live_ready():
    need = [LIVE / 'features.pkl', LIVE / 'rank.pkl', LIVE / 'universe.pkl', LIVE / 'data.json', WEB / 'artha_live.html']
    return all(p.exists() for p in need)

def live_status():
    try:
        return json.load(open(LIVE / 'status.json', encoding='utf-8'))
    except Exception:
        return {}

VALID = ROOT / 'data' / 'validation'

def secret(name, default=None):
    """Server-side secret: Streamlit secrets first, then environment variable. Never sent to the browser."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)

def is_admin():
    """Admin actions (data refresh, rebuild, validation run) are open locally and password-gated when deployed."""
    pw = secret('ARTHA_ADMIN_PASSWORD')
    return (not pw) or st.session_state.get('admin_ok', False)

def load_validation():
    try:
        return json.load(open(VALID / 'validation.json', encoding='utf-8'))
    except Exception:
        return {}

if not (WORK / 'rank.pkl').exists() or not (WORK / 'universe.pkl').exists():
    st.warning('No model outputs found yet. Put the Capitaline exports in data/raw/ and run `python run_pipeline.py`.')
    st.stop()

hist_data = load()
with st.sidebar:
    requested_mode = st.segmented_control(
        'Market data', ['Historical', 'Live'],
        default=st.session_state.get('market_mode', 'Live' if live_ready() else 'Historical'),
        key='market_mode', required=True,
        help='Historical preserves the Capitaline year-end model. Live uses current NSE prices and the latest Yahoo Finance statements, then reruns the full model.'
    )

IS_LIVE = requested_mode == 'Live' and live_ready()
if IS_LIVE:
    full, lite, meta, uni, comps, sectors, lser = load_live()
else:
    full, lite, meta, uni, comps, sectors, lser = hist_data
ranked = full[full['rank'].notna()]
# ARTHA Snapshot is a separate broad-universe assessment. It never writes into
# the full TOPSIS ranks/scores. In Live mode it automatically sees the live
# valuation overlay because it is computed from the selected universe copy.
snapshot = build_snapshot_scores(uni)
uni = uni.join(snapshot)
SNAPSHOT_BROAD_COUNT = int(((~uni['in_full'].fillna(False)) & uni['snapshot_quality_eligible'].fillna(False)).sum())
LIVE_STATUS = live_status() if IS_LIVE else {}
VALUATION_MODE = 'Live market overlay' if IS_LIVE else 'Capitaline year-end'

# ==========================================
# HELPERS
# ==========================================
DISCLAIMER = 'Model-based ranking on Capitaline fundamentals; Live mode uses current NSE prices and the latest Yahoo Finance statements. Not personalised investment advice.'
MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def ok(v):
    return v is not None and not isinstance(v, (str, list, dict)) and pd.notna(v) and np.isfinite(float(v))

def fy_label(y):
    if not ok(y): return '—'
    yr, m = divmod(int(y), 100)
    return f'FY{yr % 100:02d}' if m == 3 else f'{MONTHS[m] if 1 <= m <= 12 else m}-{yr % 100:02d}'

def f_pct(v, d=1): return f'{v:.{d}f}%' if ok(v) else '—'
def f_x(v, d=1): return f'{v:.{d}f}x' if ok(v) else '—'
def f_num(v, d=2): return f'{v:.{d}f}' if ok(v) else '—'
def f_cr(v): return f'₹{v:,.0f} cr' if ok(v) else '—'

def page_head(title, sub='', badge=None):
    b = f'<span class="badge badge-corehold">{html.escape(badge)}</span>' if badge else ''
    st.markdown(f'<div class="page-head"><div><h2>{html.escape(title)}</h2><div class="sub">{html.escape(sub)}</div></div>{b}</div>',
                unsafe_allow_html=True)

def kpis(items):
    cards = ''.join(f'<div class="kpi-card"><div class="kpi-label">{html.escape(l)}</div><div class="kpi-val">{v}</div>'
                    f'<div class="kpi-sub">{html.escape(s)}</div></div>' for l, v, s in items)
    st.markdown(f'<div class="kpi-container">{cards}</div>', unsafe_allow_html=True)

def footer():
    st.markdown(f'<div class="artha-foot">🛡️ {DISCLAIMER}</div>', unsafe_allow_html=True)

def rating_badge_html(rating):
    if not isinstance(rating, str):
        return '<span class="badge badge-neutral">Not ranked</span>'
    cls = {'Accumulate': 'badge-accumulate', 'Core Hold': 'badge-corehold', 'Watchlist': 'badge-watchlist', 'Avoid': 'badge-avoid'}.get(rating, 'badge-neutral')
    return f'<span class="badge {cls}">{rating}</span>'

def snapshot_badge_html(view):
    if not isinstance(view, str):
        return '<span class="badge badge-neutral">Data limited</span>'
    cls = {
        'Strong': 'badge-accumulate',
        'Favourable': 'badge-corehold',
        'Balanced': 'badge-neutral',
        'Cautious': 'badge-watchlist',
        'Weak': 'badge-avoid',
        'Quality only': 'badge-neutral',
    }.get(view, 'badge-neutral')
    return f'<span class="badge {cls}">{html.escape(view)}</span>'

def snapshot_metric_value(metric, value):
    if metric in {'ronw', 'roce', 'op_margin', 'net_m', 'rev_cagr2', 'pat_cagr2'}:
        return f_pct(value)
    if metric in {'icr', 'pe', 'pb', 'ev_ebitda'}:
        return f_x(value)
    return f_num(value)

def flags_text(fl):
    return ', '.join(f"{x['sev']}: {x['k'].replace('_', ' ')}" for x in (fl or []) if x['sev'] != 'INFO')

def severe(fl):
    return sum(1 for x in (fl or []) if x['sev'] in ('VETO', 'HIGH'))

def has_veto(fl):
    return any(x['sev'] == 'VETO' for x in (fl or []))

def show_flags(flags_list):
    if not [x for x in (flags_list or []) if x.get('sev') != 'INFO']:
        st.markdown('<div class="flag-chip flag-ok" style="padding: 14px 16px;"><div style="font-size: 18px;">✅</div><div>'
                    '<div style="font-weight: 700;">No severe flags</div><div style="font-size: 12.5px; margin-top: 2px;">'
                    'No forensic, debt-service or governance red flags triggered.</div></div></div>', unsafe_allow_html=True)
    order = {'VETO': 0, 'HIGH': 1, 'MED': 2, 'WARN': 2, 'INFO': 3}
    for f in sorted(flags_list or [], key=lambda x: order.get(x.get('sev'), 9)):
        sev = f.get('sev', 'WARN')
        cls, icon = {'VETO': ('flag-high', '⛔'), 'HIGH': ('flag-high', '🚨'), 'INFO': ('flag-info', 'ℹ️')}.get(sev, ('flag-warn', '⚠️'))
        st.markdown(f'<div class="flag-chip {cls}"><div style="font-size: 15px;">{icon}</div><div>'
                    f'<div style="font-weight: 700; font-size: 12px; text-transform: uppercase;">{sev}: {html.escape(f.get("k", "").replace("_", " "))}</div>'
                    f'<div style="font-size: 12.5px; margin-top: 2px;">{html.escape(f.get("msg", ""))}</div></div></div>', unsafe_allow_html=True)

def data_tag(row):
    if row.get('in_full'): return 'Ranked'
    return '1-year' if row.get('src') == 'new' else 'Broad'

LABEL = {c: f"{r['name']}  ·  {r['sector']}" for c, r in uni.sort_values('name').iterrows()}
CODES = list(LABEL)

def open_company(code):
    st.session_state['company_code'] = int(code)
    st.switch_page(PAGES['company'])


def home_live_and_validation():
    """Home-page summary: what the live layer updated and the Karl Pearson validation results."""
    if IS_LIVE and LIVE_STATUS:
        s = LIVE_STATUS
        per = ', '.join(f'{k} ({v})' for k, v in (s.get('latest_periods') or {}).items()) or 'latest available'
        st.success(f"**Live data on.** Current NSE prices for {s.get('full_model_quotes', 0)} of {s.get('full_model_total', 0)} ranked companies, and latest Yahoo Finance "
                   f"fundamentals for {s.get('full_model_fundamentals_updated', 0)}: periods {per}. ROCE, ROE, margins, growth, leverage, cash quality, P/E, P/B, "
                   f"EV/EBITDA and FCF yield were recalculated and the full ARTHA model was rerun.", icon=':material/bolt:')
    elif not IS_LIVE:
        st.info('Showing the Capitaline (historical) model. Switch **Market data → Live** in the sidebar for current prices and the latest Yahoo Finance fundamentals.', icon=':material/history:')
    v = load_validation()
    if not v:
        return
    fu = v.get('fundamentals') or {}
    pit = v.get('point_in_time') or {}
    st.markdown('#### Model validation · Karl Pearson correlation')
    cards = []
    for fy in ['FY23', 'FY21']:
        r = (fu.get(fy) or {}).get('future_return_on_capital') or {}
        q = r.get('quality_score_vs_outcome') or {}; a = r.get('artha_score_vs_outcome') or {}
        if q.get('r') is not None:
            cards.append((f'Quality score ({fy}) vs next {fu[fy]["years_ahead"]}Y ROCE', f"r = {q['r']:+.2f}", f"95% CI {q.get('ci95')} · p = {q.get('p'):.1g} · n = {q.get('n')}"))
        if a.get('r') is not None and fy == 'FY23':
            cards.append((f'ARTHA score ({fy}) vs next 3Y ROCE', f"r = {a['r']:+.2f}", f"95% CI {a.get('ci95')} · p = {a.get('p'):.1g}"))
    r3 = (pit.get('3Y') or {}).get('sector_neutral') or {}
    if r3.get('r') is not None:
        cards.append(('ARTHA score (FY23) vs next 3Y stock return', f"r = {r3['r']:+.2f}", f"95% CI {r3.get('ci95')} · p = {r3.get('p'):.2g} · n = {r3.get('n')}"))
    if cards:
        kpis(cards[:4])
        st.caption('Pearson r between ARTHA percentile and the outcome percentile, both inside each sector, with rankings rebuilt only from data available at the time. '
                   'ARTHA strongly predicts which businesses keep high returns on capital; its link to stock returns is weak, as is typical for quality/value models. Full detail on the Performance validation page.')
        if st.button('Open performance validation', icon=':material/query_stats:'):
            st.switch_page(PAGES['validation'])

# ==========================================
# PAGE: HOME
# ==========================================
def home():
    st.markdown("""
    <div class="artha-hero">
        <h1>◈ ARTHA</h1>
        <p>Sector intelligence for Indian listed companies. Full-model companies are ranked against sector peers with TOPSIS;
        broader-coverage companies receive a separate ARTHA Snapshot, with a switchable historical or live NSE valuation layer.</p>
    </div>""", unsafe_allow_html=True)

    kpis([
        ('Companies covered', f'{len(uni):,}', 'Broad universe incl. one-year data'),
        ('TOPSIS-ranked', f'{len(ranked):,}', 'Full model: multi-year methodology'),
        ('Current assessed', f'{SNAPSHOT_BROAD_COUNT:,}', 'Broad companies with a full or quality-only Snapshot'),
        ('With valuation', f'{int(uni.mcap.notna().sum()):,}', 'Current where available' if IS_LIVE else 'Year-end market cap available'),
        ('Sectors', f'{len(meta)}', 'Peer-relative analysis'),
    ])

    home_live_and_validation()

    code = st.selectbox('🔎 Find a company', CODES, index=None, format_func=LABEL.get,
                        placeholder='Type a company name, e.g. TCS, HDFC Bank, Asian Paints…')
    if code is not None:
        open_company(code)

    left, right = st.columns([1, 1], gap='large')
    with left:
        st.markdown('#### Strongest sectors')
        st.caption('Sector-level TOPSIS on median ROE spread, profit growth, breadth, valuation, Piotroski and earnings revision.')
        s = sectors.copy()
        for c in ['rank', 'n', 'score', 'ronw_spread', 'breadth']: s[c] = pd.to_numeric(s[c], errors='coerce')
        s = s.sort_values('rank').reset_index(names='sector')
        st.dataframe(s[['rank', 'sector', 'n', 'score', 'ronw_spread', 'breadth']], hide_index=True, height=390,
                     column_config={
                         'rank': st.column_config.NumberColumn('#', format='%d', width='small'),
                         'sector': st.column_config.TextColumn('Sector', width='medium'),
                         'n': st.column_config.NumberColumn('Cos', format='%d', width='small'),
                         'score': st.column_config.ProgressColumn('Score', min_value=0, max_value=1, format='%.2f'),
                         'ronw_spread': st.column_config.NumberColumn('ROE − 12%', format='%+.1f'),
                         'breadth': st.column_config.NumberColumn('% ROE > 12', format='%.0f%%'),
                     })
    with right:
        st.markdown('#### Top companies across sectors')
        st.caption('AlphaPct = percentile inside its sector × 1.10 / 1.00 / 0.90 depending on how strong the sector is.')
        t = ranked.sort_values(['alpha', 'score'], ascending=False).head(12)
        st.dataframe(t[['name', 'sector', 'rating', 'alpha', 'score']], hide_index=True, height=390,
                     column_config={
                         'name': st.column_config.TextColumn('Company', width='medium'),
                         'sector': st.column_config.TextColumn('Sector', width='medium'),
                         'rating': st.column_config.TextColumn('Rating', width='small'),
                         'alpha': st.column_config.NumberColumn('AlphaPct', format='%.0f'),
                         'score': st.column_config.NumberColumn('TOPSIS', format='%.3f'),
                     })

    st.markdown('#### Rating mix of the ranked companies')
    mix = ranked['rating'].value_counts().reindex(['Accumulate', 'Core Hold', 'Watchlist', 'Avoid']).fillna(0).astype(int)
    st.bar_chart(mix.rename('Companies'), horizontal=True, height=200, color='#3b82f6', sort=False)
    footer()

# ==========================================
# PAGE: DASHBOARD (self-contained HTML engine)
# ==========================================
def dashboard():
    page_head('Interactive Intelligence Desk', 'Full ARTHA browser engine with client-side TOPSIS recalculation.' + (' Current live snapshot loaded.' if IS_LIVE else ''), 'Live snapshot' if IS_LIVE else 'Stand-alone engine')
    st.iframe(dashboard_html(IS_LIVE), height=1150)

# ==========================================
# PAGE: SECTORS
# ==========================================
def sectors_page():
    page_head('Sector rankings', 'Every company is compared only with peers in its own sector.')
    secs = sorted(set(meta) | set(uni.sector.dropna()))
    c1, c2 = st.columns([3, 2], vertical_alignment='bottom')
    with c1:
        sec = st.selectbox('Sector', secs, index=secs.index(st.session_state.get('sector', secs[0])) if st.session_state.get('sector') in secs else 0)
        st.session_state['sector'] = sec
    with c2:
        mode = st.segmented_control('Model', ['Full model', 'Broad universe'], default='Full model', required=True,
                                    help='Full model: TOPSIS ranking with valuation (~350 companies). Broad universe: all companies, not ranked.')

    if mode == 'Full model':
        d = ranked[ranked.sector == sec].sort_values('rank')
        if d.empty:
            st.info(f'No TOPSIS-ranked companies in **{sec}**. Switch to *Broad universe* to see its companies.')
            footer(); return
        sm = meta.get(sec, {})
        kpis([
            ('Ranked peers', f'{len(d)}', sec),
            ('Leader stability', '🟢 Stable' if not sm.get('topsis_unstable') else '🟡 Sensitive', '400 Dirichlet weight draws'),
            ('Median ROCE (5Y)', f_pct(d['roce_5y_med'].median()), 'Capital efficiency'),
            ('Median P/E', f_x(d['pe'].median()), 'Current valuation' if IS_LIVE else 'Year-end valuation'),
        ])
        tab_table, tab_chart = st.tabs(['📋 Ranked table', '📈 Quality vs valuation'])
        with tab_table:
            show = d[['rank', 'name', 'score', 'Q', 'V', 'quadrant', 'rating', 'conviction', 'roce_5y_med', 'ronw', 'pe', 'pb', 'rev_cagr3']].copy()
            show['flags'] = d['flags'].apply(flags_text)
            st.dataframe(show, hide_index=True, column_config={
                'rank': st.column_config.NumberColumn('#', format='%d', width='small'),
                'name': st.column_config.TextColumn('Company', width='medium'),
                'score': st.column_config.ProgressColumn('TOPSIS score', min_value=0, max_value=1, format='%.3f', width='medium'),
                'Q': st.column_config.NumberColumn('Quality', format='%.3f', width='small'),
                'V': st.column_config.NumberColumn('Valuation', format='%.3f', width='small'),
                'quadrant': st.column_config.TextColumn('Quadrant', width='medium'),
                'rating': st.column_config.TextColumn('Rating', width='small'),
                'conviction': st.column_config.NumberColumn('Conviction', format='%d', width='small'),
                'roce_5y_med': st.column_config.NumberColumn('ROCE 5Y med', format='%.1f%%', width='small'),
                'ronw': st.column_config.NumberColumn('ROE', format='%.1f%%', width='small'),
                'pe': st.column_config.NumberColumn('P/E', format='%.1f', width='small'),
                'pb': st.column_config.NumberColumn('P/B', format='%.1f', width='small'),
                'rev_cagr3': st.column_config.NumberColumn('Rev CAGR 3Y', format='%.1f%%', width='small'),
                'flags': st.column_config.TextColumn('Flags', width='large'),
            })
            st.caption('Score = 0.70 × Quality + 0.30 × Valuation − 0.01 × share of imputed cells.')
        with tab_chart:
            st.caption('Top-right = strong business at a reasonable price. Bubble size = market cap.')
            st.scatter_chart(d, x='Q', y='V', color='rating', size='mcap', x_label='Quality (Q)', y_label='Valuation (V)', height=460)
    else:
        d = uni[uni.sector == sec].copy()
        c_a, c_b = st.columns([2, 1], vertical_alignment='bottom')
        with c_a:
            min_sales = st.select_slider('Minimum revenue (₹ crore)', [0, 100, 500, 1000, 5000], value=100)
        with c_b:
            one_year = st.toggle('Include one-year companies', value=True, help='Companies that appear only in the latest single-year Capitaline files.')
        d = d[d.sales.fillna(0) >= min_sales]
        if not one_year: d = d[d.src != 'new']
        d = d.sort_values('ronw', ascending=False)
        kpis([
            ('Companies', f'{len(d)}', f'Revenue ≥ ₹{min_sales:,} cr'),
            ('Median ROE', f_pct(d['ronw'].median()), 'Latest year'),
            ('Median P/E', f_x(d['pe'].median()), 'Current where available' if IS_LIVE else 'At year-end price'),
            ('Median P/B', f_x(d['pb'].median()), 'Current where available' if IS_LIVE else 'At year-end price'),
        ])
        d['data'] = d.apply(data_tag, axis=1); d['flags_s'] = d['flags'].apply(flags_text)
        d['snapshot_s'] = d['snapshot_score'].where(~d['in_full'].fillna(False))
        d['snapshot_view_s'] = d['snapshot_view'].where(~d['in_full'].fillna(False), '')
        d['snapshot_cov_s'] = d['snapshot_coverage'].where(~d['in_full'].fillna(False))
        st.dataframe(d[['name', 'data', 'snapshot_s', 'snapshot_view_s', 'snapshot_cov_s', 'sales', 'mcap', 'ronw', 'op_margin', 'roce', 'pe', 'pb', 'de', 'rev_cagr2', 'pat_cagr2', 'icr', 'cfo_pat3', 'promoter_pct', 'flags_s']],
                     hide_index=True, column_config={
                         'name': st.column_config.TextColumn('Company', width='medium'),
                         'data': st.column_config.TextColumn('Data', width='small', help='Ranked = in the TOPSIS model; Broad = multi-year history; 1-year = latest year only'),
                         'snapshot_s': st.column_config.NumberColumn('Snapshot', format='%.1f', help='Broad-universe current assessment only; not a rank.'),
                         'snapshot_view_s': st.column_config.TextColumn('Snapshot view', width='small'),
                         'snapshot_cov_s': st.column_config.NumberColumn('Data coverage', format='%.0f%%'),
                         'sales': st.column_config.NumberColumn('Sales (₹ cr)', format='%.0f'),
                         'mcap': st.column_config.NumberColumn('Mcap (₹ cr)', format='%.0f'),
                         'ronw': st.column_config.NumberColumn('ROE', format='%.1f%%'),
                         'op_margin': st.column_config.NumberColumn('OP margin', format='%.1f%%'),
                         'roce': st.column_config.NumberColumn('ROCE', format='%.1f%%'),
                         'pe': st.column_config.NumberColumn('P/E', format='%.1f'),
                         'pb': st.column_config.NumberColumn('P/B', format='%.1f'),
                         'de': st.column_config.NumberColumn('D/E', format='%.2f'),
                         'rev_cagr2': st.column_config.NumberColumn('Rev CAGR 2Y', format='%.1f%%'),
                         'pat_cagr2': st.column_config.NumberColumn('PAT CAGR 2Y', format='%.1f%%'),
                         'icr': st.column_config.NumberColumn('Int. cover', format='%.1fx'),
                         'cfo_pat3': st.column_config.NumberColumn('CFO/PAT 3Y', format='%.2f'),
                         'promoter_pct': st.column_config.NumberColumn('Promoter', format='%.1f%%'),
                         'flags_s': st.column_config.TextColumn('Flags', width='large'),
                     })
        st.caption('Broad universe: quality metrics, not a full TOPSIS rank. ' + ('Valuation uses the latest NSE quote where mapped; otherwise the saved Capitaline year-end value is retained.' if IS_LIVE else 'Valuation uses the year-end price in Capitaline for the same year as the accounts.'))
    footer()

# ==========================================
# PAGE: COMPANY
# ==========================================
def history_frame(code):
    """Up to 6 years of history, oldest first."""
    if code in comps:
        s = comps[code]['s']; n = 6
        df = pd.DataFrame({'Sales': s['sales'][:n], 'PAT': s['pat'][:n], 'ROCE %': s['roce'][:n], 'ROE %': s['ronw'][:n]},
                          index=[fy_label(y) for y in s['years'][:n]], dtype=float)
    elif code in lser:
        s = lser[code]; n = 6
        df = pd.DataFrame({'Sales': s['sales'][:n], 'PAT': s['pat'][:n], 'OP margin %': s['opm'][:n]},
                          index=[fy_label(y) for y in s['y'][:n]], dtype=float)
    else:
        return None
    df = df.iloc[::-1].dropna(how='all')
    return df if len(df) >= 2 else None

def company_page():
    page_head('Company tear sheet', 'Rank, rating, history, flags and closest peers.')
    prev = st.session_state.get('company_code')
    code = st.selectbox('Company', CODES, index=CODES.index(prev) if prev in LABEL else None, format_func=LABEL.get,
                        placeholder='Type to search, e.g. Chambal Fert., TCS, HDFC Bank…')
    st.session_state['company_code'] = code
    if code is None:
        st.info('Pick a company to see its tear sheet.'); footer(); return
    u = uni.loc[code]
    is_ranked = code in ranked.index
    r = full.loc[code] if is_ranked else None
    snap_eligible = (not is_ranked) and bool(u.get('snapshot_eligible', False)) and ok(u.get('snapshot_score'))
    snap_quality_only = (not is_ranked) and (not snap_eligible) and bool(u.get('snapshot_quality_eligible', False)) and ok(u.get('snapshot_quality'))
    base_tag = data_tag(u)
    if is_ranked:
        tag = 'TOPSIS-ranked'
    elif snap_eligible:
        tag = ('One-year data' if base_tag == '1-year' else 'Broad universe') + ' · ARTHA Snapshot'
    elif snap_quality_only:
        tag = ('One-year data' if base_tag == '1-year' else 'Broad universe') + ' · quality snapshot'
    else:
        tag = ('One-year data' if base_tag == '1-year' else 'Broad universe') + ' · data limited'
    right_label = 'Rating' if is_ranked else 'Snapshot view'
    right_badge = rating_badge_html(r['rating']) if is_ranked else snapshot_badge_html(u.get('snapshot_view'))

    st.markdown(f"""
    <div class="artha-card" style="margin-top: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">{html.escape(u['name'])}</h1>
                <div style="display: flex; gap: 10px; margin-top: 6px; font-size: 13.5px; color: #8892b0; flex-wrap: wrap;">
                    <span>🏢 <b>{html.escape(u['sector'])}</b></span><span>•</span>{f"<span>🧭 {html.escape(str(r['quadrant']))}</span><span>•</span>" if is_ranked and isinstance(r['quadrant'], str) else ''}<span>📅 {fy_label(u['fy'])}</span><span>•</span><span>{tag}</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 11px; text-transform: uppercase; color: #8892b0; font-weight: 600; margin-bottom: 4px;">{right_label}</div>
                {right_badge}
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if is_ranked:
        kpis([
            ('Rank in sector', f"#{int(r['rank'])} of {int(r['n'])}", u['sector']),
            ('TOPSIS score', f_num(r['score'], 3), f"Quality {f_num(r['Q'], 2)} · Valuation {f_num(r['V'], 2)}"),
            ('Conviction', f"{int(r['conviction'])}" if ok(r['conviction']) else '—', 'Robustness of the rank'),
            ('AlphaPct', f_num(r['alpha'], 0), 'Cross-sector percentile'),
        ])
    elif snap_eligible:
        st.markdown('##### ARTHA Snapshot · current assessment')
        kpis([
            ('Snapshot score', f"{u['snapshot_score']:.1f} / 100", 'Not an official TOPSIS rank'),
            ('Quality snapshot', f"{u['snapshot_quality']:.1f}", '70% of the final Snapshot'),
            ('Valuation snapshot', f"{u['snapshot_valuation']:.1f}", '30% of the final Snapshot'),
            ('Data coverage', f"{u['snapshot_coverage']:.0f}%", f"{u['snapshot_confidence']} confidence · {int(u['snapshot_metrics'])} metrics"),
        ])
        st.caption('Sector-relative current assessment using available fundamentals and valuation. Missing metrics are not imputed; thin-data pillar scores are pulled towards a neutral 50. This score is deliberately separate from the multi-year TOPSIS ranking.')
    elif snap_quality_only:
        st.markdown('##### ARTHA Quality Snapshot · valuation not sufficient')
        kpis([
            ('Quality snapshot', f"{u['snapshot_quality']:.1f} / 100", 'Peer-relative quality only'),
            ('Quality coverage', f"{u['snapshot_quality_coverage']:.0f}%", f"{int(u['snapshot_quality_metrics'])} quality metrics"),
            ('Overall Snapshot', '—', 'Not calculated without enough valuation data'),
        ])
        st.caption('There is enough current fundamental evidence to show a quality assessment, but not enough valid valuation data to preserve ARTHA’s 70% quality / 30% valuation structure. No overall Snapshot score or rank is created.')
    elif not is_ranked:
        st.info('ARTHA Snapshot is not calculated for this company because the latest available data is still too limited. Raw available metrics are shown below.')
    val_title = ('Live valuation · latest fundamentals' if isinstance(u.get('fund_source'), str) and u.get('fund_source') == 'yahoo-linked' else 'Live valuation · Capitaline fundamentals') if IS_LIVE else f'Valuation & balance sheet · {fy_label(u.get("val_fy") if ok(u.get("val_fy")) else u["fy"])}'
    st.markdown(f'##### {val_title}')
    if IS_LIVE and u.get('live_status') != 'current':
        st.caption('Latest NSE quote was unavailable for this company, so its saved Capitaline valuation is retained.')
    if IS_LIVE and isinstance(u.get('fund_source'), str):
        src = u.get('fund_source')
        if src == 'yahoo-linked':
            st.caption(f"Fundamentals: latest Yahoo Finance period ({u.get('live_period')}) chain-linked to the Capitaline history; all ratios recomputed and the model rerun.")
        else:
            st.caption(f'Fundamentals: {src}.')
    kpis([
    (
        'Current market price',
        f"₹{u['live_price']:,.2f}"
        if IS_LIVE and u.get('live_status') == 'current' and ok(u.get('live_price'))
        else '—',
        'Latest NSE quote' if IS_LIVE and u.get('live_status') == 'current' else 'Historical mode'
    ),
    ('Market cap', f_cr(u['mcap']), 'Current estimate' if IS_LIVE and u.get('live_status') == 'current' else 'Year-end'),
    ('P/E', f_x(u['pe']), 'Core earnings if other income is large'),
    ('P/B', f_x(u['pb']), 'Market cap ÷ net worth'),
    ('EV / EBITDA', f_x(u['ev_ebitda']), 'Non-financials only'),
    ('ROCE', f_pct(u['roce']), 'Latest year'),
    ('Debt / equity', f_num(u['de']), 'Latest year'),
])
    st.markdown('##### Fundamentals')
    kpis([
        ('Sales', f_cr(u['sales']), 'Latest year'),
        ('Return on equity', f_pct(u['ronw']), 'PAT ÷ net worth'),
        ('Operating margin', f_pct(u['op_margin']), 'Before other income'),
        ('Revenue CAGR 2Y', f_pct(u['rev_cagr2']), 'Needs 3 years of data'),
        ('Interest cover', f_x(u['icr']), 'PBIT ÷ finance cost'),
        ('Promoter holding', f_pct(u['promoter_pct']), f"Change {u['promoter_chg']:+.2f} pts" if ok(u['promoter_chg']) else 'Latest quarter'),
    ])
    if u['family'] != 'ind':
        st.caption('ℹ️ Lender/financial: asset quality (GNPA, capital adequacy) is not in the Capitaline data, so it is not assessed here.')

    if snap_eligible or snap_quality_only:
        with st.expander('📊 Snapshot drivers — peer percentiles'):
            prof = profile_for_family(u.get('family'))
            driver_rows = []
            for pillar_name, weights in [('Quality', prof['quality']), ('Valuation', prof['valuation'])]:
                for metric, weight in weights.items():
                    pct = u.get(f'snapshot_pct_{metric}')
                    if ok(pct):
                        driver_rows.append({
                            'Pillar': pillar_name,
                            'Metric': SNAP_LABELS.get(metric, metric),
                            'Current': snapshot_metric_value(metric, u.get(metric)),
                            'Peer percentile': float(pct),
                            'Model weight': weight * 100,
                        })
            if driver_rows:
                st.dataframe(pd.DataFrame(driver_rows), hide_index=True, width='stretch', column_config={
                    'Peer percentile': st.column_config.ProgressColumn('Peer percentile', min_value=0, max_value=100, format='%.0f'),
                    'Model weight': st.column_config.NumberColumn('Intended weight', format='%.0f%%'),
                })
                st.caption('100 = strongest peer-relative observation. Lower valuation multiples and lower industrial leverage score higher; other listed quality metrics score higher when their raw value is higher.')

    tabs = st.tabs(['📈 History', '🚩 Flags'] + (['🧱 Pillars', '👥 Closest peers'] if is_ranked else []))
    with tabs[0]:
        h = history_frame(code)
        if h is None:
            st.info('Not enough history for a chart (this company has only one year of data).')
        else:
            a, b = st.columns(2)
            a.markdown('**Sales and PAT (₹ cr)**'); a.bar_chart(h[['Sales', 'PAT']], stack=False, height=300)
            pct_cols = [c for c in h.columns if c.endswith('%')]
            b.markdown('**' + ' / '.join(pct_cols) + '**'); b.line_chart(h[pct_cols], height=300)
    with tabs[1]:
        show_flags(u['flags'])
    if is_ranked:
        with tabs[2]:
            st.caption('Percentile inside the sector on each pillar (100 = best in sector).')
            if isinstance(r.get('pillars'), dict):
                st.bar_chart(pd.Series(r['pillars'], name='Percentile'), horizontal=True, height=300, color='#3b82f6', sort=False)
        with tabs[3]:
            peers = [p for p in comps.get(code, {}).get('peers', []) if p in full.index]
            if peers:
                p = full.loc[peers, ['name', 'rank', 'rating', 'score', 'roce_5y_med', 'pe']]
                st.dataframe(p, hide_index=True, column_config={
                    'name': 'Company', 'rank': st.column_config.NumberColumn('Rank', format='%d'), 'rating': 'Rating',
                    'score': st.column_config.NumberColumn('TOPSIS', format='%.3f'),
                    'roce_5y_med': st.column_config.NumberColumn('ROCE 5Y med', format='%.1f%%'),
                    'pe': st.column_config.NumberColumn('P/E', format='%.1f')})
                st.caption('Nearest companies in the same sector on the model\'s criteria.')
                if st.button('Compare with these peers', icon=':material/compare_arrows:'):
                    st.session_state['compare_codes'] = [int(code)] + [int(x) for x in peers[:3]]
                    st.switch_page(PAGES['compare'])
    footer()

# ==========================================
# PAGE: COMPARE
# ==========================================
COMPARE_ROWS = [  # label, field, direction (+1 higher is better, -1 lower is better, 0 not judged), format
    ('Sector', 'sector', 0, str), ('Data', 'data', 0, str), ('Rating', 'rating', 0, str), ('Rank in sector', 'rank_s', 0, str),
    ('TOPSIS score', 'score', 1, lambda v: f_num(v, 3)),
    ('ARTHA Snapshot', 'snapshot_s', 0, lambda v: f'{v:.1f} / 100' if ok(v) else '—'),
    ('Snapshot view', 'snapshot_view_s', 0, str),
    ('Snapshot data coverage', 'snapshot_cov_s', 0, lambda v: f'{v:.0f}%' if ok(v) else '—'),
    ('Market cap (₹ cr)', 'mcap', 0, lambda v: f'{v:,.0f}' if ok(v) else '—'),
    ('Sales (₹ cr)', 'sales', 0, lambda v: f'{v:,.0f}' if ok(v) else '—'),
    ('PAT (₹ cr)', 'pat', 0, lambda v: f'{v:,.0f}' if ok(v) else '—'),
    ('Return on equity', 'ronw', 1, f_pct), ('Operating margin', 'op_margin', 1, f_pct), ('ROCE', 'roce', 1, f_pct),
    ('Revenue CAGR 2Y', 'rev_cagr2', 1, f_pct), ('PAT CAGR 2Y', 'pat_cagr2', 1, f_pct),
    ('Debt / equity', 'de', -1, f_num), ('Interest cover', 'icr', 1, f_x), ('CFO / PAT 3Y', 'cfo_pat3', 1, f_num),
    ('P/E', 'pe', -1, f_x), ('P/B', 'pb', -1, f_x), ('EV / EBITDA', 'ev_ebitda', -1, f_x),
    ('Promoter holding', 'promoter_pct', 0, f_pct), ('Severe flags', 'n_severe', -1, lambda v: f'{int(v)}' if ok(v) else '—'),
    ('Data year', 'fy', 0, fy_label),
]

def compare_page():
    page_head('Compare companies', 'Pick 2–4 companies. The better value on each row is highlighted in green.')
    default = [c for c in st.session_state.get('compare_codes', []) if c in LABEL]
    picks = st.multiselect('Companies', CODES, default=default, format_func=LABEL.get, max_selections=4,
                           placeholder='Choose 2 to 4 companies…')
    st.session_state['compare_codes'] = picks
    if len(picks) < 2:
        st.info('Choose at least two companies.'); footer(); return

    rows = {}
    for c in picks:
        u = uni.loc[c].to_dict(); u['data'] = data_tag(u); u['n_severe'] = severe(u['flags'])
        u['rank_s'] = f"#{int(u['rank'])} of {int(u['n'])}" if ok(u.get('rank')) else '—'
        u['rating'] = u['rating'] if isinstance(u.get('rating'), str) else '—'
        u['snapshot_s'] = u.get('snapshot_score') if not bool(u.get('in_full')) else np.nan
        u['snapshot_view_s'] = u.get('snapshot_view') if not bool(u.get('in_full')) else '—'
        u['snapshot_cov_s'] = u.get('snapshot_coverage') if not bool(u.get('in_full')) else np.nan
        rows[c] = u
    names = [rows[c]['name'] for c in picks]
    cols = [n if names.count(n) == 1 else f'{n} ({c})' for n, c in zip(names, picks)]
    same_sector = len({rows[c]['sector'] for c in picks}) == 1

    disp, mask = {}, {}
    for label, field, direction, fmt in COMPARE_ROWS:
        vals = [rows[c].get(field) for c in picks]
        disp[label] = [v if isinstance(v, str) else '—' for v in vals] if fmt is str else [fmt(v) for v in vals]
        win = [False] * len(picks)
        if direction and not (field == 'score' and not same_sector):
            num = [float(v) if ok(v) and not (field == 'pe' and v <= 0) else None for v in vals]
            good = [v for v in num if v is not None]
            if len(good) >= 2 and len(set(good)) > 1:
                best = max(good) if direction > 0 else min(good)
                win = [v == best for v in num]
        mask[label] = win
    D = pd.DataFrame(disp, index=cols).T
    M = pd.DataFrame(mask, index=cols).T
    styled = D.style.apply(lambda _: M.map(lambda w: 'background-color: rgba(16,185,129,0.20); color: #059669; font-weight: 700' if w else ''), axis=None)
    st.dataframe(styled, height=36 * (len(D) + 1) + 4)
    notes = ['Size rows (market cap, sales, PAT) and promoter holding are shown but not judged.']
    if not same_sector: notes.append('The companies are in different sectors, so TOPSIS scores are not compared (each score is relative to its own sector).')
    st.caption(' '.join(notes))

    chart = pd.DataFrame({k: [rows[c].get(f) for c in picks] for k, f in [('ROE %', 'ronw'), ('Operating margin %', 'op_margin'), ('ROCE %', 'roce')]},
                         index=cols, dtype=float)
    st.markdown('##### Returns and margins')
    st.bar_chart(chart.T, stack=False, height=320)
    footer()

# ==========================================
# PAGE: VALUATION SCREENER
# ==========================================
def screener_page():
    page_head('Valuation screener', f"Filter all {len(uni):,} companies on quality, safety and {'current NSE valuation where available' if IS_LIVE else 'year-end valuation'}.")
    with st.container(border=True):
        a, b, c = st.columns(3)
        secs = a.multiselect('Sectors', sorted(uni.sector.dropna().unique()), placeholder='All sectors')
        min_mcap = b.select_slider('Minimum market cap (₹ cr)', [0, 100, 500, 1000, 5000, 20000, 100000], value=500)
        pe_max = c.slider('Maximum P/E', 5, 150, 60)
        d_, e_, f_ = st.columns(3)
        roe_min = d_.slider('Minimum ROE %', -20, 50, 12)
        de_max = e_.slider('Maximum debt / equity', 0.0, 5.0, 1.0, 0.1)
        icr_min = f_.slider('Minimum interest cover (x)', 0.0, 25.0, 3.0, 0.5, help='Ignored for banks and other lenders.')
        g_, h_, i_ = st.columns(3)
        no_veto = g_.toggle('Hide companies with VETO flags', value=True)
        only_ranked = h_.toggle('Only TOPSIS-ranked companies', value=False)
        one_year = i_.toggle('Include one-year companies', value=True)

    d = uni[uni.pe.notna() & (uni.mcap >= min_mcap) & (uni.pe <= pe_max) & (uni.ronw >= roe_min)].copy()
    d = d[(d.family != 'ind') | (d.de <= de_max)]      # leverage and interest cover are judged for non-financials only
    d = d[(d.family != 'ind') | (d.icr >= icr_min)]
    if secs: d = d[d.sector.isin(secs)]
    if no_veto: d = d[~d['flags'].apply(has_veto)]
    if only_ranked: d = d[d.in_full]
    if not one_year: d = d[d.src != 'new']
    d['data'] = d.apply(data_tag, axis=1); d['flags_s'] = d['flags'].apply(flags_text); d['fy_s'] = d['fy'].apply(fy_label)
    d['rating'] = d['rating'].where(d['rating'].notna(), '—')
    d['snapshot_s'] = d['snapshot_score'].where(~d['in_full'].fillna(False))
    d['snapshot_view_s'] = d['snapshot_view'].where(~d['in_full'].fillna(False), '')
    d['snapshot_cov_s'] = d['snapshot_coverage'].where(~d['in_full'].fillna(False))

    sort_opts = {'ROE (high first)': ('ronw', False), 'ARTHA Snapshot (high first)': ('snapshot_s', False), 'P/E (low first)': ('pe', True), 'P/B (low first)': ('pb', True),
                 'Market cap (large first)': ('mcap', False), 'ROCE (high first)': ('roce', False), 'EV/EBITDA (low first)': ('ev_ebitda', True)}
    s1, s2 = st.columns([3, 1], vertical_alignment='bottom')
    by = s1.segmented_control('Sort by', list(sort_opts), default='ROE (high first)', required=True)
    s2.metric('Matches', f'{len(d):,}')
    col, asc = sort_opts[by]
    d = d.sort_values(col, ascending=asc, na_position='last')

    cols = ['name', 'sector', 'data', 'rating', 'snapshot_s', 'snapshot_view_s', 'snapshot_cov_s', 'fy_s', 'mcap', 'pe', 'pb', 'ev_ebitda', 'ronw', 'roce', 'op_margin', 'de', 'icr', 'rev_cagr2', 'promoter_pct', 'flags_s']
    tab_t, tab_c = st.tabs(['📋 Results', '📈 P/E vs ROE'])
    with tab_t:
        st.dataframe(d[cols], hide_index=True, height=520, column_config={
            'name': st.column_config.TextColumn('Company', width='medium'), 'sector': st.column_config.TextColumn('Sector', width='medium'),
            'data': st.column_config.TextColumn('Data', width='small'), 'rating': st.column_config.TextColumn('Rating', width='small'),
            'snapshot_s': st.column_config.NumberColumn('Snapshot', format='%.1f', help='Broad-universe assessment only; not a rank.'),
            'snapshot_view_s': st.column_config.TextColumn('Snapshot view', width='small'),
            'snapshot_cov_s': st.column_config.NumberColumn('Snapshot coverage', format='%.0f%%'),
            'fy_s': st.column_config.TextColumn('Year', width='small'),
            'mcap': st.column_config.NumberColumn('Mcap (₹ cr)', format='%.0f'),
            'pe': st.column_config.NumberColumn('P/E', format='%.1f'), 'pb': st.column_config.NumberColumn('P/B', format='%.1f'),
            'ev_ebitda': st.column_config.NumberColumn('EV/EBITDA', format='%.1f'),
            'ronw': st.column_config.NumberColumn('ROE', format='%.1f%%'), 'roce': st.column_config.NumberColumn('ROCE', format='%.1f%%'),
            'op_margin': st.column_config.NumberColumn('OP margin', format='%.1f%%'), 'de': st.column_config.NumberColumn('D/E', format='%.2f'),
            'icr': st.column_config.NumberColumn('Int. cover', format='%.1fx'), 'rev_cagr2': st.column_config.NumberColumn('Rev CAGR 2Y', format='%.1f%%'),
            'promoter_pct': st.column_config.NumberColumn('Promoter', format='%.1f%%'), 'flags_s': st.column_config.TextColumn('Flags', width='large'),
        })
        out = d[cols].rename(columns={'fy_s': 'year', 'flags_s': 'flags'})
        st.download_button('Download results (CSV)', out.to_csv(index=True).encode('utf-8'), 'artha_screen.csv', 'text/csv', icon=':material/download:')
    with tab_c:
        if len(d):
            ch = d[['pe', 'ronw', 'mcap', 'data']].rename(columns={'pe': 'P/E', 'ronw': 'ROE %', 'mcap': 'Market cap'})
            st.scatter_chart(ch, x='P/E', y='ROE %', color='data', size='Market cap', height=480)
            st.caption('Top-left = high return on equity at a low multiple. Colour shows how much data the company has.')
    st.caption(('Valuation uses the latest NSE market-price overlay where available; companies without a current NSE quote retain their saved Capitaline year-end valuation. ' if IS_LIVE else 'Valuation uses the year-end market cap in Capitaline for the same year as the accounts — not a live price. ') +
               'P/E uses continuing profit after discontinued operations, and core earnings when other income is over 40% of PBT.')
    footer()

# ==========================================
# PAGE: REBUILD DATA
# ==========================================
def rebuild_page():
    page_head('Rebuild data', 'Replace Capitaline exports and recalculate every ranking.')
    if not is_admin():
        st.info('Rebuilding data is limited to the site administrator. Unlock admin tools in the sidebar.'); footer(); return
    st.markdown('#### 1. Capitaline files used by the model (in `data/raw/`)')
    st.dataframe(pd.DataFrame([{'File': k, 'Expected name': v, 'Present': '✅' if (RAW / v).exists() else '❌ missing'} for k, v in FILES.items()]),
                 hide_index=True)
    st.markdown('#### 2. Upload replacement files')
    uploaded = st.file_uploader('Excel sheets (.xlsx) — the file name must match an expected name above', type=['xlsx'], accept_multiple_files=True)
    for up in uploaded or []:
        if up.name in FILES.values():
            (RAW / up.name).write_bytes(up.getvalue()); st.success(f'Saved **{up.name}** to data/raw/')
        else:
            st.warning(f'**{up.name}** was not saved: rename it to one of the expected names first.')
    st.markdown('#### 3. Run the pipeline')
    st.caption('Rebuilds features, TOPSIS rankings with 400 Dirichlet robustness draws, the HTML dashboard and the widened universe (~3 min).')
    if st.button('🚀 Rebuild everything', type='primary', width='stretch'):
        with st.spinner('Running load → build_lite → build → rank → export → build_html → build_extra…'):
            res = subprocess.run([sys.executable, str(ROOT / 'run_pipeline.py')], capture_output=True, text=True)
        (st.success if res.returncode == 0 else st.error)('Pipeline rebuilt successfully.' if res.returncode == 0 else 'The pipeline failed — see the output below.')
        with st.expander('Pipeline output', expanded=True):
            st.code(res.stdout[-3000:] + res.stderr[-3000:], language='bash')
        if res.returncode == 0:
            for lp in ['features.pkl', 'rank.pkl', 'universe.pkl', 'data.json', 'engine.json', 'meta.json', 'status.json']:
                try: (LIVE / lp).unlink(missing_ok=True)
                except Exception: pass
            try: (WEB / 'artha_live.html').unlink(missing_ok=True)
            except Exception: pass
            #st.session_state['market_mode'] = 'Historical'
            st.info('Historical fundamentals changed, so the previous derived live ranking was cleared. Refresh Live mode again when you want the new market overlay.')
        st.cache_data.clear()

# ==========================================
# PAGE: ASK ARTHA (server-side Claude)
# ==========================================
ASK_CHIPS = [
    'Which sector deserves capital first, and why?',
    'Explain how ARTHA weights criteria in the Pharma sector.',
    'Compare TCS, Infosys and HCL Technologies on quality and price.',
    'Find quality compounders: ROE above 18%, debt/equity under 0.5, market cap over ₹20,000 cr.',
    'Which private bank ranks best, and what can this model not see?',
    'Does the ARTHA ranking actually line up with stock returns?',
]

def _usage_file():
    return ROOT / 'data' / 'ask_usage.json'

def _daily_count(bump=False):
    p = _usage_file(); today = date.today().isoformat()
    try:
        u = json.load(open(p))
    except Exception:
        u = {}
    if u.get('date') != today:
        u = {'date': today, 'questions': 0, 'input_tokens': 0, 'output_tokens': 0}
    if bump:
        u['questions'] += 1
        try:
            p.write_text(json.dumps(u))
        except Exception:
            pass
    return u

def _record_tokens(usage):
    u = _daily_count()
    u['input_tokens'] = u.get('input_tokens', 0) + usage.get('input_tokens', 0)
    u['output_tokens'] = u.get('output_tokens', 0) + usage.get('output_tokens', 0)
    try:
        _usage_file().write_text(json.dumps(u))
    except Exception:
        pass

@st.cache_data(ttl=300, show_spinner=False)
def _claude_local():
    return _fresh_module('ask_artha').claude_local_status()


def ask_provider():
    """Which engine answers Ask ARTHA: Claude on this computer if available, then any configured key, else offline."""
    forced = str(secret('ARTHA_ENGINE', '') or '').lower()
    if forced == 'offline':
        return {'kind': 'offline', 'label': 'Offline (free, no AI key)', 'model': 'built-in'}
    if forced in ('', 'claude_local', 'local'):
        ok, msg = _claude_local()
        if ok:
            return {'kind': 'claude_local', 'label': 'Claude on this computer (your Claude subscription)', 'model': secret('ARTHA_LOCAL_MODEL', 'sonnet')}
    if secret('GROQ_API_KEY'):
        return {'kind': 'openai', 'label': 'Groq (free plan)', 'key': secret('GROQ_API_KEY'),
                'base_url': secret('ARTHA_LLM_BASE_URL', 'https://api.groq.com/openai/v1'), 'model': secret('ARTHA_MODEL', 'openai/gpt-oss-120b')}
    if secret('OPENAI_COMPAT_API_KEY') and secret('ARTHA_LLM_BASE_URL'):
        return {'kind': 'openai', 'label': 'OpenAI-compatible API', 'key': secret('OPENAI_COMPAT_API_KEY'),
                'base_url': secret('ARTHA_LLM_BASE_URL'), 'model': secret('ARTHA_MODEL', '')}
    if secret('ANTHROPIC_API_KEY'):
        from ask_artha import DEFAULT_MODEL
        return {'kind': 'claude', 'label': 'Claude', 'key': secret('ANTHROPIC_API_KEY'), 'model': secret('ARTHA_MODEL', DEFAULT_MODEL)}
    return {'kind': 'offline', 'label': 'Offline (free, no AI key)', 'model': 'built-in'}


def _fresh_module(name):
    """Import a pipeline module, reloading it if its file changed since it was loaded (no app restart needed)."""
    import importlib
    mod = importlib.import_module(name)
    try:
        mt = os.path.getmtime(mod.__file__)
        if getattr(mod, '_artha_mtime', None) != mt:      # first use in this process, or file changed
            mod = importlib.reload(mod)
        mod._artha_mtime = mt
    except Exception:
        pass
    return mod


def ask_page():
    _aa = _fresh_module('ask_artha')
    ArthaData, ask, ask_openai_compatible, answer_offline, ask_claude_local, FreeAPIError = (
        _aa.ArthaData, _aa.ask, _aa.ask_openai_compatible, _aa.answer_offline, _aa.ask_claude_local, _aa.FreeAPIError)
    page_head('Ask ARTHA', 'Ask about any sector, company, score or the methodology. Answers are built from ARTHA\'s own data through lookup tools.',
              'Live data' if IS_LIVE else 'Capitaline data')
    prov = ask_provider()
    if prov['kind'] == 'claude_local':
        st.success('Answering with **Claude on this computer** through your Claude Code sign-in (no API key, no extra cost). Each answer also fetches live NSE prices for the companies you mention.', icon=':material/bolt:')
    if prov['kind'] == 'offline':
        st.info('Running in free **offline mode**: answers come straight from ARTHA\'s data for set question types (a company, a comparison, a sector, a screen, the method, the validation). '
                'For free-form AI answers on your own computer, sign in to Claude Code once (open a terminal, run `claude`, log in) and reload; on a server, add a free `GROQ_API_KEY` (see DEPLOY.md).')
    free = prov['kind'] in ('offline', 'claude_local')
    per_session = int(secret('ARTHA_MAX_QUESTIONS_PER_SESSION', 25)) if not free else 10**6
    per_day = int(secret('ARTHA_MAX_QUESTIONS_PER_DAY', 300)) if not free else 10**9

    hist = st.session_state.setdefault('ask_history', [])
    for h in hist:
        with st.chat_message('user' if h['role'] == 'user' else 'assistant', avatar=None if h['role'] == 'user' else ':material/insights:'):
            if h.get('tools'):
                st.caption('Looked up: ' + ' · '.join(h['tools']))
            st.markdown(h['content'])

    picked = None
    if not hist:
        st.markdown('##### Try asking')
        cols = st.columns(2)
        for i, q in enumerate(ASK_CHIPS):
            if cols[i % 2].button(q, key=f'chip{i}', width='stretch'):
                picked = q
    q = st.chat_input('Ask about a sector, a company, a screen or the method…', max_chars=1000) or picked
    c1, c2 = st.columns([4, 1])
    asked = sum(1 for h in hist if h['role'] == 'user')
    c1.caption((f'{asked} of {per_session} questions used in this session · ' if not free else '')
               + f"engine: {prov['label']}" + (f" · model `{prov['model']}`" if prov['kind'] != 'offline' else '') + f' · {"live" if IS_LIVE else "historical"} dataset')
    if hist and c2.button('New conversation', width='stretch'):
        st.session_state['ask_history'] = []; st.rerun()
    if not q:
        footer(); return
    if asked >= per_session:
        st.warning('This session has reached its question limit. Reload the page later to start a new session.'); return
    if not free and _daily_count()['questions'] >= per_day:
        st.warning('Ask ARTHA has reached today\'s usage limit on this server. Please try again tomorrow.'); return

    data = ArthaData(comps, uni, sectors, meta, 'live (current prices + latest Yahoo fundamentals)' if IS_LIVE else 'historical (Capitaline year-end)',
                     status=LIVE_STATUS if IS_LIVE else {'mode': 'historical', 'source': 'Capitaline exports'}, validation=load_validation())
    history = [{'role': h['role'], 'content': h['content']} for h in hist]
    with st.chat_message('user'):
        st.markdown(q)
    with st.chat_message('assistant', avatar=':material/insights:'):
        tools_box = st.empty(); out = st.empty(); used = []
        def on_tool(name, args):
            used.append(name + (f" {json.dumps(args, ensure_ascii=False)}" if args else ''))
            tools_box.caption('Looked up: ' + ' · '.join(used))
        def on_text(t):
            out.markdown(t + ' ▌')
        answer = None; fail_note = ''
        try:
            if prov['kind'] == 'offline':
                answer, used0 = answer_offline(data, q); used.extend(used0)
            elif prov['kind'] == 'claude_local':
                with st.spinner('Fetching live prices and asking Claude on this computer…'):
                    answer, used0 = ask_claude_local(data, history, q, model=prov['model'])
                used.extend(used0)
            elif prov['kind'] == 'openai':
                _daily_count(bump=True)
                with st.spinner('Thinking…'):
                    answer, usage = ask_openai_compatible(data, history, q, prov['key'], base_url=prov['base_url'], model=prov['model'], on_tool=on_tool)
                _record_tokens(usage)
            else:
                import anthropic
                client = anthropic.Anthropic(api_key=prov['key'], max_retries=2, timeout=90)
                _daily_count(bump=True)
                answer, usage = ask(client, data, history, q, model=prov['model'], on_text=on_text, on_tool=on_tool)
                _record_tokens(usage)
        except FreeAPIError as e:
            msg = {'auth': 'The server\'s AI key was rejected. The site owner needs to update GROQ_API_KEY.',
                   'rate': 'The free AI plan is busy right now. Here is the built-in answer instead.',
                   'model': f"The configured model `{prov['model']}` was not found.",
                   'connection': 'Could not reach the AI service. Here is the built-in answer instead.'}.get(e.kind, f'AI service error: {e}')
            out.warning(msg); fail_note = f'{msg} ({e})'
        except Exception as e:
            name = type(e).__name__
            msg = {'AuthenticationError': 'The server\'s Claude API key was rejected.',
                   'RateLimitError': 'Too many requests right now. Here is the built-in answer instead.',
                   'NotFoundError': f"The configured model `{prov['model']}` was not found.",
                   'APIConnectionError': 'Could not reach Claude from the server. Here is the built-in answer instead.'}.get(name, f'Something went wrong reaching the AI service ({name}). Here is the built-in answer instead.')
            out.warning(msg); fail_note = f'{msg} ({name}: {str(e)[:300]})'
        if answer is None:                                    # always fall back to the free built-in answer
            answer, used0 = answer_offline(data, q); used.extend(used0)
            if fail_note:
                answer = f'_{prov["label"]} did not answer: {fail_note}. Built-in answer below._\n\n' + answer
            tools_box.caption('Looked up: ' + ' · '.join(used) if used else '')
            st.markdown(answer)
        else:
            out.markdown(answer)
    hist += [{'role': 'user', 'content': q}, {'role': 'assistant', 'content': answer, 'tools': used}]
    st.rerun()

# ==========================================
# PAGE: PERFORMANCE VALIDATION (Karl Pearson)
# ==========================================
def _r_text(b):
    if not b or b.get('r') is None:
        return 'Not enough data.'
    r, lo, hi, p = b['r'], b['ci95'][0], b['ci95'][1], b['p']
    strength = 'negligible' if abs(r) < 0.1 else 'weak' if abs(r) < 0.3 else 'moderate' if abs(r) < 0.5 else 'strong'
    sig = 'statistically significant at 5%' if p < 0.05 else 'not statistically different from zero at 5%'
    return f"r = {r:+.3f} ({strength}, {'positive' if r > 0 else 'negative'}); 95% CI {lo:+.2f} to {hi:+.2f}; p = {p:.3g}; n = {b['n']} — {sig}."

def _validation_block(r, predictive):
    sn, cs = r.get('sector_neutral') or {}, r.get('cross_sector') or {}
    period = f"{r.get('formed_on', r.get('from'))} → {r.get('measured_to', r.get('to'))}"
    kpis([
        ('Pearson r (sector-neutral)', f"{sn.get('r'):+.3f}" if sn.get('r') is not None else '—', f"95% CI {sn.get('ci95')} · n={sn.get('n')}"),
        ('Pearson r (cross-sector, AlphaPct)', f"{cs.get('r'):+.3f}" if cs.get('r') is not None else '—', f"p = {cs.get('p')}"),
        ('Top-minus-bottom quintile', f"{r.get('quintile_spread_q1_minus_q5'):+.1f} pts/yr" if r.get('quintile_spread_q1_minus_q5') is not None else '—',
         f"permutation p = {r.get('spread_perm_p')}"),
        ('Decile-portfolio r', f"{r.get('decile_level_r'):+.3f}" if r.get('decile_level_r') is not None else '—', f"permutation p = {r.get('decile_level_r_perm_p')}"),
        ('Top-10 ARTHA picks', f_pct(r.get('top10_equal_weight_return')), f"vs Nifty 50 {f_pct(r.get('benchmark_return'))} · bottom 10 {f_pct(r.get('bottom10_equal_weight_return'))} · universe {f_pct(r.get('universe_equal_weight_return'))} (CAGR)"),
    ])
    st.markdown(f"**Sector-neutral result:** {_r_text(sn)}")
    st.caption(f"Window {period}. Returns are annualised total returns (dividend- and split-adjusted Yahoo prices). "
               + ('Ranking formed only from data available at that fiscal year-end.' if predictive else 'Today\'s ranking compared with past returns — descriptive, not predictive.'))
    a, b = st.columns(2)
    with a:
        st.markdown('**Average annual return by ARTHA decile** (D1 = top 10% in sector)')
        q = pd.DataFrame(r.get('deciles') or [])
        if len(q):
            st.bar_chart(q.set_index('d')['mean'].rename('Mean CAGR %'), height=260, color='#3b82f6', sort=False)
        if r.get('decile_level_r') is not None:
            st.caption(f"Decile-portfolio Pearson r = {r.get('decile_level_r'):+.3f} across {r.get('decile_level_n')} deciles "
                       f"(permutation p = {r.get('decile_level_r_perm_p')}: share of 1,000 random within-sector shuffles that score at least as high). "
                       f"D1 − D10 = {r.get('decile_spread_d1_minus_d10')} pts a year.")
    with b:
        st.markdown('**Each company: ARTHA percentile vs return percentile** (both inside its sector)')
        pts = pd.DataFrame(r.get('points') or [])
        if len(pts) and 'ret_pct_sector' in pts:
            st.scatter_chart(pts, x='pctile', y='ret_pct_sector', height=300, color='#3b82f6', x_label='ARTHA percentile in sector', y_label='Return percentile in sector')
            st.caption('These are the two variables in the sector-neutral Pearson r. A strong positive relationship would show as a band rising from bottom-left to top-right.')
    c, d = st.columns(2)
    with c:
        st.markdown('**Top 10 ARTHA-ranked companies (by AlphaPct)**')
        st.dataframe(pd.DataFrame(r.get('top10_artha') or []), hide_index=True, column_config={
            'return': st.column_config.NumberColumn('Return (CAGR %)', format='%.1f'), 'alpha': st.column_config.NumberColumn('AlphaPct', format='%.0f')})
    with d:
        st.markdown('**Top 10 best-returning stocks and where ARTHA ranked them**')
        st.dataframe(pd.DataFrame(r.get('top10_returners') or []), hide_index=True, column_config={
            'return': st.column_config.NumberColumn('Return (CAGR %)', format='%.1f'), 'artha_pctile': st.column_config.NumberColumn('ARTHA pctile', format='%.0f')})
    with st.expander('Pearson r inside each sector'):
        st.dataframe(pd.DataFrame(r.get('per_sector') or []), hide_index=True)

def validation_page():
    page_head('Performance validation', 'Karl Pearson correlation between ARTHA scores and realised stock returns.')
    v = load_validation()
    if is_admin():
        with st.expander('Run / refresh validation' + (' (admin)' if secret('ARTHA_ADMIN_PASSWORD') else ''), expanded=not v):
            st.caption('Downloads ~11 years of daily adjusted prices for the full-model companies and benchmarks (cached for 20 hours), rebuilds point-in-time ARTHA rankings for FY25, FY23 and FY21, and recomputes every statistic. Takes a few minutes.')
            if st.button('Run validation', type='primary'):
                try:
                    from validation import run
                    with st.status('Running validation…', expanded=True) as box:
                        run(progress=lambda m: box.write(m))
                        box.update(label='Validation complete', state='complete')
                    st.rerun()
                except Exception as e:
                    st.error(f'Validation could not complete: {e}')
    if not v:
        st.info('Validation has not been run on this server yet. Run `python pipeline/validation.py` (or use the button above) to create it.'); footer(); return
    st.caption(f"Prices to {v.get('price_end') or '— (not downloaded)'} · current ranking used for the descriptive test: {v.get('current_ranking') or '—'} · universe: {v.get('universe')}")
    if v.get('price_error'):
        st.warning(f"Return-based tests were skipped: {v['price_error']}")
    t0, t1, t2, t3 = st.tabs(['🏭 Business results (fundamentals)', '🔮 Stock returns: point-in-time', '🪞 Current ranking vs past returns', '📐 Method & how to read it'])
    with t0:
        fu = v.get('fundamentals') or {}
        if not fu:
            st.info('Run the validation to create this test.')
        else:
            st.markdown('Does a company ARTHA ranked highly **back then** go on to earn higher returns on capital and grow profits faster **afterwards**? Rankings are rebuilt from data available at each year-end; outcomes come from the later Capitaline years. No prices are involved.')
            fy = st.segmented_control('Ranking as of', list(fu), default=list(fu)[-1], key='fu_h', required=True)
            r = fu[fy]
            rows = []
            for oc in ('future_return_on_capital', 'future_pat_cagr'):
                x = r.get(oc) or {}
                for who, key in [('ARTHA final score', 'artha_score_vs_outcome'), ('ARTHA Quality score (Q)', 'quality_score_vs_outcome')]:
                    b = x.get(key) or {}
                    rows.append({'Outcome': x.get('label'), 'Score': who, 'Pearson r': b.get('r'), '95% CI': str(b.get('ci95')), 'p-value': (f"{b['p']:.2g}" if b.get('p') is not None else '—'), 'n': b.get('n')})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch', column_config={'Pearson r': st.column_config.NumberColumn(format='%+.3f')})
            a_, b_ = st.columns(2)
            for col, oc in [(a_, 'future_return_on_capital'), (b_, 'future_pat_cagr')]:
                x = r.get(oc) or {}
                qm = pd.Series(x.get('quintile_means') or {}, dtype=float)
                with col:
                    st.markdown(f"**{x.get('label')}** by ARTHA quintile (Q1 = top 20%)")
                    if len(qm):
                        st.bar_chart(qm.rename('Mean %'), height=240, color='#10b981', sort=False)
            st.caption('Sector-neutral: both percentiles are computed inside each sector. ROCE is used for industrials, ROE for banks, NBFCs and other financials. PAT growth tends to mean-revert (companies coming off a weak base grow fastest), which a quality-and-value model does not try to capture.')
    t1, t2, t3 = t1, t2, t3
    with t1:
        pit = v.get('point_in_time') or {}
        if not pit:
            st.info('No point-in-time results.')
        else:
            h = st.segmented_control('Horizon', list(pit), default=list(pit)[0], key='pit_h', required=True)
            r = pit[h]
            st.markdown(f"Ranking rebuilt **as of {r.get('asof_fy')}** using only data available then, formed on {r.get('formed_on')}, returns measured over the next **{r.get('horizon_years')} year(s)**.")
            _validation_block(r, True)
    with t2:
        tr = v.get('trailing') or {}
        if tr:
            h = st.segmented_control('Horizon', list(tr), default=list(tr)[0], key='tr_h', required=True)
            st.warning('Descriptive only: today\'s ranking already contains growth and price-to-52-week-high inputs that partly reflect the same past returns, while the valuation pillar penalises stocks that have already rallied. A high or low r here does not show that ARTHA predicts returns.')
            _validation_block(tr[h], False)
    with t3:
        st.markdown("""
**What is correlated.** For each company, *x* = its ARTHA percentile inside its sector (100 = sector leader) and *y* = the percentile of its realised return inside the same sector. Karl Pearson's coefficient is r = cov(x, y) / (σx·σy). Using percentiles makes r robust to a few multi-bagger outliers (it is then numerically close to Spearman's ρ). The cross-sector version uses AlphaPct against the raw return percentile.

**Why sector-neutral.** ARTHA ranks companies *within* sectors. Comparing a bank's score with a defence stock's return would mostly measure sector performance, not the model.

**Point-in-time test (the one that counts).** The Capitaline history is sliced so that FY25, FY23 or FY21 becomes the "latest year"; every feature, weight (subjective + Entropy + CRITIC), TOPSIS run and the 70:30 blend is recomputed from that data alone. The ranking is formed on 1 July after the year-end (results are public by then) and held for 1, 3 or 5 years. A 10-year point-in-time test is not possible because the Capitaline file holds 10 years and the 5-year criteria need history before the start date.

**Significance.** Each r has a p-value and a Fisher-z 95% confidence interval. Portfolio sorts (quintiles and deciles) are tested with 1,000 within-sector random shuffles of returns (permutation p). The decile-portfolio correlation uses ten group averages, so it is reported together with that permutation p.

**What a realistic r looks like.** In published equity factor research the correlation between a fundamental score and next-period returns (the "information coefficient") is typically 0.02–0.15; a stable 0.05–0.10 is considered useful. Stock-level correlations of 0.7+ with future returns do not occur in genuine out-of-sample tests, so a result like that would point to look-ahead bias rather than a better model.

**Known limitations.** Survivorship bias (the universe is today's listed companies); promoter-holding change is unavailable point-in-time and is dropped by the coverage rule in the backtests; Yahoo prices may miss some corporate actions; small sectors give unstable per-sector r.
""")
    footer()

# ==========================================
# NAVIGATION
# ==========================================
PAGES = {
    'home': st.Page(home, title='Home', icon=':material/home:', default=True),
    'dashboard': st.Page(dashboard, title='Dashboard', icon=':material/dashboard:'),
    'sectors': st.Page(sectors_page, title='Sector rankings', icon=':material/leaderboard:', url_path='sectors'),
    'company': st.Page(company_page, title='Company', icon=':material/domain:', url_path='company'),
    'compare': st.Page(compare_page, title='Compare', icon=':material/compare_arrows:', url_path='compare'),
    'screener': st.Page(screener_page, title='Valuation screener', icon=':material/filter_alt:', url_path='screener'),
    'rebuild': st.Page(rebuild_page, title='Rebuild data', icon=':material/sync:', url_path='rebuild'),
    'ask': st.Page(ask_page, title='Ask ARTHA', icon=':material/forum:', url_path='ask'),
    'validation': st.Page(validation_page, title='Performance validation', icon=':material/query_stats:', url_path='validation'),
}
nav = st.navigation({
    'Overview': [PAGES['home'], PAGES['dashboard'], PAGES['ask']],
    'Analyse': [PAGES['sectors'], PAGES['company'], PAGES['compare'], PAGES['screener'], PAGES['validation']],
    'Data': [PAGES['rebuild']],
})

with st.sidebar:
    if requested_mode == 'Live':
        s0 = live_status()
        if live_ready() and s0:
            try:
                ts = pd.Timestamp(s0.get('created_at_utc')).tz_convert('Asia/Kolkata')
                st.caption(f"Latest saved market refresh: {ts.strftime('%d %b %Y, %I:%M %p IST')}")
            except Exception:
                st.caption('Latest saved market refresh is loaded.')
        else:
            st.caption('No saved live snapshot yet. Refresh once to create it.')
        if s0 and s0.get('live_fundamentals'):
            st.caption(f"Latest fundamentals for {s0.get('full_model_fundamentals_updated', 0)} of {s0.get('full_model_total', 0)} ranked companies.")
        if is_admin():
            with_fund = st.toggle('Include latest fundamentals', value=True, help='Download Yahoo annual/quarterly/TTM statements for the full-model companies and recompute every ratio. Prices-only is faster.')
            if st.button('↻ Refresh live data & rerank', type='primary', width='stretch'):
                try:
                    from live_refresh import refresh_live
                    with st.status('Refreshing live data…', expanded=True) as box:
                        refresh_live(fundamentals=with_fund, progress=lambda m: box.write(m))
                        box.update(label='Live data refreshed and model rerun', state='complete')
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f'Live refresh could not complete: {e}')
            st.caption('Companies without usable Yahoo statements keep Capitaline fundamentals; without a quote they keep the saved Capitaline valuation.')
        else:
            st.caption('Showing the latest saved live snapshot. Refreshing is limited to the site administrator.')

    st.markdown(f"""
    <div style="background: rgba(128,128,128,0.06); border-radius: 8px; padding: 12px; border: 1px solid rgba(128,128,128,0.12); font-size: 12px; line-height: 1.6;">
        <div style="font-size: 18px; font-weight: 900; letter-spacing: -0.03em; color: #3b82f6; margin-bottom: 6px;">◈ ARTHA</div>
        <div style="color: #64748b; font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; margin-bottom: 4px;">Universe coverage</div>
        <div><b>{len(ranked):,}</b> TOPSIS-ranked (full model)</div>
        <div><b>{SNAPSHOT_BROAD_COUNT:,}</b> current-assessed (full/quality Snapshot)</div>
        <div><b>{int((uni.src == 'lite').sum()):,}</b> broad universe</div>
        <div><b>{int((uni.src == 'new').sum()):,}</b> added from one-year files</div>
        <div><b>{len(meta)}</b> sectors</div>
        <div style="margin-top:4px; color:#64748b;">Mode: <b>{'Live market overlay' if IS_LIVE else 'Historical'}</b></div>
    </div>""", unsafe_allow_html=True)
    st.caption(f'🛡️ {DISCLAIMER}')
    if secret('ARTHA_ADMIN_PASSWORD'):
        with st.expander('Admin', expanded=False):
            if st.session_state.get('admin_ok'):
                st.caption('Admin tools unlocked for this session.')
            else:
                pw = st.text_input('Admin password', type='password', key='admin_pw')
                if pw:
                    import hmac
                    if hmac.compare_digest(str(pw), str(secret('ARTHA_ADMIN_PASSWORD'))):
                        st.session_state['admin_ok'] = True; st.rerun()
                    else:
                        st.error('Incorrect password.')

nav.run()
