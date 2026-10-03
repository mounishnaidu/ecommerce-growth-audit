"""Phase 1 — E-commerce Growth Audit.
Build the data dictionary workbook from the cleaned SQLite database.
Every (table, column) must have a description — the script fails loudly otherwise.
Output: Olist Data Dictionary.xlsx (uploaded to Drive; local copy is a backup).
"""
import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BASE = Path.home() / "workspace/your_files/ecommerce-growth-audit"
DB = BASE / "data" / "olist.db"
OUT = BASE / "Olist Data Dictionary.xlsx"

TABLES = {
    "orders": ("One row per order",
               "Header record for every purchase attempt: status plus the full timestamp trail from purchase to delivery."),
    "order_items": ("One row per product within an order",
                    "Line items: what was bought, from whom, at what price. Order revenue = SUM(price)."),
    "order_payments": ("One row per payment method used on an order",
                      "How each order was paid; an order can split across methods."),
    "customers": ("One row per customer_id",
                  "Customer master. customer_unique_id identifies the real person across repeat purchases."),
    "order_reviews": ("One row per review (not every order has one)",
                      "Post-delivery satisfaction scores and free-text comments."),
    "products": ("One row per product",
                 "Product catalog master with category and physical dimensions."),
    "sellers": ("One row per seller",
                "Marketplace sellers fulfilling orders."),
    "geolocation": ("One row per zip+coordinate (zips repeat)",
                    "Brazilian zip code to lat/lng reference for mapping. 261,831 exact-duplicate rows removed."),
    "category_translation": ("One row per product category",
                             "Portuguese to English product category names."),
    "mqls": ("One row per marketing qualified lead",
             "Top of the acquisition funnel: leads Olist marketing qualified."),
    "closed_deals": ("One row per won deal",
                     "Bottom of the funnel: MQLs that became Olist sellers. Join to mqls on mql_id for conversion analysis."),
}

