import streamlit as st

from ui import theme as t
from ui.assets import data_uri


def load_css():
    splash_bg = data_uri("splash_bg.webp")
    splash_bg_css = f"url('{splash_bg}'), " if splash_bg else ""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

    :root {{
        --cream: {t.CREAM};
        --card: {t.CARD};
        --border: {t.BORDER};
        --ink: {t.INK};
        --muted: {t.MUTED};
        --rust: {t.RUST};
        --rust-dark: {t.RUST_DARK};
        --sage: {t.SAGE};
        --tan: {t.TAN};
        --green: {t.GREEN};
        --amber: {t.AMBER};
        --red: {t.RED};
    }}

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
        color: var(--ink);
    }}

    #MainMenu, footer {{ display: none !important; }}

    /* Keep the header bar itself (it's what hosts the sidebar collapse/
       expand arrow) but hide everything else inside it, so the arrow is
       always there to bring the sidebar back after collapsing it.
       Multiple selectors below because Streamlit has used different
       internal names for this control across versions. */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 3rem !important;
        box-shadow: none !important;
    }}
    header[data-testid="stHeader"] * {{ visibility: hidden !important; }}
    header[data-testid="stHeader"] [data-testid="collapsedControl"],
    header[data-testid="stHeader"] [data-testid="collapsedControl"] *,
    header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"],
    header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"] *,
    header[data-testid="stHeader"] button[kind="header"],
    header[data-testid="stHeader"] button[kind="header"] * {{
        visibility: visible !important;
    }}
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    button[kind="header"] {{
        display: flex !important;
        z-index: 999999 !important;
        position: relative !important;
    }}

    /* Sidebar's own collapse arrow (the one shown when the sidebar IS
       open, to close it) — force it visible too, on the same principle. */
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
    section[data-testid="stSidebar"] button[kind="headerNoPadding"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }}
    div[data-testid="stDecoration"] {{ display: none !important; }}
    div[data-testid="stToolbar"] {{ display: none !important; }}
    div[data-testid="stStatusWidget"] {{ display: none !important; }}

    .stApp {{ background: var(--cream); }}

    div.block-container {{
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        max-width: 1500px;
    }}

    h1, h2, h3, .brv-serif {{
        font-family: 'Cormorant Garamond', serif;
    }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {t.SIDEBAR_TOP} 0%, {t.SIDEBAR_TOP} 45%, {t.SIDEBAR_BOTTOM} 100%);
        border-right: 1px solid #1a120c;
        min-width: 268px !important;
        width: 268px !important;
    }}
    section[data-testid="stSidebar"] > div {{ padding-top: 0; }}
    section[data-testid="stSidebar"] .block-container {{ padding: 0 !important; }}

    /* Native bordered containers used for chart/interactive sections */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        background: var(--card) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-radius: 16px !important; }}

    .brv-brand {{
        padding: 26px 22px 18px 22px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }}
    .brv-brand-row {{ display:flex; align-items:center; gap:10px; }}
    .brv-brand-title {{
        font-family: 'Cormorant Garamond', serif;
        font-weight: 700;
        font-size: 26px;
        letter-spacing: 2px;
        color: #F7F1E6;
        line-height: 1;
    }}
    .brv-brand-sub {{
        margin-top: 8px;
        font-size: 11px;
        line-height: 1.4;
        color: #B9AC94;
        letter-spacing: 0.2px;
    }}

    .brv-nav {{ padding: 14px 14px; }}
    .brv-nav a {{
        display:flex; align-items:center; gap:12px;
        padding: 10px 14px;
        margin-bottom: 4px;
        border-radius: 10px;
        color: #D9CDB6;
        text-decoration: none;
        font-size: 14.5px;
        font-weight: 500;
        transition: background 0.15s ease;
    }}
    .brv-nav a:hover {{ background: rgba(255,255,255,0.06); color: #F7F1E6; }}
    .brv-nav a.active {{
        background: linear-gradient(90deg, {t.RUST} 0%, {t.RUST_DARK} 100%);
        color: #FBF3EA;
        box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    }}
    .brv-nav svg {{ flex-shrink: 0; opacity: 0.95; }}

    .brv-sidebar-unit {{
        margin: 24px 16px 0 16px;
        position: relative;
        z-index: 2;
        background: rgba(20,14,10,0.55);
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px;
        padding: 12px 14px;
    }}
    .brv-sidebar-unit .name {{ color: #F5EEE1; font-weight: 700; font-size: 14px; }}
    .brv-sidebar-unit .loc {{ color: #C6B99E; font-size: 12px; margin-top: 1px; }}
    .brv-sidebar-unit .stat {{ display:flex; align-items:center; gap:6px; margin-top: 7px; font-size: 12px; color: #9FE1A8; font-weight: 600; }}
    .brv-sidebar-unit .dot {{ width:7px; height:7px; border-radius:50%; background:#4FCE6A; box-shadow: 0 0 6px #4FCE6A; }}

    .brv-sidebar-footer {{
        padding: 16px 22px 20px 22px;
        font-size: 11px;
        color: #A79A80;
        line-height: 1.5;
        letter-spacing: 0.3px;
    }}

    /* ---------- Small pill control (unit select / date range / search) ---------- */
    .brv-header-search {{
        display:inline-flex; align-items:center; gap:8px;
        background: var(--cream); border: 1px solid var(--border);
        border-radius: 9px; padding: 8px 14px; color: var(--muted); font-size: 13px;
    }}

    /* ---------- Page header ---------- */
    .brv-page-title {{
        font-family: 'Cormorant Garamond', serif;
        font-weight: 700;
        font-size: 40px;
        line-height: 1.1;
        margin: 4px 0 2px 0;
        color: var(--ink);
    }}
    .brv-page-sub {{
        color: var(--muted); font-size: 14.5px; margin-bottom: 6px;
        position: relative; padding-bottom: 14px;
    }}
    .brv-page-sub::after {{
        content:""; position:absolute; left:0; bottom:0; width:44px; height:2px; background: var(--rust);
    }}
    .brv-page-flag {{
        display:flex; align-items:center; gap:8px; color: var(--green); font-size: 13.5px; font-weight:600;
    }}
    .brv-page-flag .dot {{ width:8px; height:8px; border-radius:50%; background: var(--green); }}

    /* ---------- Cards ---------- */
    .brv-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 20px;
        height: 100%;
    }}
    .brv-card-top {{ display:flex; align-items:flex-start; gap:14px; }}
    .brv-icon-circle {{
        width:44px; height:44px; border-radius:50%;
        display:flex; align-items:center; justify-content:center; flex-shrink:0;
    }}
    .brv-metric-label {{ font-size: 13.5px; color: var(--muted); font-weight:500; margin-bottom: 4px;}}
    .brv-metric-row {{ display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; }}
    .brv-metric-value {{
        font-family: Arial, Helvetica, sans-serif; font-weight:700; font-size:30px; color: var(--ink); line-height:1;
    }}
    .brv-metric-unit {{ font-size: 14px; color: var(--muted); font-weight:500; }}
    .brv-metric-change {{ font-size: 12.5px; font-weight:700; display:inline-flex; align-items:center; gap:2px; }}
    .brv-metric-change.good {{ color: var(--green); }}
    .brv-metric-change.bad {{ color: var(--red); }}
    .brv-progress-track {{ background: #E9E2D2; border-radius: 6px; height:6px; margin-top:14px; overflow:hidden; }}
    .brv-progress-fill {{ height:100%; border-radius:6px; }}

    /* ---------- Section card (chart / table containers) ---------- */
    .brv-section {{
        background: var(--card); border: 1px solid var(--border); border-radius: 16px;
        padding: 18px 22px 20px 22px; margin-bottom: 20px;
    }}
    .brv-section-head {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }}
    .brv-section-title {{ display:flex; align-items:center; gap:10px; font-size:17px; font-weight:700; color: var(--ink); }}
    .brv-section-title .muted {{ font-weight: 500; font-size: 13px; color: var(--muted); margin-left:2px; }}
    .brv-section-link {{ color: var(--rust-dark); font-size:13px; font-weight:600; text-decoration:none; }}

    /* ---------- Status pill ---------- */
    .brv-pill {{
        display:inline-flex; align-items:center; gap:6px;
        padding: 4px 11px; border-radius: 999px; font-size:12px; font-weight:700;
    }}

    /* ---------- Tables ---------- */
    table.brv-table {{ width:100%; border-collapse: collapse; font-size: 13.5px; }}
    table.brv-table thead th {{
        text-align:left; color: var(--muted); font-weight:600; font-size:12px;
        text-transform: uppercase; letter-spacing: 0.4px;
        padding: 0 10px 10px 10px; border-bottom: 1px solid var(--border);
    }}
    table.brv-table tbody td {{
        padding: 11px 10px;
        border-bottom: 1px solid #F0EADC;
        color: var(--ink);
    }}
    table.brv-table tbody tr:last-child td {{ border-bottom: none; }}
    table.brv-table tbody tr.highlight td {{ background: #FBEFE9; }}

    /* ---------- Joint map ---------- */
    .brv-jointmap {{ position:relative; padding: 34px 10px 10px 10px; }}
    .brv-jointmap-line {{ position:absolute; left:24px; right:24px; top:64px; height:2px; background: var(--border); }}
    .brv-jointmap-row {{ display:flex; justify-content:space-between; position:relative; z-index:2; }}
    .brv-joint {{ display:flex; flex-direction:column; align-items:center; gap:6px; width: 90px; }}
    .brv-joint-label {{ font-size:13px; font-weight:700; color: var(--ink); }}
    .brv-joint-label.active {{ color: var(--red); }}
    .brv-joint-dot {{ width:18px; height:18px; border-radius:50%; border: 3px solid white; box-shadow: 0 0 0 2px currentColor; }}
    .brv-joint-dot.pulse {{ box-shadow: 0 0 0 8px rgba(198,58,46,0.15), 0 0 0 2px currentColor; }}
    .brv-joint-pos {{ font-size:12px; color: var(--muted); }}
    .brv-jointmap-ends {{ display:flex; justify-content:space-between; margin-top: 8px; font-size:12px; color: var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:0.4px; }}

    /* ---------- Progress bars (predictive) ---------- */
    .brv-barlabel {{ display:flex; justify-content:space-between; font-size:13.5px; margin-bottom:6px; }}
    .brv-barlabel .val {{ font-weight:700; }}

    /* ---------- Misc ---------- */
    .brv-divider {{ height:1px; background: var(--border); margin: 6px 0 16px 0; }}
    .brv-kv {{ display:flex; justify-content:space-between; align-items:center; padding:9px 0; border-bottom:1px solid #F0EADC; font-size:13.5px; }}
    .brv-kv:last-child {{ border-bottom:none; }}
    .brv-kv .k {{ color: var(--muted); display:flex; align-items:center; gap:8px; }}
    .brv-kv .v {{ font-weight:700; color: var(--ink); }}

    .brv-alert-row {{ display:flex; align-items:flex-start; gap:12px; padding: 11px 0; border-bottom:1px solid #F0EADC; }}
    .brv-alert-row:last-child {{ border-bottom:none; }}
    .brv-alert-dot {{ width:9px; height:9px; border-radius:50%; margin-top:6px; flex-shrink:0; }}
    .brv-alert-title {{ font-weight:600; font-size:13.5px; color: var(--ink); }}
    .brv-alert-meta {{ font-size:12px; color: var(--muted); margin-top:2px; }}
    .brv-alert-time {{ font-size:12px; color: var(--muted); white-space:nowrap; }}

    .brv-chip-row {{ display:flex; gap:8px; flex-wrap:wrap; }}
    .brv-chip {{ background: #F3E4DD; color: var(--rust-dark); font-size:12px; font-weight:600; padding:4px 10px; border-radius:999px; }}

    .brv-recommend {{
        background: #FBEFE9; border:1px solid #F1D9CE; border-radius:12px; padding:14px 16px;
        display:flex; gap:12px; align-items:flex-start; color: var(--rust-dark); font-size:13.5px; font-weight:600;
    }}

    div[data-testid="stHorizontalBlock"] {{ gap: 20px; }}

    /* ---------- Splash screen ---------- */
    .brv-splash {{
        position: fixed; inset: 0; z-index: 9999;
        background:
            linear-gradient(115deg, rgba(18,12,8,0.97) 0%, rgba(18,12,8,0.72) 42%, rgba(18,12,8,0.28) 62%, rgba(18,12,8,0.05) 80%),
            {splash_bg_css}
            linear-gradient(205deg, #3d2c1d 0%, #241a12 55%, #120c08 100%);
        background-size: cover, cover, cover;
        background-position: center, center, center;
        background-repeat: no-repeat;
        color: #EFE6D6;
        font-family: 'DM Sans', sans-serif;
        overflow: hidden;
    }}
    .brv-splash-topleft, .brv-splash-topright {{
        position:absolute; top:34px; font-size:11px; letter-spacing:3px; color:#C9BC9F; line-height:1.9; font-weight:600;
    }}
    .brv-splash-topleft {{ left:48px; }}
    .brv-splash-topright {{ right:48px; text-align:right; }}
    .brv-splash-topleft .tick {{ width:26px; height:2px; background:{t.RUST}; margin-bottom:10px; }}
    .brv-splash-main {{ position:absolute; left:9%; top:50%; transform:translateY(-50%); max-width:560px; }}
    .brv-splash-title {{
        font-family:'Cormorant Garamond',serif; font-weight:700; font-size:76px; letter-spacing:4px;
        color:#FBF4E8; margin:22px 0 6px 0; line-height:1;
    }}
    .brv-splash-subtitle {{ font-size:14px; letter-spacing:3px; color:#D9CCAE; font-weight:600; line-height:1.7; }}
    .brv-splash-divider {{ width:64px; height:2px; background:{t.RUST}; margin:22px 0; }}
    .brv-splash-tagline {{ font-size:14.5px; letter-spacing:2.5px; color:#F1E8D8; font-weight:600; line-height:1.7; margin-bottom:30px; }}
    .brv-splash-progress {{ display:flex; align-items:center; gap:14px; max-width:420px; }}
    .brv-splash-progress .track {{ flex:1; height:7px; border-radius:6px; background:rgba(255,255,255,0.14); overflow:hidden; }}
    .brv-splash-progress .fill {{ height:100%; border-radius:6px; background:linear-gradient(90deg,{t.RUST},{t.RUST_DARK}); transition:width 0.15s ease; }}
    .brv-splash-progress .pct {{ font-size:14px; font-weight:700; color:#F1E8D8; width:42px; }}
    .brv-splash-loading {{ font-size:12.5px; color:#B9AC91; margin-top:10px; letter-spacing:0.3px; }}
    .brv-splash-features {{ display:flex; gap:34px; margin-top:44px; }}
    .brv-splash-features .feat {{ display:flex; flex-direction:column; align-items:center; gap:9px; color:#D9CCAE; }}
    .brv-splash-features .feat span {{ font-size:10.5px; letter-spacing:1.6px; font-weight:700; color:#C9BC9F; }}
    .brv-splash-footer-l, .brv-splash-footer-r {{
        position:absolute; bottom:30px; font-size:11px; letter-spacing:1.5px; color:#A79A80; font-weight:600;
    }}
    .brv-splash-footer-l {{ left:48px; }}
    .brv-splash-footer-r {{ right:48px; }}

    /* Segmented range control (styled radio) */
    div[role="radiogroup"] {{ gap: 6px; }}
    div[role="radiogroup"] label[data-testid="stRadioOption"] {{
        background: var(--cream); border:1px solid var(--border); border-radius:8px !important;
        padding: 4px 14px !important; cursor:pointer;
    }}
    div[role="radiogroup"] label[data-testid="stRadioOption"] p {{
        color: var(--muted) !important; font-size:12.5px !important; font-weight:600 !important; margin:0 !important;
    }}
    div[role="radiogroup"] label[data-testid="stRadioOption"][data-selected="true"] {{
        background: var(--ink) !important; border-color: var(--ink) !important;
    }}
    div[role="radiogroup"] label[data-testid="stRadioOption"][data-selected="true"] p {{
        color: #FDFBF7 !important;
    }}
    div[role="radiogroup"] label[data-testid="stRadioOption"] > div > div > div:first-child {{
        display: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)