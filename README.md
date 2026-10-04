# E-commerce Growth Audit

An end-to-end growth marketing analytics project on a real e-commerce dataset — from raw CSVs to a shipped growth audit. Built to apply (and demonstrate) SQL, marketing analytics, statistics, Python, and BI the way a growth marketing analyst actually uses them.

## Dataset

[Olist Brazilian Marketplace](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (~100,000 orders, 2016–2018) plus Olist's [Marketing Funnel](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist) dataset (8,000 MQLs → 842 closed deals). Real, anonymized commercial data: orders, line items, payments, customers, reviews, products, sellers.

## Status

**Phases 1–4 complete.** Clean database, funnel + channel analysis, customer-economics modeling, and a published Tableau Public dashboard. Phase 5 (audit memo + final ship) is next.

**[📊 Interactive dashboard — E-commerce Growth Audit (Tableau Public)](https://public.tableau.com/app/profile/mounish.naidu/viz/E-commerceGrowthAuditOlist/GrowthOverview)**

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1. Data foundations | Kaggle download → SQLite, data dictionary, quality checks | ✅ Complete |
| 2. Funnel & channel analytics | MQL→won conversion, revenue by category/state/payment type, acquisition-month cohorts | ✅ Complete |
| 3. Customer economics | RFM segmentation, LTV, churn classifier (logistic regression + random forest) | ✅ Complete |
| 4. Dashboard | [Tableau Public: KPIs, funnel, cohort heatmap, RFM, delivery vs reviews](https://public.tableau.com/app/profile/mounish.naidu/viz/E-commerceGrowthAuditOlist/GrowthOverview) | ✅ Complete |
| 5. Report & ship | 2-page audit memo (3 findings + 3 recommendations), resume bullet | Not started |

## Key findings

- **Funnel:** 8,000 MQLs → 842 won = 10.5% conversion, median 14 days to close. Paid search converts best at volume (12.3%); social (5.6%) and email (3.0%) lag. 16.3% of wins have unknown origin — an attribution gap.
- **Revenue:** BRL 13.22M delivered; top 5 categories 39.8% of revenue; SP + RJ = 51.6%; credit card 78.3% of payment value (~3.5 installments).
- **One-and-done economics:** 97.8% churn / 2.7% repeat buyers; 6-month cohort repeat rate 1.65%, flat. LTV (BRL 141.62) ≈ AOV (BRL 137.04) — first-order value and acquisition efficiency matter more than retention modeling.
- **Inverted Pareto:** Champions + Loyal = 228 customers, 0.7% of revenue.
- **Churn model (leakage-free):** AUC 0.55 — cannot beat the base rate. A documented lesson in target leakage (first attempt hit AUC 1.000 via recency).
- **Delivery drives reviews:** on-time 93.2%; reviews fall 4.29 stars → 1.70 stars as lateness grows.

## Repo structure

```
.src/
  01_load_clean.py       # CSVs → SQLite: quality checks, cleaning, indexes (reproducible)
  02_data_dictionary.py  # Builds Olist Data Dictionary.xlsx from the database
  03_funnel.py           # MQL→won funnel analysis by channel
  04_churn.py            # Leakage-free churn classifier (logistic regression + random forest)
  05_revenue_cohorts_rfm.py  # Revenue cuts, acquisition cohorts, RFM segmentation
  06_dashboard_extracts.py   # Builds the 8 Tableau-ready CSV extracts
  07_build_spec.py       # Generates the Tableau Dashboard build spec
  build_doc.py           # Generates the project plan Word doc
ROADMAP.md               # Phase-by-phase plan
```

## Reproduce Phase 1

```bash
pip install kaggle pandas openpyxl
# place your kaggle.json at ~/.kaggle/kaggle.json
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/olist --unzip
kaggle datasets download -d olistbr/marketing-funnel-olist -p data/funnel --unzip
python .src/01_load_clean.py      # → data/olist.db + data/qa_report.txt
python .src/02_data_dictionary.py # → Olist Data Dictionary.xlsx
```

Raw data and the SQLite database are intentionally not committed — the scripts rebuild them.

## Key data notes

- Orders run Sep 2016 → Oct 2018. ~3% of orders lack delivery timestamps (canceled/unfulfilled — the missingness is the signal, so it's preserved).
- 261,831 exact-duplicate rows removed from the geolocation reference table.
- 610 products (1.9%) had no category; filled as `unknown` so their revenue stays in category totals.
- `customer_unique_id` (not `customer_id`) identifies a real person across repeat purchases.
- Category names are Portuguese; `category_translation` maps them to English.
