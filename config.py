"""Global configuration: colors, constants, field mappings."""
import os

# ── Paths ────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "sample-data")

# ── Color palette (matches PowerBI report) ───────────────────────────
WIN_COLOR = "#2E7D32"       # dark green
LOSS_COLOR = "#C62828"      # dark red
ACCENT_BLUE = "#003366"     # sidebar / header blue
HEADER_STEEL = "#4472C4"    # table header blue
BG_WHITE = "#FFFFFF"
LIGHT_GRAY = "#F5F5F5"
STAR_GOLD = "#DAA520"
BOX_DARK_RED = "#8B0000"

WINLOSS_COLORS = {"Win": WIN_COLOR, "Loss": LOSS_COLOR}

# ── Stats item names (from SingleOps) ────────────────────────────────
STAT_ITEMS = ["Quality Control", "Compliment", "Call Back", "Crew Feedback"]
DAMAGE_ITEM = "Damage Repair"

# ── Aggregation function map (PowerBI enum → name) ──────────────────
AGG_MAP = {0: "Sum", 1: "Avg", 2: "Count", 3: "Min", 4: "Max", 5: "CountNonNull"}

# ── Month ordering helpers ──────────────────────────────────────────
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL_ORDER = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
MONTH_SHORT_TO_NUM = {m: i + 1 for i, m in enumerate(MONTH_ORDER)}

# ── Default page config ─────────────────────────────────────────────
PAGE_TITLE = "Tree Care Operations Dashboard"
PAGE_ICON = "🌳"
