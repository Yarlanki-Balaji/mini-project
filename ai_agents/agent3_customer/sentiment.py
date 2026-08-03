import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def _label(text: str) -> str:
    c = _analyzer.polarity_scores(text)["compound"]
    if c >= 0.05:
        return "positive"
    if c <= -0.05:
        return "negative"
    return "neutral"


def _top_keywords(texts: list[str], n: int = 5) -> list[str]:
    """Return up to `n` most frequent non-stopword unigrams across `texts`.

    Contract: "up to n", not exactly n. Returns [] for an empty bucket and
    for a bucket whose combined vocabulary is empty after stopword removal
    (e.g. reviews consisting only of stopwords/punctuation -- CountVectorizer
    would otherwise raise ValueError: "empty vocabulary"). Returns fewer than
    n tokens when the bucket has fewer than n unique non-stopword tokens
    (e.g. a sparse bucket with only 1-2 reviews). Callers (including the
    category_insights payload) must not assume a fixed length of n.
    """
    if not texts:
        return []
    vec = CountVectorizer(stop_words="english", max_features=n, ngram_range=(1, 1))
    try:
        vec.fit(texts)
    except ValueError:
        # "empty vocabulary; perhaps the documents only contain stop words"
        return []
    return list(vec.get_feature_names_out())


def top_keywords_contrastive(
    pos_texts: list[str], neg_texts: list[str], n: int = 5, pool: int = 6
) -> tuple[list[str], list[str]]:
    """Return (top_positive, top_negative) keyword lists with no overlap.

    Plain top-n-by-frequency selects generic high-frequency nouns (e.g.
    "food", "place", "service") that dominate BOTH buckets on realistic
    review text, so positive and negative lists converge on the same words
    -- useless as a contrastive signal for a headline or an LLM prompt.
    Over-fetch a wider pool per side (n * pool), then drop anything that
    appears in both pools before truncating back down to n, so each
    returned list is skewed toward words that are actually distinctive to
    that polarity.
    """
    pos_pool = _top_keywords(pos_texts, n * pool)
    neg_pool = _top_keywords(neg_texts, n * pool)
    shared = set(pos_pool) & set(neg_pool)
    return (
        [k for k in pos_pool if k not in shared][:n],
        [k for k in neg_pool if k not in shared][:n],
    )


def aggregate_sentiment(df: pd.DataFrame) -> dict:
    """Aggregate VADER sentiment and top keywords for a category's reviews.

    payload = {
        "positive_pct": float, "neutral_pct": float, "negative_pct": float,
        "top_positive_keywords": [str, ...up to 5],
        "top_negative_keywords": [str, ...up to 5],
    }
    The keyword lists may have fewer than 5 entries (or be empty) for a
    sparse or stopword-only bucket -- see `_top_keywords`.
    """
    labels = df["text"].map(_label)
    total = len(df)
    pct = lambda k: round(100 * (labels == k).sum() / total, 1)  # noqa: E731
    top_positive, top_negative = top_keywords_contrastive(
        df.loc[labels == "positive", "text"].tolist(),
        df.loc[labels == "negative", "text"].tolist(),
    )
    return {
        "positive_pct": pct("positive"),
        "neutral_pct": pct("neutral"),
        "negative_pct": pct("negative"),
        "top_positive_keywords": top_positive,
        "top_negative_keywords": top_negative,
    }
