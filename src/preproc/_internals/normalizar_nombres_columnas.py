# 2. Normalización de nombres de columnas usando janitor
import pandas as pd


def normalizar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los nombres de las columnas del DataFrame.

    Parámetros:
    df (pd.DataFrame): DataFrame con los datos.

    Retorna:
    pd.DataFrame: DataFrame con nombres de columnas normalizados.
    """
    if df is None:
        print("No se normalizan columnas porque el DataFrame es None")
        return df
    try:
        import janitor
        df = df.clean_names()
        print("Nombres de columnas normalizados")
        return df
    except Exception as e:
        print(f"Error al normalizar nombres de columnas: {e}")
        return df