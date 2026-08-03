import json

import pandas as pd

from scripts_lib.sampling import clean_reviews, yelp_business_ids


def test_clean_reviews_drops_short_and_null():
    df = pd.DataFrame(
        {
            "rating": [5.0, 1.0, 3.0],
            "text": ["This product is genuinely great and works well.", None, "ok"],
        }
    )
    out = clean_reviews(df)
    assert list(out.columns) == ["rating", "text"]
    assert len(out) == 1  # null and <20-char rows dropped


def test_yelp_business_ids_filters_restaurants():
    lines = [
        json.dumps({"business_id": "a", "categories": "Restaurants, Indian"}),
        json.dumps({"business_id": "b", "categories": "Auto Repair"}),
        json.dumps({"business_id": "c", "categories": None}),
    ]
    assert yelp_business_ids(lines) == {"a"}
