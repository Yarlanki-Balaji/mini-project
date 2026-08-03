"""Aggregate sentiment for a category and upsert into category_insights (Supabase).

Run: ai_agents/.venv/Scripts/python -m agent3_customer.precompute food_restaurants
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.config import get_settings  # noqa: E402
from app.models.schema import CategoryInsight  # noqa: E402

from agent3_customer.sentiment import aggregate_sentiment  # noqa: E402

DATASET_NAMES = {
    "food_restaurants": "Yelp Open Dataset (sampled)",
}
DEFAULT_DATASET = "Amazon Reviews 2023 (sampled)"

slug = sys.argv[1]
df = pd.read_parquet(ROOT / "data" / "processed" / f"reviews_{slug}.parquet")
payload = aggregate_sentiment(df)

engine = create_engine(get_settings().database_url)
db = sessionmaker(bind=engine)()
row = (
    db.query(CategoryInsight)
    .filter_by(category=slug, agent="customer_insight")
    .one_or_none()
)
if row is None:
    row = CategoryInsight(category=slug, agent="customer_insight", payload=payload,
                          dataset=DATASET_NAMES.get(slug, DEFAULT_DATASET),
                          sample_size=len(df))
    db.add(row)
else:
    row.payload = payload
    row.sample_size = len(df)
    row.updated_at = datetime.now(timezone.utc)
db.commit()
db.close()
print(f"{slug}: upserted customer_insight ({len(df)} reviews) -> {payload}")
