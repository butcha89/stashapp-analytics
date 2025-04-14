"""
Visualization O-Counter Module

Dieses Modul enthält Visualisierungen, die sich auf den O-Counter beziehen –
also wie oft Performer:innen in einer Szene den Orgasmus erreicht haben (wenn getrackt).
Dies kann aufgeschlüsselt nach Jahr, Performer, Tags oder anderen Attributen visualisiert werden.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Interner Import
from core.data_models import Scene
from analysis.visualization_core import VisualizationCore

# Logger konfigurieren
logger = logging.getLogger(__name__)


class OCounterVisualization:
    """
    Visualisierungen für O-Counter-Daten (z.B. Verteilungen, Zeitverlauf, Performer-Korrelation).
    """

    def __init__(self, core: VisualizationCore):
        self.core = core
        self.stats_module = core.stats_module
        self.api = core.api
        self.config = core.config
        logger.info("O-Counter-Visualisierungsmodul initialisiert.")

    def create_ocounter_distribution(self) -> Optional[str]:
        """
        Erstellt ein Histogramm der O-Counter-Verteilung in allen Szenen.

        Returns:
            Pfad zur gespeicherten Grafik
        """
        scenes: List[Scene] = self.stats_module.get_all_scenes()
        values = [scene.o_counter for scene in scenes if scene.o_counter is not None]

        if not values:
            logger.warning("Keine O-Counter-Daten verfügbar.")
            return None

        df = pd.DataFrame({"O-Counter": values})

        fig = px.histogram(
            df,
            x="O-Counter",
            nbins=20,
            title="Verteilung des O-Counters über alle Szenen",
            template="plotly_dark"
        )

        return self.core.save_plotly_figure(fig, "ocounter_distribution.html")

    def create_ocounter_over_time(self) -> Optional[str]:
        """
        Erstellt eine Zeitreihe der durchschnittlichen O-Counter-Werte pro Jahr.

        Returns:
            Pfad zur gespeicherten Grafik
        """
        scenes: List[Scene] = self.stats_module.get_all_scenes()
        data = []

        for scene in scenes:
            if scene.o_counter is not None and scene.date:
                year = scene.date.year
                data.append((year, scene.o_counter))

        if not data:
            logger.warning("Keine ausreichenden O-Counter-Zeitdaten.")
            return None

        df = pd.DataFrame(data, columns=["Jahr", "O-Counter"])
        yearly_avg = df.groupby("Jahr").mean().reset_index()

        fig = px.line(
            yearly_avg,
            x="Jahr",
            y="O-Counter",
            markers=True,
            title="Durchschnittlicher O-Counter pro Jahr",
            template="plotly_dark"
        )

        return self.core.save_plotly_figure(fig, "ocounter_over_time.html")

    def create_ocounter_by_tag(self, min_scenes: int = 10) -> Optional[str]:
        """
        Berechnet den durchschnittlichen O-Counter pro Tag (wenn genügend Szenen vorhanden sind).

        Args:
            min_scenes: Mindestanzahl an Szenen pro Tag

        Returns:
            Pfad zur gespeicherten Grafik
        """
        scenes: List[Scene] = self.stats_module.get_all_scenes()
        tag_data = {}

        for scene in scenes:
            if scene.o_counter is not None and scene.tags:
                for tag in scene.tags:
                    if tag not in tag_data:
                        tag_data[tag] = []
                    tag_data[tag].append(scene.o_counter)

        avg_data = {
            tag: sum(ocs) / len(ocs)
            for tag, ocs in tag_data.items()
            if len(ocs) >= min_scenes
        }

        if not avg_data:
            logger.warning("Keine Tags mit ausreichenden Daten für O-Counter-Korrelation.")
            return None

        df = pd.DataFrame(list(avg_data.items()), columns=["Tag", "Ø O-Counter"]).sort_values("Ø O-Counter", ascending=False)

        fig = px.bar(
            df,
            x="Ø O-Counter",
            y="Tag",
            orientation="h",
            title="Durchschnittlicher O-Counter nach Tag",
            template="plotly_dark"
        )

        return self.core.save_plotly_figure(fig, "ocounter_by_tag.html")
