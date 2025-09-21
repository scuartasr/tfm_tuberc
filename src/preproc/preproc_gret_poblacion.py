from __future__ import annotations

"""
Script: preproc_gret_poblacion.py

Referencia: ver 'Diccionario de variables' para definiciones de `ano`, `sexo`, `edad`, `gr_et`, etc.
docs/index.md#diccionario-de-variables
"""
import argparse
import os
from typing import Optional, Sequence
import pandas as pd

# Ajuste de ruta para imports cuando se ejecuta como script
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.preproc._internals.agregar_poblacion_por_gret import agregar_poblacion_por_gret

DEFAULT_INPUT = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/processed/poblacion/poblacion_colombia_larga.csv",
	)
)
DEFAULT_OUTDIR = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"../../data/processed/poblacion",
	)
)
DEFAULT_OUTPUT = os.path.join(DEFAULT_OUTDIR, "poblacion_colombia_gr_et.csv")


def _build_output_path(output_csv: Optional[str], outdir: Optional[str]) -> str:
	if output_csv:
		return output_csv
	if outdir is None:
		outdir = DEFAULT_OUTDIR
	os.makedirs(outdir, exist_ok=True)
	return os.path.join(outdir, os.path.basename(DEFAULT_OUTPUT))


def main(argv: Optional[Sequence[str]] = None) -> int:
	parser = argparse.ArgumentParser(
		description=(
			"Lee poblacion_colombia_larga.csv y agrega por grupos etarios quinquenales (gr_et)."
		)
	)
	parser.add_argument("--input", default=DEFAULT_INPUT, help="Ruta del CSV largo de población.")
	parser.add_argument("--output", default=None, help="Ruta del CSV de salida (opcional).")
	parser.add_argument(
		"--outdir",
		default=DEFAULT_OUTDIR,
		help="Carpeta de salida si no se especifica --output.",
	)
	parser.add_argument("--dry-run", action="store_true", help="No escribe archivo, solo vista previa.")
	parser.add_argument("--rows", type=int, default=None, help="Recorta filas de vista previa.")

	args = parser.parse_args(list(argv) if argv is not None else None)

	df_out = agregar_poblacion_por_gret(args.input)
	if args.rows is not None:
		df_out = df_out.head(args.rows)

	with pd.option_context("display.max_columns", None, "display.width", 120):
		print(df_out.head(20))
		print("\nFilas totales:", len(df_out))

	if not args.dry_run:
		out_path = _build_output_path(args.output, args.outdir)
		df_out.to_csv(out_path, index=False)
		print(f"\nEscrito a: {out_path}")
	else:
		print("\nDry-run: no se escribió archivo de salida.")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())

