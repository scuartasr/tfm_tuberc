# Comparación de modelos estocásticos y de aprendizaje de máquina para el pronóstico de la mortalidad edad-específica por tuberculosis en Colombia

## Descripción general

Este repositorio almacena los códigos y los datos que dieron lugar al preprocesamiento, análisis descriptivo, ajuste de modelos y análisis posteriores que se realizaron como parte de la relación del Trabajo Final de Maestría desarrollado por **Simón Cuartas Rendón** para obtener el título de Magíster en Ingeniería - Analítica (nodo de profundización) en la Facultad de Minas de la Universidad Nacional de Colombia. Este trabajo se realizó bajo la dirección del profesor Juan David Ospina Ospina Arango, PhD.

## Créditos

Es importante dar créditos o agradecimientos a:

- El profesor Juan David, (...)
- El DANE, fuente de la información de mortalidad en Colombia que dio pie al ajuste de estos modelos.


## Preprocesamiento de datos: guía completa

Esta sección documenta el pipeline de preprocesamiento usado para construir las tablas de población, defunciones y su cruce, que sirven como insumo a los modelos.

### Flujo general

```
raw/poblacion (DANE CSV) ──▶ preproc_poblacion.py ──▶ data/processed/poblacion/poblacion_colombia_larga.csv
																					 │
																					 └─▶ preproc_gret_poblacion.py ──▶ data/processed/poblacion/poblacion_colombia_gr_et.csv

raw/defunc (Defun*.txt/csv) ──▶ preproc_tuberc.py ──▶ data/processed/defunc/defunciones_agrupadas.csv
																														└──────────────────────────────────────────▶ data/processed/defunc/defunciones_por_gr_et.csv

								 población (gr_et) + defunciones (gr_et) ──▶ preproc_poblac_defunc.py ──▶ data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv
```

Puedes orquestar todo con `src/preproc/run_all_preproc.py` o ejecutar cada paso por separado.

### Requisitos previos

- Python 3.10+ y entorno virtual activo.
- Dependencias instaladas (ver `requirements.txt`).
- Archivos de entrada:
	- `data/raw/poblacion/poblacion_colombia_dane.csv`
	- `data/raw/defunc/Defun*.txt|csv` (1979–2023 disponibles en el repo)

Activa el entorno en macOS/Linux:

```bash
source .venv/bin/activate
```

### Scripts y parámetros

1) `src/preproc/preproc_poblacion.py`

- Función: transforma el CSV del DANE (ancho) a formato largo con columnas `ano`, `sexo`, `edad`, `poblacion`.
- Flags principales:
	- `--input`: ruta de entrada (por defecto `data/raw/poblacion/poblacion_colombia_dane.csv`).
	- `--output`: ruta de salida (opcional). Si no se pasa, se usa `--outdir`.
	- `--outdir`: carpeta de salida (por defecto `data/processed/poblacion`).
	- `--dry-run`: procesa muestra pequeña y no escribe archivo.
	- `--rows N`: limita filas leídas (prioriza sobre `--dry-run`).
- Salida por defecto: `data/processed/poblacion/poblacion_colombia_larga.csv` con `sexo ∈ {"hombre","mujer"}`.

2) `src/preproc/preproc_gret_poblacion.py`

- Función: agrega la población larga a grupos etarios quinquenales (`gr_et`) y mapea `sexo` a código `{1: hombre, 2: mujer}`.
- Flags:
	- `--input`: CSV largo de población (por defecto el generado en el paso 1).
	- `--output` / `--outdir`.
	- `--dry-run`, `--rows`.
- Salida por defecto: `data/processed/poblacion/poblacion_colombia_gr_et.csv` con columnas `ano`, `sexo` (1/2), `gr_et`, `poblacion`.

3) `src/preproc/preproc_tuberc.py`

- Función: procesa masivamente `data/raw/defunc/Defun*.{txt,csv}`, concatena resultados y guarda:
	- `data/processed/defunc/defunciones_agrupadas.csv`
	- `data/processed/defunc/defunciones_por_gr_et.csv` (agregado por `ano, sexo, gr_et`)
