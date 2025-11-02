# Validaciones de integridad del pipeline

Esta página documenta las validaciones ligeras implementadas para reducir el riesgo de introducir regresiones silenciosas en el preprocesamiento de población, defunciones y su cruce.

Las funciones residen en `src/preproc/_internals/validaciones.py` y se activan añadiendo la bandera `--with-checks` al ejecutar:

- `python src/preproc/preproc_poblac_defunc.py --with-checks` (directo)
- `python src/preproc/run_all_preproc.py --with-checks` (orquestador)

## Principios de diseño

- Costo bajo: no se re-lee todo salvo lo necesario; se opera sobre el dataframe ya cargado.
- Falla temprana opcional: en modo crítico (no usado por defecto en orquestador) algunas incoherencias pueden lanzar `AssertionError`.
- Señales específicas: se monitorean puntos históricos de riesgo (bug de truncamiento de población 0–4).
- Flexibilidad: admite dos esquemas para población (largo por edad o agregado por `gr_et`).

## `validar_poblacion(df, critical=True|False)`

Acepta uno de los dos esquemas:

- Largo: columnas mínimas `{ano, sexo, edad, poblacion}`.
- Agregado: columnas mínimas `{ano, sexo, gr_et, poblacion}`.

Checks:

| Check | Descripción | Severidad |
|-------|-------------|-----------|
| Columnas mínimas | Verifica que alguna de las combinaciones válidas exista. | Error si `critical`, advertencia si no. |
| Rango de años | Reporta si el primer año > 1979 o último < 2023. | Advertencia |
| Referencia 0–4 1979 | Suma de población hombres 0–4 (o `gr_et=1`) debe ser 1,795,941. | Error si `critical`, advertencia caso contrario |
| Patrón de miles residual | Detección regex `\b\d{1,3}\.\d{3}(?:\.\d{3})*\b` en muestra inicial. | Advertencia |
| Negativos | Población < 0. | Error si `critical`, advertencia caso contrario |

Nota: El mapeo de sexo se normaliza para aceptar valores `1`, `h`, `hombre`, `m` (masculino), etc.

## `validar_defunciones(df)`

Checks:

| Check | Descripción |
|-------|-------------|
| Columnas mínimas | Requiere `{ano, sexo, gr_et, conteo_defunciones}`. |
| Valores inesperados `sexo` | Reporta códigos fuera del conjunto esperado (por defecto 1,2,9). |
| Negativos | `conteo_defunciones < 0`. |

## `validar_cruce(df)`

Checks:

| Check | Descripción |
|-------|-------------|
| Columnas mínimas | `{ano, sexo, gr_et, poblacion, conteo_defunciones}` presentes. |
| Defunciones sin población | Filas con `poblacion==0` y `conteo_defunciones>0`. |
| Defunciones > población | Casos donde `conteo_defunciones` supera a `poblacion` (indicativo de desalineación). |

## Ejemplo de uso programático

```python
from src.preproc._internals.validaciones import validar_poblacion, validar_defunciones, validar_cruce
import pandas as pd

# Cargar dataframes ya procesados
pop = pd.read_csv('data/processed/poblacion/poblacion_colombia_gr_et.csv')
defu = pd.read_csv('data/processed/defunc/defunciones_por_gr_et.csv')
cruce = pd.read_csv('data/processed/mortalidad/poblacion_defunciones_por_gr_et.csv')

warns_pop = validar_poblacion(pop, critical=False)
warns_def = validar_defunciones(defu)
warns_join = validar_cruce(cruce)

print('Población:', warns_pop or 'OK')
print('Defunciones:', warns_def or 'OK')
print('Cruce:', warns_join or 'OK')
```

## Interpretación de la referencia 1,795,941

Ese valor corresponde a la población total masculina de 0 a 4 años (suma de edades individuales) en 1979. Se usa como centinela porque un bug previo truncaba cifras con separadores de miles, reduciendo artificialmente magnitudes (ej. `380.350`→`38035`). Si la referencia varía:

1. Verificar fuente DANE por actualizaciones metodológicas.
2. Revisar paso de lectura y normalización numérica.
3. Confirmar que no se filtraron accidentalmente edades 0–4.

## Extender validaciones

Posibles extensiones futuras:

- Coherencia interanual (población no debería variar > X% entre años sucesivos por edad/grupo).
- Detección de outliers en tasas (z-score o IQR adaptado por grupo etario).
- Verificación de monotonicidad parcial en acumulados (si se generan variables acumuladas a futuro).

## Salida resumida

La utilidad auxiliar `resumen_advertencias(nombre, warns)` imprime:

```
✓ Población: sin advertencias.
Defunciones: 1 advertencia(s):
   - Valores inesperados en 'sexo': {7}
```

## Buenas prácticas

- Ejecutar con `--with-checks` al menos antes de cada commit importante del pipeline.
- Añadir pruebas unitarias de los checks críticos si se estabiliza el esquema.
- Mantener esta página sincronizada cuando se agreguen nuevas reglas.
