"""Utilidades de visualización reutilizables.

Expone funciones de estilo comunes para notebooks y scripts.
"""
from .style import (
    get_palette,
    set_font_ancizar,
    register_font_from_paths,
    apply_matplotlib_style,
    get_sequential_cmap,
)

__all__ = [
    "get_palette",
    "set_font_ancizar",
    "register_font_from_paths",
    "apply_matplotlib_style",
    "get_sequential_cmap",
]
