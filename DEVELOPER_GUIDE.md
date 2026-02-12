# Developer Guide — Tree Care Operations Dashboard

A practical reference for making changes to this Streamlit dashboard. Written for someone coming from JavaScript.

---

## File Structure at a Glance

```
tree-dashboard-project/
├── app.py                  ← Entry point. Global CSS + navigation menu.
├── config.py               ← Colors, constants, month lists. Change colors here.
├── requirements.txt        ← Python packages needed to run the app.
│
├── data/
│   ├── loader.py           ← Reads CSV/Excel files from sample-data/
│   ├── transforms.py       ← Cleans and aggregates data (the "business logic")
│   └── lineage.py          ← Metadata: describes how every number is calculated
│
├── components/
│   ├── filters.py          ← Dropdown/multiselect filter widgets
│   ├── kpi_cards.py        ← Metric cards, gauge chart, donut chart
│   ├── styled_table.py     ← Table helpers (Win/Loss coloring, pivots)
│   └── lineage_inspector.py← Click-to-trace lineage system
│
├── pages/                  ← One file per dashboard tab
│   ├── 1_crew_leader_stats.py
│   ├── 2_white_board.py
│   ├── 3_stats_detail.py
│   ├── 4_damage.py
│   ├── 5_time_detail.py
│   ├── 6_winloss_details.py
│   ├── 7_winloss_summary.py
│   ├── 8_est_v_actual.py
│   ├── 9_notes.py
│   └── 10_owner.py
│
├── sample-data/            ← CSV and Excel source files
├── design-system.html      ← Visual design mockup (open in browser)
└── DESIGN_IMPLEMENTATION_PLAN.md
```

---

## How the App Works (Big Picture)

Every page follows the same pattern:

```
1. LOAD     →  Read CSVs from disk (cached so it only happens once)
2. TRANSFORM →  Clean columns, compute new ones, aggregate
3. FILTER   →  User picks Year, Month, Crew Leader, etc.
4. DISPLAY  →  Show KPI cards, tables, and charts
```

