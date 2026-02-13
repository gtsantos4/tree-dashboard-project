"""TimeDetail — drill-through for time tracking data."""
import streamlit as st
import pandas as pd

from reports.stats.data.loader import load_time_data
from reports.stats.data.transforms import build_time_detail
from components.filters import operation_filter
from components.kpi_cards import metric_card_v2, kpi_row
from components.styled_table import page_header, filter_container, card_container, totals_bar
from components.lineage_inspector import inspectable_dataframe
from config import DEV_MODE

# ── Load ─────────────────────────────────────────────────────────────
raw = load_time_data()
df = build_time_detail(raw)

# ── Page Header ──────────────────────────────────────────────────────
page_header("Time Detail", "Time tracking entries by employee and job")

if df.empty:
    st.warning("No Time.csv data found in sample-data folder.")
    st.stop()

# ── Filters ──────────────────────────────────────────────────────────
years = sorted(df["DATE"].dropna().dt.year.unique().tolist(), reverse=True) if "DATE" in df.columns else [2025]
ops = sorted(df["Operation"].dropna().unique().tolist())
ops = [o for o in ops if o]

with filter_container():
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        sel_year = st.selectbox("Year", years, key="td_yr")
    with fc2:
        sel_op = operation_filter(ops, key="td_op")
    with fc3:
        emps = sorted(df["Title"].dropna().unique().tolist())
        sel_emp = st.selectbox("Employee", ["All"] + emps, key="td_emp")
    with fc4:
        customers = sorted(df["Customer"].dropna().unique().tolist())
        sel_cust = st.selectbox("Customer", ["All"] + customers[:200], key="td_cust")

# Apply
fdf = df.copy()
if "DATE" in fdf.columns and fdf["DATE"].notna().any():
    fdf = fdf[fdf["DATE"].dt.year == sel_year]
if sel_op and sel_op != "All":
    fdf = fdf[fdf["Operation"] == sel_op]
if sel_emp and sel_emp != "All":
    fdf = fdf[fdf["Title"] == sel_emp]
if sel_cust and sel_cust != "All":
    fdf = fdf[fdf["Customer"] == sel_cust]

# ── KPI Row ──────────────────────────────────────────────────────────
total_duration = fdf["DURATION"].sum() if "DURATION" in fdf.columns else 0
entry_count = len(fdf)
employee_count = fdf["Title"].nunique() if "Title" in fdf.columns else 0

kpi_items = [
    {"label": "Total Hours", "value": round(total_duration, 1), "icon": "🕐"},
    {"label": "Entries", "value": entry_count, "icon": "📝"},
    {"label": "Employees", "value": employee_count, "icon": "👷"},
]
kpi_row(kpi_items, cols=3)

st.markdown("")  # spacing

# ── Table in Card ────────────────────────────────────────────────────
with card_container("Time Entries"):
    display_cols = ["DATE", "Title", "ITEM", "DURATION", "InvNo", "NOTE"]
    existing = [c for c in display_cols if c in fdf.columns]
    display = fdf[existing].copy()

    # Rename display columns to match wireframe
    rename_map = {
        "DATE": "Date",
        "Title": "Employee",
        "ITEM": "Item",
        "DURATION": "Duration",
        "InvNo": "Job #",
        "NOTE": "Notes",
    }
    display = display.rename(columns=rename_map)

    if "DATE" in fdf.columns:
        display["Date"] = pd.to_datetime(fdf["DATE"], errors="coerce").dt.strftime("%m/%d/%Y").fillna("")

    inspectable_dataframe(
        fdf, display, source_so=None, key="td_tbl", height=500,
        fit_to_content_columns=["Date", "Employee", "Item", "Duration", "Job #"],
    )

# Totals bar
totals_items = [
    {"label": "Total Duration", "value": f"{total_duration:,.1f} hrs"},
    {"label": "Entries", "value": str(entry_count)},
]
totals_bar(totals_items)

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `Time.csv` → `build_time_detail()` (cast DURATION to float, parse dates, rename EMP→Title / JOB→Customer, derive Operation from ITEM)")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Operation=`{sel_op}`, Employee=`{sel_emp}`, Customer=`{sel_cust}`")
        st.markdown(f"**Total rows (unfiltered):** {len(df):,}")

        st.markdown("---")
        st.markdown(f"**Filtered time detail** — {len(fdf):,} rows")
        st.dataframe(fdf, use_container_width=True, height=300)
