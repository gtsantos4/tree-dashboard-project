"""Owner — comprehensive financial Win/Loss detail with EPH metrics."""
import streamlit as st
import pandas as pd
import numpy as np

from reports.stats.data.loader import load_all_line_items, load_time_data
from reports.stats.data.transforms import (
    build_so_line_items, build_inv_amts,
    get_years, get_operations, get_crew_leaders,
)
from components.filters import (
    apply_year, apply_months, apply_operation, apply_crew_leader,
    operation_filter, month_filter, crew_leader_filter,
)
from components.kpi_cards import kpi_row
from components.styled_table import (
    page_header, filter_container, card_container, totals_bar
)
from components.lineage_inspector import inspectable_winloss
from config import DEV_MODE

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)
years = get_years(inv)
operations = get_operations(so)
crew_leaders = get_crew_leaders(so)

# ── Page Title ───────────────────────────────────────────────────────
page_header("Owner", "Full financial view — revenue, costs, and profitability")

# ── Filters (4 columns: Year, Operation, Month, Crew Leader) ─────────
with filter_container():
    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        sel_year = st.selectbox("Year", years, key="own_yr")

    with fc2:
        sel_op = operation_filter(operations, key="own_op")

    with fc3:
        sel_months = month_filter(key="own_mo")

    with fc4:
        sel_crew = crew_leader_filter(crew_leaders, key="own_crew")

# Apply filters
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_operation(df, sel_op)
df = apply_crew_leader(df, sel_crew)

# ── Helper: Format large numbers as K/M ──────────────────────────────
def _fmt_k(val):
    """Format numbers with K/M suffix."""
    if pd.isna(val):
        return "$0"
    if abs(val) >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"${val/1_000:,.0f}K"
    return f"${val:,.0f}"

# ── KPI Row (5 cards) ────────────────────────────────────────────────
# Total Revenue, Net Revenue (win), Avg EPH, Win Rate (win), Jobs
total_revenue = df["InvTotal"].sum() if not df.empty else 0
net_revenue = df["NetInv"].sum() if not df.empty else 0
total_hours = df["TimeByInv"].sum() if not df.empty else 0
avg_eph = total_revenue / total_hours if total_hours > 0 else 0
win_count = len(df[df["WinLossText"] == "Win"]) if not df.empty else 0
total_count = len(df)
win_rate = (win_count / total_count * 100) if total_count > 0 else 0

kpi_row([
    {
        "label": "Total Revenue",
        "prefix": "$",
        "value": _fmt_k(total_revenue),
    },
    {
        "label": "Net Revenue",
        "prefix": "$",
        "value": _fmt_k(net_revenue),
        "accent": "win",
    },
    {
        "label": "Avg EPH",
        "prefix": "$",
        "value": f"{avg_eph:,.0f}",
    },
    {
        "label": "Win Rate",
        "value": f"{win_rate:.1f}%",
        "accent": "win",
    },
    {
        "label": "Jobs",
        "value": total_count,
    },
], cols=5)

# ── Table in card container ──────────────────────────────────────────
if not df.empty:
    # Compute WL_EPH (EPH only for Wins)
    df["WL_EPH"] = np.where(
        (df["WinLossText"] == "Win") & (df["TimeByInv"] > 0),
        df["InvTotal"] / df["TimeByInv"],
        0,
    )

    # Display columns in exact wireframe order
    display_cols = [
        "InvoiceDate", "Visit Ref #", "WinLossText", "Client", "Operation",
        "InvTotal", "Costs", "NetInv",
        "HoursEst", "TimeByInv", "HrsRatio",
        "EPH", "Crew Leader",
    ]
    existing = [c for c in display_cols if c in df.columns]
    tbl = df[existing].copy()
    tbl.rename(columns={
        "WinLossText": "WinLoss",
        "TimeByInv": "HrsAct",
    }, inplace=True)

    if "InvoiceDate" in tbl.columns:
        tbl["InvoiceDate"] = tbl["InvoiceDate"].dt.strftime("%m/%d/%Y").fillna("")

    # Round numerics
    for col in ["InvTotal", "Costs", "NetInv", "HoursEst", "HrsAct", "HrsRatio", "EPH"]:
        if col in tbl.columns:
            tbl[col] = tbl[col].round(2)

    with card_container("Win / Loss for Period"):
        inspectable_winloss(df, tbl, source_so=so, source_time=time_raw, wl_col="WinLoss", key="own_tbl", height=550)

        # ── Totals bar ───────────────────────────────────────────────────
        sum_cols = {
            "InvTotal": df["InvTotal"].sum(),
            "Costs": df["Costs"].sum(),
            "NetInv": df["NetInv"].sum(),
            "HoursEst": df["HoursEst"].sum(),
            "TimeByInv": df["TimeByInv"].sum(),
        }
        total_eph = sum_cols["InvTotal"] / sum_cols["TimeByInv"] if sum_cols["TimeByInv"] > 0 else 0
        wins = df[df["WinLossText"] == "Win"]
        total_wl_eph = wins["InvTotal"].sum() / wins["TimeByInv"].sum() if not wins.empty and wins["TimeByInv"].sum() > 0 else 0

        totals_bar([
            {"label": "Revenue", "value": f"${sum_cols['InvTotal']:,.2f}"},
            {"label": "Costs", "value": f"${sum_cols['Costs']:,.2f}"},
            {"label": "Net", "value": f"${sum_cols['NetInv']:,.2f}"},
            {"label": "Est Hrs", "value": f"{sum_cols['HoursEst']:,.2f}"},
            {"label": "Actual Hrs", "value": f"{sum_cols['TimeByInv']:,.2f}"},
            {"label": "EPH", "value": f"${total_eph:,.2f}"},
            {"label": "WL EPH", "value": f"${total_wl_eph:,.2f}"},
        ])

else:
    st.info("No invoiced visits for the selected filters.")

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` + WL_EPH computation")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`, Crew Leader=`{sel_crew}`")

        st.markdown("---")
        st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows, {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=300)
