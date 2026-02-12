"""Load and cache raw data from CSV / Excel files."""
import glob
import os

import pandas as pd
import streamlit as st
import openpyxl

from config import DATA_DIR


@st.cache_data(show_spinner="Loading line-item CSVs …")
def load_all_line_items() -> pd.DataFrame:
    """Append every LineItems_SO_*.csv into one DataFrame."""
    pattern = os.path.join(DATA_DIR, "LineItems_SO_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        st.error(f"No LineItems CSVs found in {DATA_DIR}")
        return pd.DataFrame()
    frames = []
    for fp in files:
        df = pd.read_csv(fp, dtype=str, keep_default_na=False)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


@st.cache_data(show_spinner="Loading crew-stat reference tables …")
def load_crew_stat_lists() -> dict[str, pd.DataFrame]:
    """Read every sheet from CrewStatLists.xlsx into a dict of DataFrames."""
    path = os.path.join(DATA_DIR, "CrewStatLists.xlsx")
    xls = pd.ExcelFile(path, engine="openpyxl")
    return {name: xls.parse(name) for name in xls.sheet_names}


@st.cache_data(show_spinner="Loading time-tracking data …")
def load_time_data() -> pd.DataFrame:
    """Load Time.csv (time-tracking export)."""
    path = os.path.join(DATA_DIR, "Time.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
