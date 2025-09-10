# 3. Filtrado de datos según causa homologada de defunción
import pandas as pd


def filtrar_por_causa_defuncion(
        df: pd.DataFrame,
        causa_columna: str,
        causas_homologadas: list
    ) -> pd.DataFrame:
    """
    Filtra el DataFrame para incluir solo las filas con causas de defunción homologadas.

    Parámetros:
    df (pd.DataFrame): DataFrame con los datos.
    causa_columna (str): Nombre de la columna que contiene la causa de defunción.
    causas_homologadas (list): Lista de causas homologadas a filtrar.

    Retorna:
    pd.DataFrame: DataFrame filtrado.
    """
    # Validaciones defensivas
    if df is None:
        print("⚠️ No se puede filtrar porque el DataFrame es None")
        return df

    if causa_columna not in df.columns:
        print(f"⚠️ La columna '{causa_columna}' no existe en el DataFrame. Columnas disponibles: {list(df.columns)[:10]}...")
        return df

    try:
        df_filtrado = df[df[causa_columna].isin(causas_homologadas)]
        print("✅ Datos filtrados correctamente")
        return df_filtrado
    except Exception as e:
        print(f"❌ Error al filtrar datos: {e}")
        return df