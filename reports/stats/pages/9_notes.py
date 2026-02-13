"""Notes — client reviews and internal notes filtered by review status."""
import streamlit as st
import pandas as pd

from reports.stats.data.loader import load_all_line_items
from reports.stats.data.transforms import build_so_line_items, build_notes, get_years
from components.filters import apply_year
from components.kpi_cards import kpi_row
from components.styled_table import (
    page_header, filter_container, card_container, totals_bar
)
from components.lineage_inspector import inspectable_dataframe
from config import DEV_MODE

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
notes = build_notes(so)
years = get_years(notes)

# ── Page Title ───────────────────────────────────────────────────────
page_header("Notes", "Review notes and comments on jobs")

# ── Filters (2 columns: Review Status, Year) ─────────────────────────
with filter_container():
    fc1, fc2 = st.columns(2)

    with fc1:
        reviews = sorted(notes["Review"].dropna().unique().tolist())
        reviews = [r for r in reviews if r]
        sel_review = st.selectbox("Review Status", ["All"] + reviews, key="n_rev")

    with fc2:
        sel_year = st.selectbox("Year", years, key="n_yr")

# Apply filters
df = notes.copy()
df = apply_year(df, sel_year)
if sel_review and sel_review != "All":
    df = df[df["Review"].str.contains(sel_review, case=False, na=False)]

# ── KPI Row (3 cards) ────────────────────────────────────────────────
# Total Notes, Reviewed (win), Pending (amber)
total_count = len(df)
reviewed_count = len(df[df["Review"].str.strip() != ""]) if not df.empty and "Review" in df.columns else 0
pending_count = total_count - reviewed_count

kpi_row([
    {
        "label": "Total Notes",
        "value": total_count,
        "icon": "📝",
    },
    {
        "label": "Reviewed",
        "value": reviewed_count,
        "accent": "win",
        "icon": "✅",
    },
    {
        "label": "Pending",
        "value": pending_count,
        "accent": "amber",
        "icon": "⏳",
    },
], cols=3)

st.markdown("")  # spacing

# ── Table in card container ──────────────────────────────────────────
display_cols = [
    "Approved Date", "Visit Ref #", "Client",
    "Review", "Review Notes", "Internal Notes",
]
existing = [c for c in display_cols if c in df.columns]
display = df[existing].copy()

if "Approved Date" in display.columns:
    display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")

with card_container("All Notes"):
    inspectable_dataframe(df, display, source_so=so, key="n_tbl", height=500)
    totals_bar([
        {"label": "Total", "value": str(len(df))}
    ])

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_notes()` (filtered to rows where Review is not empty)")
        st.markdown(f"**Active filters:** Year=`{sel_year}`, Review=`{sel_review}`")
        st.markdown(f"**Total notes (all years):** {len(notes):,}")

        st.markdown("---")
        st.markdown(f"**Filtered notes table** — {len(df):,} rows")
        st.dataframe(df, use_container_width=True, height=300)
