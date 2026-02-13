"""WinLoss Summary — monthly and yearly hours vs goals aggregation."""
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
from components.styled_table import (
    page_header, filter_container, card_container, totals_bar
)
from config import MONTH_FULL_ORDER, DEV_MODE

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
page_header("Win/Loss Summary", "Hours vs goals tracking with YTD progress")

# ── Filters (3 columns) ──────────────────────────────────────────────
with filter_container():
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_year = st.selectbox("Year", years, key="wls_yr")
    with fc2:
        sel_op = operation_filter(operations, key="wls_op")
    with fc3:
        sel_months = month_filter(key="wls_mo")

# Apply filters
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_operation(df, sel_op)

# Get monthly scheduling goal
monthly_goal = 0
if not sched_goals.empty:
    sched = sched_goals[sched_goals["Type"] == "Scheduling"]
    if sel_op and sel_op != "All":
        sched = sched[sched["Operation"] == sel_op]
        monthly_goal = sched["Month"].sum() if not sched.empty else 0
    else:
        all_row = sched[sched["Operation"] == "All"]
        if not all_row.empty:
            monthly_goal = all_row["Month"].values[0]
        else:
            monthly_goal = sched["Month"].sum()

# ── KPI Row (4 cards) ────────────────────────────────────────────────
total_jobs = len(df)
win_count = len(df[df["WinLossText"] == "Win"]) if not df.empty else 0
win_pct = (win_count / total_jobs * 100) if total_jobs > 0 else 0
ytd_hours = df["HoursEst"].sum() if not df.empty else 0

# Calculate % to Goal (for how many months we have data)
num_months = df["MonthNum"].nunique() if not df.empty and "MonthNum" in df.columns else 0
goal_total = monthly_goal * num_months if num_months > 0 else 0
pct_to_goal = (ytd_hours / goal_total * 100) if goal_total > 0 else 0
hrs_over_under = ytd_hours - goal_total

kpi_items = [
    {
        "label": "Total Jobs",
        "value": total_jobs,
        "icon": "📊",
    },
    {
        "label": "Win Rate",
        "value": f"{win_pct:.0f}%",
        "accent": "win",
        "icon": "🏆",
    },
    {
        "label": "YTD Hours",
        "value": f"{ytd_hours:,.0f}",
        "icon": "🕐",
    },
    {
        "label": "% to Goal",
        "value": f"{pct_to_goal:.0f}%",
        "accent": "win" if pct_to_goal >= 100 else None,
        "delta": f"{hrs_over_under:+,.0f} hrs",
        "icon": "🎯",
    },
]

kpi_row(kpi_items, cols=4)

st.markdown("")  # spacing

# ── Two Side-by-Side Tables ──────────────────────────────────────────
t1, t2 = st.columns(2)

with t1:
    if not df.empty and df["MonthNum"].notna().any():
        monthly = df.groupby("MonthNum").agg(
            Hours=("HoursEst", "sum"),
        ).reset_index()
        monthly["Month"] = monthly["MonthNum"].apply(
            lambda m: MONTH_FULL_ORDER[int(m) - 1] if 1 <= m <= 12 else ""
        )
        monthly["Goal"] = monthly_goal
        monthly["YTD_Hours"] = monthly["Hours"].cumsum()
        monthly["YTD_Goal"] = monthly["Goal"].cumsum()
        monthly["% to Goal"] = np.where(
            monthly["YTD_Goal"] > 0,
            (monthly["YTD_Hours"] / monthly["YTD_Goal"] * 100).round(0),
            0,
        )
        display = monthly[["Month", "Hours", "Goal", "YTD_Hours", "YTD_Goal", "% to Goal"]]

        with card_container("Monthly Hours vs Goal"):
            st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No data for selected filters.")

with t2:
    if not df.empty:
        # Yearly summary
        yearly = df.groupby("Year").agg(
            HoursEst=("HoursEst", "sum"),
            MonthCount=("MonthNum", "nunique"),
        ).reset_index()
        yearly["Hours/Mo"] = (yearly["HoursEst"] / yearly["MonthCount"]).round(0)
        yearly["Goal"] = monthly_goal
        yearly["Variance"] = yearly["Hours/Mo"] - yearly["Goal"]
        yearly["% of Goal"] = np.where(
            yearly["Goal"] > 0,
            (yearly["Hours/Mo"] / yearly["Goal"] * 100).round(0),
            0,
        )
        display = yearly[["Year", "Hours/Mo", "Goal", "Variance", "% of Goal"]]

        with card_container("Yearly Average"):
            st.dataframe(display, use_container_width=True, hide_index=True)

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` → Monthly/Yearly aggregation")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`")
        st.markdown(f"**Monthly scheduling goal:** {monthly_goal:,.0f}")
        st.markdown(f"**Goals source:** CrewStatLists.xlsx → EstHrsGoals sheet")

        st.markdown("---")
        st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows")
        st.dataframe(df, use_container_width=True, height=300)
