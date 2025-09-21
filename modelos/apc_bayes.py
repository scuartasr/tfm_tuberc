#!/usr/bin/env python3
"""
Modelo APC (Edad-Periodo-Cohorte) con enfoque bayesiano usando PyMC.

Especificación:
  D_{a,t} ~ Poisson(E_{a,t} * exp(mu + alpha_a + beta_t + gamma_c))
  Priors RW1 (random walk de primer orden) sobre alpha (edad), beta (periodo) y gamma (cohorte)
  con centrado a media cero para identifiabilidad. Cohortes indexadas como c = t_idx - a_idx + (A-1).

Entrada: data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv
  Columnas requeridas: ano, sexo, gr_et, poblacion, conteo_defunciones

Salidas (por defecto en modelos/outputs/apc_bayes):
  - alpha.csv (por gr_et), beta.csv (por ano), gamma.csv (por índice de cohorte)
  - components_summary.csv (mu y sigmas)
  - fitted_rates.csv (estimación puntual de mx por gr_et x ano)
  - idata.nc (traza en formato ArviZ NetCDF)
  - Gráficos opcionales (alpha_beta_gamma.png)

Uso rápido:
  python modelos/apc_bayes.py --sexo 1 --draws 800 --tune 800 --chains 2
"""

from __future__ import annotations

