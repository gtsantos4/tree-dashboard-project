"""Conditionally-formatted tables and pivot tables — Van Yahres design."""
from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
import streamlit as st

from config import (
    VY_RED, WIN_COLOR, LOSS_COLOR, WIN_BG, LOSS_BG, MONTH_ORDER,
    SIDEBAR_DARK, BORDER_COLOR, MEDIUM_GRAY,
)


def _wl_row_color(row, wl_col: str = "WinLoss"):
    """Styler function: green tint for Win, red tint for Loss."""
    val = row.get(wl_col, row.get("WinLossText", ""))
    if val == "Win":
        return [f"background-color: {WIN_BG};"] * len(row)
    elif val == "Loss":
        return [f"background-color: {LOSS_BG};"] * len(row)
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


# ═══════════════════════════════════════════════════════════════════════
# Wireframe UI helpers — totals bar, badges, cards, section dividers
# ═══════════════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = ""):
    """Render a styled page header matching the wireframe design.

    Shows title as a large heading with an optional subtitle underneath.
    CSS classes ``vy-page-title`` and ``vy-page-subtitle`` allow
    responsive media queries to scale the text.
    """
    sub_html = ""
    if subtitle:
        sub_html = (
            f'<div class="vy-page-subtitle" style="font-size:13px;color:{MEDIUM_GRAY};'
            f'margin-top:2px;">{subtitle}</div>'
        )
    st.markdown(
        f'<div class="vy-page-header" style="margin-bottom:20px;">'
        f'<h2 class="vy-page-title" style="font-size:22px;font-weight:700;'
        f'color:#111827;margin:0;padding:0;line-height:1.3;">{title}</h2>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


@contextmanager
def filter_container():
    """Context manager wrapping filter widgets in a styled card bar.

    Matches the wireframe filter-bar pattern: white bg, border, shadow, padding.
    White background applied via CSS targeting inline border styles in app.py.
    """
    c = st.container(border=True)
    with c:
        yield c

def totals_bar(items: list[dict]):
    """Dark totals bar rendered below a table.

    items: [{"label": "Total Revenue", "value": "$482,350"}, ...]
    Renders as a dark horizontal bar with stacked label/value pairs.
    """
    parts = []
    for it in items:
        color = it.get("color", "white")
        parts.append(
            f'<div style="display:flex;flex-direction:column;">'
            f'<span style="font-size:10px;text-transform:uppercase;opacity:0.6;'
            f'letter-spacing:0.5px;">{it["label"]}</span>'
            f'<span style="font-weight:700;font-size:15px;color:{color};">'
            f'{it["value"]}</span></div>'
        )
    inner = "".join(parts)
    st.markdown(
        f'<div class="vy-totals-bar" style="background:{SIDEBAR_DARK};color:white;'
        f'padding:12px 20px;display:flex;gap:32px;font-size:13px;'
        f'border-radius:0 0 12px 12px;margin-bottom:20px;">{inner}</div>',
        unsafe_allow_html=True,
    )


def winloss_badge(text: str) -> str:
    """Return HTML for a colored badge pill.

    Win/Reviewed → green, Loss/Callback → red, Pending → amber,
    Compliment/QC → blue, other → gray.
    """
    t = (text or "").strip()
    tl = t.lower()
    if tl in ("win", "reviewed"):
        bg, fg = WIN_BG, WIN_COLOR
    elif tl in ("loss", "callback", "call back"):
        bg, fg = LOSS_BG, LOSS_COLOR
    elif tl in ("pending",):
        bg, fg = "#FFFBEB", "#D97706"
    elif tl in ("compliment", "qc", "quality control"):
        bg, fg = "#EFF6FF", "#2563EB"
    else:
        bg, fg = "#F3F4F6", MEDIUM_GRAY
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;'
        f'font-size:11px;font-weight:600;background:{bg};color:{fg};">{t}</span>'
    )


@contextmanager
def card_container(title: str | None = None):
    """Context manager that wraps content in a bordered card with optional header.

    Injects a hidden marker div so CSS :has(.vy-card-marker) can target it.

    Usage:
        with card_container("Damage Detail"):
            st.dataframe(df, ...)
    """
    c = st.container(border=True)
    with c:
        if title:
            st.markdown(
                f'<div style="font-size:14px;font-weight:600;color:#374151;'
                f'padding-bottom:8px;border-bottom:1px solid {BORDER_COLOR};'
                f'margin-bottom:8px;">{title}</div>',
                unsafe_allow_html=True,
            )
        yield c


