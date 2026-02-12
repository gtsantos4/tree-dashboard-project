"""
Lineage metadata registry.

Maps every computed column and KPI to its formula, source columns,
and plain-English description.  The lineage inspector reads this
to show users exactly how any number was calculated.
"""

# ── Column-level lineage (for InvAmts / aggregated tables) ───────────

COLUMN_LINEAGE = {
    # ── InvAmts aggregation columns ──────────────────────────────────
    "InvTotal": {
        "formula": "sum(Line Total)  where Billable = True",
        "description": "Total invoice amount for the visit",
        "source_columns": ["Line Total"],
        "source_table": "SO_LineItems",
        "transform": "build_inv_amts",
        "filter": "Billable == True, Invoice Date is not empty",
        "aggregation": "SUM grouped by Visit Ref #",
    },
    "HoursEst": {
        "formula": "sum(Qty)  where Item category = 'Labor' and Billable = True",
        "description": "Estimated hours from labor line items",
        "source_columns": ["Qty"],
        "source_table": "SO_LineItems",
        "transform": "build_inv_amts",
        "filter": "Item category == 'Labor', Billable == True",
        "aggregation": "SUM grouped by Visit Ref #",
    },
    "Costs": {
        "formula": "sum(Line Total)  where Item category = 'Material' and Billable = True",
        "description": "Material costs for the visit",
        "source_columns": ["Line Total"],
        "source_table": "SO_LineItems",
        "transform": "build_inv_amts",
        "filter": "Item category == 'Material', Billable == True",
        "aggregation": "SUM grouped by Visit Ref #",
    },
    "Discount": {
        "formula": "sum(Line Total)  where Item category = 'Discount' and Billable = True",
        "description": "Discount amount (usually negative)",
        "source_columns": ["Line Total"],
        "source_table": "SO_LineItems",
        "transform": "build_inv_amts",
        "filter": "Item category == 'Discount', Billable == True",
        "aggregation": "SUM grouped by Visit Ref #",
    },
    "TimeByInv": {
        "formula": "sum(DURATION)  from Time.csv matched on InvNo or JobNo",
        "description": "Actual hours worked (from time-tracking export)",
        "source_columns": ["DURATION"],
        "source_table": "Time.csv",
        "transform": "build_inv_amts (join)",
        "filter": "InvNo matches Visit Ref #, or JobNo matches Visit Ref #",
        "aggregation": "SUM grouped by InvNo / JobNo",
    },

    # ── InvAmts computed columns ─────────────────────────────────────
    "HrsRatio": {
        "formula": "HoursEst / TimeByInv",
        "description": "Ratio of estimated to actual hours (>1 = beat the estimate)",
        "source_columns": ["HoursEst", "TimeByInv"],
        "source_table": "InvAmts (computed)",
        "transform": "build_inv_amts",
        "special_cases": "Returns Infinity when TimeByInv = 0",
    },
    "WinLossText": {
        "formula": "IF HrsRatio >= 1.0 THEN 'Win' ELSE 'Loss'",
        "description": "Whether the crew beat (Win) or missed (Loss) the hour estimate",
        "source_columns": ["HrsRatio"],
        "source_table": "InvAmts (computed)",
        "transform": "build_inv_amts",
        "special_cases": "Defaults to 'Win' when TimeByInv = 0 (no time data)",
    },
    "NetInv": {
        "formula": "InvTotal - Costs",
        "description": "Net invoice after subtracting material costs",
        "source_columns": ["InvTotal", "Costs"],
        "source_table": "InvAmts (computed)",
        "transform": "build_inv_amts",
    },
    "EPH": {
        "formula": "InvTotal / TimeByInv",
        "description": "Earnings per hour",
        "source_columns": ["InvTotal", "TimeByInv"],
        "source_table": "InvAmts (computed)",
        "transform": "build_inv_amts",
        "special_cases": "Returns 0 when TimeByInv = 0",
    },
    "WL_EPH": {
        "formula": "IF WinLossText = 'Win' AND TimeByInv > 0 THEN InvTotal / TimeByInv ELSE 0",
        "description": "Earnings per hour counted only for Wins",
        "source_columns": ["InvTotal", "TimeByInv", "WinLossText"],
        "source_table": "InvAmts (page-level computed)",
        "transform": "pages/10_owner.py",
        "special_cases": "Only non-zero for Win rows with time data",
    },

    # ── Stats columns ────────────────────────────────────────────────
    "Qty (Stats)": {
        "formula": "Qty from SO_LineItems where Item Name in [Quality Control, Compliment, Call Back, Crew Feedback]",
        "description": "Count / quantity for each stat-tracking line item",
        "source_columns": ["Qty"],
        "source_table": "SO_LineItems",
        "transform": "build_stats",
        "filter": "Item Name in ['Quality Control', 'Compliment', 'Call Back', 'Crew Feedback']",
    },
    "QC Grade": {
        "formula": "Extract leading letter grade (A+ through F) from Line_Item_Description",
        "description": "Letter grade parsed from the QC description text (e.g. 'A Everything looks great!' → 'A')",
        "source_columns": ["Line_Item_Description"],
        "source_table": "SO_LineItems → Stats",
        "transform": "build_stats",
        "special_cases": "Only populated for Item Name = 'Quality Control'; falls back to 'Grade: X' pattern",
    },
    "Percent": {
        "formula": "QC Grade → lookup against CrewStatLists.xlsx QC sheet (A=0.95, A-=0.92, B=0.85, …)",
        "description": "QC percentage score derived from the letter grade in Line_Item_Description",
        "source_columns": ["QC Grade"],
        "source_table": "Stats + CrewStatLists.xlsx (QC sheet)",
        "transform": "build_stats",
        "special_cases": "Only populated for Item Name = 'Quality Control'; NaN for others",
    },
}