import argparse
import os
from typing import Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # backend no interactivo
import matplotlib.pyplot as plt
import seaborn as sns


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def build_apc_data(df: pd.DataFrame, sexo: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Construye matrices y vectores necesarios para APC.

    Returns:
      ages (A,), years (T,), D (A,T), E (A,T), ai (N,), ti (N,), ci (N,)
    Donde N es el número de celdas observadas con E>0.
    """
    req = {"ano", "sexo", "gr_et", "poblacion", "conteo_defunciones"}
    miss = req - set(df.columns)
    if miss:
        raise ValueError(f"Faltan columnas: {sorted(miss)}")

    d = df.loc[df["sexo"] == sexo].copy()
    if d.empty:
        raise ValueError(f"No hay datos para sexo={sexo}")

    d.sort_values(["gr_et", "ano"], inplace=True)
    ages = np.sort(d["gr_et"].unique())
    years = np.sort(d["ano"].unique())

    D = d.pivot(index="gr_et", columns="ano", values="conteo_defunciones").reindex(index=ages, columns=years).to_numpy(float)
    E = d.pivot(index="gr_et", columns="ano", values="poblacion").reindex(index=ages, columns=years).to_numpy(float)

    A, T = D.shape
    mask = (~np.isnan(D)) & (~np.isnan(E)) & (E > 0)
    ai, ti = np.where(mask)
    N = ai.size
    if N == 0:
        raise ValueError("No hay celdas observadas con E>0")

    # Cohortes: 0..C-1 con C = A+T-1
    C = A + T - 1
    ci = (ti - ai) + (A - 1)
    assert ci.min() >= 0 and ci.max() < C

    return ages, years, D, E, ai, ti, ci


def main():
    parser = argparse.ArgumentParser(description="Modelo APC bayesiano (Poisson log-link, priors RW1)")
    parser.add_argument("--csv", default="data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv")
    parser.add_argument("--sexo", type=int, default=1)
    parser.add_argument("--output-dir", default="modelos/outputs/apc_bayes")
    parser.add_argument("--draws", type=int, default=1000)
    parser.add_argument("--tune", type=int, default=1000)
    parser.add_argument("--chains", type=int, default=2)
    parser.add_argument("--target-accept", type=float, default=0.9)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    ensure_dir(args.output_dir)
    df = pd.read_csv(args.csv)
    ages, years, D, E, ai, ti, ci = build_apc_data(df, args.sexo)

    # Observaciones
    y_obs = D[ai, ti].astype(int)
    expo = E[ai, ti]
    A, T = D.shape
    C = A + T - 1

    # Modelado con PyMC
    try:
        import pymc as pm
        import pytensor.tensor as pt
        import arviz as az
    except Exception as e:
        raise SystemExit(
            "Se requiere PyMC y ArviZ. Instala con: pip install pymc arviz\n"
            f"Error original: {e}"
        )

    with pm.Model() as model:
        mu = pm.Normal("mu", 0.0, 5.0)

        sigma_a = pm.HalfNormal("sigma_alpha", 1.0)
        sigma_t = pm.HalfNormal("sigma_beta", 1.0)
        sigma_c = pm.HalfNormal("sigma_gamma", 1.0)

        # RW1 para alpha (edad)
        eps_a = pm.Normal("delta_alpha", 0.0, 1.0, shape=A-1)
        alpha_ = pt.concatenate([pt.zeros(1), pt.cumsum(eps_a)]) * sigma_a
        alpha = pm.Deterministic("alpha", alpha_ - pt.mean(alpha_))

        # RW1 para beta (periodo)
        eps_t = pm.Normal("delta_beta", 0.0, 1.0, shape=T-1)
        beta_ = pt.concatenate([pt.zeros(1), pt.cumsum(eps_t)]) * sigma_t
        beta = pm.Deterministic("beta", beta_ - pt.mean(beta_))

        # RW1 para gamma (cohorte)
        eps_c = pm.Normal("delta_gamma", 0.0, 1.0, shape=C-1)
        gamma_ = pt.concatenate([pt.zeros(1), pt.cumsum(eps_c)]) * sigma_c
        gamma = pm.Deterministic("gamma", gamma_ - pt.mean(gamma_))

        # Índices observados
        a_idx = pm.MutableData("a_idx", ai)
        t_idx = pm.MutableData("t_idx", ti)
        c_idx = pm.MutableData("c_idx", ci)
        E_obs = pm.MutableData("E_obs", expo)
        y = pm.MutableData("y", y_obs)

        eta = mu + alpha[a_idx] + beta[t_idx] + gamma[c_idx]
        lam = E_obs * pt.exp(eta)
        pm.Poisson("obs", mu=lam, observed=y)

        idata = pm.sample(
            draws=args.draws,
            tune=args.tune,
            chains=args.chains,
            target_accept=args.target_accept,
            init="jitter+adapt_diag",
            cores=min(args.chains, 2),
            random_seed=123,
            progressbar=True,
        )

    # Guardar trazas
    az.to_netcdf(idata, os.path.join(args.output_dir, "idata.nc"))

    # Resúmenes y componentes (medias posteriores)
    post = idata.posterior
    def mean_param(name):
        arr = post[name].mean(dim=["chain", "draw"]).to_numpy()
        return np.asarray(arr)

    mu_mean = float(post["mu"].mean().to_numpy())
    alpha_mean = mean_param("alpha")  # (A,)
    beta_mean = mean_param("beta")    # (T,)
    gamma_mean = mean_param("gamma")  # (C,)

    # Exportar componentes
    pd.DataFrame({"gr_et": ages, "alpha": alpha_mean}).to_csv(
        os.path.join(args.output_dir, "alpha.csv"), index=False
    )
    pd.DataFrame({"ano": years, "beta": beta_mean}).to_csv(
        os.path.join(args.output_dir, "beta.csv"), index=False
    )
    pd.DataFrame({"cohort_index": np.arange(C), "gamma": gamma_mean}).to_csv(
        os.path.join(args.output_dir, "gamma.csv"), index=False
    )
    pd.DataFrame(
        {
            "param": ["mu", "sigma_alpha", "sigma_beta", "sigma_gamma"],
            "mean": [
                mu_mean,
                float(post["sigma_alpha"].mean().to_numpy()),
                float(post["sigma_beta"].mean().to_numpy()),
                float(post["sigma_gamma"].mean().to_numpy()),
            ],
        }
    ).to_csv(os.path.join(args.output_dir, "components_summary.csv"), index=False)

    # Fitted rates (plug-in con medias posteriores)
    # Construir matriz de índices de cohorte (A,T)
    A, T = len(ages), len(years)
    cohort_mat = np.add.outer(np.arange(T), -np.arange(A)) + (A - 1)  # shape (A,T) en orden [a,t] -> transponer
    cohort_mat = cohort_mat.T  # ahora (A,T) con convención [a,t]

    lnmx_hat = (
        mu_mean
        + alpha_mean[:, None]
        + beta_mean[None, :]
        + gamma_mean[cohort_mat]
    )
    mx_hat = np.exp(lnmx_hat)
    fitted_df = pd.DataFrame(mx_hat, index=ages, columns=years)
    fitted_df.index.name = "gr_et"
    fitted_df.to_csv(os.path.join(args.output_dir, "fitted_rates.csv"))

    # Gráficos opcionales
    if not args.no_plots:
        try:
            sns.set_context("talk")
            fig, ax = plt.subplots(3, 1, figsize=(9, 10))
            ax[0].plot(ages, alpha_mean, marker="o")
            ax[0].set_title("Efecto por edad (alpha)")
            ax[0].set_xlabel("gr_et")
            ax[0].set_ylabel("alpha")
            ax[1].plot(years, beta_mean, marker="o")
            ax[1].set_title("Efecto por periodo (beta)")
            ax[1].set_xlabel("año")
            ax[1].set_ylabel("beta")
            ax[2].plot(np.arange(C), gamma_mean, marker="o")
            ax[2].set_title("Efecto por cohorte (gamma, índice)")
            ax[2].set_xlabel("índice de cohorte")
            ax[2].set_ylabel("gamma")
            fig.tight_layout()
            fig.savefig(os.path.join(args.output_dir, "alpha_beta_gamma.png"), dpi=150)
            plt.close(fig)
        except Exception as e:
            print(f"Advertencia: no se pudieron generar gráficos: {e}")

    print(f"Listo. Salidas en: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
