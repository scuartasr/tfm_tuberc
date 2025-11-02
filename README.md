# Configuración en MacOS y Linux

Ejecute los siguientes comandos en el terminal:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
source setup.sh
```

# Configuración en Windows

Ejecute los siguientes comandos en el terminal:

```bash
python3 -m venv .venv
.venv\Scripts\activate
setup
```

# Ejecución de pruebas

Ejecute el siguiente comando en el terminal:

```bash
pytest
```

## Documentación

- Guía completa del preprocesamiento y pipeline: [`docs/index.md`](docs/index.md)
	- Sección de referencia: [Diccionario de variables](docs/index.md#diccionario-de-variables)

Comandos útiles (zsh):

```bash
# Activar entorno
source .venv/bin/activate

# Ejecutar orquestador del preprocesamiento
python src/preproc/run_all_preproc.py --fill-zeros --with-checks --tuberc-verbose 2
```

## Estilo reutilizable para gráficos (Matplotlib/Seaborn)

Se agregó un pequeño módulo de utilidades en `src/viz/style.py` para centralizar la estética usada en los notebooks:

- `get_palette(n_series, cmap_name="tab20")`: devuelve una lista de colores consistente con el notebook descriptivo.
- `set_font_ancizar(...)`: activa la familia de fuente Ancizar (si está instalada) y la aplica en Matplotlib.
- `apply_matplotlib_style(...)`: atajo para aplicar fuente y paleta globalmente.

Uso típico en un notebook (desde la carpeta `descriptivo/` u otra):

```python
import sys, os
sys.path.append(os.path.abspath("../src"))  # añade el layout "src" al PYTHONPATH

from viz.style import get_palette, apply_matplotlib_style

# Aplica fuente Ancizar (si está instalada en el sistema) y fija paleta de 7 colores
apply_matplotlib_style(n_colors=7, base_font_size=11)

# Usar paleta explícitamente
colors = get_palette(3)
plt.plot([1,2,3],[1,4,9], color=colors[0])
```

Notas:

- Si Ancizar no está instalada, se usará una familia de respaldo (por defecto, `serif`). Puedes pasar rutas a archivos `.ttf/.otf` con `search_paths` para registrarla on-the-fly.
- El módulo no incorpora archivos de fuentes por licencia; si los tienes, colócalos (por ejemplo) en `assets/fonts/` y úsalo así:

```python
apply_matplotlib_style(search_paths=["../assets/fonts"])  # registra .ttf/.otf encontrados
```

## Uso rápido del pipeline

Ejecuta todo el flujo (población → agregados → defunciones → cruce + tasas + matrices Lexis) con validaciones:

```bash
source .venv/bin/activate
python src/preproc/run_all_preproc.py --fill-zeros --with-checks --tuberc-verbose 2
```

Modo depuración (procesar pocas filas/archivos):

```bash
source .venv/bin/activate
python src/preproc/run_all_preproc.py --dry-run --rows 100 --tuberc-verbose 1 --tuberc-max-files 3
```

Ejecutar sólo el cruce final con validaciones activadas:

```bash
python src/preproc/preproc_poblac_defunc.py --fill-zeros --with-checks
```

## Validaciones de integridad (nuevo)

Se incorporó un módulo ligero de validaciones en `src/preproc/_internals/validaciones.py` para detectar regresiones tempranas:

- `validar_poblacion`: acepta esquema largo (`ano, sexo, edad, poblacion`) o agregado (`ano, sexo, gr_et, poblacion`). Verifica:
	- Columnas mínimas según el esquema.
	- Rango de años extremo (advertencias si faltan 1979 o 2023).
	- Referencia crítica hombres 0–4 año 1979 = 1,795,941 (detecta regreso del bug de truncamiento).
	- Ausencia de patrones de miles residuales (p.ej. `380.350`).
	- No negatividad de la población.
- `validar_defunciones`: columnas requeridas, valores inesperados de `sexo`, no negativos.
- `validar_cruce`: coherencia población/defunciones tras el join (no defunciones>0 con población=0 salvo casos que requieren inspección, y reporte de defunciones > población).

Para activar las validaciones en el flujo completo: añade `--with-checks` al orquestador o al script de cruce.

Ejemplo de salida esperada sin advertencias:

```
✓ Población: sin advertencias.
✓ Defunciones: sin advertencias.
✓ Cruce: sin advertencias.
```

Si aparece una advertencia representativa (ejemplo):

```
Población: 1 advertencia(s):
	 - Primer año > 1979 (1985); ¿dataset recortado o faltan filas?
