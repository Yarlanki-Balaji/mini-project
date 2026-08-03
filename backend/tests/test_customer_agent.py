import pytest
from fastapi import HTTPException

from app.models.schema import CategoryInsight
from app.services.customer_agent import get_customer_insight

PAYLOAD = {
    "positive_pct": 61.4, "neutral_pct": 14.5, "negative_pct": 24.1,
    "top_positive_keywords": ["taste", "variety", "fresh", "service", "value"],
    "top_negative_keywords": ["delivery", "cold", "slow", "refund", "stale"],
}


def _seed(db, category="food_restaurants", payload=None,
          dataset="Yelp Open Dataset (sampled)", sample_size=200000):
    db.add(CategoryInsight(category=category, agent="customer_insight",
                           payload=payload if payload is not None else PAYLOAD,
                           dataset=dataset, sample_size=sample_size))
    db.commit()


def test_contract_shape(db):
    _seed(db)
    out = get_customer_insight(db, "food_restaurants")
    assert set(out) == {"agent", "category", "status", "headline",
                        "metrics", "chart_data", "insights", "source"}
    assert out["agent"] == "customer_insight"
    assert out["status"] == "done"
    assert out["source"] == {"dataset": "Yelp Open Dataset (sampled)", "sample_size": 200000}
    assert {d["label"] for d in out["chart_data"]} == {"positive", "neutral", "negative"}


def test_missing_category_raises_404(db):
    with pytest.raises(HTTPException) as e:
        get_customer_insight(db, "education")
    assert e.value.status_code == 404


def test_endpoint(client, db):
    _seed(db)
    r = client.get("/api/customer", params={"category": "food_restaurants"})
    assert r.status_code == 200
    assert r.json()["metrics"]["positive_pct"] == 61.4


# --- Additional rigor tests --------------------------------------------------
#
# The three tests above pin shape and the 404-via-exception path, but they
# don't discriminate a swapped positive/negative metric, a dropped or
# mislabeled chart slice, or a hardcoded/recomputed sample_size -- a
# membership check (`set(out) == {...}`) or a single spot-check
# (`metrics["positive_pct"] == 61.4`) passes even if other fields are wrong.


def test_metrics_percentages_are_not_swapped(db):
    # PAYLOAD has distinct positive_pct (61.4) and negative_pct (24.1). An
    # exact-dict check fails if the implementation swapped which payload key
    # feeds which metrics key (61.4 would land under "negative_pct" instead),
    # unlike a single spot-check on one key.
    _seed(db)
    out = get_customer_insight(db, "food_restaurants")
    assert out["metrics"] == {
        "positive_pct": 61.4,
        "negative_pct": 24.1,
        "reviews_analyzed": 200000,
    }


def test_chart_data_full_content_in_order(db):
    # Pins label AND value for all three slices, in order. Catches a dropped
    # slice (list length != 3), a value pulled from the wrong payload key, or
    # a mislabeled slice -- none of which the label-only set-membership check
    # in test_contract_shape would notice.
    _seed(db)
    out = get_customer_insight(db, "food_restaurants")
    assert out["chart_data"] == [
        {"label": "positive", "value": 61.4},
        {"label": "neutral", "value": 14.5},
        {"label": "negative", "value": 24.1},
    ]


def test_source_sample_size_comes_from_db_row_not_hardcoded_or_recomputed(db):
    # sample_size=54321 appears nowhere else in this file and differs from
    # the 200000 used elsewhere, so this fails if sample_size were
    # hardcoded, derived from len(payload[...]), or read from the wrong
    # row/column.
    _seed(db, category="grocery", dataset="Amazon Reviews 2023 (sampled)", sample_size=54321)
    out = get_customer_insight(db, "grocery")
    assert out["source"] == {"dataset": "Amazon Reviews 2023 (sampled)", "sample_size": 54321}
    assert out["metrics"]["reviews_analyzed"] == 54321


def test_missing_category_endpoint_returns_404_status(client, db):
    # The brief's test_missing_category_raises_404 only checks the raised
    # Python HTTPException object directly. This drives the same case through
    # the real HTTP layer, proving FastAPI's exception handling actually
    # turns it into a 404 HTTP response for a client -- not just that the
    # exception object happens to carry status_code=404.
    r = client.get("/api/customer", params={"category": "education"})
    assert r.status_code == 404


# --- Empty-keyword combinations -----------------------------------------------
#
# Task 7's aggregate_sentiment contract is "up to 5" keywords, never padded:
# top_positive_keywords / top_negative_keywords can legitimately be [] (a
# category with zero reviews of that polarity, or a bucket whose reviews are
# all stopwords). The brief's original headline f-string indexed
# top_positive_keywords[0] / top_negative_keywords[0] unguarded, so an empty
# list raised IndexError -- a 500 for a perfectly valid, precomputed row.
# These four tests pin the fix for all four populated/empty combinations.

def _payload(pos, neg):
    return {
        "positive_pct": 61.4, "neutral_pct": 14.5, "negative_pct": 24.1,
        "top_positive_keywords": pos,
        "top_negative_keywords": neg,
    }


def test_headline_both_keyword_lists_populated(db):
    _seed(db, payload=_payload(["taste", "variety"], ["delivery", "cold"]))
    out = get_customer_insight(db, "food_restaurants")
    assert out["headline"] == "Customers praise taste; top complaint is delivery"
    assert out["insights"] == [
        "Top praises: taste, variety",
        "Top complaints: delivery, cold",
    ]


def test_headline_only_positive_keywords_populated(db):
    _seed(db, category="grocery", payload=_payload(["fresh", "value"], []))
    out = get_customer_insight(db, "grocery")
    assert out["headline"] == "Customers praise fresh; no significant complaints reported"
    assert out["insights"] == [
        "Top praises: fresh, value",
        "No standout complaints in the data",
    ]


def test_headline_only_negative_keywords_populated(db):
    _seed(db, category="beauty_personal_care", payload=_payload([], ["refund", "stale"]))
    out = get_customer_insight(db, "beauty_personal_care")
    assert out["headline"] == "No standout praise recorded; top complaint is refund"
    assert out["insights"] == [
        "No standout praises in the data",
        "Top complaints: refund, stale",
    ]


def test_headline_neither_keyword_list_populated(db):
    _seed(db, category="fashion", payload=_payload([], []))
    out = get_customer_insight(db, "fashion")
    assert out["headline"] == \
        "Not enough review data yet to surface standout praises or complaints"
    assert out["insights"] == [
        "No standout praises in the data",
        "No standout complaints in the data",
    ]
