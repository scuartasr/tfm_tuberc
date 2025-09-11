import pandas as pd


from typing import List


def derretir_a_largo(df: pd.DataFrame, col_anio: str, col_area: str, cols_poblacion: List[str]) -> pd.DataFrame:
    largo = df.melt(
        id_vars=[col_anio, col_area],
        value_vars=cols_poblacion,
        var_name="col",
        value_name="poblacion",
    )
    return largo