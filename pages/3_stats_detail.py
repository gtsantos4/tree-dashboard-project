"""Stats Detail — drill-through detail table for CrewLeaderStats."""
import streamlit as st

from data.loader import load_all_line_items, load_crew_stat_lists
from data.transforms import (
    build_so_line_items, build_stats, build_qc_scale,
    get_crew_leaders, get_years,
)
from components.filters import (
    apply_year, apply_months, apply_crew_leader,
    crew_leader_filter, month_filter,
)
from components.lineage_inspector import inspectable_dataframe
from config import STAT_ITEMS

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
sheets = load_crew_stat_lists()
qc_scale = build_qc_scale(sheets)
stats = build_stats(so, qc_scale)
years = get_years(so)
leaders = get_crew_leaders(stats)

# ── Filters ──────────────────────────────────────────────────────────
st.markdown("#### Stats Detail")

fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    sel_year = st.selectbox("Year", years, key="sd_yr")
with fc2:
    sel_leader = crew_leader_filter(leaders, key="sd_cl")
with fc3:
    sel_months = month_filter(key="sd_mo")
with fc4:
    sel_item = st.selectbox("Item Name", ["All"] + STAT_ITEMS, key="sd_item")

# Apply
df = stats.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_crew_leader(df, sel_leader)
if sel_item and sel_item != "All":
    df = df[df["Item Name"] == sel_item]

# ── Table ────────────────────────────────────────────────────────────
display_cols = [
    "Visit Ref #", "Job Ref #", "Approved Date", "Client",
    "Crew Leader", "Item Name", "Qty", "Line_Item_Description",
]
existing = [c for c in display_cols if c in df.columns]
display = df[existing].copy()
display["Qty"] = display["Qty"].astype(int)
if "Approved Date" in display.columns:
    display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")

st.markdown(f"**Total: {len(display):,}**")
inspectable_dataframe(df, display, source_so=so, key="sd_tbl", height=600)

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_stats()` (filtered to Quality Control / Compliment / Call Back / Crew Feedback)")
    st.markdown(f"**Active filters:** Year=`{sel_year}`, Months=`{sel_months or 'All'}`, Crew Leader=`{sel_leader}`, Item=`{sel_item}`")

    st.markdown("---")
    st.markdown(f"**Full stats table before display formatting** — {len(df):,} rows, {len(df.columns)} columns")
    st.dataframe(df, use_container_width=True, height=300)
