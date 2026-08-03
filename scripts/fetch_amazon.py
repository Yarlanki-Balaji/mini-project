"""Stream Amazon Reviews 2023 category subsets -> data/processed/reviews_<slug>.parquet.
Run per-category: ai_agents/.venv/Scripts/python scripts/fetch_amazon.py grocery
"""
import sys
from itertools import islice
from pathlib import Path

import pandas as pd
from datasets import load_dataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai_agents"))
from scripts_lib.sampling import clean_reviews  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TARGET = 100_000
FETCH = 130_000  # headroom for rows dropped by cleaning

CATEGORY_CONFIGS = {
    "grocery": "raw_review_Grocery_and_Gourmet_Food",
    "beauty_personal_care": "raw_review_Beauty_and_Personal_Care",
    "fashion": "raw_review_Amazon_Fashion",
    "electronics": "raw_review_Electronics",
    "software_apps": "raw_review_Software",
    "education": "raw_review_Books",
}

slug = sys.argv[1]
ds = load_dataset(
    "McAuley-Lab/Amazon-Reviews-2023",
    CATEGORY_CONFIGS[slug],
    split="full",
    streaming=True,
    trust_remote_code=True,
)
rows = [{"rating": r["rating"], "text": r["text"]} for r in islice(iter(ds), FETCH)]
df = clean_reviews(pd.DataFrame(rows)).head(TARGET)
out = ROOT / "data" / "processed" / f"reviews_{slug}.parquet"
df.to_parquet(out, index=False)
print(f"{slug}: wrote {len(df)} rows -> {out}")
