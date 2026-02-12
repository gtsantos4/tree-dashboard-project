"""
Van Yahres Tree Company — Operations Dashboard.

Streamlit multi-page app with report-grouped navigation.
Responsive design for desktop, tablet, and mobile.
"""
import html as _html

import streamlit as st
import config
from config import PAGE_TITLE, PAGE_ICON, VY_RED, SIDEBAR_DARK, BG_PAGE, BORDER_COLOR

# ── JavaScript: white backgrounds for bordered containers ─────────
# Runs in a same-origin srcdoc iframe, finds bordered containers by
# computed style, and sets background:#fff.  setInterval catches
# elements added after navigation / re-render.
_CARD_BG_JS = (
    "(function(){"
    "if(parent._vyCSS)return;"
    "parent._vyCSS=true;"
    "var S=new WeakSet();"
    "function run(){"
    "try{"
    "var bc=parent.document.querySelector('.block-container');"
    "if(!bc)return;"
    "var divs=bc.getElementsByTagName('div');"
    "for(var i=0;i<divs.length;i++){"
    "var el=divs[i];"
    "if(S.has(el))continue;"
    "S.add(el);"
    "if(el.offsetWidth<200)continue;"
    "var cs=parent.getComputedStyle(el);"
    "if(cs.borderStyle==='solid'"
    "&&parseFloat(cs.borderTopWidth)>=1"
    "&&parseFloat(cs.borderRadius)>=4"
    "&&parseFloat(cs.paddingTop)>=10){"
    "el.style.setProperty('background-color','#ffffff','important');"
    "el.style.setProperty('border-radius','12px','important');"
    "el.style.setProperty('overflow','hidden','important');"
    "}}"
    "}catch(e){}}"
    "parent.setInterval(run,500);"
    "setTimeout(run,50);"
    "})();"
)
_SRCDOC = _html.escape("<script>" + _CARD_BG_JS + "</script>", quote=True)
_CARD_STYLER_IFRAME = (
    f'<iframe srcdoc="{_SRCDOC}" '
    f'style="display:none;width:0;height:0;border:none;position:absolute;"></iframe>'
)

