"""Damage — tracking damage repair incidents by crew leader."""
import streamlit as st
import pandas as pd

from data.loader import load_all_line_items
from data.transforms import build_so_line_items, build_damage, get_crew_leaders, get_years
from components.filters import apply_year, apply_crew_leader, crew_leader_filter
from components.lineage_inspector import inspectable_dataframe, inspectable_metric

# ── Load ─────────────────────────────────────────────────────────────
raw = load_all_line_items()
so = build_so_line_items(raw)
damage = build_damage(so)
years = get_years(damage)
leaders = sorted(damage["Crew Leader"].dropna().unique().tolist())
leaders = [l for l in leaders if l]

# ── Filters ──────────────────────────────────────────────────────────
st.markdown("#### Damage")

fc1, fc2 = st.columns([3, 2])
with fc1:
    # Year button-style filter
    sel_years = st.multiselect("Year", years, default=years[:3] if len(years) >= 3 else years, key="dmg_yr")
with fc2:
    sel_leader = crew_leader_filter(leaders, key="dmg_cl")

# Apply
df = damage.copy()
if sel_years:
    df = df[df["Year"].isin(sel_years)]
df = apply_crew_leader(df, sel_leader)

# ── Layout ───────────────────────────────────────────────────────────
c1, c2 = st.columns([4, 2])

with c1:
    display_cols = ["Approved Date", "Visit Ref #", "Client", "Line_Item_Description", "Line Total", "Crew Leader"]
    existing = [c for c in display_cols if c in df.columns]
    display = df[existing].copy()
    if "Approved Date" in display.columns:
        display["Approved Date"] = display["Approved Date"].dt.strftime("%m/%d/%Y").fillna("")
    if "Line Total" in display.columns:
        display["Line Total"] = display["Line Total"].apply(lambda v: f"${v:,.2f}" if pd.notna(v) else "")
    inspectable_dataframe(df, display, source_so=so, key="dmg_tbl", height=500)

with c2:
    # Count KPI
    inspectable_metric("Count", len(df), "Damage Count", source_df=df, filters={"Years": sel_years, "Crew Leader": sel_leader}, key="dmg_count_kpi")
    st.markdown("")

    # Per-crew-leader breakdown
    if not df.empty:
        st.markdown("**Damage by Crew Leader**")
        crew_totals = (
            damage[damage["Year"].isin(sel_years)] if sel_years else damage
        ).groupby("Crew Leader")["Line Total"].sum().sort_values(ascending=False)
        for name, total in crew_totals.items():
            if name:
                st.markdown(
                    f'<div style="padding:4px 8px;margin:2px 0;background:#fff;'
                    f'border-left:3px solid #C62828;border-radius:4px;">'
                    f'<strong>{name}</strong><br/>'
                    f'<span style="font-size:18px;">${total:,.2f}</span></div>',
                    unsafe_allow_html=True,
                )

# ── Debug ────────────────────────────────────────────────────────────
with st.expander("🔍 Debug: Data Sources & Transforms"):
    st.markdown("**Pipeline:** `LineItems_SO_*.csv` → `build_so_line_items()` → `build_damage()` (filtered to Item Name = 'Damage Repair')")
    st.markdown(f"**Active filters:** Years=`{sel_years}`, Crew Leader=`{sel_leader}`")
    st.markdown(f"**Total damage rows (all years):** {len(damage):,}")

    st.markdown("---")
    st.markdown(f"**Filtered damage table** — {len(df):,} rows")
    st.dataframe(df, use_container_width=True, height=300)
