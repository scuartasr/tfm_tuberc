from __future__ import annotations

import os
import pandas as pd
from typing import Literal

from src.preproc._internals.normalizar_nombres_columnas import normalizar_nombres_columnas


def _coerce_keys(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    out = df.copy()
    for k in keys:
        if k in out.columns:
            out[k] = pd.to_numeric(out[k], errors="coerce").astype("Int64")
    return out


def juntar_poblacion_defunciones_por_gr_et(
    poblacion_csv: str,
    defunciones_csv: str,
    fill_zeros: bool = False,
) -> pd.DataFrame:
    """
    Une (left join) población y defunciones por ['ano','sexo','gr_et'].

    - Left: población (columns: ano, sexo, gr_et, poblacion)
    - Right: defunciones (columns: ano, sexo, gr_et, conteo_defunciones)
    - fill_zeros: si True, rellena NaN en conteo_defunciones con 0 (Int64)
    """
    if not os.path.exists(poblacion_csv):
        # tolerar posible error tipográfico 'colmbia'
        alt = poblacion_csv.replace("poblacion_colmbia_", "poblacion_colombia_")
        if os.path.exists(alt):
            poblacion_csv = alt
        else:
            raise FileNotFoundError(f"No existe CSV población: {poblacion_csv}")
    if not os.path.exists(defunciones_csv):
        raise FileNotFoundError(f"No existe CSV defunciones: {defunciones_csv}")

    pop = pd.read_csv(poblacion_csv)
    defun = pd.read_csv(defunciones_csv)

    pop = normalizar_nombres_columnas(pop)
    defun = normalizar_nombres_columnas(defun)

    required_pop = {"ano", "sexo", "gr_et", "poblacion"}
    required_def = {"ano", "sexo", "gr_et", "conteo_defunciones"}
    if not required_pop.issubset(pop.columns):
        raise ValueError(f"Población sin columnas requeridas: {required_pop - set(pop.columns)}")
    if not required_def.issubset(defun.columns):
        raise ValueError(f"Defunciones sin columnas requeridas: {required_def - set(defun.columns)}")

    keys = ["ano", "sexo", "gr_et"]
    pop = _coerce_keys(pop, keys)
    defun = _coerce_keys(defun, keys)

    merged = pop.merge(defun[keys + ["conteo_defunciones"]], on=keys, how="left")

    if fill_zeros:
        if "conteo_defunciones" in merged.columns:
            merged["conteo_defunciones"] = (
                pd.to_numeric(merged["conteo_defunciones"], errors="coerce")
                .fillna(0)
                .astype("Int64")
            )

    # Orden y tipos
    cols_order = [c for c in ["ano", "sexo", "gr_et", "poblacion", "conteo_defunciones"] if c in merged.columns]
    merged = merged[cols_order]
    return merged


def calcular_tasa_por_100k(
    df: pd.DataFrame,
    col_poblacion: str = "poblacion",
    col_defunciones: str = "conteo_defunciones",
    out_col: str = "tasa_x100k",
    out_col_pura: str = "tasa",
    min_rate: float | None = 1e-8,
) -> pd.DataFrame:
    """
    Añade una columna de tasa por 100.000 habitantes: (defunciones/población)*100000.
    - Si población <= 0 o NaN, la tasa queda NaN.
    - Mantiene columnas existentes y agrega 'tasa_x100k' como float.
    """
    out = df.copy()
    if col_poblacion not in out.columns or col_defunciones not in out.columns:
        return out
    pop = pd.to_numeric(out[col_poblacion], errors="coerce")
    defu = pd.to_numeric(out[col_defunciones], errors="coerce")

    # Tasa pura y por 100k.
    tasa_pura = defu / pop

    # Aplicar tasa mínima cuando no hay defunciones (0 o NaN) y población válida (>0)
    if min_rate is not None:
        mask_pob_valida = pop > 0
        mask_sin_def = defu.isna() | (defu <= 0)
        tasa_pura = tasa_pura.where(~(mask_pob_valida & mask_sin_def), other=min_rate)

    tasa_x100k = tasa_pura * 100000.0

    # Evitar valores cuando población no válida
    tasa_pura = tasa_pura.where(pop > 0)
    tasa_x100k = tasa_x100k.where(pop > 0)

    out[out_col] = tasa_x100k.astype(float)
    out[out_col_pura] = tasa_pura.astype(float)
    return out
