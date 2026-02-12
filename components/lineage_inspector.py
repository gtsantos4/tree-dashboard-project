"""
Lineage inspector — click-to-trace data lineage for every table row and KPI.

Public API
----------
inspectable_dataframe   — table with on_select row inspection
inspectable_winloss     — styled Win/Loss table + dropdown inspector
inspectable_metric      — metric card with lineage popover
inspectable_chart       — Plotly chart with lineage popover

When config.DEV_MODE is False, these render the plain component
with no lineage UI (safe for client-facing deployment).
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import streamlit as st

from reports.stats.data.lineage import COLUMN_LINEAGE, KPI_LINEAGE
from components.kpi_cards import metric_card
from config import DEV_MODE, VY_RED


# ═══════════════════════════════════════════════════════════════════════
# Public: inspectable table (plain DataFrame — supports on_select)
# ═══════════════════════════════════════════════════════════════════════

def inspectable_dataframe(
    df: pd.DataFrame,
    display_df: pd.DataFrame | None = None,
    *,
    source_so: pd.DataFrame | None = None,
    source_time: pd.DataFrame | None = None,
    ref_col: str = "Visit Ref #",
    key: str = "insp",
    height: int = 500,
):
    """
    Render a table with single-row selection (dev mode only).
    In client mode, renders a plain dataframe.
    """
    render = display_df if display_df is not None else df

    if not DEV_MODE:
        st.dataframe(render, use_container_width=True, hide_index=True, height=height)
        return

    event = st.dataframe(
        render,
        use_container_width=True,
        hide_index=True,
        height=height,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )

    selected = []
    if event and hasattr(event, "selection") and event.selection:
        selected = event.selection.rows or []

    if selected and selected[0] < len(df):
        _row_inspector(df.iloc[selected[0]], source_so, source_time, ref_col)


# ═══════════════════════════════════════════════════════════════════════
# Public: inspectable Win/Loss table (styled — uses dropdown inspector)
# ═══════════════════════════════════════════════════════════════════════

def inspectable_winloss(
    df: pd.DataFrame,
    display_df: pd.DataFrame | None = None,
    *,
    source_so: pd.DataFrame | None = None,
    source_time: pd.DataFrame | None = None,
    wl_col: str = "WinLossText",
    ref_col: str = "Visit Ref #",
    key: str = "iwl",
    height: int = 500,
):
    """
    Win/Loss-colored table with a dropdown row inspector (dev mode).
    In client mode, renders the styled table without inspector.
    """
    from components.styled_table import _wl_row_color

    render = display_df if display_df is not None else df
    display_cols = [c for c in render.columns if c != "MonthNum"]
    styled = (
        render[display_cols]
        .style
        .apply(_wl_row_color, wl_col=wl_col, axis=1)
        .format(precision=2, na_rep="")
    )
    st.dataframe(styled, use_container_width=True, height=height)

    if not DEV_MODE:
        return

    # Dropdown inspector
    if ref_col in df.columns:
        refs = [""] + df[ref_col].dropna().astype(str).unique().tolist()
        sel = st.selectbox(
            "🔍 Inspect row by Visit Ref #:",
            refs,
            key=f"{key}_sel",
        )
        if sel:
            match = df[df[ref_col].astype(str) == sel]
            if not match.empty:
                _row_inspector(match.iloc[0], source_so, source_time, ref_col)


# ═══════════════════════════════════════════════════════════════════════
# Public: inspectable metric card
# ═══════════════════════════════════════════════════════════════════════

def inspectable_metric(
    label: str,
    value,
    kpi_name: str,
    *,
    source_df: pd.DataFrame | None = None,
    filters: dict | None = None,
    key: str = "ikpi",
    prefix: str = "",
    suffix: str = "",
):
    """
    Metric card with a popover that shows KPI lineage (dev mode).
    In client mode, renders just the metric card.
    """
    metric_card(label, value, prefix=prefix, suffix=suffix)

    if not DEV_MODE:
        return

    with st.popover("🔍 Lineage"):
        _kpi_inspector(kpi_name, source_df, filters or {})


# ═══════════════════════════════════════════════════════════════════════
# Public: inspectable Plotly chart
# ═══════════════════════════════════════════════════════════════════════

def inspectable_chart(
    fig,
    kpi_name: str,
    *,
    source_df: pd.DataFrame | None = None,
    filters: dict | None = None,
    key: str = "ichart",
):
    """
    Render a Plotly chart with a lineage popover underneath (dev mode).
    In client mode, renders just the chart.
    """
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_fig")

    if not DEV_MODE:
        return

    with st.popover("🔍 Lineage"):
        _kpi_inspector(kpi_name, source_df, filters or {})


# ═══════════════════════════════════════════════════════════════════════
# Internal: row inspector panel
# ═══════════════════════════════════════════════════════════════════════

def _row_inspector(row: pd.Series, source_so, source_time, ref_col):
    """Render the row-level lineage inspector inside an expander."""
    ref = row.get(ref_col, "")
    title = f"🔍 Lineage — {ref_col}: {ref}" if ref else "🔍 Lineage — Selected Row"

    with st.expander(title, expanded=True):
        tab_labels = ["📐 Calculations"]
        if source_so is not None and ref:
            tab_labels.append("📋 Source Line Items")
        if source_time is not None and ref:
            tab_labels.append("⏱ Time Entries")

        tabs = st.tabs(tab_labels)
        idx = 0

        with tabs[idx]:
            _show_calculations(row)
        idx += 1

        if source_so is not None and ref:
            with tabs[idx]:
                _show_source_rows(source_so, str(ref), ref_col)
            idx += 1

        if source_time is not None and ref:
            with tabs[idx]:
                _show_time_entries(source_time, str(ref))


def _show_calculations(row: pd.Series):
    """Render formula breakdowns for computed columns present in the row."""
    found = False
    for col in row.index:
        info = COLUMN_LINEAGE.get(col)
        if not info:
            continue
        found = True
        val = row[col]
        display_val = _fmt(val)

        # Show input values
        src_cols = info.get("source_columns", [])
        inputs_html = ""
        if src_cols:
            parts = []
            for s in src_cols:
                if s in row.index:
                    parts.append(f"{s} = {_fmt(row[s])}")
            if parts:
                inputs_html = (
                    '<br/><span style="color:#888;font-size:12px;">'
                    f'Inputs: {" , ".join(parts)}</span>'
                )

        # Special-case warning
        warn_html = ""
        sc = info.get("special_cases", "")
        if sc and _special_case_active(row, sc):
            warn_html = (
                '<br/><span style="color:#DC2626;font-size:12px;">'
                f'⚠ {sc}</span>'
            )

        st.markdown(
            f'<div style="padding:8px 12px;margin:4px 0;background:#F9FAFB;'
            f'border-left:3px solid {VY_RED};border-radius:4px;">'
            f'<strong>{col}</strong> = <code>{info["formula"]}</code><br/>'
            f'<span style="color:#555;">{info["description"]}</span><br/>'
            f'Result: <strong>{display_val}</strong>'
            f'{inputs_html}{warn_html}</div>',
            unsafe_allow_html=True,
        )

    if not found:
        st.caption("No computed columns with registered lineage in this row.")
        data = {str(c): _fmt(row[c]) for c in row.index}
        st.json(data)


def _show_source_rows(so: pd.DataFrame, ref_val: str, ref_col: str):
    """Show raw SO_LineItems for a given Visit Ref # (or other key)."""
    matches = so[so[ref_col].astype(str) == ref_val]
    if matches.empty:
        st.info(f"No source line items for {ref_col} = {ref_val}")
        return

    st.markdown(f"**{len(matches)} line items** from SO_LineItems")

    # Summary by Item category
    if "Item category" in matches.columns and "Line Total" in matches.columns:
        agg = (
            matches.groupby("Item category")
            .agg(Count=("Line Total", "size"), Total=("Line Total", "sum"))
            .sort_values("Total", ascending=False)
        )
        agg["Total"] = agg["Total"].apply(lambda v: f"${v:,.2f}")
        st.dataframe(agg, use_container_width=True)

    # Billable split
    if "Billable" in matches.columns:
        bill = int(matches["Billable"].sum())
        non = len(matches) - bill
        st.caption(f"Billable: {bill}  |  Non-billable: {non}")

    # Detail rows
    detail_cols = [
        "Item Name", "Item category", "Qty", "Unit Cost", "Line Total",
        "Billable", "Crew Leader", "Operation", "Line_Item_Description",
    ]
    existing = [c for c in detail_cols if c in matches.columns]
    st.dataframe(
        matches[existing], use_container_width=True,
        hide_index=True, height=min(len(matches) * 38 + 60, 300),
    )


