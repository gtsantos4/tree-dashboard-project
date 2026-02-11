"""
Power Query M equivalent transformations.

Each build_* function mirrors one or more tables from the PBIX data model.
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser

import numpy as np
import pandas as pd
import streamlit as st

from config import STAT_ITEMS, DAMAGE_ITEM, MONTH_ORDER


# ── Utility helpers ──────────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    """Tiny HTML→text converter."""
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
    def handle_data(self, d: str):
        self._parts.append(d)
    def get_text(self) -> str:
        return " ".join(self._parts).strip()


def strip_html(val: str) -> str:
    if not val or "<" not in val:
        return val
    s = _HTMLStripper()
    s.feed(val)
    return s.get_text()


def parse_review_json(val: str) -> str:
    """Turn '[\"\", \"Follow Up Complete\"]' → 'Follow Up Complete'."""
    if not val:
        return ""
    try:
        items = json.loads(val.replace("'", '"'))
        if isinstance(items, list):
            return ", ".join(i for i in items if i).strip(", ") or ""
        return str(items)
    except (json.JSONDecodeError, TypeError):
        return val


def _safe_float(s: str) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_date(s: str) -> pd.Timestamp | pd.NaT:
    if not s or s.strip() == "" or s.strip() == "-":
        return pd.NaT
    try:
        return pd.to_datetime(s, format="mixed", dayfirst=False)
    except Exception:
        return pd.NaT


# ── Core transform: SO_LineItems ─────────────────────────────────────

@st.cache_data(show_spinner="Transforming line items …")
def build_so_line_items(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean and type the raw appended CSV data."""
    df = raw.copy()

    # Numeric columns
    for col in ["Qty", "Unit Cost", "Unit Markup", "Unit Total", "Line Total"]:
        df[col] = df[col].apply(_safe_float)

    # Boolean columns
    for col in ["Billable", "Actual"]:
        df[col] = df[col].str.upper().eq("TRUE")

    # Date columns
    date_cols = [
        "Line Items Created Date", "Line Items Updated Date",
        "Visits Created Date", "Visits Updated Date",
        "Accepted Date", "Scheduled Date", "Approved Date", "Invoice Date",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(_parse_date)

    # Clean text
    for col in ["Internal Notes", "Client Notes", "Crew Notes"]:
        if col in df.columns:
            df[col] = df[col].apply(strip_html)

    # Parse Review JSON
    if "Review" in df.columns:
        df["Review"] = df["Review"].apply(parse_review_json)

    # Extract Crew Leader from crews field (first name)
    if "crews" in df.columns:
        df["Crew Leader"] = df["crews"].str.strip()

    # Derived date parts from Approved Date
    valid_appr = df["Approved Date"].notna()
    df.loc[valid_appr, "Year"] = df.loc[valid_appr, "Approved Date"].dt.year.astype(int)
    df.loc[valid_appr, "MonthNum"] = df.loc[valid_appr, "Approved Date"].dt.month.astype(int)
    df.loc[valid_appr, "MonthShort"] = df.loc[valid_appr, "Approved Date"].dt.strftime("%b")

    return df


# ── Stats table ──────────────────────────────────────────────────────

@st.cache_data(show_spinner="Building stats table …")
def build_stats(so: pd.DataFrame, qc_df: pd.DataFrame) -> pd.DataFrame:
    """Filter SO_LineItems to stat-tracking items and add QC grade info."""
    df = so[so["Item Name"].isin(STAT_ITEMS)].copy()

    # For Quality Control items, map Qty → QC percentage
    # The QC lookup: Grade → Percent  (A+ = 1.0, A = 0.95, …)
    # In the data, Qty on QC items IS the percentage (0-1 range already stored as decimal)
    # We'll store Percent from the Qty for QC items, and 1.0 for others
    df["Percent"] = np.where(
        df["Item Name"] == "Quality Control",
        df["Qty"],
        np.nan,
    )

    # Map percent → letter grade via the QC scale
    if not qc_df.empty:
        grade_map = qc_df.sort_values("Percent", ascending=False)
        def _to_grade(pct):
            if pd.isna(pct):
                return ""
            for _, row in grade_map.iterrows():
                if pct >= row["Percent"]:
                    return row["Grade"]
            return grade_map.iloc[-1]["Grade"]  # lowest grade
        df["QC Grade"] = df["Percent"].apply(_to_grade)
    else:
        df["QC Grade"] = ""

    return df


# ── InvAmts (invoice-level fact table) ───────────────────────────────

@st.cache_data(show_spinner="Building invoice amounts …")
def build_inv_amts(so: pd.DataFrame, time_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate SO_LineItems to one row per invoiced visit."""
    # Only records with an invoice date
    invoiced = so[so["Invoice Date"].notna()].copy()

    # Filter to billable items for totals
    billable = invoiced[invoiced["Billable"]].copy()

    # Aggregate at visit level
    agg = billable.groupby("Visit Ref #", as_index=False).agg(
        Client=("Client", "first"),
        Operation=("Operation", "first"),
        Crew_Leader=("Crew Leader", "first"),
        Sales_Reps=("Sales Reps", "first"),
        InvoiceDate=("Invoice Date", "first"),
        ApprovedDate=("Approved Date", "first"),
        InvTotal=("Line Total", "sum"),
        Status=("Status", "first"),
    )
    agg.rename(columns={"Crew_Leader": "Crew Leader", "Sales_Reps": "Sales Reps"}, inplace=True)

    # Compute estimated hours from labor line items (Qty on Labor category)
    labor = billable[billable["Item category"] == "Labor"]
    hrs_est = labor.groupby("Visit Ref #", as_index=False)["Qty"].sum().rename(columns={"Qty": "HoursEst"})
    agg = agg.merge(hrs_est, on="Visit Ref #", how="left")
    agg["HoursEst"] = agg["HoursEst"].fillna(0)

    # Discounts (negative line totals or Discount category)
    disc = billable[billable["Item category"] == "Discount"]
    disc_agg = disc.groupby("Visit Ref #", as_index=False)["Line Total"].sum().rename(columns={"Line Total": "Discount"})
    agg = agg.merge(disc_agg, on="Visit Ref #", how="left")
    agg["Discount"] = agg["Discount"].fillna(0)

    # Material costs
    mats = billable[billable["Item category"] == "Material"]
    mat_agg = mats.groupby("Visit Ref #", as_index=False)["Line Total"].sum().rename(columns={"Line Total": "Costs"})
    agg = agg.merge(mat_agg, on="Visit Ref #", how="left")
    agg["Costs"] = agg["Costs"].fillna(0)

    # Actual hours from Time.csv (keyed by InvNo or JobNo)
    if not time_df.empty:
        tdf = time_df.copy()
        # Ensure DURATION is numeric (raw CSV loads as string)
        tdf["DURATION"] = pd.to_numeric(tdf["DURATION"], errors="coerce").fillna(0)
        time_by_inv = (
            tdf[tdf["InvNo"].astype(str).str.strip() != ""]
            .groupby("InvNo", as_index=False)["DURATION"]
            .sum()
            .rename(columns={"InvNo": "Visit Ref #", "DURATION": "TimeByInv"})
        )
        # Also aggregate by JobNo for visits without direct InvNo match
        time_by_job = (
            tdf[tdf["JobNo"].astype(str).str.strip() != ""]
            .groupby("JobNo", as_index=False)["DURATION"]
            .sum()
            .rename(columns={"JobNo": "Visit Ref #", "DURATION": "TimeByJob"})
        )
        agg = agg.merge(time_by_inv, on="Visit Ref #", how="left")
        agg = agg.merge(time_by_job, on="Visit Ref #", how="left")
        agg["TimeByInv"] = agg["TimeByInv"].fillna(agg["TimeByJob"]).fillna(0)
        agg.drop(columns=["TimeByJob"], inplace=True, errors="ignore")
    else:
        agg["TimeByInv"] = 0

    # Derived metrics
    agg["HrsRatio"] = np.where(
        agg["TimeByInv"] > 0,
        agg["HoursEst"] / agg["TimeByInv"],
        np.inf,
    )
    agg["WinLossText"] = np.where(agg["HrsRatio"] >= 1.0, "Win", "Loss")
    # Jobs with no time data → label as Win (estimated only)
    agg.loc[agg["TimeByInv"] == 0, "WinLossText"] = "Win"

    agg["NetInv"] = agg["InvTotal"] - agg["Costs"]
    agg["EPH"] = np.where(agg["TimeByInv"] > 0, agg["InvTotal"] / agg["TimeByInv"], 0)

    # Date parts
    valid = agg["InvoiceDate"].notna()
    agg.loc[valid, "Year"] = agg.loc[valid, "InvoiceDate"].dt.year.astype(int)
    agg.loc[valid, "MonthNum"] = agg.loc[valid, "InvoiceDate"].dt.month.astype(int)
    agg.loc[valid, "MonthShort"] = agg.loc[valid, "InvoiceDate"].dt.strftime("%b")
    agg.loc[valid, "MonthFull"] = agg.loc[valid, "InvoiceDate"].dt.strftime("%B")

    return agg


# ── Time detail table ────────────────────────────────────────────────

@st.cache_data(show_spinner="Building time detail …")
def build_time_detail(raw_time: pd.DataFrame) -> pd.DataFrame:
    """Clean the Time.csv export for the TimeDetail page."""
    if raw_time.empty:
        return raw_time
    df = raw_time.copy()
    df["DURATION"] = df["DURATION"].apply(_safe_float)
    for col in ["DATE", "WeekStart", "WeekEnd"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_date)

    # Rename for display compatibility
    df.rename(columns={"EMP": "Title", "JOB": "Customer"}, inplace=True)

    # Derive Operation from ITEM
    phc_items = {
        "Air Spade", "Consult", "Digital Tree Inventory", "Inject",
        "Nutrients", "Nutrients - Drench", "Plant Health Care",
        "Soil Injected Nutrients", "Spray",
    }
    tree_items = {"Emergency", "Stump Grinding", "Tree Work", "Training"}
    def _op(item):
        if item in phc_items:
            return "PHC"
        if item in tree_items:
            return "Trees"
        return ""
    df["Operation"] = df["ITEM"].apply(_op)

    # Boolean AddOn
    df["AddOn"] = df["AddOn"].str.upper().eq("TRUE")

    return df


# ── Damage table ─────────────────────────────────────────────────────

def build_damage(so: pd.DataFrame) -> pd.DataFrame:
    """Filter to Damage Repair items."""
    return so[so["Item Name"] == DAMAGE_ITEM].copy()


# ── Notes table ──────────────────────────────────────────────────────

def build_notes(so: pd.DataFrame) -> pd.DataFrame:
    """Filter to records with a non-empty Review value."""
    df = so[so["Review"].str.strip() != ""].copy()
    return df


# ── Reference / lookup tables ────────────────────────────────────────

def build_qc_scale(sheets: dict) -> pd.DataFrame:
    df = sheets.get("QC", pd.DataFrame())
    if not df.empty:
        df["Percent"] = pd.to_numeric(df["Percent"], errors="coerce")
    return df


def build_cb_scale(sheets: dict) -> pd.DataFrame:
    df = sheets.get("CB", pd.DataFrame())
    return df


def build_compliment_scale(sheets: dict) -> pd.DataFrame:
    df = sheets.get("Compliments", pd.DataFrame())
    return df


def build_scheduling_goals(sheets: dict) -> pd.DataFrame:
    df = sheets.get("EstHrsGoals", pd.DataFrame())
    return df


def build_goals_summary(sheets: dict) -> pd.DataFrame:
    df = sheets.get("EstHrsGoals (2)", pd.DataFrame())
    return df


def build_misc_inputs(goals_df: pd.DataFrame) -> pd.DataFrame:
    """Reshape scheduling goals into the MiscInputs format for Est v Actual."""
    if goals_df.empty:
        return goals_df
    sched = goals_df[goals_df["Type"] == "Scheduling"].copy()
    # Melt interval columns into rows
    rows = []
    for _, r in sched.iterrows():
        op = r.get("Operation", "All")
        for interval in ["Day", "Week", "Month", "Year"]:
            val = r.get(interval, 0)
            rows.append({
                "Title": f"{interval}lySchedulingGoal",
                "Operation": op,
                "NumericalValue1": float(val) if val else 0,
            })
    return pd.DataFrame(rows)


# ── Dimension tables ─────────────────────────────────────────────────

def build_dim_dates(so: pd.DataFrame) -> pd.DataFrame:
    """Generate a date dimension from Approved Date range."""
    dates = so["Approved Date"].dropna()
    if dates.empty:
        return pd.DataFrame()
    start = dates.min().normalize()
    end = dates.max().normalize()
    idx = pd.date_range(start, end, freq="D")
    dim = pd.DataFrame({"Date": idx})
    dim["Year"] = dim["Date"].dt.year
    dim["MonthNum"] = dim["Date"].dt.month
    dim["MonthShort"] = dim["Date"].dt.strftime("%b")
    dim["MonthFull"] = dim["Date"].dt.strftime("%B")
    dim["Week"] = dim["Date"].dt.isocalendar().week.astype(int)
    dim["Quarter"] = dim["Date"].dt.quarter
    return dim


def get_crew_leaders(so: pd.DataFrame) -> list[str]:
    return sorted(so["Crew Leader"].dropna().unique().tolist())


def get_operations(so: pd.DataFrame) -> list[str]:
    ops = so["Operation"].dropna().unique().tolist()
    return sorted([o for o in ops if o])


def get_years(so: pd.DataFrame) -> list[int]:
    yrs = so.loc[so["Year"].notna(), "Year"].unique()
    return sorted([int(y) for y in yrs], reverse=True)


def get_sales_reps(so: pd.DataFrame) -> list[str]:
    reps = so["Sales Reps"].dropna().unique().tolist()
    return sorted([r for r in reps if r])
