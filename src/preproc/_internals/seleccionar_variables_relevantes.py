# 4. Selección de variables relevantes
import pandas as pd


def seleccionar_variables_relevantes(
        df: pd.DataFrame,
        variables: list
    ) -> pd.DataFrame:
    """
    Selecciona un subconjunto de variables relevantes del DataFrame.

    Parámetros:
    df (pd.DataFrame): DataFrame con los datos.
    variables (list): Lista de nombres de columnas a seleccionar.

    Retorna:
    pd.DataFrame: DataFrame con las variables seleccionadas.
    """
    try:
        df_seleccionado = df[variables]
        print("Variables seleccionadas correctamente")
        return df_seleccionado
    except KeyError as e:
        print(f"Error al seleccionar variables: {e}")
        return df