- Variables de entorno (no usa flags CLI):
	- `DEBUG_MAX_FILES=N`: limita cantidad de archivos a procesar (útil para depurar).
	- `VERBOSE_LEVEL={0,1,2}`: controla verbosidad (0 mínimo; 2 incluye resúmenes).
	- `SHOW_SUMMARY=1|0`: si `VERBOSE_LEVEL` no está definido, habilita resumen final.

4) `src/preproc/preproc_poblac_defunc.py`

- Función: hace left-join entre población y defunciones por `['ano','sexo','gr_et']`, calcula tasas y un índice temporal `t`.
- Flags:
	- `--pop`: CSV de población por gr_et (por defecto del paso 2).
	- `--defunc`: CSV de defunciones por gr_et (por defecto del paso 3).
	- `--fill-zeros`: rellena `NaN` de `conteo_defunciones` con `0` antes de calcular tasas.
	- `--output` / `--outdir`, `--dry-run`, `--rows`.
	- Flags de opt-out para matrices Lexis (por defecto se generan todas):
		- `--no-lexis-ano` (omite `tasa_mortalidad_lexis.csv`)
		- `--no-lexis-t` (omite `tasa_mortalidad_lexis_t.csv`)
		- `--no-lexis-por-sexo` (omite `tasa_mortalidad_lexis_sexo1.csv` y `..._sexo2.csv`)
- Salidas por defecto:
	- `data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv`
	- `data/processed/mortalidad/tasas_mortalidad_gret_per.csv` (agregado por `ano`, `t`, `gr_et`, sin `sexo`), con columnas: `ano, t, gr_et, poblacion, conteo_defunciones, tasa_x100k, tasa`.
	- Matrices de Lexis (tasa por 100k, filas=`gr_et`):
		- `data/processed/mortalidad/tasa_mortalidad_lexis.csv` (columnas=`ano`)
		- `data/processed/mortalidad/tasa_mortalidad_lexis_t.csv` (columnas=`t`)
		- `data/processed/mortalidad/tasa_mortalidad_lexis_sexo1.csv` y `..._sexo2.csv`

5) Orquestador `src/preproc/run_all_preproc.py`

- Ejecuta secuencialmente los cuatro pasos anteriores.
- Flags:
	- `--dry-run`: propaga a scripts que lo soportan (no escribe salidas intermedias).
	- `--rows N`: limita filas donde aplica.
	- `--fill-zeros`: pasa a `preproc_poblac_defunc.py`.
	- `--tuberc-max-files N`: exporta `DEBUG_MAX_FILES` para `preproc_tuberc.py`.
	- `--tuberc-verbose {0,1,2}`: exporta `VERBOSE_LEVEL` para `preproc_tuberc.py`.

### Entradas y salidas esperadas

- Entradas:
	- `data/raw/poblacion/poblacion_colombia_dane.csv`
	- `data/raw/defunc/Defun1979.txt ... Defun2023.csv`
- Salidas clave del pipeline:
	- `data/processed/poblacion/poblacion_colombia_larga.csv`
	- `data/processed/poblacion/poblacion_colombia_gr_et.csv`
	- `data/processed/defunc/defunciones_agrupadas.csv`
	- `data/processed/defunc/defunciones_por_gr_et.csv`
	- `data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv`
	- `data/processed/mortalidad/tasas_mortalidad_gret_per.csv`
	- `data/processed/mortalidad/tasa_mortalidad_lexis.csv`
	- `data/processed/mortalidad/tasa_mortalidad_lexis_t.csv`
	- `data/processed/mortalidad/tasa_mortalidad_lexis_sexo1.csv` y `..._sexo2.csv`

### Ejemplos de ejecución (zsh)

- Orquestador completo (con resumen y tasas):

```bash
source .venv/bin/activate
python src/preproc/run_all_preproc.py --fill-zeros --tuberc-verbose 2
```

- Desactivar selectivamente matrices Lexis (opt-out):

```bash
# Omitir matriz por año (columnas=ano)
python src/preproc/run_all_preproc.py --no-lexis-ano

# Omitir matriz por t (columnas=t)
python src/preproc/run_all_preproc.py --no-lexis-t

# Omitir matrices por sexo
python src/preproc/run_all_preproc.py --no-lexis-por-sexo
```

- Orquestador en modo rápido (muestra pequeña y pocas fuentes de defunciones):

