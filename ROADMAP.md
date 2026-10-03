# Project Roadmap: E-commerce Growth Audit (Portfolio Project)

**Goal:** A public, portfolio-ready growth marketing analytics project for Mounish's resume and interviews.
**Dataset:** Olist Brazilian Marketplace (Kaggle) — ~100k orders (2016–2018): customers, orders, payments, reviews, products, sellers, plus a marketing-qualified-leads funnel dataset.
**Why this dataset:** Real company data, has both a marketing funnel (MQL → SQL → won) and transaction history — covers every track of the curriculum.
**Timeline:** ~12 days at 2–3 hrs/day. **Repo:** GitHub, public. **Dashboard:** Tableau Public (free).

## Phase 1 — Data foundations (Days 1–2)
- Download the Olist dataset from Kaggle; load CSVs into SQLite + pandas.
- Write a data dictionary; run quality checks (missing values, duplicates, date ranges).
- **Deliverable:** clean SQLite database + EDA notebook.

## Phase 2 — Funnel & channel analytics (Days 3–5)
- Marketing funnel: MQL → SQL → closed order conversion rates; where does it leak?
- Revenue by product category, customer state, payment type.
- Cohort analysis: repeat-purchase rate by acquisition month.
- **Deliverable:** `sql/` folder with queries + written findings.

## Phase 3 — Customer economics (Days 6–8)
- RFM segmentation; LTV estimate per segment.
- Define churn (e.g., no order in 6 months); build churn classifier (logistic regression → random forest); report feature importances.
- **Deliverable:** modeling notebook with evaluation.

## Phase 4 — Dashboard (Days 9–10)
- Tableau Public: KPI overview, funnel, cohort heatmap, churn-risk segment.
- **Deliverable:** public dashboard link.

## Phase 5 — Report & ship (Days 11–12)
- 2-page growth audit memo: 3 findings + 3 recommendations with expected impact.
- GitHub repo README linking notebooks, dashboard, memo.
- Resume bullet: "Built end-to-end growth audit on 100k-order e-commerce dataset: funnel, LTV, churn model; published interactive dashboard."

## Stretch (optional)
- Design an A/B test for checkout conversion (hypothesis, metric, sample size).
- GA4 event spec for the store (events, parameters, conversions).

## Working agreement
- Mounish builds; Shadow reviews each phase like a hiring manager.
- One phase at a time; no moving on with broken prior work.
