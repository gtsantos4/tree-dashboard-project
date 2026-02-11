"""Owner — comprehensive financial Win/Loss detail with EPH metrics."""
import streamlit as st
import pandas as pd
import numpy as np

from data.loader import load_all_line_items, load_time_data
from data.transforms import (
    build_so_line_items, build_inv_amts,
    get_years, get_operations,
)
from components.filters import (
    apply_year, apply_months, apply_operation,
    operation_filter, month_filter,
)
from components.styled_table import winloss_table
from components.lineage_inspector import inspectable_winloss, inspectable_metric

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
time_raw = load_time_data()
inv = build_inv_amts(so, time_raw)
years = get_years(inv)
operations = get_operations(so)

# ── Filters ──────────────────────────────────────────────────────────
st.markdown("#### Owner")

fc1, fc2, fc3 = st.columns(3)
with fc1:
    sel_year = st.selectbox("Year", years, key="own_yr")
with fc2:
    sel_op = operation_filter(operations, key="own_op")
with fc3:
    sel_months = month_filter(key="own_mo")

# Apply
df = inv.copy()
df = apply_year(df, sel_year)
df = apply_months(df, sel_months)
df = apply_operation(df, sel_op)

# ── KPI ──────────────────────────────────────────────────────────────
c_kpi, _ = st.columns([1, 5])
with c_kpi:
    inspectable_metric("Count", len(df), "Win/Loss Count", source_df=df, filters={"Year": sel_year, "Operation": sel_op, "Months": sel_months}, key="own_count_kpi")

# ── Detail Table ─────────────────────────────────────────────────────
st.markdown(
    '<div style="background:#8B0000;color:white;padding:6px 12px;'
    'border-radius:4px;font-weight:600;">Win / Loss for Period</div>',
    unsafe_allow_html=True,
)

if not df.empty:
    # Compute WL_EPH (EPH only for Wins)
    df["WL_EPH"] = np.where(
        (df["WinLossText"] == "Win") & (df["TimeByInv"] > 0),
        df["InvTotal"] / df["TimeByInv"],
        0,
    )

    display_cols = [
        "InvoiceDate", "Visit Ref #", "Client", "Operation",
        "InvTotal", "Costs", "NetInv", "Discount",
        "HoursEst", "TimeByInv", "HrsRatio",
        "EPH", "WL_EPH", "WinLossText",
        "Crew Leader", "Sales Reps",
    ]
    existing = [c for c in display_cols if c in df.columns]
    tbl = df[existing].copy()
    tbl.rename(columns={
        "WinLossText": "WinLoss",
        "TimeByInv": "HrsAct",
        "Discount": "Disc",
        "HoursEst": "HrsEst",
    }, inplace=True)

    if "InvoiceDate" in tbl.columns:
        tbl["InvoiceDate"] = tbl["InvoiceDate"].dt.strftime("%m/%d/%Y").fillna("")

    # Round numerics
    for col in ["InvTotal", "Costs", "NetInv", "Disc", "HrsEst", "HrsAct", "HrsRatio", "EPH", "WL_EPH"]:
        if col in tbl.columns:
            tbl[col] = tbl[col].round(2)

    inspectable_winloss(df, tbl, source_so=so, source_time=time_raw, wl_col="WinLoss", key="own_tbl", height=550)

    # ── Totals row ───────────────────────────────────────────────────
    sum_cols = {
        "InvTotal": df["InvTotal"].sum(),
        "Costs": df["Costs"].sum(),
        "NetInv": df["NetInv"].sum(),
        "HoursEst": df["HoursEst"].sum(),
        "TimeByInv": df["TimeByInv"].sum(),
    }
    total_eph = sum_cols["InvTotal"] / sum_cols["TimeByInv"] if sum_cols["TimeByInv"] > 0 else 0
    wins = df[df["WinLossText"] == "Win"]
    total_wl_eph = wins["InvTotal"].sum() / wins["TimeByInv"].sum() if wins["TimeByInv"].sum() > 0 else 0

    st.markdown(
        f"**Totals:** InvTotal: ${sum_cols['InvTotal']:,.2f} &nbsp;|&nbsp; "
        f"Costs: ${sum_cols['Costs']:,.2f} &nbsp;|&nbsp; "
        f"Net: ${sum_cols['NetInv']:,.2f} &nbsp;|&nbsp; "
        f"HrsEst: {sum_cols['HoursEst']:,.2f} &nbsp;|&nbsp; "
        f"HrsAct: {sum_cols['TimeByInv']:,.2f} &nbsp;|&nbsp; "
        f"EPH: {total_eph:,.2f} &nbsp;|&nbsp; "
        f"WL_EPH: {total_wl_eph:,.2f}"
    )

    # ── Debug ────────────────────────────────────────────────────────────
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_inv_amts()` + WL_EPH computation")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Months=`{sel_months or 'All'}`")

        st.markdown("---")
        st.markdown(f"**InvAmts table** (filtered) — {len(df):,} rows, {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=300)
else:
    st.info("No invoiced visits for the selected filters.")