```bash
source .venv/bin/activate
DEBUG_MAX_FILES=3 python src/preproc/run_all_preproc.py --dry-run --rows 100 --tuberc-verbose 1
```

- Paso a paso:

```bash
source .venv/bin/activate
# 1) Población a largo
python src/preproc/preproc_poblacion.py --outdir data/processed/poblacion

# 2) Población por gr_et
python src/preproc/preproc_gret_poblacion.py --outdir data/processed/poblacion

# 3) Defunciones (con barra de progreso)
VERBOSE_LEVEL=2 DEBUG_MAX_FILES=5 python src/preproc/preproc_tuberc.py

# 4) Join + tasas
python src/preproc/preproc_poblac_defunc.py --fill-zeros --outdir data/processed/mortalidad
```

### Notas y solución de problemas

- Rutas: los scripts usan rutas relativas al repo; ejecuta los comandos desde la raíz del proyecto.
- Codificación/CSV: el lector detecta separadores y prueba codificaciones comunes; si ves `UnicodeDecodeError`, revisa el archivo fuente.
- Columnas requeridas:
	- Población larga requiere `ano, sexo, edad, poblacion`.
	- Join requiere `ano, sexo, gr_et` en ambos CSV, más `poblacion` y `conteo_defunciones`.
- Tasas: si `poblacion <= 0` o es `NaN`, la tasa queda `NaN` por diseño para evitar divisiones por cero.
- Índice temporal `t`: es un índice entero consecutivo por año presente (no asume continuidad completa de años).
- Verbosidad: ajusta `VERBOSE_LEVEL` en `preproc_tuberc.py` (`0` mínimo, `2` con resúmenes) y opcionalmente `SHOW_SUMMARY=1`.

### Utilidades internas relevantes

- `agregar_poblacion_por_gret`: mapea `edad` a grupos quinquenales `gr_et` y `sexo` a códigos `1/2`.
- `juntar_poblacion_defunciones_por_gr_et`: hace el `left join` y puede rellenar ceros.
- `calcular_tasa_por_100k`: añade `tasa_x100k` y `tasa` (proporción pura).
- `agregar_indice_periodo`: crea la columna `t` (índice por año).


## Diccionario de variables

- `ano`: año calendario de referencia (entero).
- `t`: índice entero consecutivo por año presente tras el cruce población–defunciones. Se genera con `agregar_indice_periodo`; útil para modelos que requieren una escala temporal regular.
- `sexo`: código de sexo en formato numérico (`1` = hombres, `2` = mujeres). En algunas salidas agregadas (p. ej., `tasas_mortalidad_gret_per.csv`) no aparece porque se consolidan ambos sexos.
- `gr_et`: grupo etario quinquenal (entero) según el mapeo aplicado en `preproc_gret_poblacion.py`.
- `poblacion`: población correspondiente al cruce (`ano`, `sexo`, `gr_et`) o a su agregado por `gr_et` y periodo.
- `conteo_defunciones`: número de defunciones observadas en el cruce o agregado correspondiente.
- `tasa`: tasa de mortalidad como proporción (defunciones/población).
- `tasa_x100k`: tasa por cada 100.000 habitantes, derivada de `tasa`.

Notas:
- Cuando `poblacion <= 0` o es `NaN`, la tasa queda `NaN` por diseño para evitar divisiones por cero.
- Para evitar valores exactamente cero al modelar, se aplica una tasa mínima en `calcular_tasa_por_100k` (`min_rate=1e-8`) cuando procede.

### Mapeo de grupos etarios (`gr_et`)

Según `edad_a_gr_et_quinquenios`:

| gr_et | Rango de edad |
|-------|----------------|
| 1     | 0–4            |
| 2     | 5–9            |
| 3     | 10–14          |
| 4     | 15–19          |
| 5     | 20–24          |
| 6     | 25–29          |
| 7     | 30–34          |
| 8     | 35–39          |
| 9     | 40–44          |
| 10    | 45–49          |
| 11    | 50–54          |
| 12    | 55–59          |
| 13    | 60–64          |
| 14    | 65–69          |
| 15    | 70–74          |
| 16    | 75–79          |
| 17    | ≥ 80           |

