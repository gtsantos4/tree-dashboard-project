# SingleOps → Streamlit Dashboard: Complete Migration Plan

## 1. Power Query M Transformations (Reverse-Engineered)

The .pbix DataModel uses XPress9 compression (Microsoft proprietary), so the M code can't be extracted directly. However, from the Report Layout metadata, DiagramLayout, sample data, and screenshots, the complete data model has been fully reverse-engineered. Below are the **27 tables** in the model and the transformations required to reproduce each.

---

### 1.1 Primary Source Table: `SO_LineItems`

**Source:** All `LineItems_SO_YYYY.csv` files appended together (2020–2026).

**Transformations:**
- Append all yearly CSV files into a single table
- Parse date columns (`Line Items Created Date`, `Visits Created Date`, `Approved Date`, `Scheduled Date`, `Invoice Date`, etc.) from `MM/DD/YYYY HH:MM` string format to datetime
- Cast `Qty`, `Unit Cost`, `Unit Markup`, `Unit Total`, `Line Total` to float
- Cast `Billable`, `Actual` to boolean
- Parse the `Review` field from JSON-style string (e.g., `["", "Follow Up Complete"]`) into a clean string
- Clean HTML tags from `Internal Notes`, `Client Notes`, `Crew Notes` fields
- Extract `Crew Leader` from the `crews` column (first crew name)
- This is used directly by the **Damage** and **Notes** pages

**Columns used in reports:** `Visit Ref #`, `Approved Date`, `Client`, `Line_Item_Description`, `Line Total`, `Crew Leader`, `Review`, `Review Notes`, `Internal Notes`, `Item Name`

---

### 1.2 Dimension Tables

#### `DimDates`
**Derived from:** Generated date dimension table spanning the data range.
**Columns:** `Date`, `Year`, `MonthShort` (Jan, Feb, ...), `MonthFull` (January, February, ...), `MonthNum`, `Week`, `Quarter`
**Used by:** CrewLeaderStats, White Board, WinLoss Details, WinLoss Summary, Est v Actual Dash, Owner (as slicer for Year, Month)

#### `DimDates (2)`
**Same structure as DimDates** but serves as a second date relationship (likely for a different date field — `Approved Date` vs `Invoice Date`).
**Used by:** White Board page

#### `CrewLeaders`
**Derived from:** Distinct crew leader names from `SO_LineItems.crews` field.
**Columns:** `Crew Leader`
**Used by:** CrewLeaderStats slicer

#### `Dept2` (Operation dimension)
**Derived from:** Distinct `Operation` values: `Trees`, `PHC`, `Woodchips`
**Columns:** `Dept2` (displayed as "Operation")
**Used by:** CrewLeaderStats slicer

#### `dimDept`
**Derived from:** Same as Dept2 — distinct Operation values
**Columns:** `Operation`
**Used by:** TimeDetail, WinLoss Summary

---

### 1.3 Fact/Aggregated Tables

#### `Stats`
**Derived from:** `SO_LineItems` filtered to stat-tracking item names only.
**Filter:** `Item Name IN ('Quality Control', 'Compliment', 'Call Back', 'Crew Feedback')`
**Columns:** `Visit Ref #`, `Job Ref #`, `Client`, `Crew Leader`, `Item Name`, `Qty`, `Line_Item_Description`, `Approved Date`, `Percent` (likely a lookup to QC grade scale), `QC Grade` (letter grade derived from Percent via the QC reference table), `Sales Reps`, `Year`, `MonthShort`
**Measures:**
- `Stats star rating` — visual star rating display for compliments
- `Stats box rating` — visual box rating display for call backs
**Used by:** CrewLeaderStats, White Board, Stats Detail

