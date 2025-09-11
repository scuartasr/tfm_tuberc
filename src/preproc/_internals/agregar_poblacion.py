import pandas as pd


def agregar_poblacion(largo: pd.DataFrame, col_anio: str) -> pd.DataFrame:
    result = (
        largo.groupby([col_anio, "sexo", "edad"], dropna=False, as_index=False)["poblacion"]
             .sum(min_count=1)
             .rename(columns={col_anio: "ano"})
             .sort_values(["ano", "sexo", "edad"], ignore_index=True)
    )
    return result