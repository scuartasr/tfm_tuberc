from __future__ import annotations

import pandas as pd


def sexo_a_codigo(sexo: pd.Series) -> pd.Series:
    """Mapea sexo textual a códigos: hombre->1, mujer->2. Otros -> NA.

    Retorna Serie Int64 (1/2/NA).
    """
    s = sexo.astype(str).str.strip().str.lower()
    out = s.map({"hombre": 1, "mujer": 2})
    return out.astype("Int64")
