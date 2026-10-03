"""Phase 4 — Dashboard extracts.
Builds clean, analysis-ready CSVs for the Tableau Public dashboard, plus
one new cut: delivery lateness vs review score.
All revenue on DELIVERED orders. Customers = customer_unique_id.
Output: dashboard_extracts/*.csv (zipped for Drive upload).
"""
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd

BASE = Path.home() / "workspace/your_files/ecommerce-growth-audit"
OUT = BASE / "dashboard_extracts"
OUT.mkdir(exist_ok=True)
con = sqlite3.connect(BASE / "data" / "olist.db")

# ---------- shared: delivered orders with revenue ----------
orders = pd.read_sql(
    "SELECT order_id, customer_id, order_purchase_timestamp, "
    "       order_delivered_customer_date, order_estimated_delivery_date "
    "FROM orders WHERE order_status = 'delivered'", con,
    parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                 "order_estimated_delivery_date"])
customers = pd.read_sql(
    "SELECT customer_id, customer_unique_id, customer_state FROM customers", con)
items = pd.read_sql("SELECT order_id, product_id, price FROM order_items", con)
prods = pd.read_sql(
    "SELECT p.product_id, "
    "COALESCE(t.product_category_name_english, 'unknown') AS category "
    "FROM products p LEFT JOIN category_translation t "
    "ON p.product_category_name = t.product_category_name", con)
pays = pd.read_sql(
    "SELECT order_id, payment_type, payment_value, payment_installments "
    "FROM order_payments", con)
reviews = pd.read_sql("SELECT order_id, review_score FROM order_reviews", con)
# 551 orders have 2 reviews: collapse to one row per order (mean score)
# so the order-grain merge below doesn't fan out and double-count revenue
reviews = reviews.groupby("order_id")["review_score"].mean().reset_index()
mqls = pd.read_sql("SELECT mql_id, origin FROM mqls", con)
deals = pd.read_sql("SELECT mql_id, won_date FROM closed_deals",
                    con, parse_dates=["won_date"])
mqls_full = pd.read_sql("SELECT * FROM mqls", con,
                        parse_dates=["first_contact_date"])

d = orders.merge(customers, on="customer_id", how="left")
d = d.merge(items.groupby("order_id")["price"].sum().rename("order_revenue"),
            on="order_id", how="left")
d = d.merge(reviews, on="order_id", how="left")

# ---------- 1. KPI summary ----------
_ttc = deals[["mql_id", "won_date"]].merge(
    mqls_full[["mql_id", "first_contact_date"]], on="mql_id", how="left")
median_close = int((_ttc.won_date - _ttc.first_contact_date).dt.days.median())
kpis = pd.DataFrame([
    ("Total revenue (BRL, delivered)", round(d.order_revenue.sum(), 0)),
    ("Delivered orders", orders.order_id.nunique()),
    ("Customers", d.customer_unique_id.nunique()),
    ("Average order value (BRL)", round(d.order_revenue.sum() / len(d), 2)),
    ("Average review score (1-5)", round(d.review_score.mean(), 2)),
    ("Funnel conversion MQL -> won",
     round(len(deals) / len(mqls) * 100, 1)),
    ("Median days MQL -> won", median_close),
])
kpis.columns = ["metric", "value"]
kpis.to_csv(OUT / "kpi_summary.csv", index=False)

# on-time delivery KPI (append)
late = (d.order_delivered_customer_date - d.order_estimated_delivery_date).dt.days
ontime = pd.DataFrame([("On-time delivery %", round((late <= 0).mean() * 100, 1))],
                      columns=["metric", "value"])
pd.concat([kpis, ontime]).to_csv(OUT / "kpi_summary.csv", index=False)

# ---------- 2. funnel by channel ----------
f = mqls_full.merge(deals[["mql_id", "won_date"]], on="mql_id",
                    how="left", indicator=True)
f["won"] = (f["_merge"] == "both").astype(int)
f["days_to_close"] = (f["won_date"] - f["first_contact_date"]).dt.days
funnel = (f.groupby("origin", dropna=False)
          .agg(mqls=("won", "size"), won=("won", "sum"),
               median_days_to_close=("days_to_close", "median"))
          .reset_index())
funnel["conv_rate_pct"] = (funnel.won / funnel.mqls * 100).round(1)
funnel["origin"] = funnel.origin.fillna("missing")
funnel.sort_values("mqls", ascending=False).to_csv(
    OUT / "funnel_by_channel.csv", index=False)

# ---------- 3. revenue by category / state / payment ----------
rev_cat = (items.merge(prods, on="product_id")
           .merge(orders[["order_id"]], on="order_id")  # delivered only
           .groupby("category")
           .agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
           .reset_index().sort_values("revenue", ascending=False))
rev_cat["share_pct"] = (rev_cat.revenue / rev_cat.revenue.sum() * 100).round(2)
rev_cat.to_csv(OUT / "revenue_by_category.csv", index=False)

