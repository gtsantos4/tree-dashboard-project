"""Global configuration: colors, constants, field mappings, dev mode."""
import os

# ── Dev Mode ──────────────────────────────────────────────────────
# Set DASHBOARD_MODE=dev to see lineage inspector + debug expanders
_mode = os.environ.get("DASHBOARD_MODE", "").lower()
DEV_MODE = _mode == "dev"

# ── Paths ────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "sample-data")

# ── Van Yahres Brand Palette ─────────────────────────────────────
VY_RED = "#9B2335"
VY_RED_DARK = "#7A1C2A"
VY_RED_LIGHT = "#C4384D"
VY_RED_TINT = "#FDF2F3"

SIDEBAR_DARK = "#1E1E2E"
BG_PAGE = "#F3F4F6"
BORDER_COLOR = "#E5E7EB"
MEDIUM_GRAY = "#6B7280"
BG_WHITE = "#FFFFFF"

WIN_COLOR = "#059669"       # emerald green  (was #2E7D32)
LOSS_COLOR = "#DC2626"      # bright red     (was #C62828)
WIN_BG = "#ECFDF5"          # light green row tint
LOSS_BG = "#FEF2F2"         # light red row tint

STAR_GOLD = "#DAA520"
BOX_DARK_RED = VY_RED       # was #8B0000, now matches brand

# Backward-compat aliases (anything still referencing old names gets VY_RED)
ACCENT_BLUE = VY_RED
HEADER_STEEL = VY_RED

WINLOSS_COLORS = {"Win": WIN_COLOR, "Loss": LOSS_COLOR}

# ── Stats item names (from SingleOps) ────────────────────────────
STAT_ITEMS = ["Quality Control", "Compliment", "Call Back", "Crew Feedback"]
DAMAGE_ITEM = "Damage Repair"

# ── Aggregation function map (PowerBI enum → name) ──────────────
AGG_MAP = {0: "Sum", 1: "Avg", 2: "Count", 3: "Min", 4: "Max", 5: "CountNonNull"}

# ── Month ordering helpers ───────────────────────────────────────
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_FULL_ORDER = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]
MONTH_SHORT_TO_NUM = {m: i + 1 for i, m in enumerate(MONTH_ORDER)}

# ── Default page config ─────────────────────────────────────────
PAGE_TITLE = "Van Yahres Tree Company"
PAGE_ICON = "🌳"
