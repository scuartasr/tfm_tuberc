# 5. Agrupación de datos por año, sexo y grupo etario
import pandas as pd


def agrupar_por_ano_sexo(
        df: pd.DataFrame,
        ano_columna: str,
        sexo_columna: str,
        grupo_etario_columna: str = None
    ) -> pd.DataFrame:
    """
    Agrupa el DataFrame por año y sexo, contando el número de defunciones.

    Parámetros:
    df (pd.DataFrame): DataFrame con los datos.
    ano_columna (str): Nombre de la columna que contiene el año.
    sexo_columna (str): Nombre de la columna que contiene el sexo.

    Retorna:
    pd.DataFrame: DataFrame agrupado con conteo de defunciones.
    """
    try:
        df_agrupado = df.groupby([ano_columna, sexo_columna, grupo_etario_columna]).size().reset_index(name='conteo_defunciones')
        print("Datos agrupados correctamente")
        return df_agrupado
    except KeyError as e:
        print(f"Error al agrupar datos: {e}")
        return df