When you run `streamlit run app.py`, Streamlit starts a local web server. Every time a user changes a filter, Streamlit reruns the page script from top to bottom (this is Streamlit's core concept — the whole page re-executes on every interaction).

---

## Common Changes and Where to Make Them

### Change a page title / header

Every page has a line near the top like:
```python
st.markdown("#### Est v Actual Dash")
```
Just edit the string. The `####` is markdown for a heading (like `<h4>` in HTML).

### Change a chart title

Charts are built with Plotly. Look for either:

**In the chart's `update_layout()` call:**
```python
fig.update_layout(
    title=dict(text="Win Loss", font=dict(size=14)),   # ← change this string
    ...
)
```

**Or in the trace creation:**
```python
fig = go.Figure(go.Indicator(
    title={"text": title, "font": {"size": 14}},   # ← "title" is a parameter
    ...
))
```

**Or in the axis labels:**
```python
fig.update_layout(
    yaxis_title="HrsActual and HoursEst",   # ← Y-axis label
    xaxis_title="MonthFull",                 # ← X-axis label
)
```

### Change a color

All colors live in `config.py`:
```python
WIN_COLOR = "#2E7D32"      # green for Wins
LOSS_COLOR = "#C62828"      # red for Losses
ACCENT_BLUE = "#003366"     # headers, buttons
HEADER_STEEL = "#4472C4"    # table header background
STAR_GOLD = "#DAA520"       # star ratings
```
Change the hex code and it updates everywhere that color is used.

### Change which columns appear in a table

Look for where the display dataframe is built. It usually looks like:
```python
display = df[["Approved Date", "Visit Ref #", "Qty", "Line_Item_Description"]].copy()
```
Add or remove column names from that list. The column names must match exactly what's in the data (case-sensitive).

### Change a filter's options

Filters are in `components/filters.py`. For example, to add a new option to the Operation filter, find:
```python
def operation_filter(operations: list[str], key: str = "operation") -> str | None:
    options = ["All"] + operations
    return st.selectbox("Operation", options, key=key)
```
The options come from the data itself (passed in as the `operations` parameter), so you'd usually change what `get_operations()` returns in `data/transforms.py`.

### Change a KPI card label

In the page file, find the `inspectable_metric()` or `metric_card()` call:
```python
inspectable_metric("Compliments", comp_count, "Compliments", ...)
```
The first argument (`"Compliments"`) is the label displayed on the card.

### Change the navigation menu

The nav is defined in `app.py`:
```python
pages = {
    "Crew Leader Stats": "pages/1_crew_leader_stats.py",
    "White Board":       "pages/2_white_board.py",
    ...
}
```
Change the keys (left side) to rename tabs. Add/remove entries to add/remove tabs.

### Add global CSS styles

All global CSS is in `app.py` inside the `st.markdown("""<style>...</style>""")` block. This is regular CSS that targets Streamlit's internal elements.

---

## Page-by-Page Reference

Each page file follows this structure:

```python
# 1. Imports
import streamlit as st
from data.loader import load_all_line_items, ...
from data.transforms import build_so_line_items, ...

# 2. Load and transform data
raw = load_all_line_items()
so = build_so_line_items(raw)

# 3. Create filter widgets
sel_year = st.selectbox("Year", years, key="unique_key")

# 4. Apply filters to data
fstats = apply_year(stats, sel_year)

# 5. Display: KPIs, tables, charts
inspectable_metric("Label", value, "KPI Name", ...)
st.dataframe(display_df, use_container_width=True)

# 6. Debug expander (at the bottom)
with st.expander("🔍 Debug"):
    st.dataframe(raw_data)
```

| Page | What It Shows |
|------|--------------|
| 1 - Crew Leader Stats | Compliments, Callbacks, QC gauge, Win/Loss donut per crew leader |
| 2 - White Board | Monthly stats pivot, QC percentages, Win/Loss by month chart |
| 3 - Stats Detail | Detailed stats table with all line items (QC, Compliments, etc.) |
| 4 - Damage | Damage repair incidents list |
| 5 - Time Detail | Time tracking entries from Time.csv |
| 6 - WinLoss Details | Every invoice with Win/Loss coloring, all financial columns |
| 7 - WinLoss Summary | Aggregated Win/Loss by Crew Leader and Operation |
| 8 - Est v Actual | Estimated vs Actual hours stacked bar chart |
| 9 - Notes | Review notes and comments from line items |
| 10 - Owner | Full owner view: all invoices with EPH, Net, Win/Loss EPH |

---

## The Data Pipeline

```
sample-data/LineItems_SO_*.csv ─┐
                                ├─→ loader.py (read + append)
sample-data/Time.csv ───────────┤        │
                                │        ▼
sample-data/CrewStatLists.xlsx ─┘   transforms.py
                                         │
                                    ┌────┴─────────────────┐
                                    │                      │
                              build_so_line_items()   build_time_detail()
                                    │
                         ┌──────────┼──────────┐
                         │          │          │
                   build_stats() build_inv_amts() build_damage()
                         │          │
                   (QC, Comps,  (InvTotal, EPH,
                    Callbacks)   Win/Loss, etc.)
```

The key functions in `data/transforms.py`:

- **`build_so_line_items(raw)`** — Cleans the raw CSV data: parses dates, converts numbers, strips HTML from notes, extracts Crew Leader name, derives Year/Month columns. This is the foundation everything else builds on.

- **`build_inv_amts(so, time_raw)`** — Groups line items by Visit Ref # to create one row per job. Calculates InvTotal, HoursEst, Costs, TimeByInv (actual hours), HrsRatio, WinLossText, EPH, NetInv.

- **`build_stats(so, qc_scale)`** — Filters to stat items (QC, Compliment, Call Back, Crew Feedback). Extracts QC letter grades from descriptions and looks up percentage scores.

---

## Python for JavaScript Developers

### The Basics

| JS | Python | Notes |
|----|--------|-------|
| `const x = 5` | `x = 5` | No const/let/var. All variables are reassignable. |
| `let arr = [1, 2, 3]` | `arr = [1, 2, 3]` | Lists (same as JS arrays) |
| `let obj = {a: 1}` | `obj = {"a": 1}` | Dicts (like JS objects, but keys need quotes) |
| `function foo(x) {...}` | `def foo(x):` | Indentation defines the block (no curly braces!) |
| `if (x > 5) {...}` | `if x > 5:` | No parentheses needed, colon + indent |
| `for (let i of arr) {...}` | `for i in arr:` | |
| `arr.map(x => x * 2)` | `[x * 2 for x in arr]` | "List comprehension" — very Pythonic |
| `arr.filter(x => x > 3)` | `[x for x in arr if x > 3]` | |
| `arr.length` | `len(arr)` | |
| `console.log(x)` | `print(x)` | |
| `null` | `None` | |
| `true / false` | `True / False` | Capitalized! |
| `=== / !==` | `== / !=` | Python only has == (no ===) |
| `&&` / `\|\|` | `and` / `or` | English words, not symbols |
| `template ${var}` | `f"template {var}"` | f-strings (note the f before the quote) |
| `// comment` | `# comment` | |
| `import {x} from 'y'` | `from y import x` | Order is reversed |

### The #1 Difference: Indentation Matters

In Python, indentation IS the syntax. Where JS uses `{}` to define blocks, Python uses indent level:

```python
# Python
if score > 90:
    grade = "A"          # inside the if block (4 spaces in)
    print("Great!")      # still inside
print("Done")           # outside the if block (back to 0 spaces)
```

Use 4 spaces per indent level (your editor handles this). If your indentation is wrong, Python will throw an `IndentationError`.

### Strings

```python
name = "Grace"
greeting = f"Hello, {name}!"           # f-string (like JS template literals)
multiline = """This is
a multiline string"""                   # triple quotes for multiline
```

### Pandas (the Data Library)

Pandas is the Python equivalent of working with spreadsheet data. A `DataFrame` is basically a table:

```python
import pandas as pd

# Think of df as a spreadsheet
df = pd.read_csv("data.csv")

# Get a column (like accessing a property)
df["Name"]                     # returns the whole Name column

# Filter rows (like .filter() in JS)
wins = df[df["WinLossText"] == "Win"]

# Multiple conditions (use & for AND, | for OR, wrap each in parens)
big_wins = df[(df["WinLossText"] == "Win") & (df["InvTotal"] > 1000)]

# Aggregate (like .reduce() in JS)
df["InvTotal"].sum()           # sum of a column
df["InvTotal"].mean()          # average
df.groupby("Crew Leader")["InvTotal"].sum()   # sum per crew leader

# Add a new column
df["NetInv"] = df["InvTotal"] - df["Costs"]
```

### Streamlit (the UI Library)

Streamlit is like React but much simpler — no JSX, no state management, no build step. You just write Python and it becomes a web app:

```python
import streamlit as st

st.markdown("## My Title")              # renders markdown/HTML
st.dataframe(df)                        # renders a data table
st.plotly_chart(fig)                    # renders a Plotly chart
value = st.selectbox("Pick one", ["A", "B", "C"])   # dropdown, returns selected value
st.columns(3)                           # creates 3 side-by-side columns

# Layout with columns
col1, col2 = st.columns(2)
with col1:
    st.write("Left side")
with col2:
    st.write("Right side")
```

### Running the App

From Terminal, navigate to the project folder and run:
```bash
cd ~/Desktop/tree-dashboard-project
streamlit run app.py
```
It opens in your browser at http://localhost:8501. While it's running, every time you save a `.py` file, Streamlit detects the change and offers to rerun — just click "Rerun" in the browser (or turn on "Always rerun" in Settings).

To stop the server: press `Ctrl + C` in Terminal.

---

## Recommended Editor: VS Code

**Visual Studio Code** is the best free editor for Python and it works great on Mac.

### Install it:
1. Go to https://code.visualstudio.com and download the Mac version
2. Open the `.dmg` file and drag VS Code to Applications

### Set it up for Python:
1. Open VS Code
2. Go to Extensions (the square icon in the left sidebar, or `Cmd + Shift + X`)
3. Search for "Python" and install the one by Microsoft
4. That's it — you get syntax highlighting, error detection, and autocomplete

### Open the project:
1. File → Open Folder → select `tree-dashboard-project`
2. You'll see the full file tree in the left sidebar
3. Click any `.py` file to edit it
4. Save with `Cmd + S` (same as any Mac app)

### Useful VS Code shortcuts:
| Shortcut | What it does |
|----------|-------------|
| `Cmd + P` | Quick-open any file by typing part of its name |
| `Cmd + Shift + F` | Search across all files (great for finding where a string is used) |
| `Cmd + D` | Select the next occurrence of the selected text |
| `` Ctrl + ` `` | Open/close the built-in Terminal |
| `Cmd + /` | Toggle comment on current line |

### The VS Code Terminal:
VS Code has a built-in terminal (`` Ctrl + ` ``). You can run `streamlit run app.py` directly from there, so you can edit code and see the terminal output in one window.

