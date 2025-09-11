# ===================== Helpers SRP =====================
import pandas as pd


from typing import Iterable


def fila_cabecera(df_preview: pd.DataFrame, must_have: Iterable[str]) -> int:
    """Detecta la fila que contiene todas las etiquetas de `must_have`."""
    must_have = [m.lower() for m in must_have]
    for i in range(min(50, len(df_preview))):
        row_vals = df_preview.iloc[i].astype(str).str.strip().str.lower().tolist()
        if all(any(m == v for v in row_vals) for m in must_have):
            return i
    raise ValueError("No se pudo encontrar la fila de encabezados automáticamente.")