```

## Nuevas banderas relevantes

| Bandera | Script | Descripción |
|---------|--------|-------------|
| `--with-checks` | `run_all_preproc.py` / `preproc_poblac_defunc.py` | Ejecuta validaciones de integridad tras el cruce. |
| `--no-lexis-ano` | `preproc_poblac_defunc.py` | Omite matriz Lexis por año. |
| `--no-lexis-t` | `preproc_poblac_defunc.py` | Omite matriz Lexis por índice de periodo `t`. |
| `--no-lexis-por-sexo` | `preproc_poblac_defunc.py` | Omite matrices Lexis segmentadas por sexo. |
| `--tuberc-max-files` | Orquestador | Limita número de archivos de defunciones (depuración). |
| `--tuberc-verbose` | Orquestador → `preproc_tuberc.py` | Controla nivel de log (0–2). |

## Notas sobre el bug corregido (truncamiento de población)

Se corrigió un error histórico de parsing que truncaba poblaciones al eliminar un dígito de miles (e.g. `380.350` → `38035`). La nueva lectura fuerza tipos texto y limpia numéricamente con regex, preservando magnitudes. La validación de referencia hombres 0–4 año 1979 asegura que el valor agregado (1,795,941) se mantenga estable en futuras iteraciones.

## Próximos pasos sugeridos (opcional)

- Añadir pruebas unitarias para validar el valor de referencia y ausencia de separadores de miles.
- Documentar ejemplos de carga de tasas en notebooks de modelado.
- Incluir un flag `--skip-defunciones` en el orquestador para acelerar iteraciones cuando sólo cambia población.


### Salidas de mortalidad y flags (nuevo)

Al ejecutar `preproc_poblac_defunc.py` (directamente o vía el orquestador) se generan por defecto:

- `data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv`
- `data/processed/mortalidad/tasas_mortalidad_gret_per.csv` (agregado por `ano`, `t`, `gr_et`, sin `sexo`)
- Matrices de Lexis (tasa por 100k, filas=`gr_et`):
	- `data/processed/mortalidad/tasa_mortalidad_lexis.csv` (columnas=`ano`)
	- `data/processed/mortalidad/tasa_mortalidad_lexis_t.csv` (columnas=`t`)
	- `data/processed/mortalidad/tasa_mortalidad_lexis_sexo1.csv` y `..._sexo2.csv`

Flags de opt-out para controlar la generación de matrices (por defecto se generan todas):

```bash
# No generar matriz Lexis por año
python src/preproc/run_all_preproc.py --no-lexis-ano

# No generar matriz Lexis por t
python src/preproc/run_all_preproc.py --no-lexis-t

# No generar matrices Lexis por sexo
python src/preproc/run_all_preproc.py --no-lexis-por-sexo
```

### Salidas agregadas sin sexo (nuevo)

Además, ahora se generan versiones agregadas que excluyen el sexo (suma de ambos sexos):

- `data/processed/poblacion/poblacion_colombia_gr_et_sin_sexo.csv` (agregado por `ano` y `gr_et`), columnas: `ano, gr_et, poblacion`.
- `data/processed/defunc/defunciones_por_gr_et_sin_sexo.csv` (agregado por `ano` y `gr_et`), columnas: `ano, gr_et, conteo_defunciones`.

### Servir y publicar la documentación (MkDocs)

Servir localmente:

```bash
source .venv/bin/activate
pip install -r docs/requirements-docs.txt
mkdocs serve -a 127.0.0.1:8000
```

Despliegue automático con GitHub Pages:

- Ya está configurado el workflow en `.github/workflows/docs.yml`.
- Habilita GitHub Pages en Settings → Pages → Source: “GitHub Actions”.
- Al hacer push a `main` con cambios en `docs/**` o `mkdocs.yml`, se publica en `https://scuartasr.github.io/tfm_tuberc/`.