"""Generate synthetic diagnostic cases. Contains no AdPage data."""
import argparse
from pathlib import Path

import pandas as pd


def demo_data():
    rows = []
    for company in ["synthetic_a", "synthetic_b"]:
        for i, date in enumerate(pd.date_range("2025-01-06", periods=16, freq="W-MON")):
            if company == "synthetic_b" and i == 4:
                continue
            search = 100 + i * 10
            rows.append({"company_id": company, "date_week": date.strftime("%Y-%m-%d"),
                         "revenue": 1000 + i * 30,
                         "search_spend": search,
                         "social_spend": search * 2 if company == "synthetic_a" else 50})
    rows[3]["revenue"] = None
    rows[5]["search_spend"] = -10
    rows.append(rows[9].copy())
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    demo_data().to_csv(args.output, index=False)
