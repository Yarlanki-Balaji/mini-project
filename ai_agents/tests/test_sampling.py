import json

import pandas as pd

from scripts_lib.sampling import clean_reviews, yelp_business_ids

LONG_TEXT = "This product is genuinely great and works well."
LONG_TEXT_2 = "This review has plenty of characters to clear the length filter easily."


def test_clean_reviews_drops_short_and_null():
    df = pd.DataFrame(
        {
            "rating": [5.0, 1.0, 3.0],
            "text": [LONG_TEXT, None, "ok"],
        }
    )
    out = clean_reviews(df)
    assert list(out.columns) == ["rating", "text"]
    assert len(out) == 1  # null and <20-char rows dropped
    assert out.loc[0, "rating"] == 5.0
    assert out.loc[0, "text"] == LONG_TEXT


def test_clean_reviews_drops_short_text_independent_of_nulls():
    # No nulls at all in this frame -- isolates the length filter so it
    # cannot silently disappear without this test noticing.
    df = pd.DataFrame(
        {
            "rating": [5.0, 2.0],
            "text": [LONG_TEXT_2, "short"],
        }
    )
    out = clean_reviews(df)
    assert len(out) == 1
    assert out.loc[0, "rating"] == 5.0
    assert out.loc[0, "text"] == LONG_TEXT_2


def test_clean_reviews_drops_only_null_text_not_null_rating():
    # dropna must target the "text" column specifically: a row with a
    # null *rating* but valid long text must survive, while a row with
    # null *text* (even with a valid rating) must be dropped. This pins
    # dropna(subset=["text"]) against being mis-targeted at "rating" (or
    # any other column) -- a wrong subset drops the null-rating row and
    # lets the null-text row fall through length filtering differently,
    # changing both the row count and the surviving row's content.
    df = pd.DataFrame(
        {
            "rating": [None, 4.0],
            "text": [LONG_TEXT_2, None],
        }
    )
    out = clean_reviews(df)
    assert len(out) == 1
    assert pd.isna(out.loc[0, "rating"])
    assert out.loc[0, "text"] == LONG_TEXT_2


def test_yelp_business_ids_filters_restaurants():
    lines = [
        json.dumps({"business_id": "a", "categories": "Restaurants, Indian"}),
        json.dumps({"business_id": "b", "categories": "Auto Repair"}),
        json.dumps({"business_id": "c", "categories": None}),
    ]
    assert yelp_business_ids(lines) == {"a"}
