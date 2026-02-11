"""White Board — monthly summary of stats, QC, and Win/Loss."""
import streamlit as st
import pandas as pd
import plotly.express as px

from data.loader import load_all_line_items, load_crew_stat_lists, load_time_data
from data.transforms import (
    build_so_line_items, build_stats, build_inv_amts,
    build_qc_scale, build_cb_scale, build_compliment_scale,
    get_years,
)
from components.filters import apply_year
from components.styled_table import pivot_monthly, show_reference_table
from components.lineage_inspector import inspectable_chart
from config import MONTH_ORDER, WIN_COLOR, LOSS_COLOR

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

# ── Filters ──────────────────────────────────────────────────────────
st.markdown("#### White Board")
sel_year = st.selectbox("Year", years, key="wb_yr")

fstats = apply_year(stats, sel_year)
finv = apply_year(inv, sel_year)

# ── Stats Pivot (Item Name × Month with counts) ─────────────────────
st.markdown("##### Stats by Month")
if not fstats.empty:
    pv_counts = pivot_monthly(fstats, "Item Name", "Qty", agg_func="sum")
    st.dataframe(pv_counts.style.format("{:.0f}"), use_container_width=True)
else:
    st.info("No stats data for selected year.")

# ── QC % Pivot ───────────────────────────────────────────────────────
st.markdown("##### Quality Control % by Month")
qc_rows = fstats[fstats["Item Name"] == "Quality Control"].copy()
if not qc_rows.empty:
    pv_pct = pivot_monthly(qc_rows, "Item Name", "Percent", agg_func="mean")
    st.dataframe(
        pv_pct.style.format("{:.0%}"),
        use_container_width=True,
    )

# ── Win Loss Pivot + Chart ───────────────────────────────────────────
wl_col1, wl_col2 = st.columns([3, 4])

with wl_col1:
    st.markdown("##### Win Loss")
    if not finv.empty:
        # Pivot: Operation × WinLossText × Month
        wl_data = finv[finv["MonthShort"].notna()].copy()
        pv_wl = pd.pivot_table(
            wl_data, index=["Operation", "WinLossText"], columns="MonthShort",
            values="Visit Ref #", aggfunc="count", fill_value=0,
        )
        ordered = [m for m in MONTH_ORDER if m in pv_wl.columns]
        pv_wl = pv_wl[ordered]
        pv_wl["Total"] = pv_wl.sum(axis=1)
        st.dataframe(pv_wl.style.format("{:.0f}"), use_container_width=True)

with wl_col2:
    st.markdown("##### Win Loss Chart by Month")
    if not finv.empty:
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
            barmode="stack",
            color_discrete_map={"Win": WIN_COLOR, "Loss": LOSS_COLOR},
            labels={"MonthShort": "Month", "Count": "Count of Visit Ref #"},
        )
        fig.update_layout(
            height=350, margin=dict(l=20, r=20, t=30, b=30),
            legend=dict(title="", orientation="h", y=1.08),
            xaxis_title="MonthShort",
        )
        inspectable_chart(fig, "Win/Loss by Month Chart", source_df=chart_data, filters={"Year": sel_year}, key="wb_wl_chart")

# ── Reference Scales ─────────────────────────────────────────────────
st.markdown("---")
r1, r2, r3 = st.columns(3)
with r1:
    show_reference_table(cb_scale, "CB / Month   Pct")
with r2:
    show_reference_table(comp_scale, "Compl / Month   Pct")
with r3:
    show_reference_table(qc_scale, "QC Grade   Pct")

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_stats()` for stats pivots; `build_inv_amts()` for Win/Loss pivot")
    st.markdown(f"**Active filters:** Year=`{sel_year}`")
    st.markdown("**Reference scales** come from `CrewStatLists.xlsx` → sheets CB, Compliments, QC")

    st.markdown("---")
    st.markdown(f"**Stats table** (filtered) — {len(fstats):,} rows")
    st.dataframe(fstats, use_container_width=True, height=250)

    st.markdown(f"**InvAmts table** (filtered, for Win/Loss) — {len(finv):,} rows")
    st.dataframe(finv, use_container_width=True, height=250)
