from __future__ import annotations

import os


def build_output_path(
    output_csv: str | None,
    outdir: str | None,
    default_outdir: str,
    default_filename: str,
) -> str:
    """
    Construye la ruta de salida y asegura que la carpeta exista.

    - Si se pasa output_csv, crea su carpeta padre y devuelve esa ruta.
    - En caso contrario, usa outdir o default_outdir y concatena default_filename.
    """
    if output_csv:
        parent = os.path.dirname(output_csv)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return output_csv
    target_dir = outdir or default_outdir
    os.makedirs(target_dir, exist_ok=True)
    return os.path.join(target_dir, default_filename)
