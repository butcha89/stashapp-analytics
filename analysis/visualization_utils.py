"""
Visualization Utils Module

Hilfsfunktionen zur Unterstützung von Visualisierungen, darunter Farbschemata,
Formatierungen, Datumsoperationen und Stilkonfigurationen.
"""

import logging
import datetime
from typing import List, Union
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

def configure_plot_styles():
    """
    Konfiguriert globale Plot-Stile für Matplotlib und Seaborn.
    """
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        "figure.figsize": (12, 6),
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "font.family": "DejaVu Sans"
    })
    logger.debug("Plot-Stile konfiguriert.")

def get_color_palette(n: int, palette: str = "viridis") -> List[str]:
    """
    Liefert eine Farbliste mit n Farben basierend auf einer benannten Seaborn/Matplotlib-Palette.

    Args:
        n: Anzahl der benötigten Farben
        palette: Name der Palette

    Returns:
        Liste mit hexadezimalen Farbcodes
    """
    try:
        colors = sns.color_palette(palette, n)
        return [sns.utils.rgb2hex(c) for c in colors]
    except Exception as e:
        logger.warning(f"Fehler beim Generieren der Farbpalette '{palette}': {e}")
        return ["#CCCCCC"] * n

def shorten_label(label: str, max_length: int = 20) -> str:
    """
    Kürzt einen Text-Label, wenn er zu lang ist.

    Args:
        label: Der zu kürzende String
        max_length: Maximale Zeichenanzahl

    Returns:
        Gekürzter Labeltext
    """
    if len(label) > max_length:
        return label[:max_length - 3] + "..."
    return label

def format_percent(value: float, decimals: int = 1) -> str:
    """
    Formatiert eine Fließkommazahl als Prozentwert.

    Args:
        value: Wert (z. B. 0.85)
        decimals: Nachkommastellen

    Returns:
        Prozentualer String (z. B. "85.0 %")
    """
    return f"{value * 100:.{decimals}f} %"

def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> Union[datetime.date, None]:
    """
    Parsen eines Datumsstrings in ein datetime.date-Objekt.

    Args:
        date_str: Datum als String
        fmt: Datumsformat

    Returns:
        datetime.date oder None bei Fehler
    """
    try:
        return datetime.datetime.strptime(date_str, fmt).date()
    except Exception as e:
        logger.warning(f"Fehler beim Parsen von Datum '{date_str}': {e}")
        return None
