import pandas as pd
import sys
from pathlib import Path

# Asegurar que el proyecto raíz esté en sys.path antes de importar desde 'src.*'
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.preproc._internals._extraer_ano_de_nombre import _extraer_ano_de_nombre
from src.preproc._internals.agrupar_por_ano_sexo import agrupar_por_ano_sexo
from src.preproc._internals.filtrar_por_causa_defuncion import filtrar_por_causa_defuncion
from src.preproc._internals.leer_datos import leer_datos
from src.preproc._internals.normalizar_nombres_columnas import normalizar_nombres_columnas
from src.preproc._internals.seleccionar_variables_relevantes import seleccionar_variables_relevantes
from src.preproc._internals.corregir_grupos_etarios import corregir_grupos_etarios_agrupado, asignar_gr_et_sin_reagrupar


def procesar_archivo(ruta: str) -> pd.DataFrame | None:
    print(f"\n➡️ Procesando: {ruta}")
    df = leer_datos(ruta)
    if df is None:
        print("⚠️ Saltando archivo por error de lectura")
        return None

    df = normalizar_nombres_columnas(df)

    # Asegurar columna 'ano' si falta, usando el nombre del archivo
    if 'ano' not in df.columns:
        ano_archivo = _extraer_ano_de_nombre(ruta)
        if ano_archivo is not None:
            df['ano'] = ano_archivo
            print(f"ℹ️ Columna 'ano' añadida desde nombre de archivo: {ano_archivo}")

    # Filtrar por causa homologada (2)
    df = filtrar_por_causa_defuncion(
        df,
        causa_columna='cau_homol',
        causas_homologadas=[2]
    )

    # Variables de interés
    columnas = ['ano', 'sexo', 'gru_ed1']
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        print(f"⚠️ Columnas faltantes {faltantes} en {ruta}. Saltando archivo.")
        return None
    df = seleccionar_variables_relevantes(df, columnas)

    # Agrupar por gru_ed1 (base intermedia con conteo)
    df = agrupar_por_ano_sexo(df, 'ano', 'sexo', 'gru_ed1')

    # Asignar gr_et según reglas, sin perder el detalle por gru_ed1
    df = asignar_gr_et_sin_reagrupar(df)
    # Renombrar gru_ed1 -> edad_grupo para mayor claridad
    if 'gru_ed1' in df.columns:
        df = df.rename(columns={'gru_ed1': 'edad_grupo'})
    return df