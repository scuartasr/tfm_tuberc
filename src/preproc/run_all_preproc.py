from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence


def run_script(script_path: Path, args: Sequence[str] = (), env: Optional[dict] = None) -> None:
    if not script_path.exists():
        raise FileNotFoundError(f"No existe el script: {script_path}")
    cmd = [sys.executable, str(script_path), *args]
    print(f"→ Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, env=env)
    print(f"✓ Finalizado: {script_path.name}\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Orquestador de preprocesamiento completo")
    parser.add_argument("--dry-run", action="store_true", help="Propaga dry-run a scripts que lo soportan")
    parser.add_argument("--rows", type=int, default=None, help="Recorta filas en scripts que lo soportan")
    parser.add_argument("--fill-zeros", action="store_true", help="Rellenar ceros en cruce población-defunciones")
    parser.add_argument("--tuberc-max-files", type=int, default=None, help="Limitar archivos en preproc_tuberc.py (DEBUG_MAX_FILES)")
    parser.add_argument("--tuberc-verbose", type=int, default=2, help="Nivel de verbosidad para preproc_tuberc.py (VERBOSE_LEVEL)")

    args = parser.parse_args(list(argv) if argv is not None else None)

    base = Path(__file__).resolve().parent
    s_pop = base / "preproc_poblacion.py"
    s_gret = base / "preproc_gret_poblacion.py"
    s_tub = base / "preproc_tuberc.py"
    s_join = base / "preproc_poblac_defunc.py"

    try:
        # 1) Población (CSV largo)
        pop_args = []
        if args.dry_run:
            pop_args.append("--dry-run")
        if args.rows is not None:
            pop_args += ["--rows", str(args.rows)]
        run_script(s_pop, pop_args)

        # 2) Población por gr_et
        gret_args = []
        if args.dry_run:
            gret_args.append("--dry-run")
        if args.rows is not None:
            gret_args += ["--rows", str(args.rows)]
        run_script(s_gret, gret_args)

        # 3) Defunciones (usa variables de entorno)
        env = os.environ.copy()
        if args.tuberc_max_files is not None:
            env["DEBUG_MAX_FILES"] = str(args.tuberc_max_files)
        if args.tuberc_verbose is not None:
            env["VERBOSE_LEVEL"] = str(args.tuberc_verbose)
        run_script(s_tub, env=env)

        # 4) Cruce población-defunciones
        join_args = []
        if args.dry_run:
            join_args.append("--dry-run")
        if args.rows is not None:
            join_args += ["--rows", str(args.rows)]
        if args.fill_zeros:
            join_args.append("--fill-zeros")
        run_script(s_join, join_args)

    except subprocess.CalledProcessError as e:
        print(f"❌ Falló la ejecución de {e.cmd}: código {e.returncode}")
        return e.returncode
    except Exception as ex:
        print(f"❌ Error: {ex}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
