# Design Implementation Plan

## Reference
Open `design-system.html` in a browser to see the full visual mockup.

---

## 1. Update `config.py` — New Color Palette

Replace the current PowerBI-derived colors with the Van Yahres brand palette:

| Token | Old | New | Usage |
|-------|-----|-----|-------|
| `ACCENT` (primary) | `#003366` | `#9B2335` | Headers, active nav, table headers, KPI accents |
| `WIN_COLOR` | `#2E7D32` | `#059669` | Win rows, donut, success indicators |
| `LOSS_COLOR` | `#C62828` | `#DC2626` | Loss rows, donut, alert indicators |
| `HEADER_STEEL` | `#4472C4` | `#9B2335` | Table header background |
| `STAR_GOLD` | `#DAA520` | `#DAA520` | Keep as-is |
| `BOX_DARK_RED` | `#8B0000` | `#9B2335` | Align with brand red |
| *new* `BG_PAGE` | — | `#F3F4F6` | Page background |
| *new* `BG_CARD` | — | `#FFFFFF` | Card background |
| *new* `BORDER` | — | `#E5E7EB` | Subtle borders |
| *new* `SIDEBAR_DARK` | — | `#1E1E2E` | Sidebar background |
| *new* `VY_RED_TINT` | — | `#FDF2F3` | Hover/tint background |
| *new* `WIN_BG` | — | `#ECFDF5` | Win row background |
| *new* `LOSS_BG` | — | `#FEF2F2` | Loss row background |

---

## 2. Update `app.py` — Global CSS Overhaul

Replace the current `<style>` block with comprehensive CSS that styles all Streamlit elements:

- **Page background**: `#F3F4F6` (light gray)
- **Sidebar**: `#1E1E2E` dark background, white text, active item highlighted with VY Red
- **Logo**: Add Van Yahres logo image to sidebar (save logo to `assets/logo.png`)
- **Font**: Import Inter from Google Fonts via `<link>` tag
- **Block container**: Adequate top padding for nav, clean margins
- **Cards** (`.stMetric`, expanders): White bg, subtle shadow, rounded corners (16px), 1px border
- **Table headers** (`.stDataFrame th`): VY Red background, white text
- **Table hover**: Red tint on row hover
- **Filters** (`.stSelectbox`, `.stMultiSelect`): Gray bg inputs, uppercase labels
- **Buttons**: VY Red primary, light gray secondary
- **Popover** (lineage buttons): Styled to match brand

### Key CSS Targets
```
[data-testid="stSidebar"]           → dark bg, logo, grouped nav
.block-container                    → page bg, padding
[data-testid="stMetric"]            → card styling
.stDataFrame th                     → red header
[data-testid="stExpander"]          → border, radius
.stSelectbox label                  → uppercase, small, gray
[data-testid="stPopover"] button    → red accent
```

---

## 3. Add Logo Asset

- Save the Van Yahres logo as `assets/logo.png` (white-on-transparent version)
- Display in sidebar using `st.sidebar.image("assets/logo.png")`
- Add "Operations Dashboard" subtitle below

---

## 4. Update `components/kpi_cards.py` — Redesigned Metric Cards

Replace the current `metric_card()` HTML with the new design:

- White card with subtle shadow and border
- **3px red accent bar** at top
- Label: 12px uppercase, gray
- Value: 32px bold, dark
- Optional icon badge (top-right corner)
- Lineage button styled consistently

---

## 5. Update `components/styled_table.py` — Refined Table Styles

- Win row: `#ECFDF5` (softer green)
- Loss row: `#FEF2F2` (softer red)
- Win text: `#059669`
- Loss text: `#DC2626`
- Add dark totals bar component for pages that show totals (Owner, WinLoss Details)

---

## 6. Update `components/lineage_inspector.py` — Styled Inspector

- Row inspector: red left-border, light gray background
- Calculation steps: white cards with red-light left border, monospace formula text
- Tabs: clean styling consistent with brand
- Popover button: red accent text

---

## 7. Update Individual Pages — Layout Polish

### All pages:
- Replace `st.markdown("#### Title")` with a styled page header component
- Wrap filter controls in a visual "filter bar" container using `st.container()`
- Ensure consistent spacing between sections

### Page-specific:
- **Owner page**: Add dark totals bar below the table
- **Crew Leader Stats**: Ensure KPI cards use the new icon badges
- **WinLoss Details**: Use the refined Win/Loss row colors

---

## 8. Files to Modify

| File | Changes |
|------|---------|
| `config.py` | New color constants |
| `app.py` | Complete CSS rewrite, sidebar logo, Inter font |
| `components/kpi_cards.py` | Redesigned metric_card HTML |
| `components/styled_table.py` | New Win/Loss colors, totals bar |
| `components/lineage_inspector.py` | Styled inspector panels |
| `components/filters.py` | Optional: styled filter bar wrapper |
| `pages/1-10` | Page headers, layout spacing |
| *new* `assets/logo.png` | Logo file for sidebar |

---

## 9. Implementation Order

1. **config.py** — swap colors (5 min)
2. **app.py** — full CSS rewrite + logo (30 min)
3. **kpi_cards.py** — new card design (15 min)
4. **styled_table.py** — new colors + totals bar (10 min)
5. **lineage_inspector.py** — styled panels (10 min)
6. **Pages 1-10** — headers + spacing (20 min)
7. **Test** — visual check across all pages (10 min)

Total estimated: ~1.5 hours
