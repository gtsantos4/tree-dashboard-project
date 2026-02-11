"""Conditionally-formatted tables and pivot tables."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import WIN_COLOR, LOSS_COLOR, MONTH_ORDER


def _wl_row_color(row, wl_col: str = "WinLoss"):
    """Styler function: green for Win, red for Loss."""
    val = row.get(wl_col, row.get("WinLossText", ""))
    if val == "Win":
        return [f"background-color: rgba(46,125,50,0.12);"] * len(row)
    elif val == "Loss":
        return [f"background-color: rgba(198,40,40,0.12);"] * len(row)
    return [""] * len(row)


def winloss_table(
    df: pd.DataFrame,
    wl_col: str = "WinLossText",
    height: int | None = 500,
):
    """Display a dataframe with Win/Loss row coloring."""
    display_cols = [c for c in df.columns if c != "MonthNum"]
    styled = (
        df[display_cols]
        .style
        .apply(_wl_row_color, wl_col=wl_col, axis=1)
        .format(precision=2, na_rep="")
    )
    st.dataframe(styled, use_container_width=True, height=height)


def pivot_monthly(
    df: pd.DataFrame,
    index_col: str,
    value_col: str,
    agg_func: str = "sum",
    show_total: bool = True,
    fmt: str = ",.0f",
) -> pd.DataFrame:
    """Create a Month-as-columns pivot with optional Total column."""
    if df.empty:
        return df
    pv = pd.pivot_table(
        df, index=index_col, columns="MonthShort", values=value_col,
        aggfunc=agg_func, fill_value=0,
    )
    # Reorder months
    ordered = [m for m in MONTH_ORDER if m in pv.columns]
    pv = pv[ordered]
    if show_total:
        pv["Total"] = pv.sum(axis=1)
    return pv


def show_reference_table(df: pd.DataFrame, title: str = ""):
    """Compact reference table display."""
    if title:
        st.markdown(f"**{title}**")
    st.dataframe(df, use_container_width=True, hide_index=True, height=min(len(df) * 38 + 40, 350))


def format_currency(val):
    if pd.isna(val):
        return ""
    return f"${val:,.2f}"


def format_pct(val):
    if pd.isna(val):
        return ""
    return f"{val:.0%}"


def format_hours(val):
    if pd.isna(val):
        return ""
    return f"{val:,.1f}"