---

## Quick Recipes

### "I want to change a chart's bar colors"

Find the chart in the page file. Look for `marker_color` or `color_discrete_map`:
```python
# Single color:
fig.add_trace(go.Bar(
    marker_color=WIN_COLOR,   # ← change this (or use a hex code like "#FF0000")
))

# Color mapping (for Win/Loss):
fig = px.bar(
    color_discrete_map={"Win": WIN_COLOR, "Loss": LOSS_COLOR},   # ← change these
)
```

### "I want to change what a KPI counts"

Find the KPI in the page file. The value is computed just above where it's displayed:
```python
comp_count = int(compliments["Qty"].sum())   # ← this calculates the number
inspectable_metric("Compliments", comp_count, ...)  # ← this displays it
```

### "I want to add a new column to a table"

Find where the display columns are selected:
```python
display = df[["Col A", "Col B", "Col C"]].copy()   # ← add your column name here
```
The column name must exist in the source dataframe `df`. Use the Debug expander at the bottom of each page to see all available columns.

### "I want to rename a column header in the table"

After selecting columns, use `.rename()`:
```python
display = df[["InvTotal", "TimeByInv"]].copy()
display = display.rename(columns={"InvTotal": "Invoice Total", "TimeByInv": "Actual Hours"})
```

---

