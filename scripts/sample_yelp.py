"""Sample restaurant reviews from the Yelp Open Dataset (manual download first).

1. Download the tar from https://www.yelp.com/dataset (free academic form).
2. Extract yelp_academic_dataset_business.json and ..._review.json into data/raw/.
3. Run: ai_agents/.venv/Scripts/python scripts/sample_yelp.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai_agents"))
from scripts_lib.sampling import clean_reviews, yelp_business_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TARGET = 200_000

with open(RAW / "yelp_academic_dataset_business.json", encoding="utf-8") as f:
    keep = yelp_business_ids(f)
print(f"restaurant/food businesses: {len(keep)}")

rows = []
with open(RAW / "yelp_academic_dataset_review.json", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r["business_id"] in keep:
            rows.append({"rating": float(r["stars"]), "text": r["text"]})
            if len(rows) >= TARGET + 30_000:
                break

df = clean_reviews(pd.DataFrame(rows)).head(TARGET)
out = ROOT / "data" / "processed" / "reviews_food_restaurants.parquet"
df.to_parquet(out, index=False)
print(f"food_restaurants: wrote {len(df)} rows -> {out}")
