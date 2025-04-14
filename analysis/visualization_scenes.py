"""
Visualization Scenes Module

Dieses Modul ist verantwortlich für die Erstellung von Visualisierungen und Diagrammen
für Szenen-bezogene Daten. Es erstellt Visualisierungen zu Bewertungen, zeitlichen
Trends, Studios und andere Szenen-spezifische Analysen.
"""

import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Interner Import
from core.data_models import Scene
from analysis.visualization_core import VisualizationCore

# Logger konfigurieren
logger = logging.getLogger(__name__)

class SceneVisualization:
    """
    Klasse zur Erstellung von Szenen-bezogenen Visualisierungen.
    
    Diese Klasse erstellt verschiedene Diagramme und Visualisierungen
    für Szenen-Daten wie Bewertungen, zeitliche Verteilungen, Studios
    und andere Szenen-spezifische Analysen.
    """
    
    def __init__(self, core: VisualizationCore):
        """
        Initialisiert das Szenen-Visualisierungsmodul.
        
        Args:
            core: VisualizationCore-Instanz mit gemeinsamen Funktionen und Konfigurationen
        """
        self.core = core
        self.stats_module = core.stats_module
        self.api = core.api
        self.config = core.config
        logger.info("Szenen-Visualisierungsmodul initialisiert")
    
    def create_scene_rating_visualizations(self) -> List[str]:
        """
        Erstellt eine Visualisierung der Bewertung von Szenen über die Zeit.
        
        Returns:
            Liste von Pfaden zu den gespeicherten Diagrammen
        """
        logger.info("Erstelle Szenenbewertungs-Visualisierungen...")

        scenes: List[Scene] = self.stats_module.get_all_scenes()
        if not scenes:
            logger.warning("Keine Szenendaten gefunden.")
            return []

        df = pd.DataFrame([{
            "title": scene.title,
            "rating": scene.rating,
            "date": scene.date
        } for scene in scenes if scene.rating is not None and scene.date is not None])

        if df.empty:
            logger.warning("Keine gültigen Bewertungsdaten vorhanden.")
            return []

        df['date'] = pd.to_datetime(df['date'])

        # Durchschnittliche Bewertung pro Monat
        df_monthly = df.resample('M', on='date').mean(numeric_only=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_monthly.index,
            y=df_monthly['rating'],
            mode='lines+markers',
            name='Durchschnittliche Bewertung'
        ))

        fig.update_layout(
            title='Durchschnittliche Szenenbewertung über Zeit',
            xaxis_title='Monat',
            yaxis_title='Bewertung',
            template='plotly_dark'
        )

        output_path = self.core.save_plotly_figure(fig, "scene_rating_trend.html")
        return [output_path]

    def create_scene_count_per_studio(self) -> List[str]:
        """
        Erstellt ein Balkendiagramm der Anzahl Szenen pro Studio.
        
        Returns:
            Liste von Pfaden zu gespeicherten Diagrammen
        """
        logger.info("Erstelle Balkendiagramm für Szenenzahl pro Studio...")

        scenes: List[Scene] = self.stats_module.get_all_scenes()
        if not scenes:
            logger.warning("Keine Szenendaten gefunden.")
            return []

        df = pd.DataFrame([{
            "studio": scene.studio,
        } for scene in scenes if scene.studio])

        if df.empty:
            logger.warning("Keine Studios gefunden.")
            return []

        studio_counts = df['studio'].value_counts().nlargest(20)
        fig = px.bar(
            x=studio_counts.values,
            y=studio_counts.index,
            orientation='h',
            labels={'x': 'Anzahl Szenen', 'y': 'Studio'},
            title='Top 20 Studios nach Anzahl Szenen',
            template='plotly_dark'
        )

        output_path = self.core.save_plotly_figure(fig, "studio_scene_counts.html")
        return [output_path]
