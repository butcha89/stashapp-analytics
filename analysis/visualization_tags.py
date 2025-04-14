"""
Visualization Tags Module

Dieses Modul enthält Visualisierungen rund um Tags – insbesondere
deren Häufigkeit, Verteilungen, Korrelationen und potenzielle
Zusammenhänge mit anderen Attributen.
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


class TagVisualization:
    """
    Klasse zur Erstellung von Tag-bezogenen Visualisierungen.
    """

    def __init__(self, core: VisualizationCore):
        self.core = core
        self.stats_module = core.stats_module
        self.api = core.api
        self.config = core.config
        logger.info("Tag-Visualisierungsmodul initialisiert.")

    def create_tag_frequency_barplot(self, top_n: int = 30) -> Optional[str]:
        """
        Erstellt ein Balkendiagramm der häufigsten Tags in Szenen.

        Args:
            top_n: Anzahl der häufigsten Tags, die angezeigt werden sollen

        Returns:
            Pfad zur gespeicherten Grafik
        """
        scenes: List[Scene] = self.stats_module.get_all_scenes()
        tag_counts = {}

        for scene in scenes:
            if scene.tags:
                for tag in scene.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if not tag_counts:
            logger.warning("Keine Tag-Daten gefunden.")
            return None

        df = pd.DataFrame(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:top_n],
                          columns=['Tag', 'Anzahl'])

        fig = px.bar(
            df,
            x='Anzahl',
            y='Tag',
            orientation='h',
            title=f'Top {top_n} Tags nach Häufigkeit',
            template='plotly_dark'
        )

        return self.core.save_plotly_figure(fig, "tag_frequencies.html")

    def create_tag_heatmap(self, min_occurrence: int = 10) -> Optional[str]:
        """
        Erstellt eine Heatmap für gemeinsame Vorkommen von Tags in Szenen.

        Args:
            min_occurrence: Minimale Anzahl, damit ein Tag berücksichtigt wird

        Returns:
            Pfad zur gespeicherten Grafik
        """
        scenes: List[Scene] = self.stats_module.get_all_scenes()
        tag_sets = [set(scene.tags) for scene in scenes if scene.tags]

        from collections import Counter
        from itertools import combinations

        tag_counter = Counter(tag for tags in tag_sets for tag in tags)
        filtered_tags = {tag for tag, count in tag_counter.items() if count >= min_occurrence}

        co_occurrence = {}
        for tags in tag_sets:
            relevant = filtered_tags & tags
            for a, b in combinations(sorted(relevant), 2):
                co_occurrence[(a, b)] = co_occurrence.get((a, b), 0) + 1

        if not co_occurrence:
            logger.warning("Nicht genügend Tag-Kombinationen für Heatmap.")
            return None

        co_df = pd.DataFrame([
            {"Tag1": a, "Tag2": b, "Häufigkeit": count}
            for (a, b), count in co_occurrence.items()
        ])

        fig = px.density_heatmap(
            co_df,
            x="Tag1",
            y="Tag2",
            z="Häufigkeit",
            title="Tag-Kombinationen Heatmap",
            template="plotly_dark",
            color_continuous_scale="Viridis"
        )

        return self.core.save_plotly_figure(fig, "tag_heatmap.html")
