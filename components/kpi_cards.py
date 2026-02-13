"""KPI cards, gauges, and rating displays — Van Yahres design system."""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from config import (
    VY_RED, BORDER_COLOR, MEDIUM_GRAY, SIDEBAR_DARK,
    WIN_COLOR, LOSS_COLOR, STAR_GOLD, BOX_DARK_RED,
)

# Accent color map for KPI cards
_ACCENT_COLORS = {
    "win": WIN_COLOR,
    "loss": LOSS_COLOR,
    "amber": "#D97706",
    None: VY_RED,
}
_ACCENT_BG = {
    "win": "#ECFDF5",
    "loss": "#FEF2F2",
    "amber": "#FFFBEB",
    None: "#F3F4F6",
}


def metric_card(label: str, value, prefix: str = "", suffix: str = ""):
    """Large styled metric card with Van Yahres 3px red top accent."""
    formatted = (
        f"{prefix}{value:,.0f}{suffix}"
        if isinstance(value, (int, float))
        else f"{prefix}{value}{suffix}"
    )
    st.markdown(
        f"""<div style="background:#fff; border:1px solid {BORDER_COLOR};
        border-radius:16px; border-top:3px solid {VY_RED};
        padding:20px; text-align:center;
        box-shadow:0 1px 3px rgba(0,0,0,0.04);">
        <div style="font-size:12px; text-transform:uppercase; letter-spacing:0.5px;
             color:{MEDIUM_GRAY}; font-weight:600;">{label}</div>
        <div style="font-size:32px; font-weight:700; color:{SIDEBAR_DARK};
             margin-top:8px;">{formatted}</div></div>""",
        unsafe_allow_html=True,
    )


