import pandas as pd

from agent3_customer.sentiment import aggregate_sentiment, _top_keywords


def _df():
    pos = ["Absolutely delicious food, wonderful fresh taste and great variety."] * 6
    neg = ["Terrible slow delivery, food arrived cold and the refund was denied."] * 3
    neu = ["It was an average experience overall, nothing special to report."] * 1
    return pd.DataFrame({"rating": [5] * 6 + [1] * 3 + [3], "text": pos + neg + neu})


def test_aggregate_sentiment_shape_and_split():
    out = aggregate_sentiment(_df())
    assert set(out) == {
        "positive_pct", "neutral_pct", "negative_pct",
        "top_positive_keywords", "top_negative_keywords",
    }
    assert out["positive_pct"] > out["negative_pct"] > 0
    assert abs(out["positive_pct"] + out["neutral_pct"] + out["negative_pct"] - 100) < 0.1
    assert len(out["top_positive_keywords"]) == 5
    assert "delivery" in out["top_negative_keywords"] or "slow" in out["top_negative_keywords"]


# --- Additional rigor tests -------------------------------------------------
#
# The fixture above shares the word "food" between the positive and negative
# review texts, and its "slow"/"delivery" check only holds because "delivery"
# survives CountVectorizer's alphabetical tie-break for max_features=5 while
# "slow" does not (verified empirically). A bucket-swap bug (e.g. computing
# top_negative_keywords from the *positive* label mask) would still slip past
# that check in some fixtures, and it wouldn't be caught by the percentage
# assertions at all, since those only look at labels/counts, not text content.
#
# The tests below use a fixture with a completely disjoint pos/neg vocabulary
# (no shared words) and exactly 5 non-stopword tokens per bucket, so
# CountVectorizer's max_features=5 keeps *every* token deterministically --
# no frequency tie-breaking involved -- and the expected output is an exact,
# fully-known set rather than "one of two plausible words".

_POS_TEXT = "Wonderful amazing fantastic excellent service."
_NEG_TEXT = "Horrible disgusting awful terrible delay."
# Genuinely neutral under VADER (compound == 0.0, verified separately below;
# the brief's own "neu" sentence actually scores compound=-0.31 and is
# labelled negative, so it never exercises the neutral bucket at all).
_NEU_TEXT = "The store opened at nine and closed at six on weekdays."


def _disjoint_df():
    return pd.DataFrame(
        {
            "rating": [5] * 7 + [1] * 2 + [3] * 1,
            "text": [_POS_TEXT] * 7 + [_NEG_TEXT] * 2 + [_NEU_TEXT] * 1,
        }
    )


def test_negative_keywords_come_only_from_negative_bucket():
    # Exact-set assertion: catches a bucket swap/mixup outright, not just
    # "one of two words happens to still be there".
    out = aggregate_sentiment(_disjoint_df())
    assert out["top_positive_keywords"] == [
        "amazing", "excellent", "fantastic", "service", "wonderful",
    ]
    assert out["top_negative_keywords"] == [
        "awful", "delay", "disgusting", "horrible", "terrible",
    ]
    # Belt-and-braces: no cross-contamination between the two buckets.
    assert not set(out["top_positive_keywords"]) & set(out["top_negative_keywords"])


def test_sentiment_percentages_are_exact_not_just_ordered():
    # 7 positive + 2 negative + 1 genuinely-neutral row out of 10 -> exact,
    # individually-checked percentages. A bug that swaps the positive and
    # negative buckets (e.g. pct("positive") and pct("negative") flipped)
    # produces 20.0/10.0/70.0 here instead of 70.0/10.0/20.0 -- every one of
    # the three assertions below would fail, not just a "greater than" check.
    out = aggregate_sentiment(_disjoint_df())
    assert out["positive_pct"] == 70.0
    assert out["neutral_pct"] == 10.0
    assert out["negative_pct"] == 20.0


def test_top_keywords_empty_input_returns_empty_list():
    # Direct unit test of the guard clause: an empty text list must short
    # circuit before reaching CountVectorizer, which raises ValueError on an
    # empty vocabulary rather than returning [].
    assert _top_keywords([]) == []


def test_aggregate_sentiment_handles_category_with_zero_negative_reviews():
    # Realistic case: a category can have no negative reviews at all, so the
    # negative bucket passed into _top_keywords is an empty list. Without the
    # empty-list guard in _top_keywords, CountVectorizer.fit([]) raises
    # "ValueError: empty vocabulary; perhaps the documents only contain stop
    # words" and the whole precompute run would crash for that category.
    df = pd.DataFrame({"rating": [5] * 4, "text": [_POS_TEXT] * 4})
    out = aggregate_sentiment(df)
    assert out["negative_pct"] == 0.0
    assert out["top_negative_keywords"] == []
