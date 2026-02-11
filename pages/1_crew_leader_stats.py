"""CrewLeaderStats — crew performance scorecard."""
import streamlit as st
import pandas as pd

from data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from data.transforms import (
    build_so_line_items, build_stats, build_inv_amts,
    build_qc_scale, get_crew_leaders, get_operations, get_years,
    get_sales_reps,
)
from components.filters import (
    crew_leader_filter, operation_filter, month_filter,
    apply_year, apply_months, apply_operation, apply_crew_leader,
    apply_sales_rep,
)
from components.kpi_cards import (
    metric_card, star_rating, box_rating, gauge_chart, winloss_donut,
)
from components.lineage_inspector import inspectable_dataframe, inspectable_metric, inspectable_chart

# ── Load & transform ────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
sheets = load_crew_stat_lists()
qc_scale = build_qc_scale(sheets)
stats = build_stats(so, qc_scale)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)

years = get_years(so)
operations = get_operations(so)
leaders = get_crew_leaders(stats)
reps = get_sales_reps(so)

# ── Filters ──────────────────────────────────────────────────────────
st.markdown("#### Crew Leader Stats")
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    sel_leader = crew_leader_filter(leaders, key="cls_cl")
with fc2:
    sel_op = operation_filter(operations, key="cls_op")
with fc3:
    sel_year = st.selectbox("Year", years, key="cls_yr")
with fc4:
    sel_months = month_filter(key="cls_mo")

# Apply filters to stats
fstats = stats.copy()
fstats = apply_year(fstats, sel_year)
fstats = apply_months(fstats, sel_months)
fstats = apply_crew_leader(fstats, sel_leader)

# Apply filters to inv_amts (for WinLoss donut)
finv = inv.copy()
finv = apply_year(finv, sel_year)
finv = apply_months(finv, sel_months)
finv = apply_operation(finv, sel_op)
finv = apply_crew_leader(finv, sel_leader)

# ── KPIs Row ─────────────────────────────────────────────────────────
compliments = fstats[fstats["Item Name"] == "Compliment"]
callbacks = fstats[fstats["Item Name"] == "Call Back"]
qc_items = fstats[fstats["Item Name"] == "Quality Control"]

comp_count = int(compliments["Qty"].sum())
cb_count = int(callbacks["Qty"].sum())
grade_count = len(qc_items)
avg_pct = qc_items["Percent"].mean() * 100 if not qc_items.empty and qc_items["Percent"].notna().any() else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    inspectable_metric("Compliments", comp_count, "Compliments", source_df=compliments, filters={"Year": sel_year, "Months": sel_months, "Crew Leader": sel_leader}, key="cls_comp_kpi")
    st.markdown(star_rating(min(comp_count // 10, 10)), unsafe_allow_html=True)
with k2:
    inspectable_metric("Call Backs", cb_count, "Call Backs", source_df=callbacks, filters={"Year": sel_year, "Months": sel_months, "Crew Leader": sel_leader}, key="cls_cb_kpi")
    st.markdown(box_rating(cb_count), unsafe_allow_html=True)
with k3:
    inspectable_chart(gauge_chart(avg_pct, "Average of Percent"), "Average of Percent (Gauge)", source_df=qc_items, filters={"Year": sel_year, "Months": sel_months, "Crew Leader": sel_leader}, key="cls_gauge")
with k4:
    inspectable_metric("# Grades", grade_count, "# Grades", source_df=qc_items, filters={"Year": sel_year, "Months": sel_months, "Crew Leader": sel_leader}, key="cls_gr_kpi")
    # Sales reps indicator
    rep_list = fstats["Sales Reps"].dropna().unique()
    rep_list = [r for r in rep_list if r]
    if rep_list:
        st.caption("**Sales Reps:** " + ", ".join(rep_list[:5]))

# ── Detail tables + donut ────────────────────────────────────────────
t1, t2, t3 = st.columns([2, 2, 3])

with t1:
    st.markdown("**Compliments**")
    if not compliments.empty:
        display = compliments[["Approved Date", "Visit Ref #", "Qty", "Line_Item_Description"]].copy()
        display["Qty"] = display["Qty"].astype(int)
        display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")
        inspectable_dataframe(compliments, display, source_so=so, key="cls_comp_tbl", height=300)
        st.markdown(f"**Total: {comp_count}**")
    else:
        st.info("No compliments in selected period.")

with t2:
    st.markdown("**Call Backs**")
    if not callbacks.empty:
        display = callbacks[["Approved Date", "Visit Ref #", "Qty", "Line_Item_Description"]].copy()
        display["Qty"] = display["Qty"].astype(int)
        display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")
        inspectable_dataframe(callbacks, display, source_so=so, key="cls_cb_tbl", height=300)
        st.markdown(f"**Total: {cb_count}**")
    else:
        st.info("No call backs in selected period.")

with t3:
    win_count = len(finv[finv["WinLossText"] == "Win"])
    loss_count = len(finv[finv["WinLossText"] == "Loss"])
    inspectable_chart(winloss_donut(win_count, loss_count), "Win/Loss Donut", source_df=finv, filters={"Year": sel_year, "Months": sel_months, "Operation": sel_op, "Crew Leader": sel_leader}, key="cls_donut")

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_stats()` (filtered to Compliment / Call Back / Quality Control / Crew Feedback)")
    st.markdown(f"**Active filters:** Year=`{sel_year}`, Months=`{sel_months or 'All'}`, Crew Leader=`{sel_leader}`, Operation=`{sel_op}`")

    st.markdown("---")
    st.markdown(f"**Stats table** (filtered) — {len(fstats):,} rows")
    st.dataframe(fstats, use_container_width=True, height=250)

    st.markdown(f"**InvAmts table** (filtered, for Win/Loss donut) — {len(finv):,} rows")
    st.dataframe(finv, use_container_width=True, height=250)

    st.markdown(f"**QC Scale** (from CrewStatLists.xlsx → QC sheet)")
    st.dataframe(qc_scale, use_container_width=True)
