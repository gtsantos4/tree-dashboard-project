"""KPI cards, gauges, and rating displays."""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from config import WIN_COLOR, LOSS_COLOR, STAR_GOLD, BOX_DARK_RED, ACCENT_BLUE


def metric_card(label: str, value, prefix: str = "", suffix: str = ""):
    """Large styled metric card."""
    formatted = f"{prefix}{value:,.0f}{suffix}" if isinstance(value, (int, float)) else f"{prefix}{value}{suffix}"
    st.markdown(
        f"""<div style="background:#fff;border:1px solid #ddd;border-radius:8px;
        padding:16px 20px;text-align:center;">
        <div style="font-size:14px;color:#666;font-weight:600;">{label}</div>
        <div style="font-size:36px;font-weight:700;color:{ACCENT_BLUE};margin-top:4px;">
        {formatted}</div></div>""",
        unsafe_allow_html=True,
    )


def count_card(label: str, count: int):
    metric_card(label, count)


def star_rating(count: int, max_stars: int = 10) -> str:
    """Return HTML string of gold stars."""
    filled = min(count, max_stars)
    stars = "★" * filled + "☆" * (max_stars - filled)
    return f'<span style="color:{STAR_GOLD};font-size:18px;letter-spacing:2px;">{stars}</span>'


def box_rating(count: int, max_boxes: int = 10) -> str:
    """Return HTML string of colored boxes (dark-red filled, gray empty)."""
    filled = min(count, max_boxes)
    boxes = (
        f'<span style="color:{BOX_DARK_RED};">■</span>' * filled
        + '<span style="color:#ccc;">■</span>' * (max_boxes - filled)
    )
    return f'<span style="font-size:18px;letter-spacing:2px;">{boxes}</span>'


def gauge_chart(value: float, title: str = "", min_val: float = 0, max_val: float = 100) -> go.Figure:
    """Plotly gauge chart matching PowerBI style."""
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
                {"range": [max_val * 0.6, max_val * 0.8], "color": "#e8f5e9"},
                {"range": [max_val * 0.8, max_val], "color": "#c8e6c9"},
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
        title=dict(text="Win Loss", font=dict(size=14)),
        height=280, margin=dict(l=10, r=10, t=40, b=10),
        showlegend=True,
        legend=dict(orientation="h", y=-0.05),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
