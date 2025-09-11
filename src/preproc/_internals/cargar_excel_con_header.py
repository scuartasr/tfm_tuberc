import pandas as pd


from pathlib import Path


def cargar_excel_con_header(file_path: Path, hoja: str, header_row: int) -> pd.DataFrame:
    # Intento +1
    df = pd.read_excel(file_path, sheet_name=hoja, header=header_row + 1)
    if not set(df.columns):
        df = pd.read_excel(file_path, sheet_name=hoja, header=header_row)
    return df