from __future__ import annotations

import argparse
import os
from typing import Optional, Sequence
import pandas as pd

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.preproc._internals.join_poblacion_defunciones import juntar_poblacion_defunciones_por_gr_et, calcular_tasa_por_100k
from src.preproc._internals.io_utils import build_output_path


DEFAULT_POP = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/processed/poblacion/poblacion_colombia_gr_et.csv",
	)
)
DEFAULT_DEF = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/processed/defunc/defunciones_por_gr_et.csv",
	)
)
DEFAULT_OUTDIR = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/processed/mortalidad",
	)
)
DEFAULT_OUTPUT = os.path.join(DEFAULT_OUTDIR, "poblacion_defunciones_por_gr_et.csv")


def _build_output_path(output_csv: Optional[str], outdir: Optional[str]) -> str:
	return build_output_path(output_csv, outdir, DEFAULT_OUTDIR, os.path.basename(DEFAULT_OUTPUT))


def main(argv: Optional[Sequence[str]] = None) -> int:
	parser = argparse.ArgumentParser(
		description="Left join de población y defunciones por año/sexo/gr_et"
	)
	parser.add_argument("--pop", default=DEFAULT_POP, help="CSV de población por gr_et.")
	parser.add_argument("--defunc", default=DEFAULT_DEF, help="CSV de defunciones por gr_et.")
	parser.add_argument("--output", default=None, help="Ruta de salida del CSV unido.")
	parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Carpeta de salida si no hay --output.")
	parser.add_argument("--fill-zeros", action="store_true", help="Rellenar NaN de defunciones con 0.")
	parser.add_argument("--dry-run", action="store_true", help="No escribe archivo, solo vista previa.")
	parser.add_argument("--rows", type=int, default=None, help="Recorta filas en vista previa.")

	args = parser.parse_args(list(argv) if argv is not None else None)

	# Primero, vista previa sin forzar ceros para validar el cruce
	df_preview = juntar_poblacion_defunciones_por_gr_et(args.pop, args.defunc, fill_zeros=False)
	if args.rows is not None:
		prev = df_preview.head(args.rows)
	else:
		prev = df_preview.head(20)

	with pd.option_context("display.max_columns", None, "display.width", 140):
		print("Vista previa (NaN cuando no cruza):")
		print(prev)
		print("\nFilas totales (preview base):", len(df_preview))

	# Si se solicita, generar versión con ceros y calcular tasa
	df_final = df_preview
	if args.fill_zeros:
		df_final = juntar_poblacion_defunciones_por_gr_et(args.pop, args.defunc, fill_zeros=True)
	# Calcular tasa por 100k sobre el DataFrame final (con o sin ceros)
	df_final = calcular_tasa_por_100k(df_final)

	if not args.dry_run:
		out_path = _build_output_path(args.output, args.outdir)
		df_final.to_csv(out_path, index=False)
		print(f"\nEscrito a: {out_path}")
	else:
		print("\nDry-run: no se escribió archivo de salida.")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())

