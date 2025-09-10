#
# Preprocesamiento de datos de defunción
# Autor: [Simón Cuartas Rendón]
# Fecha: [2025-2S]

#
# 0. Librerías necesarias
import os
import sys
from pathlib import Path
import pandas as pd
try:
    from tqdm import tqdm
except Exception:
    # Fallback simple si tqdm no está disponible
    def tqdm(iterable, **kwargs):  # type: ignore
        print("⚠️ tqdm no está instalado; iterando sin barra de progreso.")
        return iterable

# Asegurar que el proyecto raíz esté en sys.path antes de importar desde 'src.*'
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.preproc._internals.procesar_archivo import procesar_archivo
from src.preproc._internals._extraer_ano_de_nombre import _extraer_ano_de_nombre

if __name__ == "__main__":
    # Verbosidad: 0 = solo barra, 1 = detalle por archivo, 2 = + resumen final
    def _parse_int(value: str, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default

    VERBOSE_ENV = os.getenv("VERBOSE_LEVEL")
    VERBOSE_LEVEL = _parse_int(VERBOSE_ENV, 2) if VERBOSE_ENV is not None else 2

    def log(msg: str, min_level: int = 1):
        if VERBOSE_LEVEL >= min_level:
            print(msg)

    from contextlib import contextmanager
    import os as _os
    import sys as _sys

    @contextmanager
    def suppress_stdout(enabled: bool):
        if not enabled:
            yield
            return
        saved_stdout = _sys.stdout
        try:
            _sys.stdout = open(_os.devnull, 'w')
            yield
        finally:
            try:
                _sys.stdout.close()
            except Exception:
                pass
            _sys.stdout = saved_stdout

    log("Este módulo contiene funciones para el preprocesamiento de datos de defunción.")

    base_dir = Path("./data/raw/defunc")
    patrones = ["Defun*.txt", "Defun*.csv"]
    archivos = []
    for pat in patrones:
        archivos.extend(sorted(base_dir.glob(pat)))

    # Ordenar por año detectado en el nombre, dejando al final los que no matchean
    archivos = sorted(
        archivos,
        key=lambda p: (_extraer_ano_de_nombre(p.name) is None, _extraer_ano_de_nombre(p.name) or 0, p.name)
    )

    # Limitar para pruebas con variable de entorno, ej.: DEBUG_MAX_FILES=3
    max_files_env = os.getenv("DEBUG_MAX_FILES")
    if max_files_env:
        try:
            max_n = int(max_files_env)
            archivos = archivos[:max_n]
            log(f"🔎 Modo debug: procesando solo {max_n} archivo(s)")
        except ValueError:
            pass

    if not archivos:
        print(f"❌ No se encontraron archivos en {base_dir}")
        sys.exit(1)

    resultados = []
    procesados = 0
    fallidos = 0

    pbar = tqdm(archivos, desc="Procesando archivos", unit="archivo", dynamic_ncols=True)
    for ruta in pbar:
        # Mostrar el nombre del archivo en curso
        try:
            pbar.set_postfix({"archivo": Path(ruta).name, "ok": procesados, "fail": fallidos})
        except Exception:
            pass
        # En nivel 0, suprimir salidas de consola del procesamiento interno
        with suppress_stdout(VERBOSE_LEVEL == 0):
            df_out = procesar_archivo(str(ruta))
        if df_out is not None and not df_out.empty:
            resultados.append(df_out)
            procesados += 1
        else:
            fallidos += 1
        # Actualizar contadores en la barra
        try:
            pbar.set_postfix({"archivo": Path(ruta).name, "ok": procesados, "fail": fallidos})
        except Exception:
            pass
    # Cerrar barra explícitamente
    try:
        pbar.close()
    except Exception:
        pass

    if not resultados:
        print("❌ No se generaron resultados. Revisa los logs anteriores.")
        sys.exit(1)

    df_final = pd.concat(resultados, ignore_index=True)
    log(f"\n📊 Tabla final concatenada: forma {df_final.shape}")

    # Guardar resultado
    out_dir = Path("./data/processed/defunc")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "defunciones_agrupadas.csv"
    df_final.to_csv(out_path, index=False)
    log(f"💾 Guardado en: {out_path.resolve()}")

    # Resumen en consola controlado por VERBOSE_LEVEL (>=2) o SHOW_SUMMARY si no se definió VERBOSE_LEVEL
    if VERBOSE_ENV is not None:
        show_summary = VERBOSE_LEVEL >= 2
    else:
        show_summary = os.getenv("SHOW_SUMMARY", "1").strip().lower() in ("1", "true", "yes", "y", "on")

    if show_summary:
        try:
            resumen_ano_sexo = (
                df_final
                .groupby(['ano', 'sexo'], as_index=False)['conteo_defunciones']
                .sum()
                .sort_values(['ano', 'sexo'])
            )
            log("\n🔎 Resumen por año y sexo:", min_level=2)
            log(resumen_ano_sexo.to_string(index=False), min_level=2)

            resumen_ano = (
                df_final
                .groupby(['ano'], as_index=False)['conteo_defunciones']
                .sum()
                .sort_values(['ano'])
            )
            log("\n🧮 Totales por año:", min_level=2)
            log(resumen_ano.to_string(index=False), min_level=2)
        except Exception as e:
            log(f"⚠️ No se pudo generar el resumen final: {e}")

    log(f"✅ Finalizado. Archivos OK: {procesados} | Fallidos/omitidos: {fallidos}")