# ── KPI-level lineage (for metric cards) ────────────────────────────

KPI_LINEAGE = {
    "Compliments": {
        "formula": "sum(Qty) where Item Name = 'Compliment'",
        "description": "Total compliments received in the period",
        "source_table": "Stats (from SO_LineItems)",
        "filters_applied": "Year, Month, Crew Leader",
    },
    "Call Backs": {
        "formula": "sum(Qty) where Item Name = 'Call Back'",
        "description": "Total call-backs in the period",
        "source_table": "Stats (from SO_LineItems)",
        "filters_applied": "Year, Month, Crew Leader",
    },
    "# Grades": {
        "formula": "count(rows) where Item Name = 'Quality Control'",
        "description": "Number of QC grades recorded",
        "source_table": "Stats (from SO_LineItems)",
        "filters_applied": "Year, Month, Crew Leader",
    },
    "Average of Percent": {
        "formula": "avg(Percent) where Item Name = 'Quality Control'",
        "description": "Average QC percentage across all graded visits",
        "source_table": "Stats (from SO_LineItems)",
        "filters_applied": "Year, Month, Crew Leader",
    },
    "Win/Loss Count": {
        "formula": "count(distinct Visit Ref #) from InvAmts",
        "description": "Number of invoiced visits in the filtered period",
        "source_table": "InvAmts (from SO_LineItems + Time.csv)",
        "filters_applied": "Year, Month, Operation",
    },
    "Damage Count": {
        "formula": "count(rows) where Item Name = 'Damage Repair'",
        "description": "Number of damage incidents",
        "source_table": "SO_LineItems",
        "filters_applied": "Year, Crew Leader",
    },
    "Notes Count": {
        "formula": "count(rows) where Review is not empty",
        "description": "Number of line items with review notes",
        "source_table": "SO_LineItems",
        "filters_applied": "Year, Review type",
    },
    "Est v Actual Count": {
        "formula": "count(distinct Visit Ref #) from InvAmts",
        "description": "Number of invoiced visits (all filters)",
        "source_table": "InvAmts (from SO_LineItems + Time.csv)",
        "filters_applied": "Year, Operation, Month",
    },

    # ── Chart-level lineage ───────────────────────────────────────────
    "Win/Loss Donut": {
        "formula": "Win = count(InvAmts where HrsRatio >= 1.0); Loss = count(InvAmts where HrsRatio < 1.0)",
        "description": "Win/Loss split for invoiced visits. A 'Win' means the crew completed the job in fewer hours than estimated (HoursEst / TimeByInv >= 1.0).",
        "source_table": "InvAmts (from SO_LineItems + Time.csv)",
        "filters_applied": "Year, Month, Operation, Crew Leader",
    },
    "Average of Percent (Gauge)": {
        "formula": "avg(Percent) where Item Name = 'Quality Control'  x  100",
        "description": "Average QC score as a percentage. The letter grade is extracted from Line_Item_Description, mapped to a decimal via the QC scale (A=0.95, B=0.85, etc.), then averaged and scaled to 0-100.",
        "source_table": "Stats (from SO_LineItems via build_stats, filtered to Quality Control)",
        "filters_applied": "Year, Month, Crew Leader",
    },
    "Win/Loss by Month Chart": {
        "formula": "count(Visit Ref #) grouped by MonthShort and WinLossText",
        "description": "Stacked bar chart showing monthly Win vs Loss visit counts.",
        "source_table": "InvAmts (from SO_LineItems + Time.csv)",
        "filters_applied": "Year",
    },
    "Est v Actual Chart": {
        "formula": "HrsActual = sum(TimeByInv) by MonthFull; HoursEst = sum(HoursEst) by MonthFull",
        "description": "Stacked bar chart comparing actual hours worked (from Time.csv) against estimated hours (from Labor line items) each month.",
        "source_table": "InvAmts (from SO_LineItems + Time.csv)",
        "filters_applied": "Year, Operation, Month",
    },
}


