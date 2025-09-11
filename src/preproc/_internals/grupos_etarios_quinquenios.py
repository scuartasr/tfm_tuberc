from __future__ import annotations

import pandas as pd


def edad_a_gr_et_quinquenios(edad: pd.Series) -> pd.Series:
    """Convierte edades (años) a grupos etarios quinquenales (1..17).

    Reglas:
    - 0-4 -> 1, 5-9 -> 2, ..., 75-79 -> 16, >=80 -> 17.
    - Valores inválidos devuelven NA.

    Retorna una Serie con dtype Int64.
    """
    e = pd.to_numeric(edad, errors="coerce")
    gr = pd.Series(pd.NA, index=e.index, dtype="Int64")
    m_valid = e.notna() & (e >= 0)
    m_lt80 = m_valid & (e < 80)
    gr.loc[m_lt80] = (e.loc[m_lt80] // 5 + 1).astype("Int64")
    gr.loc[m_valid & (e >= 80)] = 17
    return gr