def metric_card_v2(
    label: str,
    value,
    *,
    prefix: str = "",
    suffix: str = "",
    accent: str | None = None,
    delta: str | None = None,
    icon: str | None = None,
    extra_html: str | None = None,
):
    """Enhanced metric card with optional accent, delta, icon, and extra content.

    accent: "win"|"loss"|"amber"|None — changes the 3px top border color.
    delta:  small text below value (e.g. "↑ 154 Wins / 95 Losses").
    icon:   emoji shown in a small colored circle top-right.
    extra_html: arbitrary HTML rendered below the value (progress bars, ratings).
    """
    border_color = _ACCENT_COLORS.get(accent, VY_RED)
    formatted = (
        f"{prefix}{value:,.0f}{suffix}"
        if isinstance(value, (int, float))
        else f"{prefix}{value}{suffix}"
    )

    # Icon HTML — top-right corner
    icon_html = ""
    if icon:
        icon_bg = _ACCENT_BG.get(accent, "#F3F4F6")
        icon_html = (
            f'<div class="vy-kpi-icon" style="position:absolute;top:16px;right:16px;'
            f'width:36px;height:36px;border-radius:10px;background:{icon_bg};'
            f'display:flex;align-items:center;justify-content:center;font-size:16px;">'
            f'{icon}</div>'
        )

    # Delta HTML
    delta_html = ""
    if delta:
        delta_color = _ACCENT_COLORS.get(accent, MEDIUM_GRAY)
        delta_html = (
            f'<div style="font-size:12px;margin-top:4px;font-weight:500;'
            f'color:{delta_color};">{delta}</div>'
        )

    # Extra HTML (progress bars, ratings, etc.)
    extra = extra_html or ""

    st.markdown(
        f'<div class="vy-kpi-card" style="background:#fff;border:1px solid {BORDER_COLOR};'
        f'border-radius:12px;border-top:3px solid {border_color};'
        f'padding:20px;text-align:center;position:relative;'
        f'overflow:hidden;min-height:150px;'
        f'display:flex;flex-direction:column;justify-content:center;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.03);">'
        f'{icon_html}'
        f'<div class="vy-kpi-label" style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;'
        f'color:{MEDIUM_GRAY};font-weight:600;margin-bottom:8px;text-align:center;">{label}</div>'
        f'<div class="vy-kpi-value" style="font-size:28px;font-weight:700;color:{SIDEBAR_DARK};">'
        f'{formatted}</div>'
        f'{delta_html}'
        f'<div class="vy-kpi-extra" style="overflow:hidden;max-width:100%;">{extra}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items: list[dict], cols: int | None = None):
    """Render a row of KPI cards in a grid.

    items: list of dicts with keys matching metric_card_v2 params:
        label, value, prefix, suffix, accent, delta, icon, extra_html
    cols: number of columns (defaults to len(items)).
    """
    n = cols or len(items)
    columns = st.columns(n)
    for i, item in enumerate(items):
        with columns[i % n]:
            metric_card_v2(
                item["label"],
                item["value"],
                prefix=item.get("prefix", ""),
                suffix=item.get("suffix", ""),
                accent=item.get("accent"),
                delta=item.get("delta"),
                icon=item.get("icon"),
                extra_html=item.get("extra_html"),
            )


def progress_bar(value: float, max_val: float = 100, color: str | None = None) -> str:
    """Return HTML string for an inline progress bar.

    Used inside KPI cards (QC grade) and table cells (% to Goal).
    """
    pct = min(value / max_val * 100, 100) if max_val > 0 else 0
    if color is None:
        if pct >= 100:
            color = WIN_COLOR
        elif pct >= 90:
            color = "#D97706"  # amber
        else:
            color = LOSS_COLOR
    return (
        f'<div style="height:6px;background:{BORDER_COLOR};border-radius:3px;margin-top:8px;">'
        f'<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:3px;"></div>'
        f'</div>'
    )


def count_card(label: str, count: int):
    metric_card(label, count)


def star_rating(count: int, max_stars: int = 10) -> str:
    """Return HTML string of gold stars that wraps within its container."""
    filled = min(count, max_stars)
    stars = "★" * filled + "☆" * (max_stars - filled)
    return (
        f'<span style="color:{STAR_GOLD};font-size:clamp(10px,2.5vw,18px);'
        f'letter-spacing:1px;word-break:break-all;line-height:1.4;">{stars}</span>'
    )


def box_rating(count: int, max_boxes: int = 10) -> str:
    """Return HTML string of colored boxes that wraps within its container."""
    filled = min(count, max_boxes)
    boxes = (
        f'<span style="color:{BOX_DARK_RED};">■</span>' * filled
        + '<span style="color:#ccc;">■</span>' * (max_boxes - filled)
    )
    return (
        f'<span style="font-size:clamp(10px,2.5vw,18px);letter-spacing:1px;'
        f'word-break:break-all;line-height:1.4;">{boxes}</span>'
    )


def gauge_chart(value: float, title: str = "", min_val: float = 0, max_val: float = 100) -> go.Figure:
    """Plotly gauge chart with Van Yahres colors."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 28}},
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickwidth": 1},
            "bar": {"color": WIN_COLOR},
            "bgcolor": "#eee",
            "steps": [
                {"range": [min_val, max_val * 0.6], "color": "#f5f5f5"},
                {"range": [max_val * 0.6, max_val * 0.8], "color": "#d1fae5"},
                {"range": [max_val * 0.8, max_val], "color": "#a7f3d0"},
            ],
        },
    ))
    fig.update_layout(
        height=200, margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def winloss_donut(win_count: int, loss_count: int) -> go.Figure:
    """Donut chart for Win/Loss split."""
    fig = go.Figure(go.Pie(
        values=[win_count, loss_count],
        labels=["Win", "Loss"],
        hole=0.55,
        marker=dict(colors=[WIN_COLOR, LOSS_COLOR]),
        textinfo="label+value+percent",
        textposition="inside",
        textfont=dict(size=13),
    ))
    fig.update_layout(
        title=dict(text="Win / Loss", font=dict(size=14)),
        height=280, margin=dict(l=10, r=10, t=40, b=10),
        showlegend=True,
        legend=dict(orientation="h", y=-0.05),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
