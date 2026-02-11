"""Est v Actual Dash — scheduling goals reference + bar chart of est vs actual hours."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from data.transforms import (
    build_so_line_items, build_inv_amts,
    build_scheduling_goals, build_misc_inputs,
    get_years, get_operations,
)
from components.filters import (
    apply_year, apply_months, apply_operation,
    operation_filter, month_filter,
)
from components.lineage_inspector import inspectable_dataframe, inspectable_metric
from config import MONTH_FULL_ORDER, WIN_COLOR, ACCENT_BLUE

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
st.markdown("#### Est v Actual Dash")

# ── KPI ──────────────────────────────────────────────────────────────
c_kpi, _ = st.columns([1, 5])
with c_kpi:
    inspectable_metric("Count", len(inv), "Est v Actual Count", source_df=inv, filters={}, key="eva_count_kpi")

st.markdown("---")

fc1, fc2, fc3 = st.columns(3)
with fc1:
    sel_year = st.selectbox("Year", years, key="eva_yr")
with fc2:
    sel_op = operation_filter(operations, key="eva_op")
with fc3:
    sel_month = st.selectbox("Month", ["All"] + MONTH_FULL_ORDER, key="eva_mo")

# Apply
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_operation(df, sel_op)
if sel_month and sel_month != "All":
    df = df[df["MonthFull"] == sel_month]

# ── Scheduling Goals Reference Table ─────────────────────────────────
misc = build_misc_inputs(sched_goals)
if sel_op and sel_op != "All":
    misc = misc[misc["Operation"] == sel_op]
else:
    misc = misc[misc["Operation"] == "All"] if "All" in misc["Operation"].values else misc

ref_col, chart_col = st.columns([2, 5])

with ref_col:
    if not misc.empty:
        st.dataframe(
            misc[["Title", "NumericalValue1"]].rename(
                columns={"NumericalValue1": "Sum of NumericalValue1"}
            ),
            use_container_width=True, hide_index=True,
        )

# ── Stacked Bar Chart: HrsActual vs HoursEst by Month ───────────────
with chart_col:
    st.markdown(
        '<div style="background:#8B0000;color:white;padding:6px 12px;'
        'border-radius:4px;font-weight:600;">Win / Loss for Period</div>',
        unsafe_allow_html=True,
    )

    if not df.empty and df["MonthFull"].notna().any():
        monthly = df.groupby("MonthFull").agg(
            HrsActual=("TimeByInv", "sum"),
            HoursEst=("HoursEst", "sum"),
        ).reset_index()
        # Sort by month order
        monthly["order"] = monthly["MonthFull"].apply(
            lambda m: MONTH_FULL_ORDER.index(m) if m in MONTH_FULL_ORDER else 99
        )
        monthly.sort_values("order", inplace=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="HrsActual", x=monthly["MonthFull"], y=monthly["HrsActual"],
            marker_color=WIN_COLOR,
        ))
        fig.add_trace(go.Bar(
            name="HoursEst", x=monthly["MonthFull"], y=monthly["HoursEst"],
            marker_color=ACCENT_BLUE,
        ))
        fig.update_layout(
            barmode="stack",
            height=420,
            margin=dict(l=30, r=20, t=30, b=40),
            yaxis_title="HrsActual and HoursEst",
            xaxis_title="MonthFull",
            legend=dict(orientation="h", y=1.05),
        )
        # Add value labels on bars
        for trace in fig.data:
            fig.update_traces(texttemplate="%{y:.1f}", textposition="inside",
                              selector=dict(name=trace.name))
        from components.lineage_inspector import inspectable_chart
        inspectable_chart(fig, "Est v Actual Chart", source_df=monthly, filters={"Year": sel_year, "Operation": sel_op, "Month": sel_month}, key="eva_chart")
    else:
        st.info("No data for selected period.")

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` → Monthly aggregation of HrsActual (TimeByInv) and HoursEst")
    st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Month=`{sel_month}`")
    st.markdown(f"**Scheduling goals source:** CrewStatLists.xlsx → EstHrsGoals sheet → `build_misc_inputs()`")

    st.markdown("---")
    st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows")
    st.dataframe(df, use_container_width=True, height=300)