# ── Dev mode URL escape hatch (?dev=1) ───────────────────────────
if st.query_params.get("dev") == "1":
    config.DEV_MODE = True

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS — Van Yahres Design System + Responsive ───────────
st.markdown(f"""
<style>
    /* ── Inter font ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ── Dark sidebar ───────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR_DARK};
    }}
    [data-testid="stSidebar"] * {{
        color: rgba(255,255,255,0.85) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {{
        font-size: 13px;
        padding: 6px 12px;
        border-radius: 8px;
        margin: 2px 8px;
        opacity: 0.7;
        transition: all 0.15s ease;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {{
        opacity: 1;
        background: rgba(255,255,255,0.08);
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {{
        opacity: 1;
        background: {VY_RED} !important;
        color: white !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] * {{
        color: white !important;
    }}
    /* Put logo above nav: reverse flex order (Streamlit renders nav first) */
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
        display: flex !important;
        flex-direction: column-reverse !important;
        gap: 0 !important;
        align-items: stretch !important;
        justify-content: flex-end !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] > * {{
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSidebarNav"],
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] > *:has([data-testid="stSidebarNavLink"]) {{
        margin-top: -56px !important;
    }}
    .vy-sidebar-brand {{
        margin-bottom: 0 !important;
    }}

    /* Section headers in sidebar */
    [data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{
        color: rgba(255,255,255,0.4) !important;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 16px 20px 4px;
        font-weight: 600;
    }}
    /* Scrollbar styling for dark sidebar */
    [data-testid="stSidebar"]::-webkit-scrollbar {{
        width: 4px;
    }}
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb {{
        background: rgba(255,255,255,0.2);
        border-radius: 4px;
    }}

    /* ── Page background (grey — only bordered cards get white) ─ */
    .stApp,
    .block-container {{
        background-color: {BG_PAGE} !important;
    }}

    /* ── White bg for HTML-rendered cards (KPI, crew grid, expanders) ─ */
    /* Bordered st.container() cards are styled via JS — see _CARD_BG_JS */
    .vy-kpi-card,
    .vy-crew-grid > div,
    [data-testid="stExpander"] {{
        background-color: #fff !important;
    }}

    /* ── Overflow protection — nothing should spill out of cards ──── */
    .vy-kpi-card,
    .vy-kpi-extra {{
        overflow: hidden !important;
        max-width: 100% !important;
    }}
    .vy-kpi-extra > * {{
        max-width: 100% !important;
    }}
    /* Bordered containers (JS-applied white bg) — clip children */
    [data-testid="stVerticalBlock"] {{
        max-width: 100% !important;
    }}
    /* Plotly and dataframe inside cards — respect container width */
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"] {{
        max-width: 100% !important;
        overflow: hidden !important;
    }}
    /* Totals bar — never wider than parent */
    .vy-totals-bar {{
        max-width: 100% !important;
        box-sizing: border-box !important;
    }}

    /* ── Content area spacing ───────────────────────────────── */
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }}

    /* ── Table headers — VY Red ─────────────────────────────── */
    .stDataFrame th {{
        background-color: {VY_RED} !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }}
    /* Horizontal scroll for tables on small screens */
    .stDataFrame {{
        overflow-x: auto;
    }}

    /* ── Compact metrics ────────────────────────────────────── */
    [data-testid="stMetric"] {{
        padding: 8px 0;
    }}

    /* ── Primary buttons — VY Red ───────────────────────────── */
    .stButton > button[kind="primary"] {{
        background-color: {VY_RED};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #7A1C2A;
        color: white;
    }}
    .stButton > button[kind="secondary"] {{
        background-color: white;
        color: #333;
        border: 1px solid {BORDER_COLOR};
        border-radius: 8px;
    }}

    /* ── Selectbox / input styling ──────────────────────────── */
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label {{
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        color: #6B7280;
    }}

    /* ── Expander styling ───────────────────────────────────── */
    .streamlit-expanderHeader {{
        font-size: 14px;
        font-weight: 600;
    }}

    /* ── Popover styling for lineage ────────────────────────── */
    [data-testid="stPopover"] > button {{
        font-size: 12px;
        color: {VY_RED} !important;
        font-weight: 600;
    }}

    /* ── Move header/toolbar bar (with Deploy etc.) to bottom ─── */
    [data-testid="stHeader"] {{
        position: fixed !important;
        top: auto !important;
        bottom: 0 !important;
    }}

    /* ═══════════════════════════════════════════════════════════
       RESPONSIVE — Tablet (≤ 1024px)
       ═══════════════════════════════════════════════════════════ */
    @media (max-width: 1024px) {{
        .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100% !important;
        }}

        /* Page header — slightly smaller */
        .vy-page-title {{
            font-size: 20px !important;
        }}

        /* KPI cards — smaller text */
        .vy-kpi-card .vy-kpi-value {{
            font-size: 22px !important;
        }}

        /* Plotly charts — cap height */
        [data-testid="stPlotlyChart"] {{
            max-height: 350px !important;
            overflow: hidden;
        }}
    }}

    /* ═══════════════════════════════════════════════════════════
       RESPONSIVE — Mobile (≤ 768px)
       ═══════════════════════════════════════════════════════════ */
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 0.5rem;
            max-width: 100% !important;
        }}

        /* Page header — compact */
        .vy-page-header {{
            margin-bottom: 12px !important;
        }}
        .vy-page-title {{
            font-size: 18px !important;
        }}
        .vy-page-subtitle {{
            font-size: 11px !important;
        }}

        /* Force Streamlit columns to stack vertically */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            flex: 1 1 100% !important;
            min-width: 100% !important;
            width: 100% !important;
        }}

        /* Allow 2 KPI cards per row (half width each) */
        [data-testid="stHorizontalBlock"]:has(.vy-kpi-card) > [data-testid="stColumn"] {{
            flex: 1 1 48% !important;
            min-width: 48% !important;
            width: 48% !important;
        }}

        /* KPI cards — compact */
        .vy-kpi-card {{
            padding: 14px !important;
        }}
        .vy-kpi-card .vy-kpi-value {{
            font-size: 20px !important;
        }}
        .vy-kpi-card .vy-kpi-label {{
            font-size: 10px !important;
        }}
        .vy-kpi-card .vy-kpi-icon {{
            width: 28px !important;
            height: 28px !important;
            font-size: 13px !important;
        }}

        /* Totals bar — wrap items, smaller text */
        .vy-totals-bar {{
            flex-wrap: wrap !important;
            gap: 12px 24px !important;
            padding: 10px 14px !important;
            font-size: 12px !important;
        }}

        /* Crew mini-cards — single column */
        .vy-crew-grid {{
            grid-template-columns: 1fr !important;
        }}

        /* Filter labels — smaller */
        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label {{
            font-size: 10px !important;
        }}

        /* Tables — smaller text, horizontal scroll */
        .stDataFrame {{
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }}
        .stDataFrame td, .stDataFrame th {{
            font-size: 11px !important;
            padding: 6px 8px !important;
            white-space: nowrap;
        }}

        /* Plotly charts — reduce height */
        [data-testid="stPlotlyChart"] {{
            max-height: 280px !important;
            overflow: hidden;
        }}

        /* Expander headers — compact */
        .streamlit-expanderHeader {{
            font-size: 13px !important;
        }}
    }}

    /* ═══════════════════════════════════════════════════════════
       RESPONSIVE — Small mobile (≤ 480px)
       ═══════════════════════════════════════════════════════════ */
    @media (max-width: 480px) {{
        .block-container {{
            padding-left: 0.25rem;
            padding-right: 0.25rem;
        }}

        /* Page header — minimal */
        .vy-page-title {{
            font-size: 16px !important;
        }}
        .vy-page-subtitle {{
            font-size: 10px !important;
        }}

        /* KPI cards — full width, single column */
        [data-testid="stHorizontalBlock"]:has(.vy-kpi-card) > [data-testid="stColumn"] {{
            flex: 1 1 100% !important;
            min-width: 100% !important;
            width: 100% !important;
        }}
        .vy-kpi-card {{
            padding: 12px !important;
        }}
        .vy-kpi-card .vy-kpi-value {{
            font-size: 18px !important;
        }}
        .vy-kpi-card .vy-kpi-icon {{
            display: none !important;
        }}

        /* Totals bar — tighter */
        .vy-totals-bar {{
            gap: 8px 16px !important;
            padding: 8px 10px !important;
            font-size: 11px !important;
            border-radius: 0 0 8px 8px !important;
        }}

        /* Tables — even smaller */
        .stDataFrame td, .stDataFrame th {{
            font-size: 10px !important;
            padding: 4px 6px !important;
        }}

        /* Filter labels */
        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label {{
            font-size: 9px !important;
        }}
    }}
</style>
{_CARD_STYLER_IFRAME}
""", unsafe_allow_html=True)

