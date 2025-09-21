#!/usr/bin/env python3
from __future__ import annotations

import os
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


DATA_CSV = "data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv"
LC_FITTED = "modelos/outputs/lee_carter/fitted_rates.csv"
APC_FITTED = "modelos/outputs/apc_bayes/fitted_rates.csv"
OUTDIR = "modelos/outputs/eval"


def haldane_mx(d: np.ndarray, e: np.ndarray) -> np.ndarray:
    e = np.where(e <= 0, np.nan, e)
    return (d + 0.5) / e


def load_observed(sexo: int = 1) -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV)
    req = {"ano", "sexo", "gr_et", "poblacion", "conteo_defunciones"}
    miss = req - set(df.columns)
    if miss:
        raise ValueError(f"Faltan columnas en {DATA_CSV}: {sorted(miss)}")
    df = df.loc[df["sexo"] == sexo].copy()
    if df.empty:
        raise ValueError(f"No hay registros para sexo={sexo}")
    df.sort_values(["gr_et", "ano"], inplace=True)
    df["mx_obs"] = haldane_mx(df["conteo_defunciones"].to_numpy(), df["poblacion"].to_numpy())
    obs = df.pivot(index="gr_et", columns="ano", values="mx_obs")
    return obs


def metrics_for(fitted_path: str, obs_pivot: pd.DataFrame, name: str) -> dict:
    if not os.path.exists(fitted_path):
        raise FileNotFoundError(f"No existe {fitted_path}. Ejecuta el modelo {name} primero.")
    fitted = pd.read_csv(fitted_path, index_col=0)
    # Alinear índices y columnas al cruce común
    ages = sorted(set(obs_pivot.index).intersection(set(fitted.index)))
    years = sorted(set(obs_pivot.columns.astype(int)).intersection(set(map(int, fitted.columns))))
    if not ages or not years:
        raise ValueError(f"No hay cruce común edad-año entre observado y {name}")
    obs_al = obs_pivot.loc[ages, years]
    fit_al = fitted.loc[ages, list(map(str, years))]

    # Vectorizar y filtrar NaNs
    y_true = obs_al.to_numpy().ravel()
    y_pred = fit_al.to_numpy().ravel()
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    # MAPE seguro (valores > 0 por Haldane)
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100.0)
    mpe = float(np.mean(((y_pred - y_true) / y_true)) * 100.0)
    r2 = r2_score(y_true, y_pred)
    bias = float(np.mean(y_pred - y_true))
    return {
        "modelo": name,
        "n": int(y_true.size),
        "MAE": mae,
        "RMSE": rmse,
        "%MAPE": mape,
        "%MPE": mpe,
        "R2": r2,
        "Bias": bias,
    }


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    obs = load_observed(sexo=1)
    m_lc = metrics_for(LC_FITTED, obs, name="Lee-Carter")
    m_apc = metrics_for(APC_FITTED, obs, name="APC-Bayes")
    res = pd.DataFrame([m_lc, m_apc])
    out_csv = os.path.join(OUTDIR, "metrics_overall.csv")
    res.to_csv(out_csv, index=False)
    # Mostrar resumen limpio
    print("Métricas globales (sexo=1), comparando mx ajustada vs observada (Haldane):")
    print(res.to_string(index=False, float_format=lambda x: f"{x:0.6f}"))
    print(f"Guardado en: {out_csv}")


if __name__ == "__main__":
    main()
