import pandas as pd


def summarize_df(name: str, df: pd.DataFrame) -> dict:
    total = df.shape[0] * df.shape[1]
    nulls = int(df.isna().sum().sum())
    return {
        "name": name,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "null_pct": round(100 * nulls / total, 1) if total else 0.0,
    }
