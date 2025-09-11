from src.preproc._internals.fila_cabecera import fila_cabecera


import pandas as pd


from pathlib import Path


def detectar_header_row(file_path: Path, hoja: str, nrows: int = 60) -> int:
    preview = pd.read_excel(file_path, sheet_name=hoja, header=None, nrows=nrows)
    return fila_cabecera(preview, must_have=["año", "área geográfica", "sexo y edad simple"])