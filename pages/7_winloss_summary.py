"""WinLoss Summary — estimated hours vs scheduling goals by month/year."""
import streamlit as st
import pandas as pd
import numpy as np

from data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from data.transforms import (
    build_so_line_items, build_inv_amts,
    build_scheduling_goals, get_years, get_operations,
)
from components.filters import (
    apply_year, apply_months, apply_operation,
    operation_filter, month_filter,
)
from components.lineage_inspector import inspectable_dataframe, inspectable_metric
from config import MONTH_ORDER, MONTH_FULL_ORDER

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
st.markdown("#### WinLoss Summary")

st.markdown("---")

# ── KPI ──────────────────────────────────────────────────────────────
c_kpi, _ = st.columns([1, 5])
with c_kpi:
    inspectable_metric("Count", len(inv), "Win/Loss Count", source_df=inv, filters={}, key="wls_count_kpi")

st.markdown("---")

fc1, fc2, fc3 = st.columns(3)
with fc1:
    sel_year = st.selectbox("Year", years, key="wls_yr")
with fc2:
    sel_op = operation_filter(operations, key="wls_op")
with fc3:
    sel_months = month_filter(key="wls_mo")

# Apply
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

# ── Estimated Hours v Goals — Monthly ────────────────────────────────
t1, t2 = st.columns(2)

with t1:
    st.markdown("**Estimated Hours v Goals**")
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
        st.dataframe(
            display.style.format({
                "Hours": "{:,.0f}", "Goal": "{:,.0f}",
                "YTD_Hours": "{:,.0f}", "YTD_Goal": "{:,.0f}",
                "% to Goal": "{:.0f}%",
            }),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No data for selected filters.")

with t2:
    st.markdown("**Estimated Hours v Goals — Monthly Average**")
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
        st.dataframe(
            display.style.format({
                "Year": "{:.0f}",
                "Hours/Mo": "{:,.0f}", "Goal": "{:,.0f}",
                "Variance": "{:+,.0f}", "% of Goal": "{:.0f}%",
            }),
            use_container_width=True, hide_index=True,
        )

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` → Monthly/Yearly aggregation")
    st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`")
    st.markdown(f"**Monthly scheduling goal:** {monthly_goal:,.0f}")
    st.markdown(f"**Goals source:** CrewStatLists.xlsx → EstHrsGoals sheet")

    st.markdown("---")
    st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows")
    st.dataframe(df, use_container_width=True, height=300)