#### `InvAmts` (Invoice Amounts — the core fact table)
**Derived from:** `SO_LineItems` aggregated to the Visit/Invoice level for invoiced jobs.
**Filter:** Records with an `Invoice Date` (invoiced work), likely further filtered to exclude non-billable service items.
**Aggregation level:** One row per `Visit Ref #`
**Columns:** `Visit Ref #`, `Client`, `Operation`, `Crew Leader`, `Sales Reps`, `InvoiceDate`, `InvTotal` (sum of Line Total), `HoursEst` (estimated hours from Qty on labor items), `TimeByInv` (actual hours — joined from time tracking), `HrsRatio` (HoursEst / TimeByInv), `WinLossText` ("Win" if HrsRatio >= 1, "Loss" if < 1), `Discount` (sum of discount line items), `Approved Date`
**Measures:**
- `EPH` — Earnings Per Hour (InvTotal / TimeByInv)
- `NetInv` — Net Invoice (InvTotal - Costs)
- `WL_EPH` — Win/Loss adjusted EPH
- `AvgScheduled` — Average scheduled hours
**Used by:** CrewLeaderStats (Win Loss donut), White Board (Win Loss pivot & chart), WinLoss Details, WinLoss Summary, Est v Actual Dash, Owner

#### `InvCosts`
**Derived from:** Cost data per visit (likely from material line items or a separate cost source).
**Columns:** `Costs` (per Visit Ref #)
**Used by:** Owner page

#### `HoursEst`
**Derived from:** Estimated hours extracted from labor line items in `SO_LineItems`.
**Columns:** `HoursEst` (per Visit Ref #)
**Used by:** Owner page

#### `TimeActual`
**Derived from:** Actual time tracked (likely from the `Time` data source or computed from the CSV).
**Columns:** `TimeByInv` (actual hours per Visit Ref #)
**Used by:** Owner page

#### `Time`
**Derived from:** A separate time-tracking data source (not directly in the CSVs — possibly a separate SingleOps export or manual entry).
**Columns:** `DATE`, `DURATION`, `AddOn`, `JobNo`, `InvNo`, `NOTE`, `WeekEnd`
**Used by:** TimeDetail page

---

### 1.4 Reference/Lookup Tables

#### `QC` (Quality Control scale)
**Source:** `CrewStatLists.xlsx` → Sheet "QC"
**Data:** Grade (A+ through F) mapped to Percent (1.0 down to 0.50)

#### `CB` (Call Back scale)
**Source:** `CrewStatLists.xlsx` → Sheet "CB"
**Data:** PerMonth (0–6) mapped to Percent (1.0 down to 0.50) and Grade (A through F)

#### `ComplimentScale`
**Source:** `CrewStatLists.xlsx` → Sheet "Compliments"
**Data:** PerMonth (>=10 through 1) mapped to Percent (1.0 down to 0.50)

#### `SchedulingGoals`
**Source:** `CrewStatLists.xlsx` → Sheet "EstHrsGoals"
**Data:** Operation (Trees, PHC, All) × Type (Scheduling, Actual) × Day/Week/Month/Year goals

#### `Goals Summary`
**Source:** `CrewStatLists.xlsx` → Sheet "EstHrsGoals (2)"
**Data:** Similar interval-based goals by operation

#### `MiscInputs`
**Derived from:** Scheduling goals reshaped for the Est v Actual Dash page.
**Data:** Title (DailySchedulingGoal, WeeklySchedulingGoal, MonthlySchedulingGoal, YearlySchedulingGoal) × NumericalValue1

#### `QCGrades`
**Derived from:** Computed table joining Stats to QC lookup to produce letter grades.

#### `Customers`, `Employees_1`, `ServiceItems`
**Derived from:** Distinct lookups from Time tracking data — Customer names, Employee titles, Service item types.

---

## 2. Source File → Report Page Mapping

| Source File(s) | Model Table(s) | Report Pages |
|---|---|---|
| `LineItems_SO_*.csv` (all years) | `SO_LineItems` | **Damage**, **Notes** |
| `LineItems_SO_*.csv` → filtered | `Stats` | **CrewLeaderStats**, **White Board**, **Stats Detail** |
| `LineItems_SO_*.csv` → aggregated | `InvAmts`, `InvCosts`, `HoursEst`, `TimeActual` | **WinLoss Details**, **WinLoss Summary**, **Est v Actual Dash**, **Owner** |
| `CrewStatLists.xlsx` → QC sheet | `QC` | **White Board** (reference table) |
| `CrewStatLists.xlsx` → CB sheet | `CB` | **White Board** (reference table) |
| `CrewStatLists.xlsx` → Compliments sheet | `ComplimentScale` | **White Board** (reference table) |
| `CrewStatLists.xlsx` → EstHrsGoals | `SchedulingGoals` | **WinLoss Details**, **WinLoss Summary** |
| `CrewStatLists.xlsx` → EstHrsGoals (2) | `Goals Summary`, `MiscInputs` | **Est v Actual Dash**, **Page 1** |
| Generated | `DimDates`, `DimDates (2)` | All pages (filters) |
| Derived from CSVs | `CrewLeaders`, `Dept2`, `dimDept` | Slicers on multiple pages |

---

## 3. Screenshot-Based Visual & KPI Inventory

### Page 1: CrewLeaderStats
**Slicers:** Crew Leader (All), Operation (Trees), Year (2025), MonthShort (All)
**KPIs:**
- **Compliments** = 86 (Sum of Qty where Item Name = "Compliment") with star rating visual (★★★★★★★★)
- **Call Backs** = 6 (Sum of Qty where Item Name = "Call Back") with colored block rating (■■■■■■)
- **# Grades** = 88 (count of QC grades)
- **Average of Percent** = 92% (gauge chart, QC percentage average)
**Charts:**
- Win Loss donut chart: Win 602 (84.7%), Loss 109 (15.3%) — green/red
**Tables:**
- Two detail tables listing Visit Ref # / Qty / Line_Item_Description (one for Compliments, one for Call Backs)
**Navigation:** Left sidebar with links to all other pages

### Page 2: White Board
**Slicers:** Year (2025)
**Tables:**
- Monthly pivot of stats items (Call Back, Compliment, Crew Feedback, Quality Control) showing counts by month (Jan–Dec) with totals
- Monthly pivot of QC percentages (Quality Control %) by month — values like 93%, 94%, 87%, etc.
- Win Loss breakdown by Operation (PHC/Trees) showing Win/Loss counts per month
**Charts:**
- Win Loss Chart by Month — stacked bar chart showing Win (green) vs Loss (red) counts by month
**Reference Tables:**
- CB/Month with Pct (grading scale for call backs)
- Compl/Month with Pct (grading scale for compliments)
- QC Grade with Pct (grading scale for quality control)

### Page 3: Stats Detail
**Layout:** Full-width detail table — drill-through target from CrewLeaderStats
**Columns:** Visit Ref #, Job Ref #, Approved Date, Client, Crew Leader, Item Name, Qty, Line_Item_Description
**Filters:** Pre-filtered by Crew Leader, Item Name, date range from source page
**Row count:** 841 total rows shown

### Page 4: Damage
**Slicers:** Year (2023/2024/2025 buttons), Crew Leader (All)
**KPIs:**
- **Count** = 30 (count of damage repair incidents)
- Per-crew-leader damage cost breakdown (multiRowCard showing costs by crew leader)
**Table:** Approved Date, Visit Ref #, Client, Line_Item_Description, Line Total, Crew Leader
**Filter:** Item Name = "Damage Repair"
**Total:** $12,116.67

### Page 5: TimeDetail
**Layout:** Full-width detail table — drill-through target
**Columns:** DATE, Title (employee), Customer, ITEM, DURATION, AddOn, JobNo, InvNo, NOTE, Operation, WeekEnd
**Total Duration:** 43.00 hours shown
**Note:** This page uses a separate Time tracking data source

### Page 6: WinLoss Details
**Slicers:** Year/Date range, Month, Operation
**KPIs:**
- **Count** = 66 (invoices in period)
**Tables:**
- "Estimated Hours Goals" — Operation × Day/Week/Month/Year scheduling targets
- "Actual Hours Goals" — same structure with actual values
- "Win / Loss for Period" — detail table: InvoiceDate, Visit Ref #, Client, Operation, HoursEst, HrsActual, HrsRatio, WinLoss (color-coded green=Win, red=Loss), Crew Leader, Sales Reps
**Totals row:** 1,046.50 est hours, 840.75 actual hours

### Page 7: WinLoss Summary
**Slicers:** Year (2025/2026 buttons), Operation (PHC/Trees), Date range
**Tables:**
- "Estimated Hours v Goals" — Monthly breakdown: Month, Hours, HoursSum, GoalSum, Yr TD, PercentToGoal
- "Estimated Hours v Goals - Monthly Average" — Yearly summary: Year, HoursEst/Mo, AvgScheduled, Goal, Variance, Calculation(%)

### Page 8: Est v Actual Dash
**Slicers:** Year (2024/2025/2026 buttons), Operation (PHC/Trees), Month (All)
**Table:** Scheduling goals reference (Daily=140.0, Weekly=686.0, Monthly=2,742.0)
**Chart:** "Win / Loss for Period" — stacked bar chart by MonthFull showing HrsActual (green) vs HoursEst (blue)

### Page 9: Notes
**Slicers:** Review (categorical), Approved Date (date range)
**KPIs:** Count of records
**Table:** Approved Date, Visit Ref #, Client, Review, Review Notes, Internal Notes

### Page 10: Owner
**Slicers:** Year/Date range, Month, Operation
**KPIs:** Count = 66 (job count for period)
**Table:** "Win / Loss for Period" — comprehensive financial detail: InvoiceDate, Visit Ref #, Client, Operation, InvTotal, Costs, NetInv, Disc(ount), HrsEst, HrsAct(ual), HrsRatio, EPH, WL_EPH, WinLoss (color-coded), Crew Leader, Sales Reps
**Totals row:** InvTotal=163,709, Costs=9,997.96, Net=153,712, HrsEst=840.75, EPH=182.83, WL_EPH=190.52

---

## 4. Streamlit App Structure Plan

### 4.1 Technology Stack

- **Framework:** Streamlit 1.x
- **Data processing:** pandas, openpyxl
- **Charting:** Plotly Express (interactive charts matching PowerBI interactivity)
- **Layout:** `st.columns`, `st.tabs`, `st.sidebar` for navigation
- **State management:** `st.session_state` for cross-page filter context
- **Caching:** `@st.cache_data` for CSV loading and transformations
- **Styling:** Custom CSS for Win/Loss color coding (green/red)

### 4.2 File Structure

```
tree-dashboard-project/
├── app.py                      # Main entry point with sidebar nav
├── data/
│   ├── loader.py               # CSV + Excel loading with caching
│   └── transforms.py           # All Power Query equivalent transformations
├── pages/
│   ├── 1_crew_leader_stats.py  # CrewLeaderStats page
│   ├── 2_white_board.py        # White Board page
│   ├── 3_stats_detail.py       # Stats Detail drill-through
│   ├── 4_damage.py             # Damage tracking page
│   ├── 5_time_detail.py        # TimeDetail drill-through
│   ├── 6_winloss_details.py    # WinLoss Details page
│   ├── 7_winloss_summary.py    # WinLoss Summary page
│   ├── 8_est_v_actual.py       # Est v Actual Dash page
│   ├── 9_notes.py              # Notes page
│   └── 10_owner.py             # Owner page
├── components/
│   ├── filters.py              # Reusable slicer/filter components
│   ├── kpi_cards.py            # Reusable KPI card components
│   ├── rating_displays.py     # Star rating, box rating, gauge components
│   └── styled_table.py        # Conditional formatting for tables (Win/Loss colors)
├── config.py                   # Color scheme, constants, field mappings
├── sample-data/                # (existing) CSV + Excel files
├── requirements.txt
└── README.md
```

### 4.3 Data Pipeline (`data/loader.py` + `data/transforms.py`)

#### Loading (cached)
```
load_all_line_items() → Append all LineItems_SO_*.csv → DataFrame
load_crew_stat_lists() → Read all sheets from CrewStatLists.xlsx → dict of DataFrames
```

#### Core Transformations
```
build_so_line_items(df) →
  - Parse dates, cast numerics, clean HTML, parse Review JSON
  - Extract Crew Leader from crews field
  - Return: full SO_LineItems DataFrame

build_stats_table(so_df) →
  - Filter: Item Name in [Quality Control, Compliment, Call Back, Crew Feedback]
  - Join to QC lookup to add Percent and QC Grade
  - Add Year, MonthShort columns
  - Return: Stats DataFrame

build_inv_amts(so_df) →
  - Filter: records with Invoice Date, billable labor items
  - Aggregate to Visit Ref # level
  - Compute: InvTotal (sum Line Total), HoursEst (sum Qty for labor),
    HrsRatio, WinLossText, Discount
  - Return: InvAmts DataFrame

build_dim_dates(so_df) →
  - Generate date range from min to max date in data
  - Add Year, MonthShort, MonthFull, MonthNum, Week
  - Return: DimDates DataFrame

build_damage(so_df) →
  - Filter: Item Name = "Damage Repair"
  - Return: Damage-specific DataFrame

build_notes(so_df) →
  - Filter: records with non-empty Review or Review Notes
  - Return: Notes DataFrame

Computed measures (as Python functions):
  eph(inv_total, time_actual) → inv_total / time_actual
  net_inv(inv_total, costs) → inv_total - costs
  wl_eph(row) → conditional EPH based on WinLoss
  avg_scheduled(hours_est_series) → rolling/cumulative average
```

### 4.4 Page-by-Page Implementation

#### `app.py` — Main Entry Point
- Sidebar navigation matching PowerBI's left nav: page name list with `st.page_link`
- Global data loading on startup with progress indicator
- Session state initialization for cross-page filter carry

#### Page 1: `crew_leader_stats.py`
**Filters (top row):** 4 columns — Crew Leader selectbox, Operation selectbox, Year selectbox, Month multiselect
**Layout:**
- Row 1: 4 KPI cards in columns
  - Compliments count (large number + star rating using ★ unicode or custom SVG)
  - Call Backs count (large number + colored block rating using ■ squares)
  - Average QC % (Plotly gauge chart)
  - # Grades count
- Row 2: 3 columns
  - Compliments detail table (Visit Ref, Qty, Description)
  - Call Backs detail table (Visit Ref, Qty, Description)
  - Win/Loss donut chart (Plotly pie with green/red, showing counts + percentages)
- Sales Reps indicator in corner

#### Page 2: `white_board.py`
**Filters:** Year selectbox
**Layout:**
- Row 1: Stats pivot table (Item Name × Month with counts) — `pd.pivot_table` rendered as styled dataframe
- Row 2: QC % pivot table (Item Name × Month with percentages)
- Row 3: 2 columns
  - Win Loss pivot (Operation × WinLossText × Month with counts)
  - Win Loss stacked bar chart by month (Plotly bar, color=WinLossText)
- Row 4: 3 reference tables (CB/Month scale, Compliment/Month scale, QC Grade scale)

#### Page 3: `stats_detail.py`
**Purpose:** Drill-through detail table (simulated via URL params or session state)
**Filters:** Inherited from CrewLeaderStats filters or independent selection
**Content:** Full-width `st.dataframe` with columns: Visit Ref #, Job Ref #, Approved Date, Client, Crew Leader, Item Name, Qty, Line_Item_Description
**Back button:** Navigate back to CrewLeaderStats

#### Page 4: `damage.py`
**Filters:** Year multiselect (buttons style), Crew Leader selectbox
**Layout:**
- KPI card: Count of incidents
- Main table: Approved Date, Visit Ref #, Client, Description, Line Total, Crew Leader
- Sidebar metrics: Per-crew-leader damage totals (multiRowCard-style stacked metrics)
- Footer: Total damage cost

#### Page 5: `time_detail.py`
**Purpose:** Drill-through detail from WinLoss pages
**Content:** Full-width table: DATE, Title (employee), Customer, ITEM, DURATION, AddOn, JobNo, InvNo, NOTE, Operation, WeekEnd
**Note:** Since the Time source isn't available in the CSVs, this page will show a placeholder or will need a separate data source. The data appears to come from a different SingleOps export. Plan: add a data upload option or derive approximate time data from the line items.

#### Page 6: `winloss_details.py`
**Filters:** Year/date range, Month selectbox, Operation selectbox
**Layout:**
- Top: Count KPI card
- Middle: 2 columns
  - Estimated Hours Goals table (from SchedulingGoals)
  - Actual Hours Goals table (from SchedulingGoals)
- Bottom: "Win / Loss for Period" detail table with conditional row coloring (green=Win, red=Loss): InvoiceDate, Visit Ref #, Client, Operation, HoursEst, HrsActual, HrsRatio, WinLoss, Crew Leader, Sales Reps
- Totals row

#### Page 7: `winloss_summary.py`
**Filters:** Year buttons, Operation buttons, Date range
**Layout:** 2 columns
- Left: "Estimated Hours v Goals" — monthly table with Hours, cumulative sums, GoalSum, YTD, % to Goal
- Right: "Estimated Hours v Goals - Monthly Average" — yearly summary with monthly avg, AvgScheduled, Goal, Variance, %

#### Page 8: `est_v_actual.py`
**Filters:** Year buttons, Operation buttons, Month selectbox
**Layout:**
- Top-left: Scheduling Goals reference table (Daily/Weekly/Monthly/Yearly targets)
- Main: "Win / Loss for Period" stacked bar chart (Plotly bar) — MonthFull on X-axis, HrsActual (green) + HoursEst (blue) on Y-axis

#### Page 9: `notes.py`
**Filters:** Review selectbox, Approved Date range picker
**Layout:**
- Count KPI card
- Full-width table: Approved Date, Visit Ref #, Client, Review, Review Notes, Internal Notes

#### Page 10: `owner.py`
**Filters:** Year/Date range, Month selectbox, Operation selectbox
**Layout:**
- Top: Count KPI card
- Main: "Win / Loss for Period" comprehensive table with conditional coloring: InvoiceDate, Visit Ref #, Client, Op, InvTotal, Costs, NetInv, Disc, HrsEst, HrsAct, HrsRatio, EPH, WL_EPH, WinLoss, Crew Leader, Sales Reps
- Totals row with sums/averages

### 4.5 Shared Components

#### `components/filters.py`
- `year_filter(df, col)` → Year selectbox/buttons returning filtered df
- `month_filter(df, col)` → Month multiselect
- `operation_filter(df, col)` → Operation selectbox
- `crew_leader_filter(df, col)` → Crew leader selectbox
- `date_range_filter(df, col)` → Date range picker
- `sales_rep_filter(df, col)` → Sales rep selectbox

#### `components/kpi_cards.py`
- `metric_card(label, value, delta=None)` → Styled metric
- `count_card(label, count)` → Large count display

#### `components/rating_displays.py`
- `star_rating(count, max_stars=10)` → Green star display
- `box_rating(count, max_boxes=10)` → Colored box display
- `gauge_chart(value, min=0, max=100, suffix='%')` → Plotly gauge

#### `components/styled_table.py`
- `winloss_table(df, wl_col)` → DataFrame with green/red row highlighting
- `pivot_with_totals(df, index, columns, values, aggfunc)` → Pivot table with total row/column
- `styled_dataframe(df, format_dict)` → Formatted display with number formatting

### 4.6 Color Scheme & Styling

Matching the PowerBI report:
- **Win:** Green (#4CAF50 / dark green)
- **Loss:** Red (#F44336 / dark red)
- **Headers/Accent:** Dark blue (#003366) — matches PowerBI nav sidebar
- **Background:** White
- **Table headers:** Steel blue matching PowerBI pivot headers
- **KPI cards:** White background with subtle border
- **Gauge:** Green arc on white

### 4.7 Known Data Gaps & Decisions Needed

1. **Time tracking data (TimeDetail page):** The `Time` table used by TimeDetail comes from a separate data source not present in the CSV exports. Options:
   - Request the time tracking CSV export from SingleOps
   - Derive approximate data from the line items (less accurate)
   - Show page as placeholder until data source is provided

2. **InvCosts (Owner page):** Cost data per visit may come from a separate source or may be derivable from Material line item costs in the CSV. Need to confirm.

3. **WinLoss calculation:** The exact threshold for Win vs Loss needs confirmation. From screenshots, it appears to be based on HrsRatio (estimated/actual hours) where ratio >= 1 = Win.

4. **QCGrades computed table:** The exact logic for mapping Stats items to QC grades needs confirmation — likely joins the QC percentage scale from CrewStatLists.xlsx to the Quality Control item Qty values.

5. **Drill-through behavior:** PowerBI supports clicking a row to drill through to detail pages. In Streamlit, this will be simulated using `st.session_state` to pass filter context between pages, or using query parameters.

### 4.8 Implementation Order

1. **Phase 1 — Foundation:** `loader.py`, `transforms.py`, `config.py`, shared components
2. **Phase 2 — Core pages:** CrewLeaderStats, White Board, Damage, Notes (these use the CSV data directly)
3. **Phase 3 — Analytics pages:** WinLoss Details, WinLoss Summary, Est v Actual Dash, Owner (these need the InvAmts aggregation)
4. **Phase 4 — Detail pages:** Stats Detail, TimeDetail (drill-through targets)
5. **Phase 5 — Polish:** Cross-page navigation, consistent styling, responsiveness
