# ===================== Orquestador público =====================
from typing import Optional
from src.preproc._internals.normalizar_nombres_columnas import normalizar_nombres_columnas
from src.preproc._internals.agregar_poblacion import agregar_poblacion
from src.preproc._internals.cargar_excel_con_header import cargar_excel_con_header
from src.preproc._internals.derretir_a_largo import derretir_a_largo
from src.preproc._internals.detectar_cols_poblacion import detectar_cols_poblacion
from src.preproc._internals.detectar_header_row import detectar_header_row
from src.preproc._internals.exportar_opcional import exportar_opcional
from src.preproc._internals.filtrar_area_total import filtrar_area_total
from src.preproc._internals.separar_y_convertir import separar_y_convertir


import pandas as pd


from pathlib import Path


def transformacion_poblacion(
    file_path: str,
    sheet_name: Optional[str] = None,
    export_csv: Optional[str] = None,
    export_xlsx: Optional[str] = None,
) -> pd.DataFrame:
    """
    Lee el archivo de proyecciones y devuelve columnas: ano, sexo, edad, poblacion.
    SRP: cada paso se delega a helpers específicos. Reutiliza normalizar_nombres_columnas.
    """
    file_path = Path(file_path)
    xls = pd.ExcelFile(file_path)
    hoja = sheet_name if sheet_name is not None else xls.sheet_names[0]

    header_row = detectar_header_row(file_path, hoja)
    df_raw = cargar_excel_con_header(file_path, hoja, header_row)

    # Normalización de nombres reutilizando helper interno
    df_norm = normalizar_nombres_columnas(df_raw)

    # Columnas esperadas tras normalización
    col_anio = "ano"
    col_area = "area_geografica"
    if col_anio not in df_norm.columns or col_area not in df_norm.columns:
        raise KeyError(f"No se encuentran columnas requeridas: '{col_anio}' y/o '{col_area}'. Columnas: {list(df_norm.columns)[:10]}...")

    df_total = filtrar_area_total(df_norm, col_area)
    cols_poblacion = detectar_cols_poblacion(df_total.columns)
    if not cols_poblacion:
        raise ValueError("No se encontraron columnas de población 'hombres_X'/'mujeres_X' tras normalización.")

    largo = derretir_a_largo(df_total, col_anio, col_area, cols_poblacion)
    largo = separar_y_convertir(largo)
    result = agregar_poblacion(largo, col_anio)

    exportar_opcional(result, export_csv, export_xlsx)
    return result