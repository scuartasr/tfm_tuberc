import pandas as pd
from typing import Optional, Sequence


def minusculizar_valores(df: pd.DataFrame, cols: Optional[Sequence[str]] = None) -> pd.DataFrame:
    df = df.copy()
    target_cols = cols if cols is not None else [c for c in df.columns if df[c].dtype == "object"]
    for c in target_cols:
        df[c] = df[c].astype(str).str.strip().str.lower()
    return df
