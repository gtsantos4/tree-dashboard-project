"""White Board — monthly summary of stats, QC, and Win/Loss with wireframe redesign."""
import streamlit as st
import pandas as pd
import plotly.express as px

from reports.stats.data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from reports.stats.data.transforms import (
    build_so_line_items, build_stats, build_inv_amts,
    build_qc_scale, build_cb_scale, build_compliment_scale,
    get_years, get_operations,
)
from components.filters import apply_year, apply_operation
from components.kpi_cards import metric_card_v2, kpi_row
from components.styled_table import (
    page_header, filter_container, pivot_monthly, show_reference_table,
    section_divider, _wl_row_color, card_container
)
from components.lineage_inspector import inspectable_chart
from config import MONTH_ORDER, WIN_COLOR, LOSS_COLOR, DEV_MODE

# ── Load data ────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
sheets = load_crew_stat_lists()
qc_scale = build_qc_scale(sheets)
stats = build_stats(so, qc_scale)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)

cb_scale = build_cb_scale(sheets)
comp_scale = build_compliment_scale(sheets)
years = get_years(so)
operations = get_operations(so)

# ── Page Header ──────────────────────────────────────────────────────
page_header("White Board", "Monthly performance matrix")

# ── Filters ──────────────────────────────────────────────────────────
with filter_container():
    fc1, fc2 = st.columns(2)
    with fc1:
        sel_year = st.selectbox("Year", years, key="wb_yr")
    with fc2:
        sel_op = st.selectbox(
            "Operation",
            ["All"] + operations,
            key="wb_op"
        )

fstats = apply_year(stats, sel_year)
fstats = apply_operation(fstats, sel_op)

finv = apply_year(inv, sel_year)
finv = apply_operation(finv, sel_op)

# ── Calculate KPI metrics ─────────────────────────────────────────────
qc_items = fstats[fstats["Item Name"] == "Quality Control"]
comp_items = fstats[fstats["Item Name"] == "Compliment"]
cb_items = fstats[fstats["Item Name"] == "Call Back"]

qc_count = len(qc_items)
qc_avg_pct = qc_items["Percent"].mean() * 100 if not qc_items.empty and qc_items["Percent"].notna().any() else 0
comp_count = int(comp_items["Qty"].sum())
cb_count = int(cb_items["Qty"].sum())

# ── KPI Row (4 cards) ─────────────────────────────────────────────────
kpi_items = [
    {
        "label": "Total QC Grades",
        "value": qc_count,
        "icon": "📋",
    },
    {
        "label": "Avg QC Score",
        "value": f"{qc_avg_pct:.0f}%",
        "icon": "📊",
        "accent": "win",
    },
    {
        "label": "Compliments",
        "value": comp_count,
        "icon": "⭐",
    },
    {
        "label": "Call Backs",
        "value": cb_count,
        "icon": "📞",
        "accent": "loss",
    },
]

kpi_row(kpi_items, cols=4)

# ── Tabbed Section: Stats by Month / QC % by Month ────────────────────
st.markdown("")  # Spacing
with card_container("Monthly Metrics"):
    tab1, tab2 = st.tabs(["Stats by Month", "QC % by Month"])

    with tab1:
        if not fstats.empty:
            pv_counts = pivot_monthly(fstats, "Item Name", "Qty", agg_func="sum")
            st.dataframe(pv_counts.style.format("{:.0f}"), use_container_width=True)
        else:
            st.info("No stats data for selected year and operation.")

    with tab2:
        qc_rows = fstats[fstats["Item Name"] == "Quality Control"].copy()
        if not qc_rows.empty:
            pv_pct = pivot_monthly(qc_rows, "Item Name", "Percent", agg_func="mean")
            st.dataframe(
                pv_pct.style.format("{:.0%}"),
                use_container_width=True,
            )
        else:
            st.info("No Quality Control data for selected year and operation.")

# ── Win / Loss by Month Section ───────────────────────────────────────
section_divider("Win / Loss by Month")

wl_col1, wl_col2 = st.columns([5, 7])

with wl_col1:
    with card_container("Win/Loss Pivot"):
        if not finv.empty:
            wl_data = finv[finv["MonthShort"].notna()].copy()
            pv_wl = pd.pivot_table(
                wl_data, index=["Operation", "WinLossText"], columns="MonthShort",
                values="Visit Ref #", aggfunc="count", fill_value=0,
            )
            ordered = [m for m in MONTH_ORDER if m in pv_wl.columns]
            pv_wl = pv_wl[ordered]
            pv_wl["Total"] = pv_wl.sum(axis=1)

            # Apply Win/Loss row coloring
            styled = (
                pv_wl
                .style
                .apply(_wl_row_color, wl_col="WinLossText", axis=1)
                .format("{:.0f}")
            )
            st.dataframe(styled, use_container_width=True)
        else:
            st.info("No Win/Loss data for selected year and operation.")

with wl_col2:
    if not finv.empty:
        wl_data = finv[finv["MonthShort"].notna()].copy()
        chart_data = (
            wl_data.groupby(["MonthShort", "WinLossText"])
            .size()
            .reset_index(name="Count")
        )
        # Sort months
        chart_data["MonthNum"] = chart_data["MonthShort"].map(
            {m: i for i, m in enumerate(MONTH_ORDER)}
        )
        chart_data.sort_values("MonthNum", inplace=True)
        fig = px.bar(
            chart_data, x="MonthShort", y="Count", color="WinLossText",
            barmode="group",
            color_discrete_map={"Win": WIN_COLOR, "Loss": LOSS_COLOR},
            labels={"MonthShort": "Month", "Count": "Count of Visit Ref #"},
        )
        fig.update_layout(
            height=350, margin=dict(l=20, r=20, t=30, b=30),
            legend=dict(title="", orientation="h", y=1.08),
            xaxis_title="",
            yaxis_title="Count",
        )
        with card_container("Win/Loss Trend"):
            st.plotly_chart(fig, use_container_width=True)
        if DEV_MODE:
            inspectable_chart(fig, "Win/Loss by Month Chart", source_df=chart_data, filters={"Year": sel_year, "Operation": sel_op}, key="wb_wl_chart")
    else:
        st.info("No chart data available.")

# ── Reference Scales (in expander) ────────────────────────────────────
with st.expander("📋 Reference Tables"):
    r1, r2, r3 = st.columns(3)
    with r1:
        show_reference_table(cb_scale, "CB / Month   Pct")
    with r2:
        show_reference_table(comp_scale, "Compl / Month   Pct")
    with r3:
        show_reference_table(qc_scale, "QC Grade   Pct")

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_stats()` for stats pivots; `build_inv_amts()` for Win/Loss pivot")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`")
        st.markdown("**Reference scales** come from `CrewStatLists.xlsx` → sheets CB, Compliments, QC")

        st.markdown("---")
        st.markdown(f"**Stats table** (filtered) — {len(fstats):,} rows")
        st.dataframe(fstats, use_container_width=True, height=250)

        st.markdown(f"**InvAmts table** (filtered, for Win/Loss) — {len(finv):,} rows")
        st.dataframe(finv, use_container_width=True, height=250)
