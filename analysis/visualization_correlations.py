"""
Visualization Correlations Module

Dieses Modul enthält Visualisierungen zur Untersuchung von Zusammenhängen und
Korrelationen zwischen verschiedenen Attributen in den Datensätzen.
Beispiele sind Streudiagramme, Korrelationsmatrizen und Regressionsanalysen.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# Interner Import
from analysis.visualization_core import VisualizationCore

# Logger konfigurieren
logger = logging.getLogger(__name__)


class CorrelationVisualization:
    """
    Modul zur Erstellung von Korrelationen und zusammenhängenden Visualisierungen
    (z.B. Korrelationsmatrix, Streudiagramme, Regressionslinien).
    """

    def __init__(self, core: VisualizationCore):
        self.core = core
        self.stats_module = core.stats_module
        self.api = core.api
        self.config = core.config
        logger.info("Korrelations-Visualisierungsmodul initialisiert.")

    def create_correlation_matrix(self, df: pd.DataFrame, numeric_columns: Optional[List[str]] = None) -> Optional[str]:
        """
        Erstellt eine Korrelationsmatrix als Heatmap.
        
        Args:
            df: Pandas DataFrame mit numerischen Daten
            numeric_columns: Liste der Spalten, die für die Korrelation verwendet werden sollen
            
        Returns:
            Pfad zur gespeicherten Grafik oder None
        """
        if numeric_columns:
            df = df[numeric_columns]
        else:
            df = df.select_dtypes(include='number')

        if df.empty or df.shape[1] < 2:
            logger.warning("Nicht genügend numerische Daten für Korrelation.")
            return None

        corr = df.corr()

        fig = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale='RdBu_r',
            title='Korrelationsmatrix',
        )
        return self.core.save_plotly_figure(fig, "correlation_matrix.html")

    def create_scatter_plot(self, df: pd.DataFrame, x: str, y: str, color: Optional[str] = None) -> Optional[str]:
        """
        Erstellt ein Streudiagramm zweier numerischer Variablen.
        
        Args:
            df: Pandas DataFrame
            x: Spalte für x-Achse
            y: Spalte für y-Achse
            color: Optional – Gruppierung nach Kategorie
        
        Returns:
            Pfad zur gespeicherten Grafik oder None
        """
        if x not in df.columns or y not in df.columns:
            logger.warning(f"Spalten {x} oder {y} nicht im DataFrame enthalten.")
            return None

        fig = px.scatter(
            df, x=x, y=y, color=color,
            trendline="ols",
            title=f'Streudiagramm: {x} vs. {y}',
            template='plotly_dark'
        )

        return self.core.save_plotly_figure(fig, f"scatter_{x}_vs_{y}.html")
