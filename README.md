# E-commerce Growth Audit

An end-to-end growth marketing analytics project on a real e-commerce dataset — from raw CSVs to a shipped growth audit. Built to apply (and demonstrate) SQL, marketing analytics, statistics, Python, and BI the way a growth marketing analyst actually uses them.

## Dataset

[Olist Brazilian Marketplace](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (~100,000 orders, 2016–2018) plus Olist's [Marketing Funnel](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist) dataset (8,000 MQLs → 842 closed deals). Real, anonymized commercial data: orders, line items, payments, customers, reviews, products, sellers.

## Status

**Phase 1 — Data Foundations: complete.** The dataset is downloaded, loaded into SQLite, quality-checked, cleaned, and documented.

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1. Data foundations | Kaggle download → SQLite, data dictionary, quality checks | ✅ Complete |
| 2. Funnel & channel analytics | MQL→SQL→order conversion, revenue by category/state/payment type, acquisition-month cohorts | Not started |
| 3. Customer economics | RFM segmentation, LTV, churn classifier (logistic regression + random forest) | Not started |
| 4. Dashboard | Tableau Public: KPIs, funnel, cohort heatmap, churn-risk segment | Not started |
| 5. Report & ship | 2-page audit memo (3 findings + 3 recommendations), resume bullet | Not started |

## Repo structure

```
.src/
  01_load_clean.py       # CSVs → SQLite: quality checks, cleaning, indexes (reproducible)
  02_data_dictionary.py  # Builds Olist Data Dictionary.xlsx from the database
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
