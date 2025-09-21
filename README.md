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
python src/preproc/run_all_preproc.py --fill-zeros --tuberc-verbose 2
```

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