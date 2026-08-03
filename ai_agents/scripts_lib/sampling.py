import json

import pandas as pd

MIN_CHARS = 20


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rating+text, drop nulls and near-empty reviews."""
    out = df[["rating", "text"]].dropna(subset=["text"]).copy()
    out = out[out["text"].str.len() >= MIN_CHARS]
    return out.reset_index(drop=True)


def yelp_business_ids(lines) -> set[str]:
    """Business IDs whose categories mention Restaurants or Food."""
    keep = set()
    for line in lines:
        b = json.loads(line)
        cats = b.get("categories") or ""
        if "Restaurant" in cats or "Food" in cats:
            keep.add(b["business_id"])
    return keep
