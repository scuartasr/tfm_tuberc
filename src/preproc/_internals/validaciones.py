from __future__ import annotations
"""Validaciones ligeras de integridad para datasets de población, defunciones y cruces.

Estas funciones NO detienen la ejecución salvo en checks críticos con assert explícito.
Se busca balance entre robustez y bajo costo computacional.
"""

from typing import Iterable
import pandas as pd
import re

_PATRON_MILES = re.compile(r"\b\d{1,3}\.\d{3}(?:\.\d{3})*\b")


# -------------------- Población -------------------- #

def validar_poblacion(df: pd.DataFrame, critical: bool = True) -> list[str]:
    """Realiza validaciones sobre el DataFrame de población (largo por edad o agregado por gr_et).

    Soporta dos esquemas:
      1. Largo: columnas {ano, sexo, edad, poblacion}
      2. Agregado: columnas {ano, sexo, gr_et, poblacion}

    Checks comunes:
      - Presencia de columnas mínimas para alguno de los esquemas.
      - Año mínimo/máximo esperados (solo advertencias si faltan extremos).
      - Valor de referencia hombres 0-4 año 1979 (solo posible en esquema largo o inferible de gr_et=1).
      - Ausencia de patrones de miles (ya limpiados) en 'poblacion'.
      - No negativos.

    Retorna lista de advertencias. Si critical=True y falta el conjunto mínimo de columnas para ambos esquemas, levanta AssertionError.
    """
    warnings: list[str] = []

    has_largo = {"ano", "sexo", "edad", "poblacion"}.issubset(df.columns)
    has_agregado = {"ano", "sexo", "gr_et", "poblacion"}.issubset(df.columns)
    if not (has_largo or has_agregado):
        msg = ("Faltan columnas requeridas en población para esquema largo (ano,sexo,edad,poblacion) "
               "o agregado (ano,sexo,gr_et,poblacion)")
        if critical:
            raise AssertionError(msg)
        warnings.append(msg)
        return warnings

    # Rango de años (flexible si el dataset se recorta)
    anos = df["ano"].dropna().unique()
    if len(anos) > 0:
        min_ano, max_ano = anos.min(), anos.max()
        if min_ano > 1979:
            warnings.append(f"Primer año > 1979 ({min_ano}); ¿dataset recortado o faltan filas?")
        if max_ano < 2023:
            warnings.append(f"Último año < 2023 ({max_ano}); ¿dataset incompleto?")

    # Valor de referencia crítico (hombres 0-4, año 1979) adaptable
    try:
        # Normalizar sexo a forma textual para comparar (acepta 1 -> hombre, 2 -> mujer)
        sexo_series = df["sexo"].astype(str).str.lower()
        sexo_es_hombre = sexo_series.isin(["1", "h", "hombre", "masculino", "m"])
        if has_largo:
            ref = df[(df["ano"] == 1979) & sexo_es_hombre & (df["edad"].between(0, 4))]
            label_ref = "(esquema largo edades 0-4)"
        elif has_agregado:
            # Usar gr_et=1 (que corresponde a 0-4) como aproximación
            ref = df[(df["ano"] == 1979) & sexo_es_hombre & (df["gr_et"] == 1)]
            label_ref = "(agregado gr_et=1)"
        else:
            ref = pd.DataFrame()
            label_ref = ""
        if not ref.empty:
            total_ref = int(ref["poblacion"].sum())
            if total_ref != 1_795_941:
                msg = (f"Valor de referencia población hombres 0-4 año 1979 inesperado {label_ref}: "
                       f"{total_ref} != 1795941")
                if critical:
                    raise AssertionError(msg)
                warnings.append(msg)
        else:
            warnings.append("No se encontró referencia hombres 0-4 año 1979 (posible recorte o esquema no compatible).")
    except Exception as e:
        warnings.append(f"No se pudo evaluar referencia 0-4 1979: {e}")

    # Patrón miles (no debería existir tras limpieza)
    sample = df.head(1000)
    try:
        if sample["poblacion"].astype(str).str.contains(_PATRON_MILES).any():
            warnings.append("Detectado patrón de miles en 'poblacion' (posible error de limpieza).")
    except Exception as e:
        warnings.append(f"Error evaluando patrón de miles: {e}")

    # No negativas
    if (df["poblacion"] < 0).any():
        msg = "Valores negativos en poblacion detectados."
        if critical:
            raise AssertionError(msg)
        warnings.append(msg)

    return warnings


# -------------------- Defunciones -------------------- #

def validar_defunciones(df: pd.DataFrame, expected_sex_values: Iterable[int] | None = (1, 2, 9)) -> list[str]:
    warnings: list[str] = []
    required_cols = {"ano", "sexo", "gr_et", "conteo_defunciones"}
    missing = required_cols - set(df.columns)
    if missing:
        warnings.append(f"Faltan columnas en defunciones: {missing}")
        return warnings

    # Sexo esperado
    sex_values = set(df["sexo"].dropna().unique())
    if expected_sex_values is not None:
        extra = sex_values - set(expected_sex_values)
        if extra:
            warnings.append(f"Valores inesperados en 'sexo' (defunciones): {extra}")

    # No negativos
    if (df["conteo_defunciones"] < 0).any():
        warnings.append("Valores negativos en conteo_defunciones.")

    return warnings


# -------------------- Cruce -------------------- #

def validar_cruce(df: pd.DataFrame) -> list[str]:
    warnings: list[str] = []
    required_cols = {"ano", "sexo", "gr_et", "poblacion", "conteo_defunciones"}
    if not required_cols.issubset(df.columns):
        warnings.append(f"Cruce incompleto; faltan columnas: {required_cols - set(df.columns)}")
        return warnings

    # Población cero con defunciones positivas (puede ser real si es un sub-grupo ausente en población)
    mask = (df["poblacion"] == 0) & (df["conteo_defunciones"] > 0)
    if mask.any():
        warnings.append(
            f"Hay {mask.sum()} filas con defunciones>0 pero población=0 (revisar imputaciones/fill_zeros)."
        )

    # Defunciones mayores que población (en magnitud puede ocurrir en ventanas pequeñas, pero se reporta)
    mask2 = df["conteo_defunciones"] > df["poblacion"]
    if mask2.any():
        warnings.append(f"{mask2.sum()} filas con conteo_defunciones > poblacion (verificar consistencia).")

    return warnings


def resumen_advertencias(nombre: str, warns: list[str]) -> None:
    if not warns:
        print(f"✓ {nombre}: sin advertencias.")
    else:
        print(f"⚠️ {nombre}: {len(warns)} advertencia(s):")
        for w in warns:
            print(f"   - {w}")
