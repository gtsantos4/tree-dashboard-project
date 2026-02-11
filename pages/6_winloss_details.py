"""WinLoss Details — estimated vs actual hours with Win/Loss classification."""
import streamlit as st
import pandas as pd

from data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from data.transforms import (
    build_so_line_items, build_inv_amts,
    build_scheduling_goals, get_years, get_operations,
)
from components.filters import (
    apply_year, apply_months, apply_operation,
    operation_filter, month_filter,
)
from components.styled_table import winloss_table, show_reference_table
from components.lineage_inspector import inspectable_winloss, inspectable_metric
from config import MONTH_ORDER

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)
sheets = load_crew_stat_lists()
sched_goals = build_scheduling_goals(sheets)
years = get_years(inv)
operations = get_operations(so)

# ── Filters ──────────────────────────────────────────────────────────
st.markdown("#### WinLoss Details")

fc1, fc2, fc3 = st.columns(3)
with fc1:
    sel_year = st.selectbox("Year", years, key="wld_yr")
with fc2:
    sel_op = operation_filter(operations, key="wld_op")
with fc3:
    sel_months = month_filter(key="wld_mo")

# Apply
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_operation(df, sel_op)

# ── KPI ──────────────────────────────────────────────────────────────
c_kpi, _ = st.columns([1, 5])
with c_kpi:
    inspectable_metric("Count", len(df), "Win/Loss Count", source_df=df, filters={"Year": sel_year, "Operation": sel_op, "Months": sel_months}, key="wld_count_kpi")

# ── Scheduling Goals Tables ──────────────────────────────────────────
st.markdown("---")
g1, g2 = st.columns(2)

with g1:
    st.markdown("**Estimated Hours Goals**")
    if not sched_goals.empty:
        est = sched_goals[sched_goals["Type"] == "Scheduling"].copy()
        if sel_op and sel_op != "All":
            est = est[est["Operation"] == sel_op]
        display_cols = ["Operation", "Day", "Week", "Month", "Year"]
        existing = [c for c in display_cols if c in est.columns]
        st.dataframe(est[existing], use_container_width=True, hide_index=True)

with g2:
    st.markdown("**Actual Hours Goals**")
    if not sched_goals.empty:
        act = sched_goals[sched_goals["Type"] == "Actual"].copy()
        if sel_op and sel_op != "All":
            act = act[act["Operation"] == sel_op]
        display_cols = ["Operation", "Day", "Week", "Month", "Year"]
        existing = [c for c in display_cols if c in act.columns]
        st.dataframe(act[existing], use_container_width=True, hide_index=True)

# ── Win / Loss Detail Table ──────────────────────────────────────────
st.markdown("---")
st.markdown("**Win / Loss for Period**")

if not df.empty:
    display_cols = [
        "Visit Ref #", "Operation", "WinLossText", "Crew Leader",
        "InvoiceDate", "Client", "HoursEst", "TimeByInv", "HrsRatio",
        "Sales Reps",
    ]
    existing = [c for c in display_cols if c in df.columns]
    tbl = df[existing].copy()
    tbl.rename(columns={"WinLossText": "WinLoss", "TimeByInv": "HrsActual"}, inplace=True)
    if "InvoiceDate" in tbl.columns:
        tbl["InvoiceDate"] = tbl["InvoiceDate"].dt.strftime("%m/%d/%Y").fillna("")
    for nc in ["HoursEst", "HrsActual", "HrsRatio"]:
        if nc in tbl.columns:
            tbl[nc] = tbl[nc].round(2)

    inspectable_winloss(df, tbl, source_so=so, source_time=time_raw, wl_col="WinLoss", key="wld_tbl", height=500)

    # Totals
    totals = df.agg({"HoursEst": "sum", "TimeByInv": "sum"}).to_dict()
    st.markdown(
        f"**Totals — Est: {totals['HoursEst']:,.2f}  |  "
        f"Actual: {totals['TimeByInv']:,.2f}**"
    )
else:
    st.info("No invoiced visits for the selected filters.")

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` (aggregated to visit level, joined with Time.csv)")
    st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`")
    st.markdown(f"**Scheduling goals source:** CrewStatLists.xlsx → EstHrsGoals sheet")

    st.markdown("---")
    st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows")
    st.dataframe(df, use_container_width=True, height=300)
