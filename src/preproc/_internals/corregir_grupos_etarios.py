import pandas as pd
import numpy as np


def corregir_grupos_etarios_agrupado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recibe una base agrupada por ['ano','sexo','gru_ed1'] con la columna 'conteo_defunciones'
    y corrige los grupos etarios (gr_et) según el año, agregando nuevamente por ['ano','sexo','gr_et'].

    Reglas:
    - 1979-1997:
        gr_et = 1 si gru_ed1 < 8
        gr_et = gru_ed1 - 6 si 7 < gru_ed1 < 23
        gr_et = 17 si gru_ed1 > 22 y gru_ed1 != 25
    - 1998-2007:
        gr_et = 1 si gru_ed1 < 9
        gr_et = gru_ed1 - 7 si 8 < gru_ed1 < 24
        gr_et = 17 si gru_ed1 > 23 y gru_ed1 != 26
    - 2008-2023:
        gr_et = 1 si gru_ed1 < 9
        gr_et = gru_ed1 - 7 si 8 < gru_ed1 < 24
        gr_et = 17 si gru_ed1 > 23 y gru_ed1 != 29

    Filas con 'gr_et' sin asignar (p. ej., gru_ed1 == 25/26/29 en sus rangos) se descartan.
    """
    required_cols = {"ano", "sexo", "gru_ed1", "conteo_defunciones"}
    if not required_cols.issubset(df.columns):
        print(f"⚠️ No se corrigen grupos etarios: faltan columnas {required_cols - set(df.columns)}")
        return df

    datos = df.copy()
    # Asegurar tipos numéricos
    datos["ano"] = pd.to_numeric(datos["ano"], errors="coerce")
    datos["gru_ed1"] = pd.to_numeric(datos["gru_ed1"], errors="coerce")

    # Inicializar gr_et como NaN
    datos["gr_et"] = np.nan

    ano = datos["ano"]
    g = datos["gru_ed1"]

    # 1979-1997
    m_a = (ano >= 1979) & (ano <= 1997)
    datos.loc[m_a & (g < 8), "gr_et"] = 1
    datos.loc[m_a & (g > 7) & (g < 23), "gr_et"] = g[m_a & (g > 7) & (g < 23)] - 6
    datos.loc[m_a & (g > 22) & (g != 25), "gr_et"] = 17

    # 1998-2007
    m_b = (ano >= 1998) & (ano <= 2007)
    datos.loc[m_b & (g < 9), "gr_et"] = 1
    datos.loc[m_b & (g > 8) & (g < 24), "gr_et"] = g[m_b & (g > 8) & (g < 24)] - 7
    datos.loc[m_b & (g > 23) & (g != 26), "gr_et"] = 17

    # 2008-2023
    m_c = (ano >= 2008) & (ano <= 2023)
    datos.loc[m_c & (g < 9), "gr_et"] = 1
    datos.loc[m_c & (g > 8) & (g < 24), "gr_et"] = g[m_c & (g > 8) & (g < 24)] - 7
    datos.loc[m_c & (g > 23) & (g != 29), "gr_et"] = 17

    # Eliminar filas sin asignación de gr_et
    datos = datos.dropna(subset=["gr_et"]).copy()
    if datos.empty:
        print("⚠️ Tras la corrección de grupos etarios no quedaron filas.")
        return datos

    datos["gr_et"] = datos["gr_et"].astype(int)

    # Re-agrupar por gr_et
    out = (
        datos.groupby(["ano", "sexo", "gr_et"], as_index=False)["conteo_defunciones"].sum()
    )
    print("✅ Grupos etarios corregidos y datos re-agrupados")
    return out
