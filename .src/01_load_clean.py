"""Phase 1 — E-commerce Growth Audit.
Load Olist CSVs into SQLite, run quality checks, clean, write cleaned tables.
Reproducible: re-running rebuilds data/olist.db from data/olist + data/funnel.
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path.home() / "workspace/your_files/ecommerce-growth-audit" / "data"
DB = BASE / "olist.db"

FILES = {
    # orders domain
    "orders": ("olist/olist_orders_dataset.csv", None),
    "order_items": ("olist/olist_order_items_dataset.csv", None),
    "order_payments": ("olist/olist_order_payments_dataset.csv", None),
    "customers": ("olist/olist_customers_dataset.csv", None),
    "order_reviews": ("olist/olist_order_reviews_dataset.csv", None),
    "products": ("olist/olist_products_dataset.csv", None),
    "sellers": ("olist/olist_sellers_dataset.csv", None),
    "geolocation": ("olist/olist_geolocation_dataset.csv", None),
    "category_translation": ("olist/product_category_name_translation.csv", None),
    # funnel domain
    "mqls": ("funnel/olist_marketing_qualified_leads_dataset.csv", None),
    "closed_deals": ("funnel/olist_closed_deals_dataset.csv", None),
}

DATE_COLS = {
    "orders": ["order_purchase_timestamp", "order_approved_at",
               "order_delivered_carrier_date", "order_delivered_customer_date",
               "order_estimated_delivery_date"],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
    "mqls": ["first_contact_date"],
    "closed_deals": ["won_date"],
}
# Zip prefixes are identifiers, not numbers — keep leading zeros.
STR_COLS = {
    "customers": ["customer_zip_code_prefix"],
    "sellers": ["seller_zip_code_prefix"],
    "geolocation": ["geolocation_zip_code_prefix"],
}

report = []


def qa(name, df):
    lines = [f"--- {name}: {df.shape[0]:,} rows x {df.shape[1]} cols"]
    miss = df.isna().sum()
    miss = miss[miss > 0].sort_values(ascending=False)
    for col, n in miss.items():
        lines.append(f"  missing {col}: {n:,} ({n/len(df):.1%})")
    dupes = df.duplicated().sum()
    lines.append(f"  exact-duplicate rows: {dupes:,}")
    for col in DATE_COLS.get(name, []):
        s = pd.to_datetime(df[col], errors="coerce")
        lines.append(f"  {col}: {s.min()} -> {s.max()}")
    report.append("\n".join(lines))


def clean(name, df):
    df = df.copy()
    for col in DATE_COLS.get(name, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in STR_COLS.get(name, []):
        df[col] = df[col].astype("string").str.zfill(5)
    if name == "products":
        n = df["product_category_name"].isna().sum()
        df["product_category_name"] = df["product_category_name"].fillna("unknown")
        report.append(f"products: filled {n:,} missing category names with 'unknown'")
    # money columns: flag (don't silently drop) impossible negatives
    for col in ["price", "freight_value", "payment_value"]:
        if col in df.columns:
            neg = (df[col] < 0).sum()
            if neg:
                report.append(f"WARNING {name}.{col}: {neg:,} negative values")
    df = df.drop_duplicates()
    return df


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    for name, (rel, _) in FILES.items():
        df = pd.read_csv(BASE / rel)
        qa(name, df)          # quality check on RAW data
        df = clean(name, df)  # then clean
        df.to_sql(name, con, index=False, if_exists="replace")
        report.append(f"{name}: wrote {len(df):,} cleaned rows to SQLite")
    # indexes on join keys for Phase 2/3 queries
    idx = [
        ("orders", "order_id"), ("orders", "customer_id"),
        ("order_items", "order_id"), ("order_items", "product_id"),
        ("order_items", "seller_id"), ("order_payments", "order_id"),
        ("customers", "customer_id"), ("order_reviews", "order_id"),
        ("products", "product_id"), ("sellers", "seller_id"),
        ("mqls", "mql_id"), ("closed_deals", "mql_id"),
    ]
    for tbl, col in idx:
        con.execute(f"CREATE INDEX IF NOT EXISTS ix_{tbl}_{col} ON {tbl}({col})")
    con.commit()
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    report.append(f"SQLite tables: {tables}")
    con.close()
    text = "\n".join(report)
    (BASE / "qa_report.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
