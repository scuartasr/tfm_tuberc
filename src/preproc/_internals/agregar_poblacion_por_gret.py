from __future__ import annotations

import os
import pandas as pd

from src.preproc._internals.normalizar_nombres_columnas import normalizar_nombres_columnas
from src.preproc._internals.minusculizar_valores import minusculizar_valores
from src.preproc._internals.grupos_etarios_quinquenios import edad_a_gr_et_quinquenios
from src.preproc._internals.mapear_sexo import sexo_a_codigo


def agregar_poblacion_por_gret(input_csv: str) -> pd.DataFrame:
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"No se encontró el archivo: {input_csv}")

    df = pd.read_csv(input_csv)
    df = normalizar_nombres_columnas(df)
    df = minusculizar_valores(df)

    required = {"ano", "sexo", "edad", "poblacion"}
    if not required.issubset(df.columns):
        falt = required - set(df.columns)
        raise ValueError(f"Faltan columnas requeridas en el CSV: {falt}")

    df["sexo"] = sexo_a_codigo(df["sexo"])  # 1/2/NA
    df = df[df["sexo"].isin([1, 2])].copy()

    df["gr_et"] = edad_a_gr_et_quinquenios(df["edad"]).astype("Int64")
    df = df[df["gr_et"].notna()].copy()

    out = (
        df.groupby(["ano", "sexo", "gr_et"], as_index=False)["poblacion"].sum()
        .sort_values(["ano", "sexo", "gr_et"], ignore_index=True)
    )
    return out