# ── Sidebar: logo + company (must render before st.navigation) ────
st.sidebar.markdown("""
<div class="vy-sidebar-brand" style="padding: 20px 16px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 8px;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:36px;height:36px;background:#9B2335;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">🌳</div>
        <div>
            <div style="color:white !important; font-weight:700; font-size:15px; line-height:1.2;">Van Yahres</div>
            <div style="color:rgba(255,255,255,0.45) !important; font-size:11px; font-weight:400;">Tree Company</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation — grouped by report ───────────────────────────────
pg = st.navigation({
    "Stats": [
        st.Page("reports/stats/pages/1_crew_leader_stats.py", title="Crew Leader Stats", icon=":material/groups:"),
        st.Page("reports/stats/pages/2_white_board.py", title="White Board", icon=":material/dashboard:"),
        st.Page("reports/stats/pages/3_stats_detail.py", title="Stats Detail", icon=":material/analytics:"),
        st.Page("reports/stats/pages/4_damage.py", title="Damage", icon=":material/warning:"),
        st.Page("reports/stats/pages/5_time_detail.py", title="Time Detail", icon=":material/schedule:"),
        st.Page("reports/stats/pages/6_winloss_details.py", title="WinLoss Details", icon=":material/trending_up:"),
        st.Page("reports/stats/pages/7_winloss_summary.py", title="WinLoss Summary", icon=":material/bar_chart:"),
        st.Page("reports/stats/pages/8_est_v_actual.py", title="Est v Actual", icon=":material/compare_arrows:"),
        st.Page("reports/stats/pages/9_notes.py", title="Notes", icon=":material/notes:"),
        st.Page("reports/stats/pages/10_owner.py", title="Owner", icon=":material/person:"),
    ],
    # Future reports added here as new sections:
    # "Financial": [ st.Page("reports/financial/pages/..."), ... ],
})
pg.run()
