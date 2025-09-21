from __future__ import annotations

from typing import Optional
import pandas as pd


def agregar_indice_periodo(
    df: pd.DataFrame,
    col_ano: str = "ano",
    col_indice: str = "t",
) -> pd.DataFrame:
    """
    Asigna un índice temporal entero consecutivo por año.

    Reglas:
    - `t = 1` para el año mínimo presente en el DataFrame.
    - Aumenta de a 1 para cada año siguiente presente (no asume continuidad).
    - Mantiene NA cuando `ano` no es convertible a número.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame con una columna de año.
    col_ano : str
        Nombre de la columna que contiene el año (por defecto "ano").
    col_indice : str
        Nombre de la columna de índice a crear (por defecto "t").

    Retorna
    -------
    pd.DataFrame
        Copia del DataFrame con la columna de índice temporal agregada.
    """
    if col_ano not in df.columns:
        raise KeyError(f"La columna '{col_ano}' no existe en el DataFrame.")

    out = df.copy()
    anos_num = pd.to_numeric(out[col_ano], errors="coerce")

    anos_ordenados = sorted(anos_num.dropna().unique().tolist())
    if len(anos_ordenados) == 0:
        out[col_indice] = pd.array([pd.NA] * len(out), dtype="Int64")
        return out

    mapeo = {year: idx + 1 for idx, year in enumerate(anos_ordenados)}
    out[col_indice] = anos_num.map(mapeo).astype("Int64")
    return out
