import pandas as pd


def limpiar_poblacion(df: pd.DataFrame, col: str = "poblacion") -> pd.DataFrame:
    out = df.copy()
    cleaned = out[col].astype(str).str.replace(r"[^0-9]", "", regex=True)
    out[col] = pd.to_numeric(cleaned, errors="coerce").astype("Int64")
    return out
