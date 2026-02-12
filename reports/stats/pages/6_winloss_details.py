"""WinLoss Details — detailed table with inspectable rows, totals bar, and scheduling goals."""
import streamlit as st
import pandas as pd
import numpy as np

from reports.stats.data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from reports.stats.data.transforms import (
    build_so_line_items, build_inv_amts,
    build_scheduling_goals, get_years, get_operations,
)
from components.filters import (
    apply_year, apply_months, apply_operation,
    operation_filter, month_filter,
)
from components.kpi_cards import kpi_row
from components.styled_table import page_header, filter_container, card_container, totals_bar
from components.lineage_inspector import inspectable_winloss
from config import WIN_COLOR, LOSS_COLOR, DEV_MODE

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)
sheets = load_crew_stat_lists()
sched_goals = build_scheduling_goals(sheets)
years = get_years(inv)
operations = get_operations(so)

# ── Page Title ───────────────────────────────────────────────────────
page_header("Win/Loss Details", "Job-level Win/Loss with hours comparison")

# ── Filters (3 columns) ──────────────────────────────────────────────
with filter_container():
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_year = st.selectbox("Year", years, key="wld_yr")
    with fc2:
        sel_op = operation_filter(operations, key="wld_op")
    with fc3:
        sel_months = month_filter(key="wld_mo")

# Apply filters
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_operation(df, sel_op)

# ── KPI Row (4 cards) ────────────────────────────────────────────────
# Calculate metrics
total_jobs = len(df)
win_count = len(df[df["WinLossText"] == "Win"]) if not df.empty else 0
loss_count = len(df[df["WinLossText"] == "Loss"]) if not df.empty else 0
win_pct = (win_count / total_jobs * 100) if total_jobs > 0 else 0
avg_hrs_ratio = df["HrsRatio"].mean() if not df.empty and "HrsRatio" in df.columns else 0
total_revenue = df["InvTotal"].sum() if not df.empty and "InvTotal" in df.columns else 0

# Format revenue as "482K" style
if total_revenue >= 1_000_000:
    rev_str = f"{total_revenue / 1_000_000:.1f}M"
elif total_revenue >= 1_000:
    rev_str = f"{total_revenue / 1_000:.0f}K"
else:
    rev_str = f"{total_revenue:.0f}"

# KPI items
kpi_items = [
    {
        "label": "Total Jobs",
        "value": total_jobs,
    },
    {
        "label": "Win Rate",
        "value": f"{win_pct:.0f}%",
        "accent": "win",
        "delta": f"{win_count} Wins",
    },
    {
        "label": "Avg Hours Ratio",
        "value": round(avg_hrs_ratio, 2),
    },
    {
        "label": "Total Revenue",
        "prefix": "$",
        "value": rev_str,
    },
]

kpi_row(kpi_items, cols=4)

# ── Win / Loss Detail Table ──────────────────────────────────────────
with card_container("Win / Loss for Period"):
    if not df.empty:
        display_cols = [
            "Visit Ref #", "WinLossText", "Operation", "Crew Leader",
            "InvoiceDate", "Client", "HoursEst", "TimeByInv", "HrsRatio",
            "Sales Reps",
        ]
        existing = [c for c in display_cols if c in df.columns]
        tbl = df[existing].copy()
        tbl.rename(columns={"WinLossText": "WinLoss", "TimeByInv": "HrsActual"}, inplace=True)

        # Format date column
        if "InvoiceDate" in tbl.columns:
            tbl["InvoiceDate"] = tbl["InvoiceDate"].dt.strftime("%m/%d/%Y").fillna("")

        # Round numeric columns
        for nc in ["HoursEst", "HrsActual", "HrsRatio"]:
            if nc in tbl.columns:
                tbl[nc] = tbl[nc].round(2)

        inspectable_winloss(
            df, tbl,
            source_so=so, source_time=time_raw,
            wl_col="WinLoss", ref_col="Visit Ref #",
            key="wld_tbl", height=500
        )

        # Totals bar
        est_total = df["HoursEst"].sum() if "HoursEst" in df.columns else 0
        actual_total = df["TimeByInv"].sum() if "TimeByInv" in df.columns else 0
        totals_bar([
            {"label": "Est Hours", "value": f"{est_total:,.0f}"},
            {"label": "Actual Hours", "value": f"{actual_total:,.0f}"},
            {"label": "Wins", "value": str(win_count), "color": WIN_COLOR},
            {"label": "Losses", "value": str(loss_count), "color": LOSS_COLOR},
        ])
    else:
        st.info("No invoiced visits for the selected filters.")

# ── Scheduling Goals Reference (in expander) ────────────────────────
with st.expander("📋 Scheduling Goals Reference"):
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("**Estimated Hours Goals**")
        if not sched_goals.empty:
            est = sched_goals[sched_goals["Type"] == "Scheduling"].copy()
            if sel_op and sel_op != "All":
                est = est[est["Operation"] == sel_op]
            display_cols = ["Operation", "Day", "Week", "Month", "Year"]
            existing = [c for c in display_cols if c in est.columns]
            if existing:
                st.dataframe(est[existing], use_container_width=True, hide_index=True)

    with g2:
        st.markdown("**Actual Hours Goals**")
        if not sched_goals.empty:
            act = sched_goals[sched_goals["Type"] == "Actual"].copy()
            if sel_op and sel_op != "All":
                act = act[act["Operation"] == sel_op]
            display_cols = ["Operation", "Day", "Week", "Month", "Year"]
            existing = [c for c in display_cols if c in act.columns]
            if existing:
                st.dataframe(act[existing], use_container_width=True, hide_index=True)

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` (aggregated to visit level, joined with Time.csv)")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`")
        st.markdown(f"**Scheduling goals source:** CrewStatLists.xlsx → EstHrsGoals sheet")

        st.markdown("---")
        st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows")
        st.dataframe(df, use_container_width=True, height=300)
