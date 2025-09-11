import pandas as pd


def filtrar_dpnom_nacional(df: pd.DataFrame) -> pd.DataFrame:
    if "dpnom" not in df.columns:
        return df
    mask = df["dpnom"].astype(str).str.strip().str.lower() == "nacional"
    return df.loc[mask].copy()


def filtrar_rango_anios(df: pd.DataFrame, col: str = "ano", min_year: int = 1979, max_year: int = 2023) -> pd.DataFrame:
    if col not in df.columns:
        return df
    out = df.copy()
    out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    mask = (out[col] >= min_year) & (out[col] <= max_year)
    return out.loc[mask].copy()