## Debugging Tips

1. **Use the Debug expander** — Every page has a `🔍 Debug` section at the bottom that shows the raw data and active filters. Expand it to see what data is available.

2. **Use the Lineage inspector** — Click any row in a table or the 🔍 button on a KPI card to see exactly how that number was calculated.

3. **Check the Terminal** — If something breaks, the error message appears in the Terminal where `streamlit run` is running. Python error messages read bottom-to-top: the actual error is on the last line, and the lines above show where it happened.

4. **Common errors:**
   - `KeyError: 'ColumnName'` — You typed a column name wrong (check capitalization)
   - `IndentationError` — Your indentation is off (use 4 spaces per level)
   - `SyntaxError` — Usually a missing colon after `if`/`for`/`def`, or mismatched quotes

---

## Key Streamlit Concepts

**Rerun model:** Every widget interaction (dropdown change, button click) reruns the entire page script from top to bottom. This means your code doesn't need event listeners — it just runs linearly.

**`st.session_state`:** Persists values across reruns (like React state). Filter selections are stored here automatically via the `key` parameter.

**`@st.cache_data`:** Decorator that caches a function's return value. Used on data loading so CSVs aren't re-read on every rerun:
```python
@st.cache_data
def load_all_line_items():
    ...  # only runs once, then returns cached result
```

**`unsafe_allow_html=True`:** Required whenever you use raw HTML in `st.markdown()`. Without it, HTML tags are escaped and displayed as text.
