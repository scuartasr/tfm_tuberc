import pandas as pd


def separar_y_convertir(largo: pd.DataFrame) -> pd.DataFrame:
    # regex robusto para extraer genero y edad
    sexo = largo["col"].astype(str).str.extract(r"^(hombres?|mujeres?)", expand=False)
    edad = largo["col"].astype(str).str.extract(r"_([0-9]{1,3})$", expand=False)
    out = largo.copy()
    out["sexo"] = sexo.str.strip().str.lower().replace({"hombres": "hombre", "mujeres": "mujer"})
    out["edad"] = pd.to_numeric(edad, errors="coerce").astype("Int64")
    out = out[out["sexo"].isin(["hombre", "mujer"]) & out["edad"].notna()].copy()
    # La limpieza numérica de 'poblacion' se hace en un paso posterior dedicado
    return out.drop(columns=["col"])