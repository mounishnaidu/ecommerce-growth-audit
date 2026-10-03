"""Phase 2/3 (rest) — Revenue cuts, acquisition cohorts, RFM + LTV.
Revenue = SUM(order_items.price) on DELIVERED orders only.
Customers are identified by customer_unique_id (real person).
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path.home() / "workspace/your_files/ecommerce-growth-audit"
con = sqlite3.connect(BASE / "data" / "olist.db")

# ---------- 1. REVENUE CUTS ----------
rev_cat = pd.read_sql("""
    SELECT COALESCE(t.product_category_name_english, 'unknown') AS category,
           SUM(oi.price) AS revenue,
           COUNT(DISTINCT o.order_id) AS orders
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation t
      ON p.product_category_name = t.product_category_name
    WHERE o.order_status = 'delivered'
    GROUP BY 1 ORDER BY revenue DESC""", con)
total_rev = rev_cat.revenue.sum()
print(f"Total delivered revenue: BRL {total_rev:,.0f}")
print("\n--- Top 12 categories by revenue ---")
top = rev_cat.head(12).copy()
top["share"] = top.revenue / total_rev
print(top.round({"revenue": 0, "share": 4}).to_string(index=False))
print(f"\nTop 5 categories share: {top.head(5).share.sum():.1%} | "
      f"Top 10 share: {top.head(10).share.sum():.1%}")

rev_state = pd.read_sql("""
    SELECT c.customer_state AS state, SUM(oi.price) AS revenue,
           COUNT(DISTINCT o.order_id) AS orders,
           COUNT(DISTINCT c.customer_unique_id) AS customers
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1 ORDER BY revenue DESC""", con)
rev_state["share"] = rev_state.revenue / total_rev
rev_state["aov"] = rev_state.revenue / rev_state.orders
print("\n--- Revenue by state (top 10) ---")
print(rev_state.head(10).round({"revenue": 0, "share": 4, "aov": 2})
      .to_string(index=False))
print(f"\nSP+ RJ share: "
      f"{rev_state[rev_state.state.isin(['SP','RJ'])].share.sum():.1%}")

rev_pay = pd.read_sql("""
    SELECT payment_type, SUM(payment_value) AS revenue,
           COUNT(DISTINCT order_id) AS orders,
           AVG(payment_installments) AS avg_installments
    FROM order_payments GROUP BY 1 ORDER BY revenue DESC""", con)
rev_pay["share"] = rev_pay.revenue / rev_pay.revenue.sum()
print("\n--- Revenue by payment type ---")
print(rev_pay.round({"revenue": 0, "share": 4, "avg_installments": 2})
      .to_string(index=False))

# ---------- 2. ACQUISITION COHORTS ----------
d = pd.read_sql("""
    SELECT c.customer_unique_id, o.order_id,
           DATE(o.order_purchase_timestamp) AS d
    FROM orders o JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'""", con, parse_dates=["d"])
d["cohort"] = d.groupby("customer_unique_id")["d"].transform("min") \
               .dt.to_period("M")
d["omonth"] = d["d"].dt.to_period("M")
d["n_month"] = (d["omonth"] - d["cohort"]).apply(lambda p: p.n)
coh_size = d.groupby("cohort")["customer_unique_id"].nunique()
active = (d.groupby(["cohort", "n_month"])["customer_unique_id"].nunique()
          .unstack(fill_value=0))
ret = active.div(coh_size, axis=0).round(4)
print("\n--- Cohort repeat rate: % of cohort ordering again within 6 months ---")
rep6 = (d[d.n_month.between(1, 6)].groupby("cohort")["customer_unique_id"]
        .nunique() / coh_size).round(4)
print(rep6.to_string())
# fair average: cohorts with a full 6-month observation window, weighted
fair = rep6[[c for c in rep6.index if c <= pd.Period("2018-04", "M")]].dropna()
w = coh_size[fair.index]
print(f"\nWeighted 6-month repeat rate (cohorts thru 2018-04): "
      f"{(fair * w).sum() / w.sum():.2%}")
print("\n--- Retention matrix (rows=cohort, cols=months since acquisition) ---")
print(ret.iloc[:, :6].to_string())

# ---------- 3. RFM + LTV ----------
MAXD = d["d"].max()
cust = d.groupby("customer_unique_id").agg(
    last=("d", "max"), n_orders=("order_id", "nunique"))
spend = pd.read_sql("""
    SELECT c.customer_unique_id, SUM(oi.price) AS monetary
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1""", con)
rfm = cust.merge(spend, on="customer_unique_id")
rfm["recency"] = (MAXD - rfm["last"]).dt.days
rfm["frequency"] = rfm["n_orders"]


def q(s, n, rev=False):
    # quintiles on continuous-ish variables; ties broken deterministically
    r = s.rank(pct=True, method="first")
    if rev:
        r = 1 - r
    return pd.qcut(r, n, labels=list(range(1, n + 1))).astype(int)


rfm["R"] = q(rfm["recency"], 5, rev=True)
# Frequency is 97%+ single-order: quintiling it would be theater.
# Score it honestly: 1 order -> 1, 2 orders -> 3, 3+ orders -> 5.
rfm["F"] = rfm["frequency"].map(lambda x: 1 if x == 1 else (3 if x == 2 else 5))
rfm["M"] = q(rfm["monetary"], 5)


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
            total_rev=("monetary", "sum"),
            avg_orders=("frequency", "mean"))
       .round(2).sort_values("customers", ascending=False))
seg["rev_share"] = seg.total_rev / seg.total_rev.sum()
print("\n--- RFM segments ---")
print(seg.round({"rev_share": 4}).to_string())
print(f"\nOverall historical LTV (avg spend per customer): "
      f"BRL {rfm.monetary.mean():,.2f}")
print(f"Overall AOV (per order): BRL "
      f"{rfm.monetary.sum() / rfm.frequency.sum():,.2f}")
con.close()
