from __future__ import annotations

"""
Script: preproc_poblacion.py

Referencia: ver 'Diccionario de variables' para definiciones de `ano`, `sexo`, `edad`, `poblacion` y más.
docs/index.md#diccionario-de-variables
"""

import argparse
import os
import re
import unicodedata
from typing import Optional, Sequence

import pandas as pd


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
DEFAULT_OUTPUT = os.path.join(DEFAULT_OUTDIR, "poblacion_colombia_larga.csv")


def _normalize_name(s: str) -> str:
    """Normaliza nombres de columnas: minúsculas, sin acentos, con guiones bajos.
    No se aplica a valores del DataFrame (solo a nombres de columnas).
    """
    s = str(s).strip().lower()
    # eliminar acentos/diacríticos
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    # reemplazar separadores comunes por guion bajo
    s = re.sub(r"[\s\-]+", "_", s)
    # dejar solo alfanum y guion bajo
    s = re.sub(r"[^a-z0-9_]", "", s)
    # compactar múltiples guiones bajos
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _lowercase_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_normalize_name(c) for c in df.columns]
    return df


def _lowercase_object_values(df: pd.DataFrame, cols: Optional[Sequence[str]] = None) -> pd.DataFrame:
    df = df.copy()
    target_cols = cols if cols is not None else [c for c in df.columns if df[c].dtype == "object"]
    for c in target_cols:
        df[c] = df[c].astype(str).str.strip().str.lower()
    return df


def _detect_value_columns(df: pd.DataFrame) -> Sequence[str]:
    """
    Detect columns with population by the rule: columns to the right of 'area_geografica'.
    Additionally, filter them by a regex like '^(hombre|mujer)[_]\\d+$' to avoid
    accidentally melting non-population columns.
    """
    cols = list(df.columns)
    pat = re.compile(r"^(hombre|hombres|mujer|mujeres)_[0-9]{1,3}$")

    if "area_geografica" in cols:
        idx = cols.index("area_geografica")
        candidate_cols = cols[idx + 1 :]
        value_cols = [c for c in candidate_cols if pat.match(str(c))]
        if value_cols:
            return value_cols
        raise KeyError("No se detectaron columnas con patrón 'genero_edad' a la derecha de 'area_geografica'.")

    # Si no existe 'area_geografica', detectar por regex en todas las columnas
    value_cols = [c for c in cols if pat.match(str(c))]
    if value_cols:
        return value_cols

    raise KeyError("No se pudieron detectar columnas de valores 'genero_edad'.")


def _id_columns(df: pd.DataFrame) -> Sequence[str]:
    cols = list(df.columns)
    if "area_geografica" not in cols:
        return cols
    idx = cols.index("area_geografica")
    return cols[: idx + 1]


def _read_population_csv(path: str, nrows: Optional[int] = None) -> pd.DataFrame:
    """Lee CSV detectando separador y probando codificaciones comunes."""
    try:
        # IMPORTANTE: leemos todo como texto (dtype=str) para NO perder ceros finales
        # cuando pandas interpreta '380.350' como 380.35 (float) y luego se trunca a 38035.
        # Más adelante normalizamos quitando separadores de miles con _clean_poblacion_numeric.
        return pd.read_csv(
            path,
            nrows=nrows,
            sep=';',
            engine='python',
            dtype=str,
        )
    except UnicodeDecodeError:
        return pd.read_csv(
            path,
            nrows=nrows,
            sep=';',
            engine='python',
            encoding='latin1',
            dtype=str,
        )


def _melt_genero_edad(df: pd.DataFrame) -> pd.DataFrame:
    value_cols = _detect_value_columns(df)
    id_cols = [c for c in df.columns if c not in value_cols]
    largo = df.melt(id_vars=id_cols, value_vars=value_cols, var_name="grupo", value_name="poblacion")
    return largo


def _split_grupo_en_sexo_y_edad(largo: pd.DataFrame) -> pd.DataFrame:
    """Extrae 'sexo' y 'edad' desde 'grupo' con regex y descarta filas inválidas."""
    largo = largo.copy()
    sexo = largo["grupo"].astype(str).str.extract(r"^(hombres?|mujeres?|total|ambos)", expand=False)
    edad = largo["grupo"].astype(str).str.extract(r"_([0-9]{1,3})$", expand=False)
    largo["sexo"] = sexo.str.strip().str.lower()
    largo["sexo"] = largo["sexo"].replace({
        "hombres": "hombre",
        "mujeres": "mujer",
        "ambos": "total",
    })
    # dejar solo hombre/mujer
    largo = largo[largo["sexo"].isin(["hombre", "mujer"])].copy()
    largo["edad"] = pd.to_numeric(edad, errors="coerce").astype("Int64")
    largo = largo[largo["sexo"].notna() & largo["edad"].notna()]
    return largo.drop(columns=["grupo"])


def _clean_poblacion_numeric(df: pd.DataFrame, col: str = "poblacion") -> pd.DataFrame:
    """Convierte poblacion a número entero removiendo separadores de miles (., , espacios)."""
    out = df.copy()
    # eliminar todo lo que no sea dígito
    cleaned = out[col].astype(str).str.replace(r"[^0-9]", "", regex=True)
    nums = pd.to_numeric(cleaned, errors="coerce")
    out[col] = nums.astype("Int64")
    return out


def _filter_area_total(df: pd.DataFrame) -> pd.DataFrame:
    if "area_geografica" not in df.columns:
        return df
    return df[df["area_geografica"].astype(str).str.strip().str.lower() == "total"].copy()


