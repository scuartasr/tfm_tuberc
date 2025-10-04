# 1. Lectura de datos
import pandas as pd
"""Utilidad para lectura robusta de archivos de defunciones.

Mejoras clave:
 - Detección automática de encoding (utf-8, latin-1, cp1252).
 - Opción `force_object` para forzar todos los campos como texto, evitando coerciones que
   puedan truncar valores (similar al fix aplicado a población).
 - Preservación y normalización de códigos administrativos asegurando ceros a la izquierda.
 - Alerta preventiva si se detectan patrones de separadores de miles (p.ej. '1.234').
"""

from pathlib import Path
import re
import pandas as pd

_PATRON_MILES = re.compile(r"\b\d{1,3}\.\d{3}(?:\.\d{3})*\b")


def leer_datos(
    ruta_archivo: str,
    nrows: int | None = None,
    force_object: bool = False,
    preserve_codes: bool = True,
    warn_thousands: bool = True,
) -> pd.DataFrame | None:
    """Lee datos desde un archivo .csv o .txt detectando automáticamente el separador.

    Parámetros
    ----------
    ruta_archivo : str
        Ruta al archivo a leer.
    nrows : int | None
        Número de filas a leer (None = todas).
    force_object : bool
        Si True, fuerza `dtype=str` (útil si hubiera separadores de miles o códigos con ceros a la izquierda).
    preserve_codes : bool
        Normaliza códigos administrativos a longitud fija con ceros a la izquierda.
    warn_thousands : bool
        Si True, alerta si se detecta patrón de separadores de miles y no se utilizó `force_object`.
    """
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        print(f"❌ El archivo no existe: {ruta_archivo}")
        return None

    encodings = ["utf-8", "latin-1", "cp1252"]
    last_error: Exception | None = None
    read_kwargs: dict = {}
    if force_object:
        read_kwargs["dtype"] = str

    for enc in encodings:
        try:
            datos = pd.read_csv(
                ruta,
                sep=None,
                engine="python",
                encoding=enc,
                nrows=nrows,
                **read_kwargs,
            )
            print(
                f"✅ Datos leídos correctamente desde {ruta_archivo} con encoding '{enc}'. Forma: {datos.shape}"
            )
            datos = _postprocess(
                datos,
                preserve_codes=preserve_codes,
                ruta_archivo=ruta_archivo,
                force_object=force_object,
                warn_thousands=warn_thousands,
            )
            return datos
        except UnicodeDecodeError as e:
            last_error = e
        except Exception as e:
            print(f"❌ Error al leer el archivo {ruta_archivo} con encoding '{enc}': {e}")
            return None

    # Intento final con reemplazo de caracteres problemáticos
    try:
        datos = pd.read_csv(
            ruta,
            sep=None,
            engine="python",
            encoding=encodings[-1],
            errors="replace",
            nrows=nrows,
            **read_kwargs,
        )
        print(
            f"✅ Datos leídos con reemplazo de caracteres desde {ruta_archivo}. Forma: {datos.shape}"
        )
        datos = _postprocess(
            datos,
            preserve_codes=preserve_codes,
            ruta_archivo=ruta_archivo,
            force_object=force_object,
            warn_thousands=warn_thousands,
        )
        return datos
    except Exception:
        print(f"❌ Error al leer el archivo {ruta_archivo}: {last_error}")
        return None


# ------------------ Utilidades internas ------------------ #

def _postprocess(
    df: pd.DataFrame,
    preserve_codes: bool,
    ruta_archivo: str,
    force_object: bool,
    warn_thousands: bool,
) -> pd.DataFrame:
    if preserve_codes:
        df = _preservar_codigos(df)
    if warn_thousands and not force_object:
        try:
            if _detectar_patron_miles(df):
                print(
                    f"⚠️ Posible separador de miles detectado en '{ruta_archivo}'. "
                    "Considere usar force_object=True y limpieza posterior."
                )
        except Exception as e:  # Defensivo: no romper flujo
            print(f"⚠️ Advertencia: fallo al detectar patrón de miles ({e}).")
    return df


def _detectar_patron_miles(df: pd.DataFrame, sample_rows: int = 500) -> bool:
    muestra = df.head(sample_rows)
    for col in muestra.columns:
        if muestra[col].dtype == object:
            serie = muestra[col].dropna().astype(str)
            if serie.str.contains(_PATRON_MILES).any():
                return True
    return False


def _preservar_codigos(df: pd.DataFrame) -> pd.DataFrame:
    map_lens = {
        "cod_dpto": 2,
        "COD_DPTO": 2,
        "cod_munic": 3,
        "COD_MUNIC": 3,
        "codptore": 2,
        "CODPTORE": 2,
        "codmunre": 3,
        "CODMUNRE": 3,
    }
    for col, width in map_lens.items():
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(".0$", "", regex=True)
            df[col] = df[col].str.replace(r"[^0-9]", "", regex=True).str.zfill(width)
    return df
