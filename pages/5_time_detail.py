"""TimeDetail — drill-through for time tracking data."""
import streamlit as st
import pandas as pd

from data.loader import load_time_data
from data.transforms import build_time_detail
from components.filters import operation_filter
from components.lineage_inspector import inspectable_dataframe, inspectable_metric

# ── Load ─────────────────────────────────────────────────────────────
raw = load_time_data()
df = build_time_detail(raw)

st.markdown("#### Time Detail")

if df.empty:
    st.warning("No Time.csv data found in sample-data folder.")
    st.stop()

# ── Filters ──────────────────────────────────────────────────────────
ops = sorted(df["Operation"].dropna().unique().tolist())
ops = [o for o in ops if o]

fc1, fc2, fc3 = st.columns(3)
with fc1:
    sel_op = operation_filter(ops, key="td_op")
with fc2:
    emps = sorted(df["Title"].dropna().unique().tolist())
    sel_emp = st.selectbox("Employee", ["All"] + emps, key="td_emp")
with fc3:
    customers = sorted(df["Customer"].dropna().unique().tolist())
    sel_cust = st.selectbox("Customer", ["All"] + customers[:200], key="td_cust")

# Apply
fdf = df.copy()
if sel_op and sel_op != "All":
    fdf = fdf[fdf["Operation"] == sel_op]
if sel_emp and sel_emp != "All":
    fdf = fdf[fdf["Title"] == sel_emp]
if sel_cust and sel_cust != "All":
    fdf = fdf[fdf["Customer"] == sel_cust]

# ── Table ────────────────────────────────────────────────────────────
display_cols = ["DATE", "Title", "Customer", "ITEM", "DURATION", "AddOn", "JobNo", "InvNo", "NOTE", "Operation", "WeekEnd"]
existing = [c for c in display_cols if c in fdf.columns]
display = fdf[existing].copy()
if "DATE" in display.columns:
    display["DATE"] = pd.to_datetime(display["DATE"], errors="coerce").dt.strftime("%m/%d/%Y").fillna("")
if "WeekEnd" in display.columns:
    display["WeekEnd"] = pd.to_datetime(display["WeekEnd"], errors="coerce").dt.strftime("%m/%d/%Y").fillna("")

total_dur = fdf["DURATION"].sum()

inspectable_dataframe(fdf, display, source_so=None, key="td_tbl", height=550)
st.markdown(f"**Total Duration: {total_dur:,.2f}**")

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `Time.csv` → `build_time_detail()` (cast DURATION to float, parse dates, rename EMP→Title / JOB→Customer, derive Operation from ITEM)")
    st.markdown(f"**Active filters:** Operation=`{sel_op}`, Employee=`{sel_emp}`, Customer=`{sel_cust}`")
    st.markdown(f"**Total rows (unfiltered):** {len(df):,}")

    st.markdown("---")
    st.markdown(f"**Filtered time detail** — {len(fdf):,} rows")
    st.dataframe(fdf, use_container_width=True, height=300)
