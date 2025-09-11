from __future__ import annotations

import argparse
import os
from typing import Optional, Sequence

import pandas as pd

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.preproc._internals.transformar_poblacion_csv import transformar_poblacion_csv


DEFAULT_INPUT = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/raw/poblacion/poblacion_colombia_dane.csv",
	)
)

DEFAULT_OUTDIR = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/processed/poblacion",
	)
)

DEFAULT_OUTPUT_NAME = "poblacion_colombia_larga.csv"


def _build_output_path(output_csv: Optional[str], outdir: Optional[str]) -> Optional[str]:
	if output_csv:
		return output_csv
	if outdir is None:
		outdir = DEFAULT_OUTDIR
	os.makedirs(outdir, exist_ok=True)
	return os.path.join(outdir, DEFAULT_OUTPUT_NAME)


def main(argv: Optional[Sequence[str]] = None) -> int:
	parser = argparse.ArgumentParser(description="Transforma población DANE CSV a formato largo.")
	parser.add_argument("--input", default=DEFAULT_INPUT, help="Ruta del CSV de entrada.")
	parser.add_argument("--output", default=None, help="Ruta completa del CSV de salida.")
	parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Carpeta de salida.")
	parser.add_argument("--dry-run", action="store_true", help="No escribe archivo, solo vista previa.")
	parser.add_argument("--rows", type=int, default=None, help="Limitar filas leídas (útil para pruebas).")
	parser.add_argument("--min-year", type=int, default=1979)
	parser.add_argument("--max-year", type=int, default=2023)
	parser.add_argument("--nrows", type=int, default=None, help="Leer solo N filas del archivo (acelera pruebas)")

	args = parser.parse_args(list(argv) if argv is not None else None)

	input_path = args.input
	if not os.path.exists(input_path):
		alt = input_path.replace("poblacion_colombia_dane.csv", "poblacion_colombiana_dane.csv")
		if os.path.exists(alt):
			input_path = alt
		else:
			raise FileNotFoundError(f"No se encontró el archivo: {args.input}")

	# Transformar
	df = transformar_poblacion_csv(input_path, min_year=args.min_year, max_year=args.max_year, nrows=args.nrows)
	if args.rows is not None:
		df = df.head(args.rows)

	# Vista previa
	with pd.option_context("display.max_columns", None, "display.width", 120):
		print(df.head(10))
		print("\nFilas totales:", len(df))

	# Guardar si no es dry-run
	if not args.dry_run:
		out_path = _build_output_path(args.output, args.outdir)
		df.to_csv(out_path, index=False)
		print(f"\nEscrito a: {out_path}")
	else:
		print("\nDry-run: no se escribió archivo de salida.")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
