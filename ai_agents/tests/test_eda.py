import pandas as pd

from scripts_lib.eda import summarize_df


def test_summarize_df():
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    s = summarize_df("demo", df)
    assert s == {"name": "demo", "rows": 2, "cols": 2, "null_pct": 25.0}
