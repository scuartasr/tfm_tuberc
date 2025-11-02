from __future__ import annotations

"""
Script: preproc_poblac_defunc.py

Nota: ver 'Diccionario de variables' en docs para significados de columnas como
`ano`, `t`, `sexo`, `gr_et`, `poblacion`, `conteo_defunciones`, `tasa`, `tasa_x100k`:
docs/index.md#diccionario-de-variables
"""

import argparse
import os
from typing import Optional, Sequence
import pandas as pd

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.preproc._internals.join_poblacion_defunciones import juntar_poblacion_defunciones_por_gr_et, calcular_tasa_por_100k
from src.preproc._internals.periodo_utils import agregar_indice_periodo
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
	parser.add_argument("--with-checks", action="store_true", help="Ejecutar validaciones de integridad tras generar los dataframes.")
	parser.add_argument("--dry-run", action="store_true", help="No escribe archivo, solo vista previa.")
	parser.add_argument("--rows", type=int, default=None, help="Recorta filas en vista previa.")
	# Flags de control para matrices de Lexis (por defecto: generar todas)
	parser.add_argument("--no-lexis-ano", action="store_true", help="No generar 'tasa_mortalidad_lexis.csv' (columnas por año).")
	parser.add_argument("--no-lexis-t", action="store_true", help="No generar 'tasa_mortalidad_lexis_t.csv' (columnas por periodo t).")
	parser.add_argument("--no-lexis-por-sexo", action="store_true", help="No generar matrices de Lexis separadas por sexo.")

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

	# Si se solicita, generar versión con ceros
	df_final = df_preview
	if args.fill_zeros:
		df_final = juntar_poblacion_defunciones_por_gr_et(args.pop, args.defunc, fill_zeros=True)

	# Calcular tasa por 100k sobre el DataFrame final (con o sin ceros)
	# Por defecto, aplica una tasa mínima (min_rate=1e-8) cuando no hay defunciones y población > 0
	df_final = calcular_tasa_por_100k(df_final, min_rate=1e-8)

	# Indexar el periodo usando utilitario interno
	df_final = agregar_indice_periodo(df_final)

	# Validaciones opcionales
	if args.with_checks:
		try:
			from src.preproc._internals.validaciones import (
				validar_poblacion,
				validar_defunciones,
				validar_cruce,
				resumen_advertencias,
			)
		except ImportError as e:
			print(f"No se pudieron importar validaciones: {e}")
		else:
			# Intentar leer población y defunciones originales para validación (si existen en disco)
			try:
				df_pop = pd.read_csv(args.pop)
				pop_warns = validar_poblacion(df_pop, critical=False)
				resumen_advertencias("Población", pop_warns)
			except Exception as e:
				print(f"No se pudo validar población: {e}")
			try:
				df_def = pd.read_csv(args.defunc)
				def_warns = validar_defunciones(df_def)
				resumen_advertencias("Defunciones", def_warns)
			except Exception as e:
				print(f"No se pudo validar defunciones: {e}")
			cruce_warns = validar_cruce(df_final)
			resumen_advertencias("Cruce", cruce_warns)

	if not args.dry_run:
		out_path = _build_output_path(args.output, args.outdir)
		df_final.to_csv(out_path, index=False)
		print(f"\nEscrito a: {out_path}")

		# Adicional: generar archivo agregado por grupo etario y periodo (sin sexo)
		try:
			cols_needed = {"ano", "t", "gr_et", "poblacion", "conteo_defunciones"}
			if cols_needed.issubset(df_final.columns):
				# Agregar por año/periodo y grupo etario, sumando población y defunciones
				df_per = (
					df_final.groupby(["ano", "t", "gr_et"], as_index=False)[["poblacion", "conteo_defunciones"]]
					.sum()
				)
				# Recalcular tasas en el agregado
				df_per = calcular_tasa_por_100k(df_per, min_rate=1e-8)

				# Orden de columnas semejante al archivo base pero sin 'sexo'
				cols_out = [
					"ano",
					"t",
					"gr_et",
					"poblacion",
					"conteo_defunciones",
					"tasa_x100k",
					"tasa",
				]
				cols_out = [c for c in cols_out if c in df_per.columns]

				outdir = args.outdir or DEFAULT_OUTDIR
				os.makedirs(outdir, exist_ok=True)
				alt_out_path = os.path.join(outdir, "tasas_mortalidad_gret_per.csv")
				df_per[cols_out].to_csv(alt_out_path, index=False)
				print(f"Escrito agregado por gr_et y periodo (sin sexo) a: {alt_out_path}")

				# Crear matrices de Lexis a partir del agregado (manejar errores de forma segura)
				try:
					# Matriz por año
					if (not args.no_lexis_ano) and all(c in df_per.columns for c in ["gr_et", "ano", "tasa_x100k"]):
						df_lexis = (
							df_per.pivot(index="gr_et", columns="ano", values="tasa_x100k")
							.sort_index()
						)
						# Ordenar columnas por año ascendente y exportar
						df_lexis = df_lexis.reindex(sorted(df_lexis.columns), axis=1)
						df_lexis.reset_index().to_csv(os.path.join(outdir, "tasa_mortalidad_lexis.csv"), index=False)
						print(f"Escrita matriz de Lexis (tasa_x100k) a: {os.path.join(outdir, 'tasa_mortalidad_lexis.csv')}")

					# Matriz por periodo t
					if (not args.no_lexis_t) and ("t" in df_per.columns):
						df_lexis_t = (
							df_per.pivot(index="gr_et", columns="t", values="tasa_x100k")
							.sort_index()
						)
						df_lexis_t = df_lexis_t.reindex(sorted(df_lexis_t.columns), axis=1)
						df_lexis_t.reset_index().to_csv(os.path.join(outdir, "tasa_mortalidad_lexis_t.csv"), index=False)
						print(f"Escrita matriz de Lexis por periodo t (tasa_x100k) a: {os.path.join(outdir, 'tasa_mortalidad_lexis_t.csv')}")

					# Matrices por sexo (columnas por año)
					if (not args.no_lexis_por_sexo) and ("sexo" in df_final.columns):
						df_per_sexo = (
							df_final.groupby(["ano", "t", "gr_et", "sexo"], as_index=False)[["poblacion", "conteo_defunciones"]]
							.sum()
						)
						df_per_sexo = calcular_tasa_por_100k(df_per_sexo, min_rate=1e-8)

						for sx in sorted([s for s in df_per_sexo["sexo"].dropna().unique().tolist()]):
							try:
								df_sx = df_per_sexo[df_per_sexo["sexo"] == sx]
								df_lexis_sx = (
									df_sx.pivot(index="gr_et", columns="ano", values="tasa_x100k")
									.sort_index()
								)
								df_lexis_sx = df_lexis_sx.reindex(sorted(df_lexis_sx.columns), axis=1)
								df_lexis_sx.reset_index().to_csv(
									os.path.join(outdir, f"tasa_mortalidad_lexis_sexo{sx}.csv"),
									index=False,
								)
								print(
									f"Escrita matriz de Lexis por sexo={sx} (tasa_x100k) a: {os.path.join(outdir, f'tasa_mortalidad_lexis_sexo{sx}.csv')}"
								)
							except Exception as e:
								print(f"No se pudo generar Lexis para sexo={sx}: {e}")
				except Exception as e:
					print(f"Error generando matrices de Lexis: {e}")
			else:
				print("No se encontraron todas las columnas necesarias para generar 'tasas_mortalidad_gret_per.csv'.")
		except Exception as e:
			print(f"Error generando 'tasas_mortalidad_gret_per.csv': {e}")
	else:
		print("\nDry-run: no se escribió archivo de salida.")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())

