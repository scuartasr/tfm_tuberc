from typing import Iterable, List


def detectar_cols_poblacion(columns: Iterable[str]) -> List[str]:
    def es_col(c: str) -> bool:
        if not isinstance(c, str):
            return False
        c2 = c.strip().lower()
        return (c2.startswith("hombres_") or c2.startswith("mujeres_")) and "_" in c2

    return [c for c in columns if es_col(c)]