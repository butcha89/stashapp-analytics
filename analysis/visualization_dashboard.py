"""
Visualization Dashboard Module

Dieses Modul erstellt kombinierte Visualisierungen und interaktive Dashboards,
die mehrere Aspekte wie Performer, Szenen, Tags und O-Counter-Daten zusammenfassen.
Es nutzt Plotly zur Erstellung ansprechender Visual-Dashboards.
"""

import logging
from typing import List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Interner Import
from analysis.visualization_core import VisualizationCore
from analysis.visualization_performer import PerformerVisualization
from analysis.visualization_scenes import SceneVisualization
from analysis.visualization_o_counter import OCounterVisualization
from analysis.visualization_tags import TagVisualization

logger = logging.getLogger(__name__)


class DashboardVisualization:
    """
    Visualisierungsmodul für kombinierte Dashboards.
    """

    def __init__(self, core: VisualizationCore):
        self.core = core
        self.performer_viz = PerformerVisualization(core)
        self.scene_viz = SceneVisualization(core)
        self.o_counter_viz = OCounterVisualization(core)
        self.tag_viz = TagVisualization(core)
        logger.info("Dashboard-Visualisierungsmodul initialisiert.")

    def _get_subplot_trace_from_html(self, html_path: str) -> Optional[go.Figure]:
        """
        Dummy-Loader für gespeicherte HTML-Visualisierungen (optional für echte Integration).

        Args:
            html_path: Pfad zur gespeicherten HTML-Datei

        Returns:
            Plotly-Figure-Objekt (falls rekonstruierbar)
        """
        # Hinweis: Realistischer wäre ein Zwischenspeicher mit Plotly-JSON-Daten
        logger.debug(f"Laden von Plotly-Grafik aus {html_path} derzeit nicht implementiert.")
        return None

    def create_dashboard_preview(self) -> Optional[str]:
        """
        Erstellt eine kombinierte Dashboard-Vorschau mit mehreren Subplots.

        Returns:
            Pfad zur gespeicherten interaktiven HTML-Datei
        """
        logger.info("Dashboard-Vorschau wird erstellt...")

        # Einfache Variante: Kombinierte Subplots aus Performer-, Szene- und Tag-Daten
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Performer Ratings", 
                "O-Counter Verteilung", 
                "Top Tags", 
                "Szenen-Ratings"
            ),
            horizontal_spacing=0.1,
            vertical_spacing=0.15
        )

        # Einzelne Visuals abrufen
        performer_rating_fig = self.performer_viz.create_performer_rating_distribution()
        o_counter_fig = self.o_counter_viz.create_ocounter_distribution()
        tag_fig = self.tag_viz.create_tag_frequency_barplot(top_n=15)
        scene_rating_fig = self.scene_viz.create_scene_rating_visualizations()

        # Falls HTML gespeichert wurde, könnten diese rekonstruiert werden (optional)
        # Hier: Simulation durch Neuberechnung (vereinfachte Demo)

        if any(v is None for v in [performer_rating_fig, o_counter_fig, tag_fig, scene_rating_fig]):
            logger.warning("Mindestens eine Visualisierung konnte nicht geladen werden.")
            return None

        # Hinweis: Plotly-Figuren können keine Spuren einfach "gemerged" werden,
        # deshalb wäre eine Replikation der Subplots sinnvoller als externer HTML-Import.
        logger.warning("Für echtes Dashboard müssten Original-Traces verwendet werden.")

        return None  # Platzhalter

    def create_full_dashboard(self) -> Optional[str]:
        """
        Erzeugt ein vollständiges interaktives Plotly-Dashboard (mehrseitig oder tab-basiert möglich).

        Returns:
            Pfad zur gespeicherten HTML-Datei
        """
        # Diese Methode kann später erweitert werden, z.B. mit Dash, Panel oder Streamlit.
        logger.info("Vollständiges Dashboard-Rendering noch nicht implementiert.")
        return None