# (table, column) -> (description, key, notes)
COLUMNS = {
    ("orders", "order_id"): ("Unique order identifier.", "PK", "Join key to order_items, order_payments, order_reviews."),
    ("orders", "customer_id"): ("Purchasing customer.", "FK -> customers", "One real person can have several customer_ids; see customer_unique_id."),
    ("orders", "order_status"): ("Order state at extract time: delivered, shipped, invoiced, processing, approved, created, canceled, unavailable.", "", ""),
    ("orders", "order_purchase_timestamp"): ("When the customer placed the order.", "", "Basis for acquisition-month cohorts."),
    ("orders", "order_approved_at"): ("When payment was approved.", "", "Missing 0.2% — canceled orders never approved."),
    ("orders", "order_delivered_carrier_date"): ("When the carrier picked up the order.", "", "Missing 1.8% — orders never shipped."),
    ("orders", "order_delivered_customer_date"): ("When the customer received the order.", "", "Missing 3.0% — canceled/unfulfilled orders."),
    ("orders", "order_estimated_delivery_date"): ("Delivery date promised at purchase.", "", "Compare with actual for lateness analysis."),

    ("order_items", "order_id"): ("Order the line item belongs to.", "FK -> orders", "Part of composite PK (order_id, order_item_id)."),
    ("order_items", "order_item_id"): ("Line number within the order (1, 2, 3...).", "PK (composite)", ""),
    ("order_items", "product_id"): ("Product purchased.", "FK -> products", ""),
    ("order_items", "seller_id"): ("Seller fulfilling this line item.", "FK -> sellers", "Each line item can ship from a different seller."),
    ("order_items", "shipping_limit_date"): ("Deadline Olist gave the seller to ship.", "", "Some values fall in 2020, past the order window — source quirk, left as-is."),
    ("order_items", "price"): ("Item selling price in BRL.", "", "Sum per order = order revenue. No negatives found."),
    ("order_items", "freight_value"): ("Freight charged for this item in BRL.", "", ""),

    ("order_payments", "order_id"): ("Order being paid for.", "FK -> orders", ""),
    ("order_payments", "payment_sequential"): ("1, 2, 3... when an order uses more than one payment method.", "", ""),
    ("order_payments", "payment_type"): ("credit_card, boleto, voucher, debit_card, not_defined.", "", ""),
    ("order_payments", "payment_installments"): ("Number of installments (credit_card).", "", "0/1 = paid in full."),
    ("order_payments", "payment_value"): ("Amount paid via this method in BRL.", "", "No negatives found."),

    ("customers", "customer_id"): ("Purchase-level customer key.", "PK", "Join key to orders."),
    ("customers", "customer_unique_id"): ("Stable person identifier across repeat purchases.", "", "Use this — not customer_id — to count repeat buyers."),
    ("customers", "customer_zip_code_prefix"): ("5-digit zip prefix.", "", "Stored as text; leading zeros preserved."),
    ("customers", "customer_city"): ("Customer city.", "", ""),
    ("customers", "customer_state"): ("Customer state (2-letter).", "", ""),

    ("order_reviews", "review_id"): ("Unique review identifier.", "PK", ""),
    ("order_reviews", "order_id"): ("Order being reviewed.", "FK -> orders", ""),
    ("order_reviews", "review_score"): ("Satisfaction score, 1-5 stars.", "", ""),
    ("order_reviews", "review_comment_title"): ("Review headline written by the buyer.", "", "Missing 88.3% — scored without writing a title."),
    ("order_reviews", "review_comment_message"): ("Review body written by the buyer.", "", "Missing 58.7% — scored without writing."),
    ("order_reviews", "review_creation_date"): ("When the review was submitted.", "", ""),
    ("order_reviews", "review_answer_timestamp"): ("When Olist/seller responded.", "", ""),

    ("products", "product_id"): ("Unique product identifier.", "PK", ""),
    ("products", "product_category_name"): ("Category in Portuguese; see category_translation.", "", "610 missing (1.9%) filled with 'unknown' so their revenue stays in totals."),
    ("products", "product_name_lenght"): ("Product name character count (source spelling kept).", "", ""),
    ("products", "product_description_lenght"): ("Description character count (source spelling kept).", "", ""),
    ("products", "product_photos_qty"): ("Number of product photos.", "", ""),
    ("products", "product_weight_g"): ("Weight in grams.", "", "2 missing — negligible, left as-is."),
    ("products", "product_length_cm"): ("Length in cm.", "", ""),
    ("products", "product_height_cm"): ("Height in cm.", "", ""),
    ("products", "product_width_cm"): ("Width in cm.", "", ""),

    ("sellers", "seller_id"): ("Unique seller identifier.", "PK", ""),
    ("sellers", "seller_zip_code_prefix"): ("5-digit zip prefix.", "", "Stored as text; leading zeros preserved."),
    ("sellers", "seller_city"): ("Seller city.", "", ""),
    ("sellers", "seller_state"): ("Seller state (2-letter).", "", ""),

    ("geolocation", "geolocation_zip_code_prefix"): ("5-digit zip prefix.", "", "Stored as text; leading zeros preserved. Zips repeat with different coordinates."),
    ("geolocation", "geolocation_lat"): ("Latitude.", "", ""),
    ("geolocation", "geolocation_lng"): ("Longitude.", "", ""),
    ("geolocation", "geolocation_city"): ("City for this zip.", "", ""),
    ("geolocation", "geolocation_state"): ("State for this zip.", "", ""),

    ("category_translation", "product_category_name"): ("Category name in Portuguese.", "PK", "Join key to products."),
    ("category_translation", "product_category_name_english"): ("Category name in English.", "", ""),

    ("mqls", "mql_id"): ("Unique lead identifier.", "PK", "Join key to closed_deals."),
    ("mqls", "first_contact_date"): ("When the lead first converted.", "", "Basis for funnel cohort timing."),
    ("mqls", "landing_page_id"): ("Landing page that captured the lead.", "", ""),
    ("mqls", "origin"): ("Acquisition channel (paid_search, organic_search, social, email, ...).", "", "60 missing (0.8%) — left as unknown."),

    ("closed_deals", "mql_id"): ("Lead that became a customer.", "FK -> mqls", ""),
    ("closed_deals", "seller_id"): ("Seller account created by the deal.", "FK -> sellers", ""),
    ("closed_deals", "sdr_id"): ("Sales development rep who prospected the lead.", "", ""),
    ("closed_deals", "sr_id"): ("Sales rep who closed the deal.", "", ""),
    ("closed_deals", "won_date"): ("When the deal was won.", "", ""),
    ("closed_deals", "business_segment"): ("Lead's business segment.", "", "1 missing."),
    ("closed_deals", "lead_type"): ("Lead type classification.", "", "6 missing."),
    ("closed_deals", "lead_behaviour_profile"): ("Behavioral profile from marketing.", "", "177 missing (21.0%)."),
    ("closed_deals", "has_company"): ("Whether the lead has a registered company.", "", "779 missing (92.5%) — optional enrichment."),
    ("closed_deals", "has_gtin"): ("Whether products have GTIN barcodes.", "", "778 missing (92.4%) — optional enrichment."),
    ("closed_deals", "average_stock"): ("Declared average stock.", "", "776 missing (92.2%) — optional enrichment."),
    ("closed_deals", "business_type"): ("Type of business.", "", "10 missing."),
    ("closed_deals", "declared_product_catalog_size"): ("Declared catalog size.", "", "773 missing (91.8%) — optional enrichment."),
    ("closed_deals", "declared_monthly_revenue"): ("Declared monthly revenue.", "", "Optional enrichment."),
}


