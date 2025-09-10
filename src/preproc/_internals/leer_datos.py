# 1. Lectura de datos
import pandas as pd
from pathlib import Path


def leer_datos(ruta_archivo: str) -> pd.DataFrame | None:
    """
    Lee datos desde un archivo .csv o .txt detectando automáticamente el separador.

    Parámetros:
    ruta_archivo (str): Ruta al archivo a leer.

    Retorna:
    pd.DataFrame: DataFrame con los datos leídos o None si ocurre un error.
    """
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        print(f"❌ El archivo no existe: {ruta_archivo}")
        return None

    # Intentar lecturas con distintos encodings comunes en archivos del DANE
    # Orden: utf-8, latin-1, cp1252
    encodings = ["utf-8", "latin-1", "cp1252"]
    last_error = None
    for enc in encodings:
        try:
            datos = pd.read_csv(
                ruta,
                sep=None,              # inferir delimitador automáticamente
                engine="python",      # necesario para sep=None
                encoding=enc,
            )
            print(f"✅ Datos leídos correctamente desde {ruta_archivo} con encoding '{enc}'. Forma: {datos.shape}")
            return datos
        except UnicodeDecodeError as e:
            # Probar siguiente encoding
            last_error = e
        except Exception as e:
            # Errores no relacionados al encoding (p. ej., columnas mal formadas)
            print(f"❌ Error al leer el archivo {ruta_archivo} con encoding '{enc}': {e}")
            return None

    # Si ninguno de los encodings funcionó
    # Intento final: reemplazar caracteres problemáticos para rescatar el máximo de datos
    try:
        datos = pd.read_csv(
            ruta,
            sep=None,
            engine="python",
            encoding=encodings[-1],
            errors="replace",
        )
        print(f"✅ Datos leídos con reemplazo de caracteres desde {ruta_archivo}. Forma: {datos.shape}")
        return datos
    except Exception:
        print(f"❌ Error al leer el archivo {ruta_archivo}: {last_error}")
        return None
