"""Phase 2 (part) — Funnel analysis: MQL -> Closed Won.
Note: the dataset has no explicit SQL stage, so the measurable funnel is
MQL (8,000) -> Won (842). All 842 deals join cleanly to mqls on mql_id.
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path.home() / "workspace/your_files/ecommerce-growth-audit"
con = sqlite3.connect(BASE / "data" / "olist.db")

mqls = pd.read_sql("SELECT * FROM mqls", con, parse_dates=["first_contact_date"])
deals = pd.read_sql("SELECT * FROM closed_deals", con, parse_dates=["won_date"])
con.close()

f = mqls.merge(
    deals[["mql_id", "won_date", "business_segment", "lead_type",
           "lead_behaviour_profile"]],
    on="mql_id", how="left", indicator=True)
f["won"] = (f["_merge"] == "both").astype(int)
f["days_to_close"] = (f["won_date"] - f["first_contact_date"]).dt.days

print(f"MQLs: {len(f):,} | Won: {f.won.sum():,} | "
      f"Overall conversion: {f.won.mean():.1%}")
print(f"Lost: {(f.won == 0).sum():,} ({1 - f.won.mean():.1%})")
print(f"Median days MQL -> won: "
      f"{f.loc[f.won == 1, 'days_to_close'].median():.0f}")


def conv_table(df, col):
    g = df.groupby(col, dropna=False)["won"].agg(["count", "sum", "mean"])
    g.columns = ["mqls", "won", "conv_rate"]
    return g.sort_values("mqls", ascending=False).round(4)


print("\n--- Conversion by origin channel ---")
print(conv_table(f, "origin").to_string())

print("\n--- Conversion by business_segment ---")
print(conv_table(f, "business_segment").to_string())

print("\n--- Conversion by lead_type ---")
print(conv_table(f, "lead_type").to_string())

print("\n--- Conversion by lead_behaviour_profile ---")
print(conv_table(f, "lead_behaviour_profile").to_string())

print("\n--- Median days to close by origin (won deals) ---")
ttc = f[f.won == 1].groupby("origin")["days_to_close"].median().sort_values()
print(ttc.round(0).to_string())

print("\n--- MQLs by month (volume trend) ---")
f["mql_month"] = f["first_contact_date"].dt.to_period("M")
print(f.groupby("mql_month").size().to_string())
