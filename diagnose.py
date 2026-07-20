"""Run this to see WHY rows are being rejected. Prints actual column headers
and a sample of rows that fail to parse, for each problem file."""
import pandas as pd
import os

FILES = [
    ("data/raw/profitandloss.xlsx", 1),
    ("data/raw/balancesheet.xlsx", 1),
    ("data/raw/cashflow.xlsx", 1),
    ("data/raw/documents.xlsx", 1),
    ("data/raw/analysis.xlsx", 1),
    ("data/raw/prosandcons.xlsx", 1),
    ("data/supporting/financial_ratios.xlsx", 0),
    ("data/supporting/peer_groups.xlsx", 0),
]

for fpath, header in FILES:
    if not os.path.exists(fpath):
        print(f"\n=== {fpath} === NOT FOUND")
        continue
    df = pd.read_excel(fpath, header=header)
    print(f"\n=== {fpath} (header={header}) ===")
    print("COLUMNS:", list(df.columns))
    print(df.head(3).to_string())
