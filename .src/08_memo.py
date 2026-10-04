"""Builds the 2-page growth audit memo docx."""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "/home/hatch/workspace/your_files/ecommerce-growth-audit/Growth Audit Memo.docx"
DASHBOARD = "https://public.tableau.com/app/profile/mounish.naidu/viz/E-commerceGrowthAuditOlist/GrowthOverview"
REPO = "https://github.com/mounishnaidu/ecommerce-growth-audit"

doc = Document()
doc.core_properties.title = "E-commerce Growth Audit - Memo"
doc.core_properties.author = "Mounish Naidu"

style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

def title_block():
    t = doc.add_paragraph()
    r = t.add_run("E-commerce Growth Audit")
    r.bold = True
    r.font.size = Pt(22)
    sub = doc.add_paragraph()
    r = sub.add_run("Olist Brazilian Marketplace  |  Mounish Naidu  |  October 2026")
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

def h(text):
    doc.add_heading(text, level=1)

def para(text, bold=False, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    return p

def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")

title_block()

h("Executive Summary")
para("Olist is a ~100,000-order Brazilian marketplace (2016-2018) with a B2B seller-acquisition "
     "funnel attached. The audit finds a business that acquires efficiently through one channel, "
     "monetizes exactly once, and almost never sees the customer again. Growth therefore comes "
     "from three levers: cheaper efficient acquisition, bigger first orders, and protecting the "
     "delivery experience that fuels reviews.")

h("Finding 1 - One channel earns its keep; the rest don't")
para("8,000 MQLs become 842 closed-won deals: a 10.5% conversion rate with a median 14 days to "
     "close. Paid search converts at 12.3% with real volume - the only proven scale channel. "
     "Social (5.6%) and email (3.0%) convert at less than half that rate. And 16.3% of won deals "
     "carry an unknown origin: the attribution system is leaking at the exact moment it should "
     "be informing budget decisions.")

h("Finding 2 - Customers buy once and leave")
para("97.8% of customers never place a second delivered order within 180 days; the fairly-observed "
     "6-month repeat rate is 1.65%, flat across acquisition cohorts. Historical LTV (BRL 141.62) "
     "barely exceeds AOV (BRL 137.04) - the second purchase most retention models assume simply "
     "doesn't happen. A leakage-free churn classifier (AUC 0.55) confirms repeat behavior is "
     "essentially unpredictable from first-order signals. Retention marketing here is fighting "
     "arithmetic, not competitors.")

h("Finding 3 - Revenue is concentrated and operationally fragile")
para("SP + RJ drive 51.6% of delivered revenue; the top 5 product categories drive 39.8%. "
     "Meanwhile 93.2% of orders arrive on time - but when they don't, reviews collapse from "
     "4.29 stars to 1.70 stars at 8+ days late. In a marketplace, ratings are acquisition "
     "infrastructure: every late delivery burns the social proof the next buyer reads.")

h("Recommendation 1 - Reallocate spend to paid search and fix attribution")
para("Shift budget from social/email into paid search, and instrument origin capture to shrink "
     "the 16.3% unknown bucket. Illustrative impact: lifting blended MQL-to-won conversion from "
     "10.5% to 12.5% on 8,000 MQLs yields roughly 160 additional won deals per cycle - without "
     "spending more.")

h("Recommendation 2 - Grow the first order, not the second")
para("With LTV approximately equal to AOV, every real of AOV growth is nearly a real of LTV "
     "growth. Prioritize bundles, free-shipping thresholds, and cross-sell at checkout over "
     "retention programs. Illustrative: a 10% AOV lift (BRL 137 to BRL 151) across ~96,000 "
     "delivered orders is roughly BRL 1.3M in incremental revenue.")

h("Recommendation 3 - Treat on-time delivery as a growth lever")
para("Late delivery doesn't just annoy buyers; it burns the review base that drives marketplace "
     "conversion. Tighten fulfillment SLAs on the worst lanes and set honest delivery expectations "
     "at checkout. Defending the 4.29-star base protects rating-driven organic acquisition - "
     "the cheapest acquisition there is.")

h("What the data can't tell us")
para("Read this before quoting the memo:", italic=True)
bullets([
    "No channel-spend data: channel efficiency is judged on conversion, not true CAC or ROAS.",
    "No COGS or margin data: revenue findings are not profit findings.",
    "No session, cart, or checkout events: the checkout funnel can't be diagnosed.",
    "The funnel (B2B seller acquisition) and the orders (B2C purchases) are different motions - they don't join into one funnel.",
])

h("Appendix - Reproduce it")
bullets([
    "Interactive dashboard: " + DASHBOARD,
    "Code and analysis: " + REPO,
    "Dashboard extracts and build spec: project Drive folder.",
])

doc.save(OUT)
print("saved", OUT)
