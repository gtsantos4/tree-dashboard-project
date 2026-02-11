"""
Tree Care Operations Dashboard — Streamlit multi-page app.

Mirrors the PowerBI "Stats" report built on SingleOps data.
"""
import streamlit as st
from config import PAGE_TITLE, PAGE_ICON

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar nav styling */
    [data-testid="stSidebar"] {background-color: #f8f9fa;}
    [data-testid="stSidebar"] h1 {font-size: 18px; color: #003366;}
    /* Compact metrics */
    [data-testid="stMetric"] {padding: 8px 0;}
    /* Table header color */
    .stDataFrame th {background-color: #4472C4 !important; color: white !important;}
    /* Tighten bottom padding but leave room for the top nav bar */
    .block-container {padding-top: 3.5rem; padding-bottom: 1rem;}
    /* Button row styling for year/op filters */
    .stButton > button[kind="primary"] {
        background-color: #003366; color: white; border: none;
    }
    .stButton > button[kind="secondary"] {
        background-color: #e0e0e0; color: #333; border: none;
    }
</style>
""", unsafe_allow_html=True)

# ── Navigation ───────────────────────────────────────────────────────
pages = {
    "Crew Leader Stats": "pages/1_crew_leader_stats.py",
    "White Board":       "pages/2_white_board.py",
    "Stats Detail":      "pages/3_stats_detail.py",
    "Damage":            "pages/4_damage.py",
    "TimeDetail":        "pages/5_time_detail.py",
    "WinLoss Details":   "pages/6_winloss_details.py",
    "WinLoss Summary":   "pages/7_winloss_summary.py",
    "Est v Actual Dash": "pages/8_est_v_actual.py",
    "Notes":             "pages/9_notes.py",
    "Owner":             "pages/10_owner.py",
}

pg = st.navigation([st.Page(path, title=title) for title, path in pages.items()])
pg.run()
