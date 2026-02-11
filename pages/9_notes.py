"""Notes — client reviews and internal notes filtered by review status."""
import streamlit as st
import pandas as pd

from data.loader import load_all_line_items
from data.transforms import build_so_line_items, build_notes, get_years
from components.filters import apply_year, date_range_filter
from components.lineage_inspector import inspectable_dataframe, inspectable_metric

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
notes = build_notes(so)
years = get_years(notes)

st.markdown("#### Notes")

# ── Filters ──────────────────────────────────────────────────────────
reviews = sorted(notes["Review"].dropna().unique().tolist())
reviews = [r for r in reviews if r]

fc1, fc2, fc3 = st.columns(3)
with fc1:
    sel_review = st.selectbox("Review", ["All"] + reviews, key="n_rev")
with fc2:
    sel_year = st.selectbox("Year", years, key="n_yr")
with fc3:
    pass  # reserved for date range if needed

# Apply
df = notes.copy()
df = apply_year(df, sel_year)
if sel_review and sel_review != "All":
    df = df[df["Review"].str.contains(sel_review, case=False, na=False)]

# ── KPI ──────────────────────────────────────────────────────────────
c_kpi, _ = st.columns([1, 5])
with c_kpi:
    inspectable_metric("Count", len(df), "Notes Count", source_df=df, filters={"Year": sel_year, "Review": sel_review}, key="n_count_kpi")

# ── Table ────────────────────────────────────────────────────────────
display_cols = [
    "Approved Date", "Visit Ref #", "Client",
    "Review", "Review Notes", "Internal Notes",
]
existing = [c for c in display_cols if c in df.columns]
display = df[existing].copy()
if "Approved Date" in display.columns:
    display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")

inspectable_dataframe(df, display, source_so=so, key="n_tbl", height=550)

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_notes()` (filtered to rows where Review is not empty)")
    st.markdown(f"**Active filters:** Year=`{sel_year}`, Review=`{sel_review}`")
    st.markdown(f"**Total notes (all years):** {len(notes):,}")

    st.markdown("---")
    st.markdown(f"**Filtered notes table** — {len(df):,} rows")
    st.dataframe(df, use_container_width=True, height=300)