def _show_time_entries(time_df: pd.DataFrame, ref_val: str):
    """Show Time.csv entries matched by InvNo or JobNo."""
    by_inv = time_df[time_df["InvNo"].astype(str).str.strip() == ref_val]
    by_job = time_df[time_df["JobNo"].astype(str).str.strip() == ref_val]
    matches = pd.concat([by_inv, by_job]).drop_duplicates()

    if matches.empty:
        st.info(f"No time entries for Visit Ref # {ref_val}")
        return

    dur = pd.to_numeric(matches["DURATION"], errors="coerce").fillna(0)
    st.markdown(
        f"**{len(matches)} time entries** — Total: **{dur.sum():,.2f} hrs**"
    )

    detail_cols = ["DATE", "EMP", "JOB", "ITEM", "DURATION", "InvNo", "JobNo", "NOTE"]
    existing = [c for c in detail_cols if c in matches.columns]
    st.dataframe(
        matches[existing], use_container_width=True,
        hide_index=True, height=min(len(matches) * 38 + 60, 300),
    )


# ═══════════════════════════════════════════════════════════════════════
# Internal: KPI inspector
# ═══════════════════════════════════════════════════════════════════════

def _kpi_inspector(kpi_name: str, source_df, filters: dict):
    """Content for the KPI lineage popover."""
    info = KPI_LINEAGE.get(kpi_name, {})
    if info:
        st.markdown(f"**Formula:** `{info.get('formula', '—')}`")
        st.markdown(f"**Description:** {info.get('description', '')}")
        st.markdown(f"**Source:** {info.get('source_table', '')}")
        if info.get("filters_applied"):
            st.markdown(f"**Standard filters:** {info['filters_applied']}")

    if filters:
        st.markdown("**Active filter values:**")
        parts = [f"`{k}` = `{v}`" for k, v in filters.items()]
        st.caption(" · ".join(parts))

    if source_df is not None and not source_df.empty:
        st.markdown(f"**Underlying data** — {len(source_df):,} rows")
        st.dataframe(
            source_df.head(100), use_container_width=True,
            hide_index=True, height=200,
        )
    elif source_df is not None:
        st.info("No data for current filters.")


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _fmt(val) -> str:
    """Format a value for display in the inspector."""
    if pd.isna(val):
        return "—"
    if isinstance(val, float):
        if val == float("inf"):
            return "∞"
        if abs(val) >= 1_000:
            return f"{val:,.2f}"
        if val != int(val):
            return f"{val:.4f}"
        return f"{val:.0f}"
    return str(val)


def _special_case_active(row, note: str) -> bool:
    """Return True if a special-case note is relevant for this row."""
    if "TimeByInv = 0" in note and row.get("TimeByInv", 1) == 0:
        return True
    if "Win rows" in note and row.get("WinLossText") != "Win":
        return True
    return False