# ── Transform-level lineage (for the pipeline overview) ─────────────

TRANSFORM_LINEAGE = {
    "build_so_line_items": {
        "display_name": "Clean & Type Line Items",
        "source": "LineItems_SO_*.csv (all years appended)",
        "key_steps": [
            "Parse date columns from MM/DD/YYYY HH:MM strings",
            "Cast Qty, Unit Cost, Unit Markup, Unit Total, Line Total to float",
            "Cast Billable, Actual to boolean",
            "Strip HTML from Internal Notes, Client Notes, Crew Notes",
            "Parse Review field from JSON array string",
            "Extract Crew Leader from crews field",
            "Derive Year, MonthNum, MonthShort from Approved Date",
        ],
    },
    "build_inv_amts": {
        "display_name": "Invoice Amounts (visit-level fact table)",
        "source": "SO_LineItems (cleaned) + Time.csv",
        "key_steps": [
            "Filter to records with Invoice Date (invoiced work only)",
            "Filter to Billable items",
            "Group by Visit Ref # → aggregate Client, Operation, Crew Leader, Sales Reps",
            "Sum Line Total → InvTotal",
            "Sum Qty for Labor items → HoursEst",
            "Sum Line Total for Material items → Costs",
            "Sum Line Total for Discount items → Discount",
            "Join Time.csv on InvNo (then JobNo as fallback) → TimeByInv",
            "Compute HrsRatio = HoursEst / TimeByInv",
            "Compute WinLossText = Win if HrsRatio >= 1.0 else Loss",
            "Compute NetInv = InvTotal - Costs",
            "Compute EPH = InvTotal / TimeByInv",
        ],
    },
    "build_stats": {
        "display_name": "Stats (crew performance items)",
        "source": "SO_LineItems filtered to stat items",
        "key_steps": [
            "Filter Item Name to: Quality Control, Compliment, Call Back, Crew Feedback",
            "For QC items: extract Percent from Qty column",
            "Lookup Percent → QC Grade via CrewStatLists.xlsx QC sheet",
        ],
    },
    "build_damage": {
        "display_name": "Damage Repair incidents",
        "source": "SO_LineItems",
        "key_steps": ["Filter Item Name = 'Damage Repair'"],
    },
    "build_notes": {
        "display_name": "Notes / Reviews",
        "source": "SO_LineItems",
        "key_steps": ["Filter to records where Review field is not empty"],
    },
    "build_time_detail": {
        "display_name": "Time Tracking Detail",
        "source": "Time.csv",
        "key_steps": [
            "Cast DURATION to float",
            "Parse DATE, WeekStart, WeekEnd to datetime",
            "Rename EMP → Title, JOB → Customer",
            "Derive Operation from ITEM (PHC items vs Tree items)",
        ],
    },
}
