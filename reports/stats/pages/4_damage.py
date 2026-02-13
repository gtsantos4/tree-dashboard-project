"""Damage — tracking damage repair incidents by crew leader."""
import streamlit as st
import pandas as pd

from reports.stats.data.loader import load_all_line_items
from reports.stats.data.transforms import build_so_line_items, build_damage, get_years
from components.filters import apply_year, apply_crew_leader, crew_leader_filter
from components.kpi_cards import metric_card_v2, kpi_row
from components.styled_table import page_header, filter_container, card_container, crew_mini_cards
from components.lineage_inspector import inspectable_dataframe
from config import DEV_MODE, LOSS_COLOR

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
damage = build_damage(so)
years = get_years(damage)
leaders = sorted(damage["Crew Leader"].dropna().unique().tolist())
leaders = [l for l in leaders if l]

# ── Page Header ──────────────────────────────────────────────────────
page_header("Damage", "Damage repair incidents and costs")

# ── Filters ──────────────────────────────────────────────────────────
with filter_container():
    fc1, fc2 = st.columns([3, 2])
    with fc1:
        default_years = [2025] if 2025 in years else (years[:3] if len(years) >= 3 else years)
        sel_years = st.multiselect("Year", years, default=default_years, key="dmg_yr")
    with fc2:
        sel_leader = crew_leader_filter(leaders, key="dmg_cl")

# Apply
df = damage.copy()
if sel_years:
    df = df[df["Year"].isin(sel_years)]
df = apply_crew_leader(df, sel_leader)

# ── KPI Row ──────────────────────────────────────────────────────────
incident_count = len(df)
total_cost = df["Line Total"].sum() if "Line Total" in df.columns else 0
avg_per_incident = total_cost / incident_count if incident_count > 0 else 0

kpi_items = [
    {"label": "Incidents", "value": incident_count, "accent": "loss", "icon": "⚠️"},
    {"label": "Total Cost", "value": total_cost, "prefix": "$", "accent": "loss", "icon": "💰"},
    {"label": "Avg per Incident", "value": avg_per_incident, "prefix": "$", "icon": "📊"},
]
kpi_row(kpi_items, cols=3)

st.markdown("")  # spacing

# ── Layout: Left + Right ─────────────────────────────────────────────
c1, c2 = st.columns([8, 4])

with c1:
    with card_container("Damage Detail"):
        display_cols = ["Approved Date", "Visit Ref #", "Client", "Crew Leader", "Line_Item_Description", "Line Total"]
        existing = [c for c in display_cols if c in df.columns]
        display = df[existing].copy()
        if "Approved Date" in display.columns:
            display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")
        if "Line Total" in display.columns:
            display["Line Total"] = display["Line Total"].apply(lambda v: f"${v:,.2f}" if pd.notna(v) else "")

        inspectable_dataframe(
            df, display, source_so=so, key="dmg_tbl", height=500,
            fit_to_content_columns=["Approved Date", "Visit Ref #", "Client", "Crew Leader", "Line Total"],
        )

with c2:
    if not df.empty and sel_years:
        crew_totals = (
            damage[damage["Year"].isin(sel_years)]
        ).groupby("Crew Leader").agg(
            total=("Line Total", "sum"),
            count=("Line Total", "size")
        ).sort_values("total", ascending=False)

        crew_cards_data = []
        for name, row in crew_totals.iterrows():
            if name:
                crew_cards_data.append({
                    "name": name,
                    "value": f"${row['total']:,.0f}",
                    "sub": f"{int(row['count'])} incidents"
                })

        if crew_cards_data:
            crew_mini_cards(crew_cards_data)
        else:
            st.info("No crew data available.")
    else:
        st.info("Select years to see crew breakdown.")

# ── Debug ────────────────────────────────────────────────────────────
if DEV_MODE:
    with st.expander("🔍 Debug: Data Sources & Transforms"):
        st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_damage()` (filtered to Item Name = 'Damage Repair')")
        st.markdown(f"**Active filters:** Years=`{sel_years}`, Crew Leader=`{sel_leader}`")
        st.markdown(f"**Total damage rows (all years):** {len(damage):,}")

        st.markdown("---")
        st.markdown(f"**Filtered damage table** — {len(df):,} rows")
        st.dataframe(df, use_container_width=True, height=300)
