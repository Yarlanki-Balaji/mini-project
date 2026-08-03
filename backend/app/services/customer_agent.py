from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.schema import CategoryInsight


def _headline(positive_keywords: list[str], negative_keywords: list[str]) -> str:
    """Build a natural-reading headline from up-to-5, possibly-empty keyword
    lists.

    Task 7's aggregate_sentiment contract is "up to 5" keywords, never
    padded: either list can legitimately be [] -- a category with zero
    reviews of that polarity, or a bucket whose reviews are all stopwords
    (verified reachable through real VADER labelling). Indexing
    keywords[0] unguarded raises IndexError on a perfectly valid,
    precomputed row, so all four populated/empty combinations are handled
    explicitly here rather than padding with filler tokens.
    """
    if positive_keywords and negative_keywords:
        return (
            f"Customers praise {positive_keywords[0]}; "
            f"top complaint is {negative_keywords[0]}"
        )
    if positive_keywords:
        return f"Customers praise {positive_keywords[0]}; no significant complaints reported"
    if negative_keywords:
        return f"No standout praise recorded; top complaint is {negative_keywords[0]}"
    return "Not enough review data yet to surface standout praises or complaints"


def _feedback_line(keywords: list[str], kind: str) -> str:
    """`kind` is "praises" or "complaints"; used as both the empty-case noun
    and the populated-case label prefix."""
    if not keywords:
        return f"No standout {kind} in the data"
    return f"Top {kind}: " + ", ".join(keywords)


def get_customer_insight(db: Session, category: str) -> dict:
    row = (
        db.query(CategoryInsight)
        .filter_by(category=category, agent="customer_insight")
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"No insights for '{category}' yet")
    p = row.payload
    return {
        "agent": "customer_insight",
        "category": category,
        "status": "done",
        "headline": _headline(p["top_positive_keywords"], p["top_negative_keywords"]),
        "metrics": {
            "positive_pct": p["positive_pct"],
            "negative_pct": p["negative_pct"],
            "reviews_analyzed": row.sample_size,
        },
        "chart_data": [
            {"label": "positive", "value": p["positive_pct"]},
            {"label": "neutral", "value": p["neutral_pct"]},
            {"label": "negative", "value": p["negative_pct"]},
        ],
        "insights": [
            _feedback_line(p["top_positive_keywords"], "praises"),
            _feedback_line(p["top_negative_keywords"], "complaints"),
        ],
        "source": {"dataset": row.dataset, "sample_size": row.sample_size},
    }
