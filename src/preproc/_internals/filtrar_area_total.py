import pandas as pd


def filtrar_area_total(df: pd.DataFrame, col_area: str) -> pd.DataFrame:
    mask = df[col_area].astype(str).str.strip().str.lower() == "total"
    return df.loc[mask].copy()