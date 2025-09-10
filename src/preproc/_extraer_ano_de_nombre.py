import re
from pathlib import Path


def _extraer_ano_de_nombre(ruta_archivo: str) -> int | None:
    nombre = Path(ruta_archivo).name
    m = re.search(r"(19|20)\d{2}", nombre)
    return int(m.group(0)) if m else None
