"""CrewLeaderStats — crew performance scorecard with wireframe redesign."""
import streamlit as st
import pandas as pd

from reports.stats.data.loader import load_all_line_items, load_crew_stat_lists
from reports.stats.data.transforms import (
    build_so_line_items, build_stats,
    build_qc_scale, get_crew_leaders, get_years,
)
from components.filters import (
    crew_leader_filter, month_filter,
    apply_year, apply_months, apply_crew_leader,
)
from components.kpi_cards import (
    metric_card_v2, kpi_row, star_rating, box_rating, progress_bar,
)
from components.styled_table import (
    page_header, filter_container, card_container, totals_bar
)
from components.lineage_inspector import inspectable_dataframe
from config import DEV_MODE

# ── Load & transform ────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
sheets = load_crew_stat_lists()
qc_scale = build_qc_scale(sheets)
stats = build_stats(so, qc_scale)

years = get_years(so)
leaders = get_crew_leaders(stats)

# ── Page Header ──────────────────────────────────────────────────────
page_header("Crew Leader Stats", "Performance overview by crew leader")

# ── Filters ──────────────────────────────────────────────────────────
with filter_container():
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_leader = crew_leader_filter(leaders, key="cls_cl")
    with fc2:
        sel_year = st.selectbox("Year", years, key="cls_yr")
    with fc3:
        sel_months = month_filter(key="cls_mo")

# Apply filters to stats
fstats = stats.copy()
fstats = apply_year(fstats, sel_year)
fstats = apply_months(fstats, sel_months)
fstats = apply_crew_leader(fstats, sel_leader)

# ── Calculate KPI metrics ─────────────────────────────────────────────
compliments = fstats[fstats["Item Name"] == "Compliment"]
callbacks = fstats[fstats["Item Name"] == "Call Back"]
qc_items = fstats[fstats["Item Name"] == "Quality Control"]

comp_count = int(compliments["Qty"].sum())
cb_count = int(callbacks["Qty"].sum())
grade_count = len(qc_items)
avg_pct = qc_items["Percent"].mean() * 100 if not qc_items.empty and qc_items["Percent"].notna().any() else 0

# ── KPI Row (4 cards) ─────────────────────────────────────────────────
kpi_items = [
    {
        "label": "Compliments",
        "value": comp_count,
        "icon": "⭐",
        "extra_html": star_rating(min(comp_count // 10, 10)),
    },
    {
        "label": "Call Backs",
        "value": cb_count,
        "icon": "📞",
        "accent": "loss",
        "extra_html": box_rating(cb_count),
    },
    {
        "label": "Avg QC Grade",
        "value": f"{avg_pct:.0f}%",
        "icon": "📊",
        "accent": "win",
        "extra_html": progress_bar(avg_pct, 100),
    },
    {
        "label": "# of Grades",
        "value": grade_count,
        "icon": "📝",
    },
]

kpi_row(kpi_items, cols=4)

# ── Compliments / Call Backs — full-width tabbed card ─────────────────
st.markdown("")  # Spacing
with card_container("Compliments / Call Backs"):
    tab_comp, tab_cb = st.tabs(["Compliments", "Call Backs"])

    with tab_comp:
        if not compliments.empty:
            display = compliments[["Approved Date", "Visit Ref #", "Line_Item_Description"]].copy()
            display.columns = ["Approved Date", "Visit Ref #", "Description"]
            display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")
            inspectable_dataframe(
                compliments, display,
                source_so=so, key="cls_comp_tbl", height=350
            )
        else:
            st.info("No compliments in selected period.")

    with tab_cb:
        if not callbacks.empty:
            display = callbacks[["Approved Date", "Visit Ref #", "Line_Item_Description"]].copy()
            display.columns = ["Approved Date", "Visit Ref #", "Description"]
            display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")
            inspectable_dataframe(
                callbacks, display,
                source_so=so, key="cls_cb_tbl", height=350
            )
        else:
            st.info("No call backs in selected period.")

totals_bar([
    {"label": "Compliments", "value": str(comp_count)},
    {"label": "Call Backs", "value": str(cb_count)},
])

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_stats()` (filtered to Compliment / Call Back / Quality Control)")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Months=`{sel_months or 'All'}`, Crew Leader=`{sel_leader}`")

        st.markdown("---")
        st.markdown(f"**Stats table** (filtered) — {len(fstats):,} rows")
        st.dataframe(fstats, use_container_width=True, height=250)

        st.markdown(f"**QC Scale** (from CrewStatLists.xlsx → QC sheet)")
        st.dataframe(qc_scale, use_container_width=True)
