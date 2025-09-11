from typing import Optional
import pandas as pd


from pathlib import Path


def exportar_opcional(df: pd.DataFrame, export_csv: Optional[str], export_xlsx: Optional[str]) -> None:
    if export_csv:
        Path(export_csv).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(export_csv, index=False, encoding="utf-8")
    if export_xlsx:
        Path(export_xlsx).parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(export_xlsx, index=False)