def style_header(ws, ncols):
    fill = PatternFill("solid", fgColor="1F4E5F")
    font = Font(bold=True, color="FFFFFF")
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(ncols)}1"


def main():
    con = sqlite3.connect(DB)
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

    # coverage check: every column documented, no extras
    actual = set()
    for t in tables:
        for r in con.execute(f"PRAGMA table_info({t})"):
            actual.add((t, r[1]))
    documented = set(COLUMNS)
    assert set(TABLES) == set(tables), f"table mismatch: {set(tables) ^ set(TABLES)}"
    assert actual == documented, (
        f"undocumented: {sorted(actual - documented)}; stale: {sorted(documented - actual)}")

    wb = Workbook()
    wb.properties.title = "Olist E-commerce — Data Dictionary"

    ws = wb.active
    ws.title = "Tables"
    ws.append(["Table", "Rows", "Grain (one row = ...)", "Description"])
    for t in tables:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        grain, desc = TABLES[t]
        ws.append([t, n, grain, desc])
    style_header(ws, 4)
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 38
    ws.column_dimensions["D"].width = 90

    ws2 = wb.create_sheet("Columns")
    ws2.append(["Table", "Column", "Type", "Key", "Description", "Example", "Notes"])
    for t in tables:
        info = {r[1]: r[2] for r in con.execute(f"PRAGMA table_info({t})")}
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for col, typ in info.items():
            desc, key, notes = COLUMNS[(t, col)]
            ex = con.execute(
                f'SELECT "{col}" FROM {t} WHERE "{col}" IS NOT NULL LIMIT 1').fetchone()
            ex = "" if ex is None else str(ex[0])
            miss = con.execute(
                f'SELECT COUNT(*) FROM {t} WHERE "{col}" IS NULL').fetchone()[0]
            note_bits = []
            if miss:
                note_bits.append(f"missing {miss:,} ({miss/n:.1%})")
            if notes:
                note_bits.append(notes)
            ws2.append([t, col, typ, key, desc, ex, " ".join(note_bits)])
    style_header(ws2, 7)
    for col, w in zip("ABCDEFG", [20, 32, 12, 16, 70, 28, 60]):
        ws2.column_dimensions[col].width = w

    con.close()
    wb.save(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
