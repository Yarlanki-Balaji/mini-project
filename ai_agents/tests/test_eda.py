import pandas as pd

from scripts_lib.eda import summarize_df


def test_summarize_df():
    # Non-square 3x2 fixture with asymmetric null pattern to detect rows/cols swap:
    # Total cells = 3 * 2 = 6; nulls = 1; null_pct = (1/6)*100 = 16.7
    # If implementation swapped rows/cols, it would return rows=2, cols=3 (detectable).
    df = pd.DataFrame({"a": [1, None, 3], "b": ["x", "y", "z"]})
    s = summarize_df("demo", df)
    assert s == {"name": "demo", "rows": 3, "cols": 2, "null_pct": 16.7}
