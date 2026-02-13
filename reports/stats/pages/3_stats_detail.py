"""Stats Detail — drill-through detail table for CrewLeaderStats."""
import streamlit as st

from reports.stats.data.loader import load_all_line_items, load_crew_stat_lists
from reports.stats.data.transforms import (
    build_so_line_items, build_stats, build_qc_scale,
    get_crew_leaders, get_years,
)
from components.filters import (
    apply_year, apply_months, apply_crew_leader,
    crew_leader_filter, month_filter,
)
from components.kpi_cards import metric_card_v2, kpi_row
from components.styled_table import page_header, filter_container, card_container, totals_bar
from components.lineage_inspector import inspectable_dataframe
from config import STAT_ITEMS, DEV_MODE

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
sheets = load_crew_stat_lists()
qc_scale = build_qc_scale(sheets)
stats = build_stats(so, qc_scale)
years = get_years(so)
leaders = get_crew_leaders(stats)

# ── Page Header ──────────────────────────────────────────────────────
page_header("Stats Detail", "All stat line items with full detail")

# ── Filters ──────────────────────────────────────────────────────────
with filter_container():
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        sel_year = st.selectbox("Year", years, key="sd_yr")
    with fc2:
        sel_leader = crew_leader_filter(leaders, key="sd_cl")
    with fc3:
        sel_months = month_filter(key="sd_mo")
    with fc4:
        sel_item = st.selectbox("Item Type", ["All"] + STAT_ITEMS, key="sd_item")

# Apply
df = stats.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_crew_leader(df, sel_leader)
if sel_item and sel_item != "All":
    df = df[df["Item Name"] == sel_item]

# ── KPI Row ──────────────────────────────────────────────────────────
qc_count = len(df[df["Item Name"] == "Quality Control"])
compliments_count = int(df[df["Item Name"] == "Compliment"]["Qty"].sum())
callbacks_count = int(df[df["Item Name"] == "Call Back"]["Qty"].sum())
feedback_count = int(df[df["Item Name"] == "Crew Feedback"]["Qty"].sum())

kpi_items = [
    {"label": "Quality Control", "value": qc_count, "icon": "📋"},
    {"label": "Compliments", "value": compliments_count, "icon": "⭐"},
    {"label": "Call Backs", "value": callbacks_count, "icon": "📞"},
    {"label": "Crew Feedback", "value": feedback_count, "icon": "💬"},
]
kpi_row(kpi_items, cols=4)

st.markdown("")  # spacing

# ── Table in Card ────────────────────────────────────────────────────
with card_container("All Stats Line Items"):
    display_cols = [
        "Approved Date", "Visit Ref #", "Job Ref #", "Client",
        "Crew Leader", "Item Name", "Line_Item_Description",
    ]
    existing = [c for c in display_cols if c in df.columns]
    display = df[existing].copy()
    if "Approved Date" in display.columns:
        display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")

    inspectable_dataframe(
        df, display, source_so=so, key="sd_tbl", height=500,
        fit_to_content_columns=["Approved Date", "Visit Ref #", "Job Ref #", "Client", "Crew Leader", "Item Name"],
    )

# Totals bar
totals_items = [
    {"label": "Total Items", "value": str(len(display))},
    {"label": "QC", "value": str(qc_count)},
    {"label": "Compliments", "value": str(compliments_count)},
    {"label": "Call Backs", "value": str(callbacks_count)},
    {"label": "Feedback", "value": str(feedback_count)},
]
totals_bar(totals_items)

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_stats()` (filtered to Quality Control / Compliment / Call Back / Crew Feedback)")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Months=`{sel_months or 'All'}`, Crew Leader=`{sel_leader}`, Item=`{sel_item}`")

        st.markdown("---")
        st.markdown(f"**Full stats table before display formatting** — {len(df):,} rows, {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=300)