rev_state = (d.groupby("customer_state")
             .agg(revenue=("order_revenue", "sum"),
                  orders=("order_id", "nunique"),
                  customers=("customer_unique_id", "nunique"))
             .reset_index().sort_values("revenue", ascending=False))
rev_state["share_pct"] = (rev_state.revenue / rev_state.revenue.sum() * 100).round(2)
rev_state["aov"] = (rev_state.revenue / rev_state.orders).round(2)
rev_state.to_csv(OUT / "revenue_by_state.csv", index=False)

rev_pay = (pays.groupby("payment_type")
           .agg(revenue=("payment_value", "sum"),
                orders=("order_id", "nunique"),
                avg_installments=("payment_installments", "mean"))
           .reset_index().sort_values("revenue", ascending=False))
rev_pay["share_pct"] = (rev_pay.revenue / rev_pay.revenue.sum() * 100).round(2)
rev_pay.to_csv(OUT / "revenue_by_payment.csv", index=False)

# ---------- 4. cohort matrix (long format for Tableau heatmap) ----------
dd = d[["customer_unique_id", "order_id", "order_purchase_timestamp"]].copy()
dd["cohort"] = (dd.groupby("customer_unique_id")["order_purchase_timestamp"]
                .transform("min").dt.to_period("M").astype(str))
dd["omonth"] = dd["order_purchase_timestamp"].dt.to_period("M")
dd["n_month"] = (pd.PeriodIndex(dd["omonth"], freq="M").asi8 -
                 pd.PeriodIndex(dd["cohort"], freq="M").asi8)
coh_size = dd.groupby("cohort")["customer_unique_id"].nunique()
mat = (dd.groupby(["cohort", "n_month"])["customer_unique_id"].nunique()
       .reset_index(name="active"))
mat["retention_pct"] = (mat["active"] / mat["cohort"].map(coh_size) * 100).round(2)
mat[mat.n_month <= 5].to_csv(OUT / "cohort_matrix.csv", index=False)

# ---------- 5. RFM segments ----------
MAXD = d.order_purchase_timestamp.max()
rfm = (d.groupby("customer_unique_id")
       .agg(last=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("order_revenue", "sum")).reset_index())
rfm["recency_days"] = (MAXD - rfm["last"]).dt.days


def q(s, n, rev=False):
    r = s.rank(pct=True, method="first")
    if rev:
        r = 1 - r
    return pd.qcut(r, n, labels=list(range(1, n + 1))).astype(int)


rfm["R"] = q(rfm.recency_days, 5, rev=True)
rfm["F"] = rfm.frequency.map(lambda x: 1 if x == 1 else (3 if x == 2 else 5))
rfm["M"] = q(rfm.monetary, 5)


def segment(r):
    if r["R"] >= 4 and r["F"] >= 4:
        return "Champions"
    if r["F"] >= 4:
        return "Loyal"
    if r["R"] >= 4:
        return "New / one-time"
    if r["R"] <= 2 and r["F"] >= 3:
        return "At risk"
    if r["R"] <= 2:
        return "Hibernating"
    return "Potential"


rfm["segment"] = rfm.apply(segment, axis=1)
seg = (rfm.groupby("segment")
       .agg(customers=("monetary", "size"),
            avg_ltv=("monetary", "mean"),
            total_revenue=("monetary", "sum"),
            avg_orders=("frequency", "mean")).reset_index())
seg["rev_share_pct"] = (seg.total_revenue / seg.total_revenue.sum() * 100).round(2)
seg.round({"avg_ltv": 2, "total_revenue": 0, "avg_orders": 2}) \
   .to_csv(OUT / "rfm_segments.csv", index=False)

# ---------- 6. delivery lateness vs reviews ----------
dl = d[d.review_score.notna() &
       d.order_delivered_customer_date.notna()].copy()
dl["days_late"] = (dl.order_delivered_customer_date -
                   dl.order_estimated_delivery_date).dt.days


def bucket(x):
    if x <= 0:
        return "On time / early"
    if x <= 3:
        return "1-3 days late"
    if x <= 7:
        return "4-7 days late"
    return "8+ days late"


dl["lateness"] = dl.days_late.map(bucket)
lab = (dl.groupby("lateness")
       .agg(orders=("order_id", "nunique"),
            avg_review=("review_score", "mean"))
       .reset_index())
order = ["On time / early", "1-3 days late", "4-7 days late", "8+ days late"]
lab["lateness"] = pd.Categorical(lab.lateness, order, ordered=True)
lab.sort_values("lateness").round({"avg_review": 2}) \
   .to_csv(OUT / "delivery_vs_reviews.csv", index=False)

con.close()

# ---------- zip ----------
zpath = BASE / "dashboard_extracts.zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for csv in sorted(OUT.glob("*.csv")):
        z.write(csv, f"dashboard_extracts/{csv.name}")
print(f"wrote {zpath} ({zpath.stat().st_size/1024:.0f} KB): "
      f"{len(list(OUT.glob('*.csv')))} CSVs")
