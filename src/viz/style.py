"""Funciones de estilo reutilizables para gráficos (Matplotlib/Seaborn).

Incluye:
- get_palette: paleta consistente basada en tu notebook.
- set_font_ancizar: registra/activa la familia de fuente Ancizar si está instalada y la aplica a Matplotlib.
- register_font_from_paths: registra archivos .ttf/.otf desde rutas dadas.
- apply_matplotlib_style: aplica ajustes útiles de estilo (paleta y fuente) a nivel global.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib import font_manager as fm
from cycler import cycler

try:
    import seaborn as sns  # opcional; si no está, seguimos con Matplotlib puro
except Exception:  # pragma: no cover
    sns = None  # type: ignore


def get_palette(n_series: int, cmap_name: str = "tab20"):
    """
    Retorna una lista de colores según el número de series.

    Replica la lógica usada en tu notebook `analisis_descriptivo.ipynb`:
    - Usa una paleta base específica cuando `n_series` <= len(colores_base).
    - Si no alcanza, genera colores desde un colormap de Matplotlib.

    Parámetros:
    - n_series: cantidad de elementos únicos en la visualización.
    - cmap_name: nombre del colormap de Matplotlib a usar como respaldo (por defecto, "tab20").

    Devuelve:
    - list de colores en formato aceptado por Matplotlib (tuplas RGBA o RGB normalizadas 0–1).
    """
    colores_base = [
        (148 / 255, 180 / 255, 59 / 255),   # verde claro
        (166 / 255, 28 / 255, 49 / 255),    # rojo vino
        (70 / 255, 107 / 255, 63 / 255),    # verde oscuro
        (118 / 255, 35 / 255, 47 / 255),    # rojo oscuro
        (86 / 255, 90 / 255, 92 / 255),     # gris
        (117 / 255, 178 / 255, 176 / 255),  # verde agua
        (0 / 255, 0 / 255, 0 / 255),        # negro
    ]

    if n_series <= len(colores_base):
        return colores_base[:n_series]

    cmap = plt.cm.get_cmap(cmap_name)
    return [cmap(i) for i in np.linspace(0, 1, n_series)]


def get_sequential_cmap(
    index: int = 0,
    *,
    name: Optional[str] = None,
    reverse: bool = False,
    anchor_white: tuple = (1.0, 1.0, 1.0, 1.0),
) -> LinearSegmentedColormap:
    """
    Construye un colormap secuencial basado en un color de la paleta discreta.

    Útil para heatmaps coherentes con la identidad cromática del proyecto.

    Parámetros:
    - index: índice del color en la paleta base (0 = primer color de `get_palette`).
    - name: nombre opcional del colormap.
    - reverse: si True, invierte el gradiente (color→blanco en lugar de blanco→color).
    - anchor_white: color RGBA usado como extremo claro (por defecto, blanco puro).
    """
    base_color = get_palette(index + 1)[index]
    base_rgba = to_rgba(base_color)
    colors = [anchor_white, base_rgba]
    if reverse:
        colors = list(reversed(colors))
    cm_name = name or f"seq_from_palette_{index}{'_r' if reverse else ''}"
    return LinearSegmentedColormap.from_list(cm_name, colors)


def _find_font_family_in_manager(family_substr: str) -> List[str]:
    family_substr_lower = family_substr.lower()
    return [f.name for f in fm.fontManager.ttflist if family_substr_lower in f.name.lower()]


def register_font_from_paths(paths: Iterable[str]) -> List[str]:
    """
    Registra fuentes .ttf/.otf desde rutas proporcionadas (archivos o carpetas).

    Devuelve:
    - Lista de rutas de fuentes registradas exitosamente.
    """
    registered: List[str] = []
    for p in paths:
        try:
            if p.lower().endswith((".ttf", ".otf")):
                fm.fontManager.addfont(p)
                registered.append(p)
            else:
                # Si es carpeta, intenta registrar todos los .ttf/.otf dentro
                import os

                if os.path.isdir(p):
                    for fname in os.listdir(p):
                        if fname.lower().endswith((".ttf", ".otf")):
                            fpath = os.path.join(p, fname)
                            fm.fontManager.addfont(fpath)
                            registered.append(fpath)
        except Exception:
            # No detenernos por un archivo problemático
            continue

    # Reconstruir caché después de añadir
    try:
        fm._load_fontmanager(try_read_cache=False)
    except Exception:
        pass

    return registered


def set_font_ancizar(
    family: str = "Ancizar Serif",
    *,
    fallback_family: str = "serif",
    search_paths: Optional[Iterable[str]] = None,
    base_font_size: Optional[int] = None,
) -> str:
    """
    Activa la familia de fuente "Ancizar" en Matplotlib si está disponible.

    - Si no está instalada, puede intentar registrarla buscando archivos .ttf/.otf en
      `search_paths` (carpetas o archivos). No incluye fuentes en el repo por defecto.
    - Ajusta rcParams['font.family'] y retorna la familia efectivamente aplicada.

    Parámetros:
    - family: nombre preferido (p.ej., "Ancizar Serif" o "Ancizar Sans").
    - fallback_family: familia de respaldo si no se encuentra Ancizar.
    - search_paths: iterable de rutas (archivos .ttf/.otf o carpetas) para registrar fuentes.
    - base_font_size: si se proporciona, ajusta rcParams['font.size'].

    Devuelve:
    - Nombre de la familia aplicada finalmente.
    """
    # Intento directo
    found = _find_font_family_in_manager("Ancizar")
    if not found and search_paths:
        register_font_from_paths(search_paths)
        found = _find_font_family_in_manager("Ancizar")

    # Determinar familia a usar
    applied_family = family if any(family.lower() == f.lower() for f in found) else (
        found[0] if found else fallback_family
    )

    plt.rcParams["font.family"] = applied_family
    if base_font_size is not None:
        plt.rcParams["font.size"] = base_font_size

    return applied_family


def apply_matplotlib_style(
    *,
    n_colors: Optional[int] = None,
    cmap_name: str = "tab20",
    font_family: str = "Ancizar Serif",
    fallback_family: str = "serif",
    search_paths: Optional[Iterable[str]] = None,
    base_font_size: Optional[int] = 11,
    seaborn_context: str = "notebook",
    seaborn_style: str = "white",
    background: Optional[str] = "white",
    transparent: bool = False,
) -> str:
    """
    Aplica una configuración de estilo coherente (fuente + paleta) a Matplotlib y, si está, Seaborn.

    - Establece la familia de fuente (intenta Ancizar) y tamaño base opcional.
    - Si `n_colors` se proporciona, ajusta el ciclo de colores de ejes con `get_palette(n_colors)`.

    Devuelve:
    - La familia de fuente aplicada finalmente (útil para logs/depuración).
    """
    applied_family = set_font_ancizar(
        family=font_family,
        fallback_family=fallback_family,
        search_paths=search_paths,
        base_font_size=base_font_size,
    )

    if n_colors is not None and n_colors > 0:
        colors = get_palette(n_colors, cmap_name=cmap_name)
        plt.rcParams["axes.prop_cycle"] = cycler(color=colors)

    # Fondo blanco (o el especificado) para ejes y figura, y guardado
    if background is not None:
        plt.rcParams["figure.facecolor"] = background
        plt.rcParams["axes.facecolor"] = background
    # Controlar transparencia al guardar
    plt.rcParams["savefig.transparent"] = bool(transparent)
    if not transparent:
        # Si no es transparente, forzamos blanco al guardar (evita grises en backends)
        plt.rcParams["savefig.facecolor"] = background or "white"

    # Ajustes Seaborn (opcional)
    if sns is not None:
        try:
            # Usamos un estilo claro por defecto y respetamos facecolors forzados
            rc = {}
            if background is not None:
                rc = {"axes.facecolor": background, "figure.facecolor": background}
            sns.set_theme(context=seaborn_context, style=seaborn_style, font=applied_family, rc=rc)
        except Exception:
            # En caso de que la fuente no sea reconocida por Seaborn
            sns.set_theme(context=seaborn_context, style=seaborn_style)

    return applied_family
