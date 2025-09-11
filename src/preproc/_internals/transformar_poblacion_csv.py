from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.preproc._internals.leer_datos import leer_datos
from src.preproc._internals.normalizar_nombres_columnas import normalizar_nombres_columnas
from src.preproc._internals.minusculizar_valores import minusculizar_valores
from src.preproc._internals.filtros_basicos import filtrar_dpnom_nacional, filtrar_rango_anios
from src.preproc._internals.filtrar_area_total import filtrar_area_total
from src.preproc._internals.detectar_cols_poblacion import detectar_cols_poblacion
from src.preproc._internals.derretir_a_largo import derretir_a_largo
from src.preproc._internals.separar_y_convertir import separar_y_convertir
from src.preproc._internals.limpiar_poblacion import limpiar_poblacion


def transformar_poblacion_csv(
    input_csv: str,
    min_year: int = 1979,
    max_year: int = 2023,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Orquesta la transformación desde CSV a columnas: ano, sexo, edad, poblacion."""
    # lectura
    df = leer_datos(input_csv, nrows=nrows)
    if df is None:
        raise FileNotFoundError(f"No se pudo leer el archivo: {input_csv}")

    # normalización de nombres y valores
    df = normalizar_nombres_columnas(df)
    df = minusculizar_valores(df)

    # filtros: dpnom, area total, rango de años
    df = filtrar_dpnom_nacional(df)
    df = filtrar_area_total(df, col_area="area_geografica")
    df = filtrar_rango_anios(df, col="ano", min_year=min_year, max_year=max_year)

    # detectar columnas de población y derretir
    cols_poblacion = detectar_cols_poblacion(df.columns)
    if not cols_poblacion:
        raise ValueError("No se encontraron columnas de población hombre/mujer por edad.")
    largo = derretir_a_largo(df, col_anio="ano", col_area="area_geografica", cols_poblacion=cols_poblacion)

    # separar y convertir a tipos adecuados, dejar solo hombre/mujer
    largo = separar_y_convertir(largo)

    # limpiar población numérica y seleccionar columnas finales
    largo = limpiar_poblacion(largo, col="poblacion")
    result = largo[["ano", "sexo", "edad", "poblacion"]].copy()
    return result