def section_divider(title: str):
    """Section header with a horizontal line extending to the right."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'margin:16px 0 16px 0;">'
        f'<span style="font-size:16px;font-weight:600;color:#374151;'
        f'white-space:nowrap;">{title}</span>'
        f'<div style="flex:1;height:1px;background:{BORDER_COLOR};"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def crew_mini_cards(data: list[dict]):
    """Grid of mini-cards for crew leader breakdowns.

    data: [{"name": "Josh R", "value": "$8,200", "sub": "9 incidents"}, ...]
    Renders as a 2-column grid of compact cards.
    """
    cards_html = ""
    for d in data:
        cards_html += (
            f'<div style="padding:12px;border-radius:8px;border:1px solid {BORDER_COLOR};'
            f'background:#fff;">'
            f'<div style="font-size:12px;font-weight:600;color:#374151;">{d["name"]}</div>'
            f'<div style="font-size:18px;font-weight:700;color:#111827;margin-top:2px;">'
            f'{d["value"]}</div>'
            f'<div style="font-size:11px;color:{MEDIUM_GRAY};">{d.get("sub", "")}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div class="vy-crew-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">'
        f'{cards_html}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
# Raw-HTML card system — white background baked directly into the markup
# ═══════════════════════════════════════════════════════════════════════

def _fmt_cell(val):
    """Format a single cell value for HTML display."""
    if pd.isna(val):
        return ""
    if isinstance(val, float):
        if abs(val) >= 1000:
            return f"{val:,.2f}"
        return f"{val:.2f}"
    return str(val)


def styled_table_html(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    height: int = 400,
    formatters: dict | None = None,
) -> str:
    """Convert a DataFrame to a styled HTML table string.

    Returns raw HTML (not rendered). Pass the result to ``html_card()``.

    Parameters
    ----------
    df : DataFrame to render
    columns : optional subset / ordering of columns
    height : max-height in px (scrollable)
    formatters : {col_name: callable} for custom formatting
    """
    if columns:
        df = df[[c for c in columns if c in df.columns]]

    fmts = formatters or {}

    # Header
    header_cells = "".join(
        f'<th style="padding:8px 12px;text-align:left;font-size:12px;'
        f'font-weight:600;text-transform:uppercase;letter-spacing:0.3px;'
        f'white-space:nowrap;position:sticky;top:0;background:{VY_RED};'
        f'color:white;z-index:1;">{col}</th>'
        for col in df.columns
    )

    # Rows
    rows_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        bg = "#fff" if i % 2 == 0 else "#F9FAFB"
        cells = ""
        for col in df.columns:
            val = row[col]
            text = fmts[col](val) if col in fmts else _fmt_cell(val)
            cells += (
                f'<td style="padding:8px 12px;font-size:13px;'
                f'border-bottom:1px solid {BORDER_COLOR};">{text}</td>'
            )
        rows_html += f'<tr style="background:{bg};">{cells}</tr>'

    return (
        f'<div style="max-height:{height}px;overflow-y:auto;'
        f'border-radius:8px;border:1px solid {BORDER_COLOR};">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>'
    )


def totals_bar_html(items: list[dict]) -> str:
    """Return HTML string for a dark totals bar (does NOT render).

    Pass the result as an argument to ``html_card()``.
    """
    parts = []
    for it in items:
        color = it.get("color", "white")
        parts.append(
            f'<div style="display:flex;flex-direction:column;">'
            f'<span style="font-size:10px;text-transform:uppercase;opacity:0.6;'
            f'letter-spacing:0.5px;">{it["label"]}</span>'
            f'<span style="font-weight:700;font-size:15px;color:{color};">'
            f'{it["value"]}</span></div>'
        )
    inner = "".join(parts)
    return (
        f'<div class="vy-totals-bar" style="background:{SIDEBAR_DARK};color:white;'
        f'padding:12px 20px;display:flex;gap:32px;font-size:13px;'
        f'border-radius:0 0 12px 12px;'
        f'margin:12px -16px -16px -16px;">{inner}</div>'
    )


def html_card(title: str | None = None, *content_html: str):
    """Render a white card with baked-in background, border, and content.

    All content is raw HTML passed as positional arguments.
    The entire card is a single ``st.markdown`` call — no Streamlit
    container styling issues.

    Usage::

        html_card(
            "Compliments",
            styled_table_html(df, columns),
            totals_bar_html([{"label": "Total", "value": "42"}]),
        )
    """
    title_part = ""
    if title:
        title_part = (
            f'<div style="font-size:14px;font-weight:600;color:#374151;'
            f'padding-bottom:8px;border-bottom:1px solid {BORDER_COLOR};'
            f'margin-bottom:12px;">{title}</div>'
        )
    body = "".join(content_html)
    st.markdown(
        f'<div style="background:#fff;border:1px solid {BORDER_COLOR};'
        f'border-radius:12px;padding:16px;margin-bottom:16px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'{title_part}{body}</div>',
        unsafe_allow_html=True,
    )
