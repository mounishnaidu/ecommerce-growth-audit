"""Build spec for the Tableau Public dashboard (Phase 4).
Generates: Tableau Dashboard - Build Spec.docx
The dashboard itself is assembled by Mounish in Tableau Public; this spec
makes every sheet mechanical. Data: dashboard_extracts.zip (same Drive folder).
"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = ("/home/hatch/workspace/goals/data-skills-learning-from-scratch/files/"
       "ecommerce-growth-audit/Tableau Dashboard - Build Spec.docx")

doc = Document()
doc.core_properties.title = "Tableau Dashboard - Build Spec"
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)


def h1(t):
    doc.add_heading(t, level=1)


def h2(t):
    doc.add_heading(t, level=2)


def para(t, bold=False):
    p = doc.add_paragraph()
    r = p.add_run(t)
    r.bold = bold
    return p


def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


t = doc.add_paragraph()
r = t.add_run("Tableau Dashboard — Build Spec")
r.bold = True
r.font.size = Pt(22)
sub = doc.add_paragraph()
r = sub.add_run("E-commerce Growth Audit  |  Phase 4")
r.font.size = Pt(12)
r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

h1("What you're building")
para("Two Tableau Public dashboards from 8 pre-built CSV extracts "
     "(dashboard_extracts.zip, same Drive folder). Each CSV is its own data "
     "source — no joins needed in Tableau; all aggregation is done.")
bullets([
    "Dashboard 1 — Growth Overview: KPI BANs, funnel by channel, revenue by category, payment mix.",
    "Dashboard 2 — Customer Economics: cohort heatmap, RFM segments, revenue map by state, delivery vs reviews.",
])
para("Expected build time: 30-45 minutes of drag-and-drop.", bold=True)

h1("The 8 data files")
files = [
    ("kpi_summary.csv", "8 rows: metric | value. One row per KPI BAN."),
    ("funnel_by_channel.csv", "origin | mqls | won | conv_rate_pct | median_days_to_close."),
    ("revenue_by_category.csv", "category | revenue | orders | share_pct. Sorted desc."),
    ("revenue_by_state.csv", "customer_state | revenue | orders | customers | share_pct | aov."),
    ("revenue_by_payment.csv", "payment_type | revenue | orders | avg_installments | share_pct."),
    ("cohort_matrix.csv", "cohort | n_month | active | retention_pct. Long format, months 0-5."),
    ("rfm_segments.csv", "segment | customers | avg_ltv | total_revenue | avg_orders | rev_share_pct."),
    ("delivery_vs_reviews.csv", "lateness | orders | avg_review. 4 buckets, pre-ordered."),
]
table = doc.add_table(rows=1, cols=2)
table.style = "Light Grid Accent 1"
table.rows[0].cells[0].text = "File"
table.rows[0].cells[1].text = "Contents"
for name, desc in files:
    row = table.add_row().cells
    row[0].text = name
    row[1].text = desc

h1("Sheet-by-sheet spec")
sheets = [
    ("1. KPI BANs (x8)",
     "kpi_summary.csv",
     "8 tiny worksheets, one per metric. Type: Text table. Put metric on Rows, "
     "value on Text, format value as big bold number (22pt). Title each sheet with "
     "the metric name. Arrange 4 per row on the dashboard."),
    ("2. Funnel by channel",
     "funnel_by_channel.csv",
     "Horizontal bar. Rows: origin (sort descending by conv_rate_pct). "
     "Columns: conv_rate_pct. Color: conv_rate_pct (sequential blue). "
     "Label: conv_rate_pct as %. Tooltip: mqls, won, median_days_to_close. "
     "Title: 'MQL to won conversion by channel'."),
    ("3. Revenue by category",
     "revenue_by_category.csv",
     "Horizontal bar, top 12. Rows: category (sort by revenue desc). Columns: revenue. "
     "Color: revenue (sequential green). Label: share_pct. "
     "Title: 'Revenue by category (delivered, BRL)'."),
    ("4. Revenue map by state",
     "revenue_by_state.csv",
     "Filled map. Tableau auto-recognizes Brazilian states from customer_state. "
     "Color: revenue (sequential). Tooltip: revenue, share_pct, aov, orders. "
     "Title: 'Revenue by state — the Southeast is the business'."),
    ("5. Payment mix",
     "revenue_by_payment.csv",
     "Donut (pie with white circle overlay) on share_pct by payment_type. "
     "Beside it, a small bar of avg_installments by payment_type. "
     "Title: 'How customers pay'."),
    ("6. Cohort heatmap",
     "cohort_matrix.csv",
     "Highlight table. Rows: cohort. Columns: n_month. Color: retention_pct "
     "(white-to-red sequential, 0 fixed at white). Text: retention_pct as %. "
     "Title: 'Repeat purchase by acquisition cohort (%)'. Expect mostly pale — "
     "that IS the finding (1.65% 6-month repeat)."),
    ("7. RFM segments",
     "rfm_segments.csv",
     "Side-by-side bars or treemap. Show customers AND rev_share_pct per segment "
     "(dual axis or two sheets). Sort by customers desc. "
     "Title: 'RFM segments — the inverted Pareto'. Annotation: Champions+Loyal "
     "= 228 customers, 0.7% of revenue."),
    ("8. Delivery vs reviews",
     "delivery_vs_reviews.csv",
     "Bar. Columns: lateness in the given order (it is pre-ordered). "
     "Rows: avg_review. Color: avg_review (red-yellow-green diverging, "
     "center 3). Label orders on each bar. "
     "Title: 'Late delivery kills reviews (4.3 -> 1.7 stars)'."),
]
for title, src, spec in sheets:
    h2(title)
    para("Data: " + src, bold=True)
    para(spec)

h1("Dashboard layouts")
h2("Dashboard 1 — Growth Overview (fits 1280x800)")
bullets([
    "Top: 8 KPI BANs in two rows of four.",
    "Middle left: Funnel by channel. Middle right: Revenue by category.",
    "Bottom: Payment mix donut + Revenue map by state side by side.",
])
h2("Dashboard 2 — Customer Economics")
bullets([
    "Top: Cohort heatmap (wide).",
    "Bottom left: RFM segments. Bottom right: Delivery vs reviews.",
])
para("Add a text box on each dashboard with the one-line takeaway "
     "(e.g. Dashboard 2: 'Only 1.65% of customers order again within 6 months — "
     "growth must come from acquisition and first-order value.').", bold=True)

h1("Publish to Tableau Public")
bullets([
    "Server menu -> Tableau Public -> Save to Tableau Public (sign in).",
    "Name it 'E-commerce Growth Audit — Olist'.",
    "Copy the public link into the plan doc's Phase 4 deliverable line and the GitHub README.",
])

doc.save(OUT)
print("saved", OUT)
