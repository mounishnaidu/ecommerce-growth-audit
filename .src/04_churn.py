"""Phase 2/3 — Churn analysis on Olist consumers.
Design decisions (all defensible in an interview):
- Population: customers whose FIRST delivered order was on/before 2017-10-17.
- Features use ONLY orders up to 2017-10-17 (feature cutoff).
- Churned = no delivered order in the next 180 days (2017-10-18..2018-04-17).
  Binary, observable, and leakage-free: features never see the outcome window.
- Only DELIVERED orders count as purchases (canceled != bought).
- NOTE: an earlier version computed recency from the same last_order date
  used in the target and got AUC = 1.000 — textbook target leakage.
  It is kept out of this script; the fix is the split-window design above.
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

BASE = Path.home() / "workspace/your_files/ecommerce-growth-audit"
con = sqlite3.connect(BASE / "data" / "olist.db")

orders = pd.read_sql(
    "SELECT order_id, customer_id, order_status, order_purchase_timestamp "
    "FROM orders", con, parse_dates=["order_purchase_timestamp"])
customers = pd.read_sql("SELECT customer_id, customer_unique_id, customer_state "
                        "FROM customers", con)
items = pd.read_sql("SELECT order_id, price FROM order_items", con)
pays = pd.read_sql("SELECT order_id, payment_type FROM order_payments", con)
reviews = pd.read_sql("SELECT order_id, review_score FROM order_reviews", con)
prods = pd.read_sql(
    "SELECT p.product_id, t.product_category_name_english AS category "
    "FROM products p LEFT JOIN category_translation t "
    "ON p.product_category_name = t.product_category_name", con)
item_prod = pd.read_sql("SELECT order_id, product_id FROM order_items", con)
con.close()

print("order_status mix:")
print(orders.order_status.value_counts().to_string())

# ---- build customer grain (delivered orders only) ----
d = (orders[orders.order_status == "delivered"]
     .merge(customers, on="customer_id", how="left"))
spend = items.groupby("order_id")["price"].sum().rename("spend")
d = d.merge(spend, on="order_id", how="left")
pay_mode = (pays.groupby("order_id")["payment_type"]
            .agg(lambda s: s.mode().iloc[0]).rename("pay_type"))
d = d.merge(pay_mode, on="order_id", how="left")
rev = reviews.groupby("order_id")["review_score"].mean().rename("review")
d = d.merge(rev, on="order_id", how="left")
cat = (item_prod.merge(prods, on="product_id", how="left")
       .groupby("order_id")["category"]
       .agg(lambda s: s.mode().iloc[0] if s.notna().any() else "unknown")
       .rename("category"))
d = d.merge(cat, on="order_id", how="left")

CUTOFF = pd.Timestamp("2018-04-17")          # 180 days before max order date
T_FEAT = pd.Timestamp("2017-10-17")          # feature cutoff ...
T_END = pd.Timestamp("2018-04-17")           # ... outcome window ends 180d later
# Features may only use orders <= T_FEAT; the target looks at (T_FEAT, T_END].
# Population: first delivered order on/before T_FEAT (existed at feature time).
feat_base = d[d["order_purchase_timestamp"] <= T_FEAT]
g = feat_base.groupby("customer_unique_id")
def safe_mode(s):
    m = s.mode()
    return m.iloc[0] if len(m) else "unknown"


first_cat = (d.sort_values("order_purchase_timestamp")
             .groupby("customer_unique_id")["category"].first()
             .rename("first_category"))
feat = pd.DataFrame({
    "first_order": g["order_purchase_timestamp"].min(),
    "last_order": g["order_purchase_timestamp"].max(),
    "n_orders": g["order_id"].nunique(),
    "total_spend": g["spend"].sum(),
    "avg_review": g["review"].mean(),
    "state": g["customer_state"].first(),
    "fav_pay": g["pay_type"].agg(safe_mode),
}).join(first_cat)
# target: any delivered order AFTER the feature cutoff? (no leakage:
# features never see the outcome window)
later = d[d["order_purchase_timestamp"] > T_FEAT].groupby(
    "customer_unique_id")["order_id"].nunique().rename("n_later")
feat = feat.join(later)
feat["n_later"] = feat["n_later"].fillna(0)
feat["churned"] = (feat["n_later"] == 0).astype(int)
feat["tenure_days"] = (feat["last_order"] - feat["first_order"]).dt.days
feat["recency_days"] = (T_FEAT - feat["last_order"]).dt.days
feat["avg_order_value"] = feat["total_spend"] / feat["n_orders"]

print(f"\nAt-risk customers: {len(feat):,}")
print(f"Churn rate: {feat.churned.mean():.1%} "
      f"({feat.churned.sum():,} churned / {(feat.churned == 0).sum():,} retained)")
print(f"Repeat-buyer rate (2+ orders): {(feat.n_orders > 1).mean():.1%}")

print("\n--- Churn rate by state (top 10 by volume) ---")
by_state = feat.groupby("state")["churned"].agg(["count", "mean"]).round(4)
by_state.columns = ["customers", "churn_rate"]
print(by_state.sort_values("customers", ascending=False).head(10).to_string())

print("\n--- Churn rate by first-purchase category (top 10 by volume) ---")
by_cat = feat.groupby("first_category")["churned"].agg(["count", "mean"]).round(4)
by_cat.columns = ["customers", "churn_rate"]
print(by_cat.sort_values("customers", ascending=False).head(10).to_string())

print("\n--- Churn rate by acquisition cohort (first order month) ---")
feat["cohort"] = feat["first_order"].dt.to_period("M")
by_coh = feat.groupby("cohort")["churned"].agg(["count", "mean"]).round(4)
by_coh.columns = ["customers", "churn_rate"]
print(by_coh.to_string())

print("\n--- Churn rate by repeat vs one-time ---")
print(feat.groupby(feat.n_orders > 1)["churned"].agg(["count", "mean"]).round(4).to_string())

# ---- model ----
X = feat[["n_orders", "total_spend", "avg_order_value", "tenure_days",
          "recency_days", "avg_review"]].copy()
X["avg_review"] = X["avg_review"].fillna(X["avg_review"].median())
for col in ["state", "first_category", "fav_pay"]:
    top = feat[col].value_counts().head(8).index
    for v in top:
        X[f"{col}={v}"] = (feat[col] == v).astype(int)
y = feat["churned"]

Xtr, Xte, ytr, yte = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y)

sc = StandardScaler()
lr = LogisticRegression(max_iter=1000).fit(sc.fit_transform(Xtr), ytr)
lr_auc = roc_auc_score(yte, lr.predict_proba(sc.transform(Xte))[:, 1])

rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(Xtr, ytr)
rf_auc = roc_auc_score(yte, rf.predict_proba(Xte)[:, 1])

print(f"\nLogistic regression AUC: {lr_auc:.3f}")
print(f"Random forest AUC:       {rf_auc:.3f}")
print("\nRandom forest (test set):")
print(classification_report(yte, rf.predict(Xte),
                            target_names=["retained", "churned"]))

print("--- Top 12 feature importances (random forest) ---")
imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values(
    ascending=False).head(12)
print(imp.round(4).to_string())

print("\n--- Logistic regression coefficients (standardized) ---")
coef = pd.Series(lr.coef_[0], index=X.columns).sort_values(
    key=np.abs, ascending=False).head(12)
print(coef.round(4).to_string())
