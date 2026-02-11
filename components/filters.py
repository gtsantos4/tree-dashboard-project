"""Reusable filter / slicer widgets matching the PowerBI slicers."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config import MONTH_ORDER


def year_filter(years: list[int], key: str = "year", default_idx: int = 0) -> int | None:
    """Horizontal button-style year selector. Returns selected year."""
    if not years:
        return None
    cols = st.columns(len(years))
    selected = st.session_state.get(key, years[default_idx])
    for i, yr in enumerate(years):
        if cols[i].button(str(yr), key=f"{key}_{yr}", use_container_width=True,
                          type="primary" if yr == selected else "secondary"):
            st.session_state[key] = yr
            selected = yr
    return int(selected) if selected else None


def year_select(years: list[int], key: str = "year") -> int | None:
    if not years:
        return None
    return st.selectbox("Year", years, key=key)


def month_filter(key: str = "month") -> list[str]:
    """Month multiselect returning short-month names."""
    return st.multiselect("Month", MONTH_ORDER, default=[], key=key)


def month_select(key: str = "month") -> str | None:
    return st.selectbox("Month", ["All"] + MONTH_ORDER, key=key)


def operation_filter(operations: list[str], key: str = "operation") -> str | None:
    options = ["All"] + operations
    return st.selectbox("Operation", options, key=key)


def crew_leader_filter(leaders: list[str], key: str = "crew_leader") -> str | None:
    options = ["All"] + leaders
    return st.selectbox("Crew Leader", options, key=key)


def sales_rep_filter(reps: list[str], key: str = "sales_rep") -> str | None:
    options = ["All"] + reps
    return st.selectbox("Sales Reps", options, key=key)


def date_range_filter(df: pd.DataFrame, col: str, key: str = "date_range"):
    """Return (start, end) date tuple from a date range picker."""
    valid = df[col].dropna()
    if valid.empty:
        return None, None
    mn, mx = valid.min().date(), valid.max().date()
    vals = st.date_input("Date Range", value=(mn, mx), min_value=mn, max_value=mx, key=key)
    if isinstance(vals, tuple) and len(vals) == 2:
        return vals
    return mn, mx


# ── Apply helpers ────────────────────────────────────────────────────

def apply_year(df: pd.DataFrame, year, col: str = "Year") -> pd.DataFrame:
    if year is None:
        return df
    return df[df[col] == year]


def apply_months(df: pd.DataFrame, months: list[str], col: str = "MonthShort") -> pd.DataFrame:
    if not months:
        return df
    return df[df[col].isin(months)]


def apply_operation(df: pd.DataFrame, op: str | None, col: str = "Operation") -> pd.DataFrame:
    if not op or op == "All":
        return df
    return df[df[col] == op]


def apply_crew_leader(df: pd.DataFrame, cl: str | None, col: str = "Crew Leader") -> pd.DataFrame:
    if not cl or cl == "All":
        return df
    return df[df[col] == cl]


def apply_sales_rep(df: pd.DataFrame, rep: str | None, col: str = "Sales Reps") -> pd.DataFrame:
    if not rep or rep == "All":
        return df
    return df[df[col] == rep]
