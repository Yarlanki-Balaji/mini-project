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
    if not texts:
        return []
    vec = CountVectorizer(stop_words="english", max_features=n, ngram_range=(1, 1))
    vec.fit(texts)
    return list(vec.get_feature_names_out())


def aggregate_sentiment(df: pd.DataFrame) -> dict:
    labels = df["text"].map(_label)
    total = len(df)
    pct = lambda k: round(100 * (labels == k).sum() / total, 1)  # noqa: E731
    return {
        "positive_pct": pct("positive"),
        "neutral_pct": pct("neutral"),
        "negative_pct": pct("negative"),
        "top_positive_keywords": _top_keywords(df.loc[labels == "positive", "text"].tolist()),
        "top_negative_keywords": _top_keywords(df.loc[labels == "negative", "text"].tolist()),
    }
