"""Est v Actual — grouped bar chart comparing estimated vs actual hours by month."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from reports.stats.data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from reports.stats.data.transforms import (
    build_so_line_items, build_inv_amts,
    build_scheduling_goals, build_misc_inputs,
    get_years, get_operations,
)
from components.filters import (
    apply_year, apply_months, apply_operation,
    operation_filter, month_filter,
)
from components.kpi_cards import kpi_row
from components.styled_table import page_header, filter_container, card_container
from components.lineage_inspector import inspectable_chart
from config import MONTH_FULL_ORDER, WIN_COLOR, DEV_MODE

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)
sheets = load_crew_stat_lists()
sched_goals = build_scheduling_goals(sheets)
misc = build_misc_inputs(sched_goals)
years = get_years(inv)
operations = get_operations(so)

# ── Page Title ───────────────────────────────────────────────────────
page_header("Estimated vs Actual Hours", "Estimated hours vs actual hours by month")

# ── Filters (3 columns) ──────────────────────────────────────────────
with filter_container():
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_year = st.selectbox("Year", years, key="eva_yr")
    with fc2:
        sel_op = operation_filter(operations, key="eva_op")
    with fc3:
        sel_months = month_filter(key="eva_mo")

# Apply filters
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_operation(df, sel_op)

# ── KPI Row (4 cards) ────────────────────────────────────────────────
jobs = len(df)
est_hours = df["HoursEst"].sum() if not df.empty else 0
actual_hours = df["TimeByInv"].sum() if not df.empty else 0
efficiency = (actual_hours / est_hours * 100) if est_hours > 0 else 0
hrs_saved = est_hours - actual_hours

kpi_items = [
    {
        "label": "Jobs",
        "value": jobs,
    },
    {
        "label": "Est. Hours",
        "value": f"{est_hours:,.0f}",
    },
    {
        "label": "Actual Hours",
        "accent": "win",
        "value": f"{actual_hours:,.0f}",
    },
    {
        "label": "Efficiency",
        "accent": "win" if efficiency > 100 else None,
        "value": f"{efficiency:.0f}%",
        "delta": f"{hrs_saved:+,.0f} hrs saved" if hrs_saved >= 0 else f"{hrs_saved:+,.0f} hrs over",
    },
]

kpi_row(kpi_items, cols=4)

# ── Full-Width Chart Card ────────────────────────────────────────────
with card_container("Estimated vs Actual Hours by Month"):
    if not df.empty and df["MonthFull"].notna().any():
        monthly = df.groupby("MonthFull").agg(
            Estimated=("HoursEst", "sum"),
            Actual=("TimeByInv", "sum"),
        ).reset_index()

        # Sort by month order
        monthly["order"] = monthly["MonthFull"].apply(
            lambda m: MONTH_FULL_ORDER.index(m) if m in MONTH_FULL_ORDER else 99
        )
        monthly.sort_values("order", inplace=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Estimated",
            x=monthly["MonthFull"],
            y=monthly["Estimated"],
            marker_color="#2563EB",
        ))
        fig.add_trace(go.Bar(
            name="Actual",
            x=monthly["MonthFull"],
            y=monthly["Actual"],
            marker_color=WIN_COLOR,
        ))
        fig.update_layout(
            barmode="group",
            height=400,
            margin=dict(l=30, r=20, t=30, b=40),
            yaxis_title="Hours",
            xaxis_title="Month",
            legend=dict(orientation="h", y=1.05, x=0),
            hovermode="x unified",
        )

        inspectable_chart(
            fig, "Est v Actual Chart",
            source_df=monthly,
            filters={"Year": sel_year, "Operation": sel_op, "Months": sel_months or "All"},
            key="eva_chart"
        )
    else:
        st.info("No data for selected period.")

# ── Scheduling Reference (in expander) ───────────────────────────────
with st.expander("📋 Scheduling Reference"):
    misc_filtered = misc.copy()
    if sel_op and sel_op != "All":
        misc_filtered = misc_filtered[misc_filtered["Operation"] == sel_op]
    else:
        misc_filtered = misc_filtered[misc_filtered["Operation"] == "All"] if "All" in misc_filtered["Operation"].values else misc_filtered

    if not misc_filtered.empty:
        st.dataframe(
            misc_filtered[["Title", "NumericalValue1"]].rename(
                columns={"NumericalValue1": "Value"}
            ),
            use_container_width=True, hide_index=True,
        )

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` → Monthly aggregation of Actual (TimeByInv) and Estimated (HoursEst)")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`")
        st.markdown(f"**Scheduling goals source:** CrewStatLists.xlsx → EstHrsGoals sheet → `build_misc_inputs()`")

        st.markdown("---")
        st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows")
        st.dataframe(df, use_container_width=True, height=300)
