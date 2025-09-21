#!/usr/bin/env python3
"""
Modelo Lee–Carter para mortalidad edad-específica

Fuente de datos: data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv
Filtra sexo=1 por defecto. Ajuste por SVD y pronóstico opcional de k_t (ARIMA RW con deriva).

Salidas (por defecto en modelos/outputs/lee_carter):
- components.csv: ax y bx por grupo etario (gr_et)
- kt.csv: serie temporal de k_t por año (t)
- fitted_rates.csv: matriz de mx ajustadas (filas gr_et, columnas año)
- forecast_rates.csv (opcional): matriz de mx pronosticadas para horizontes futuros
- Gráficos PNG: ax_bx.png, kt.png, heatmaps de observado/ajustado y pronóstico

Uso rápido:
  python modelos/lee-carter.py --sexo 1 --horizon 10
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from numpy.linalg import svd

try:
	from statsmodels.tsa.arima.model import ARIMA
except Exception:  # statsmodels opcional para pronóstico
	ARIMA = None  # type: ignore


# -------------------------------
# Utilidades del modelo
# -------------------------------

@dataclass
class LeeCarterResult:
	ages: np.ndarray  # gr_et ordenados
	years: np.ndarray  # años ordenados
	ax: np.ndarray  # por edad
	bx: np.ndarray  # por edad (normalizado a sum(bx)=1)
	kt: np.ndarray  # por año (centrado a sum(kt)=0)
	lnmx: np.ndarray  # log mx observado (edad x año)
	lnmx_fit: np.ndarray  # log mx ajustado (edad x año)


def haldane_adjusted_mx(D: np.ndarray, E: np.ndarray) -> np.ndarray:
	"""Calcula m_{x,t} con ajuste de Haldane para evitar ceros: (D + 0.5)/E.
	Reemplaza E<=0 por NaN para evitar divisiones inválidas.
	"""
	E = np.where(E <= 0, np.nan, E)
	return (D + 0.5) / E


def fit_lee_carter(lnmx: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
	"""Ajusta Lee–Carter via SVD sobre la matriz ln(mx) de tamaño (X edades x T años).

	Retorna: ax, bx, kt, lnmx_fit
	- ax: promedio temporal del lnmx por edad
	- bx: primer vector singular izquierdo, reescalado a sum(bx)=1
	- kt: primer componente temporal, reescalado y centrado s.t. sum(kt)=0
	- lnmx_fit: ax[:,None] + bx[:,None] * kt[None,:]
	"""
	# ax: media temporal por edad
	ax = np.nanmean(lnmx, axis=1)
	R = lnmx - ax[:, None]
	# Rellenar posibles NaNs residuales con 0 (si filtramos bien no deberían quedar)
	R = np.where(np.isnan(R), 0.0, R)

	U, s, Vt = svd(R, full_matrices=False)
	u1 = U[:, 0]
	v1 = Vt[0, :]
	s1 = s[0]

	bx_raw = u1
	kt_raw = s1 * v1

	# Normalización identifiabilidad: sum_x b_x = 1
	bx_sum = np.sum(bx_raw)
	if np.isclose(bx_sum, 0.0):
		# Evitar división por cero: normalizar por norma L1
		bx_sum = np.sum(np.abs(bx_raw)) + 1e-12
	bx = bx_raw / bx_sum
	kt = kt_raw * bx_sum

	# Segundo constraint: sum_t k_t = 0
	kt_mean = np.mean(kt)
	kt = kt - kt_mean
	ax = ax + bx * kt_mean  # ajustar ax para mantener la igualdad

	lnmx_fit = ax[:, None] + bx[:, None] * kt[None, :]
	return ax, bx, kt, lnmx_fit


def forecast_kt(years: np.ndarray, kt: np.ndarray, horizon: int) -> Tuple[np.ndarray, np.ndarray]:
	"""Pronostica k_t por un horizonte dado. Intenta ARIMA(0,1,0)+drift.
	Si no está disponible statsmodels o hay fallo, cae a tendencia lineal.
	Devuelve (years_f, kt_f).
	"""
	if horizon <= 0:
		return years.copy(), kt.copy()

	last_year = int(years.max())
	future_years = np.arange(last_year + 1, last_year + 1 + horizon)

	# ARIMA Random Walk with Drift
	if ARIMA is not None:
		try:
			model = ARIMA(kt, order=(0, 1, 0), trend="t")
			res = model.fit()
			f = res.get_forecast(steps=horizon)
			kt_future = f.predicted_mean
			years_f = np.concatenate([years, future_years])
			kt_f = np.concatenate([kt, kt_future])
			return years_f, kt_f
		except Exception:
			pass

	# Fallback: tendencia lineal simple
	t = years.astype(float)
	coef = np.polyfit(t, kt, 1)
	kt_future = np.polyval(coef, future_years)
	years_f = np.concatenate([years, future_years])
	kt_f = np.concatenate([kt, kt_future])
	return years_f, kt_f


def ensure_dir(path: str) -> None:
	os.makedirs(path, exist_ok=True)


def main():
	parser = argparse.ArgumentParser(description="Ajusta un modelo Lee–Carter sobre mortalidad edad-específica.")
	parser.add_argument(
		"--csv",
		default="data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv",
		help="Ruta al CSV de entrada",
	)
	parser.add_argument("--sexo", type=int, default=1, help="Sexo a filtrar (1 por defecto)")
	parser.add_argument("--horizon", type=int, default=10, help="Horizonte de pronóstico en años")
	parser.add_argument(
		"--output-dir",
		default="modelos/outputs/lee_carter",
		help="Directorio donde guardar salidas",
	)
	parser.add_argument("--no-plots", action="store_true", help="No generar gráficos")
	args = parser.parse_args()

	outdir = os.path.abspath(args.output_dir)
	ensure_dir(outdir)

	# 1) Cargar y filtrar
	df = pd.read_csv(args.csv)
	needed_cols = {"ano", "sexo", "gr_et", "poblacion", "conteo_defunciones"}
	missing = needed_cols - set(df.columns)
	if missing:
		raise ValueError(f"Faltan columnas en el CSV: {sorted(missing)}")

	df = df.loc[df["sexo"] == args.sexo].copy()
	if df.empty:
		raise ValueError(f"No hay registros para sexo={args.sexo}")

	# 2) Calcular mx ajustado y ln(mx)
	df["mx"] = haldane_adjusted_mx(df["conteo_defunciones"].to_numpy(), df["poblacion"].to_numpy())
	df["lnmx"] = np.log(df["mx"])  # ln(mx)

	# 3) Pivotear a matriz edad x año
	# Asegurar orden
	df.sort_values(["gr_et", "ano"], inplace=True)
	ages = np.sort(df["gr_et"].unique())
	years = np.sort(df["ano"].unique())
	mat = df.pivot(index="gr_et", columns="ano", values="lnmx").reindex(index=ages, columns=years)

	# Filtrar filas/columnas con NaN completos
	mat = mat.dropna(axis=0, how="all").dropna(axis=1, how="all")
	# Si hay NaNs parciales, podemos eliminarlos de forma conservadora
	if mat.isna().any().any():
		# Eliminar años con NaN
		mat = mat.dropna(axis=1)
		# Eliminar edades con NaN
		mat = mat.dropna(axis=0)

	ages_used = mat.index.to_numpy()
	years_used = mat.columns.to_numpy()
	lnmx = mat.to_numpy(dtype=float)

	# 4) Ajustar LC
	ax, bx, kt, lnmx_fit = fit_lee_carter(lnmx)

	# 5) Guardar resultados base
	components = pd.DataFrame({"gr_et": ages_used, "ax": ax, "bx": bx})
	components.to_csv(os.path.join(outdir, "components.csv"), index=False)

	kt_df = pd.DataFrame({"ano": years_used, "kt": kt})
	kt_df.to_csv(os.path.join(outdir, "kt.csv"), index=False)

	fitted_mx = np.exp(lnmx_fit)
	fitted_df = pd.DataFrame(fitted_mx, index=ages_used, columns=years_used)
	fitted_df.index.name = "gr_et"
	fitted_df.to_csv(os.path.join(outdir, "fitted_rates.csv"))

	# 6) Pronóstico opcional
	if args.horizon and args.horizon > 0:
		years_f, kt_f = forecast_kt(years_used.astype(int), kt, args.horizon)
		# Construir lnmx futuro con mismos ax,bx
		lnmx_future = ax[:, None] + bx[:, None] * kt_f[None, :]
		mx_future = np.exp(lnmx_future)
		# Particionar histórico y futuro
		future_cols = years_f
		mx_future_df = pd.DataFrame(mx_future, index=ages_used, columns=future_cols)
		mx_future_df.index.name = "gr_et"
		mx_future_df.to_csv(os.path.join(outdir, "forecast_rates.csv"))

		# Guardar kt extendido
		kt_ext_df = pd.DataFrame({"ano": years_f, "kt": kt_f})
		kt_ext_df.to_csv(os.path.join(outdir, "kt_extended.csv"), index=False)
	else:
		years_f, kt_f = years_used, kt

	# 7) Gráficos
	if not args.no_plots:
		try:
			sns.set_context("talk")

			# ax y bx
			fig, axplt = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
			axplt[0].plot(ages_used, ax, marker="o")
			axplt[0].set_title("Componente a_x (promedio ln(mx))")
			axplt[0].set_ylabel("a_x")
			axplt[1].plot(ages_used, bx, marker="o", color="C1")
			axplt[1].set_title("Componente b_x (sensibilidad)")
			axplt[1].set_xlabel("Grupo etario (gr_et)")
			axplt[1].set_ylabel("b_x")
			fig.tight_layout()
			fig.savefig(os.path.join(outdir, "ax_bx.png"), dpi=150)
			plt.close(fig)

			# kt histórico y extendido
			fig, ax1 = plt.subplots(figsize=(9, 4))
			ax1.plot(years_used, kt, label="kt (hist)")
			if years_f is not None and len(years_f) > len(years_used):
				ax1.plot(years_f, kt_f, label="kt (extendido)", linestyle="--")
			ax1.axhline(0, color="k", lw=0.8, alpha=0.5)
			ax1.set_title("Componente k_t")
			ax1.set_xlabel("Año")
			ax1.set_ylabel("k_t")
			ax1.legend()
			fig.tight_layout()
			fig.savefig(os.path.join(outdir, "kt.png"), dpi=150)
			plt.close(fig)

			# Heatmaps observado vs ajustado
			fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
			sns.heatmap(np.exp(lnmx), ax=axes[0], cmap="mako", cbar_kws={"label": "mx"})
			axes[0].set_title("mx observado (sexo=%d)" % args.sexo)
			axes[0].set_xlabel("t (años)")
			axes[0].set_ylabel("gr_et (filas)")
			axes[0].set_xticks(np.linspace(0.5, lnmx.shape[1]-0.5, 5))
			axes[0].set_xticklabels(
				[str(y) for y in np.linspace(years_used.min(), years_used.max(), 5, dtype=int)]
			)
			sns.heatmap(np.exp(lnmx_fit), ax=axes[1], cmap="mako", cbar_kws={"label": "mx"})
			axes[1].set_title("mx ajustado (Lee–Carter)")
			axes[1].set_xlabel("t (años)")
			fig.tight_layout()
			fig.savefig(os.path.join(outdir, "heatmap_observado_vs_ajustado.png"), dpi=150)
			plt.close(fig)

			# Heatmap pronóstico (si hay futuro)
			if years_f is not None and len(years_f) > len(years_used):
				# Mostrar solo parte futura
				fut_mask = np.isin(years_f, np.setdiff1d(years_f, years_used))
				mx_future_only = np.exp(ax[:, None] + bx[:, None] * kt_f[None, :])[:, fut_mask]
				fig, ax2 = plt.subplots(figsize=(8, 6))
				sns.heatmap(mx_future_only, ax=ax2, cmap="mako", cbar_kws={"label": "mx"})
				ax2.set_title("mx pronosticado (futuro)")
				ax2.set_xlabel("t (años futuros)")
				ax2.set_ylabel("gr_et (filas)")
				fig.tight_layout()
				fig.savefig(os.path.join(outdir, "heatmap_pronostico.png"), dpi=150)
				plt.close(fig)
		except Exception as e:
			print(f"Advertencia: no se pudieron generar gráficos: {e}")

	print(f"Listo. Salidas en: {outdir}")


if __name__ == "__main__":
	main()