def _filter_dpnom_nacional(df: pd.DataFrame) -> pd.DataFrame:
    if "dpnom" not in df.columns:
        return df
    mask = df["dpnom"].astype(str).str.strip().str.lower() == "nacional"
    return df[mask].copy()


def _filter_year_range(df: pd.DataFrame, col: str = "ano", min_year: int = 1979, max_year: int = 2023) -> pd.DataFrame:
    if col not in df.columns:
        return df
    df = df.copy()
    anos = pd.to_numeric(df[col], errors="coerce")
    df[col] = anos.astype("Int64")
    mask = (df[col] >= min_year) & (df[col] <= max_year)
    return df[mask].copy()


def _drop_columns(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    existing = [c for c in cols if c in df.columns]
    return df.drop(columns=existing) if existing else df


def _build_output_path(output_csv: Optional[str], outdir: Optional[str]) -> Optional[str]:
    if output_csv:
        return output_csv
    if outdir is None:
        outdir = DEFAULT_OUTDIR
    os.makedirs(outdir, exist_ok=True)
    return os.path.join(outdir, os.path.basename(DEFAULT_OUTPUT))


def transformar_poblacion(
    input_csv: str = DEFAULT_INPUT,
    output_csv: Optional[str] = DEFAULT_OUTPUT,
    nrows: Optional[int] = None,
    outdir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Lee el CSV de población (DANE), convierte columnas genero_edad a formato largo con
    columnas 'sexo' y 'edad', y deja todo en minúsculas. Si se pasa output_csv, lo escribe.

    Params:
    - input_csv: ruta al archivo de entrada.
    - output_csv: ruta al CSV de salida (si None, no escribe a disco).
    - nrows: si se provee, limitar filas leídas (útil para dry-run).

    Return: DataFrame transformado en formato largo.
    """

    if not os.path.exists(input_csv):
        # Nota: el usuario mencionó 'poblacion_colombiana_dane.csv', pero el repo tiene
        # 'poblacion_colombia_dane.csv'. Probamos un alias común por si acaso.
        alt = input_csv.replace("poblacion_colombia_dane.csv", "poblacion_colombiana_dane.csv")
        if os.path.exists(alt):
            input_csv = alt
        else:
            raise FileNotFoundError(f"No se encontró el archivo: {input_csv}")

    # Leer CSV con detección de separador y manejo de codificación
    df = _read_population_csv(input_csv, nrows=nrows)
    df = _lowercase_columns(df)
    df = _lowercase_object_values(df)

    # Filtros de alto nivel
    df = _filter_dpnom_nacional(df)
    df = _filter_area_total(df)
    # Tras filtrar, eliminar columna de area
    df = _drop_columns(df, ["area_geografica"])
    # Filtrar por rango de años
    df = _filter_year_range(df, col="ano", min_year=1979, max_year=2023)
    # Eliminar columnas dp, dpnom
    df = _drop_columns(df, ["dp", "dpnom"])

    # Calcular columnas id como las que están hasta 'area_geografica'
    # Con columnas removidas arriba, las id serán las no-valor (usualmente 'ano')
    value_cols = _detect_value_columns(df)
    id_cols = [c for c in df.columns if c not in value_cols]

    # Derretir a formato largo y separar sexo/edad
    largo = df.melt(id_vars=id_cols, value_vars=value_cols, var_name="grupo", value_name="poblacion")
    largo = _split_grupo_en_sexo_y_edad(largo)

    # Asegurar minúsculas en valores alfabéticos
    largo = _lowercase_object_values(largo)

    # Limpiar y convertir poblacion a numérico entero
    largo = _clean_poblacion_numeric(largo, col="poblacion")

    # Reordenar columnas finales: ano, sexo, edad, poblacion
    # Asegurar que 'ano' exista o derivarlo si necesario
    final_cols = [c for c in ["ano", "sexo", "edad", "poblacion"] if c in largo.columns]
    largo = largo[final_cols]

    # Escribir si se solicita
    out_path: Optional[str] = None
    if output_csv is not None or outdir is not None:
        out_path = _build_output_path(output_csv, outdir)
        if out_path:
            largo.to_csv(out_path, index=False)

    return largo


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convierte población DANE ancha (genero_edad en columnas) a formato largo con 'sexo' y 'edad'."
        )
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Ruta del CSV de entrada (por defecto: data/raw/poblacion/poblacion_colombia_dane.csv)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta completa del CSV de salida. Si no se especifica, se usa --outdir + nombre por defecto.",
    )
    parser.add_argument(
        "--outdir",
        default=DEFAULT_OUTDIR,
        help="Carpeta donde guardar el archivo de salida (por defecto: ./data/processed/poblacion)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Procesa solo unas pocas filas para validación rápida sin escribir todo.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Limitar número de filas leídas (sobrescribe --dry-run).",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    nrows = 50 if args.dry_run and args.rows is None else args.rows
    out = None if args.dry_run else args.output

    df_largo = transformar_poblacion(
        input_csv=args.input,
        output_csv=out,
        nrows=nrows,
        outdir=None if args.dry_run else args.outdir,
    )

    # Mostrar una vista previa pequeña
    with pd.option_context("display.max_columns", None, "display.width", 120):
        print(df_largo.head(10))
        print("\nFilas totales:", len(df_largo))
        if not args.dry_run:
            # Resolver ruta efectiva de salida para informar correctamente
            final_path = _build_output_path(out, args.outdir)
            if final_path:
                print(f"\nEscrito a: {final_path}")
        else:
            print("\nDry-run: no se escribió archivo de salida.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
