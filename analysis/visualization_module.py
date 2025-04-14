"""
Visualization Module

Dieses Modul ist verantwortlich für die Erstellung von Visualisierungen und Diagrammen
basierend auf den berechneten Statistiken aus dem StatisticsModule.
Es nutzt Matplotlib, Seaborn und Plotly für verschiedene Arten von Visualisierungen.
"""

import os
import json
import math
import time
import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as ticker
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Interne Importe
from core.stash_api import StashAPI
from core.data_models import Performer, Scene
from core.utils import ensure_dir
from analysis.statistics_module import StatisticsModule
from management.config_manager import ConfigManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class VisualizationModule:
    """
    Klasse zur Erstellung von Visualisierungen aus statistischen Daten.
    
    Diese Klasse ist verantwortlich für:
    - Erstellung von Diagrammen für verschiedene Statistiken
    - Anpassung der Visualisierungsformate und -stile
    - Speicherung der erzeugten Visualisierungen
    """
    
    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        """
        Initialisiert das Visualisierungs-Modul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.stats_module = stats_module
        self.config = config
        
        # Lade Konfigurationsoptionen für Visualisierungen
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')
        self.visualization_dir = self.config.get('Visualization', 'visualization_dir', 
                                                fallback=os.path.join(self.output_dir, 'graphs'))
        
        # Einstellungen für Visualisierungen
        self.image_format = self.config.get('Visualization', 'image_format', fallback='png')
        self.image_dpi = self.config.getint('Visualization', 'image_dpi', fallback=300)
        self.color_scheme = self.config.get('Visualization', 'color_scheme', fallback='viridis')
        
        # Diagrammgrößen
        self.figure_height = self.config.getfloat('Visualization', 'figure_height', fallback=6)
        self.figure_width = self.config.getfloat('Visualization', 'figure_width', fallback=10)
        
        # Schriftgrößen
        self.title_fontsize = self.config.getint('Visualization', 'title_fontsize', fallback=16)
        self.label_fontsize = self.config.getint('Visualization', 'label_fontsize', fallback=12)
        self.legend_fontsize = self.config.getint('Visualization', 'legend_fontsize', fallback=10)
        
        # Weitere Einstellungen
        self.show_grid = self.config.getboolean('Visualization', 'show_grid', fallback=True)
        
        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        ensure_dir(self.visualization_dir)
        
        # Seaborn-Style setzen
        sns.set_style("whitegrid" if self.show_grid else "white")
        sns.set_context("notebook", font_scale=1.1)
        
        # Farbpaletten definieren
        self.palettes = {
            'categorical': sns.color_palette(self.color_scheme, 10),
            'sequential': sns.color_palette(f"{self.color_scheme}_r", 10),
            'diverging': sns.diverging_palette(240, 10, n=10),
            'pastel': sns.color_palette("pastel", 10)
        }
        
        logger.info("Visualisierungs-Modul initialisiert")
    
    def create_all_visualizations(self) -> List[str]:
        """
        Erstellt alle Visualisierungen und speichert sie im Ausgabeverzeichnis.
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Visualisierungen...")
        
        # Stelle sicher, dass Statistiken verfügbar sind
        if not hasattr(self.stats_module, 'performer_stats') or not self.stats_module.performer_stats:
            logger.warning("Keine Performer-Statistiken verfügbar. Berechne Statistiken...")
            self.stats_module.calculate_all_statistics()
        
        # Liste der erstellten Visualisierungen
        created_visualizations = []
        
        # Performer-Visualisierungen
        created_visualizations.extend(self._create_cup_size_visualizations())
        created_visualizations.extend(self._create_bmi_visualizations())
        created_visualizations.extend(self._create_age_visualizations())
        created_visualizations.extend(self._create_rating_visualizations())
        created_visualizations.extend(self._create_tag_visualizations())
        
        # Szenen-Visualisierungen
        created_visualizations.extend(self._create_scene_rating_visualizations())
        created_visualizations.extend(self._create_o_counter_visualizations())
        created_visualizations.extend(self._create_time_series_visualizations())
        
        # Korrelations-Visualisierungen
        created_visualizations.extend(self._create_correlation_visualizations())
        
        # Dashboard-Übersicht
        created_visualizations.extend(self._create_dashboard_preview())
        
        logger.info(f"{len(created_visualizations)} Visualisierungen erfolgreich erstellt")
        return created_visualizations
    
    def _save_figure(self, fig, filename: str, tight_layout: bool = True) -> str:
        """
        Speichert eine Matplotlib-Figur im Ausgabeverzeichnis.
        
        Args:
            fig: Matplotlib-Figur
            filename: Dateiname (ohne Pfad und Erweiterung)
            tight_layout: Ob tight_layout angewendet werden soll
            
        Returns:
            str: Vollständiger Pfad zur gespeicherten Datei
        """
        # Pfad zur Ausgabedatei erstellen
        file_path = os.path.join(self.visualization_dir, f"{filename}.{self.image_format}")
        
        # Layout optimieren, falls gewünscht
        if tight_layout:
            fig.tight_layout()
        
        # Figur speichern
        try:
            fig.savefig(file_path, dpi=self.image_dpi, bbox_inches='tight')
            logger.info(f"Visualisierung gespeichert: {file_path}")
            plt.close(fig)
            return file_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Visualisierung '{filename}': {str(e)}")
            plt.close(fig)
            return ""
    
    def _save_plotly_figure(self, fig, filename: str) -> str:
        """
        Speichert eine Plotly-Figur im Ausgabeverzeichnis.
        
        Args:
            fig: Plotly-Figur
            filename: Dateiname (ohne Pfad und Erweiterung)
            
        Returns:
            str: Vollständiger Pfad zur gespeicherten Datei
        """
        # Pfad zur Ausgabedatei erstellen
        file_path = os.path.join(self.visualization_dir, f"{filename}.html")
        
        # Plotly-Figur als HTML speichern
        try:
            fig.write_html(file_path)
            
            # Optional auch als Bild speichern
            img_path = os.path.join(self.visualization_dir, f"{filename}.{self.image_format}")
            fig.write_image(img_path)
            
            logger.info(f"Interaktive Visualisierung gespeichert: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Plotly-Visualisierung '{filename}': {str(e)}")
            return ""
    
    def _create_cup_size_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen für Cup-Größen-Statistiken.
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Cup-Größen-Visualisierungen...")
        visualizations = []
        
        # Überprüfe, ob Cup-Größen-Statistiken verfügbar sind
        if not hasattr(self.stats_module, 'cup_size_groups') or not self.stats_module.cup_size_groups:
            logger.warning("Keine Cup-Größen-Statistiken verfügbar")
            return visualizations
        
        # Cup-Größen-Verteilung
        try:
            # Daten vorbereiten
            cup_distribution = self.stats_module.performer_stats.cup_distribution
            if not cup_distribution:
                return visualizations
                
            # Sortiere die Cup-Größen (alphanumerisch)
            sorted_cups = sorted(cup_distribution.keys(), key=lambda x: (len(x), x))
            counts = [cup_distribution[cup] for cup in sorted_cups]
            
            # Erstelle das Balkendiagramm
            fig, ax = plt.subplots(figsize=(self.figure_width, self.figure_height))
            
            bars = ax.bar(sorted_cups, counts, color=self.palettes['categorical'])
            
            # Beschriftungen hinzufügen
            ax.set_title('Verteilung der Cup-Größen', fontsize=self.title_fontsize)
            ax.set_xlabel('Cup-Größe', fontsize=self.label_fontsize)
            ax.set_ylabel('Anzahl', fontsize=self.label_fontsize)
            
            # Zahlen über den Balken
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
            
            # Diagramm speichern
            path = self._save_figure(fig, "cup_size_distribution")
            if path:
                visualizations.append(path)
            
            # Erstelle ein Kuchendiagramm für die Cup-Größen
            fig, ax = plt.subplots(figsize=(self.figure_width, self.figure_height))
            
            # Berechne Prozentsätze
            total = sum(counts)
            percentages = [count / total * 100 for count in counts]
            
            # Kuchendiagramm mit Prozentangaben
            patches, texts, autotexts = ax.pie(counts, labels=sorted_cups, autopct='%1.1f%%',
                                              colors=self.palettes['pastel'], startangle=90)
            
            # Formatierung
            for text in texts:
                text.set_fontsize(self.label_fontsize)
            for autotext in autotexts:
                autotext.set_fontsize(self.label_fontsize - 2)
                autotext.set_color('white')
            
            ax.set_title('Prozentuale Verteilung der Cup-Größen', fontsize=self.title_fontsize)
            ax.axis('equal')  # Sorgt für ein kreisförmiges Diagramm
            
            # Diagramm speichern
            path = self._save_figure(fig, "cup_size_pie_chart")
            if path:
                visualizations.append(path)
            
            # Interaktives Plotly-Diagramm für Cup-Größen
            df = pd.DataFrame({
                'Cup-Größe': sorted_cups,
                'Anzahl': counts,
                'Prozent': percentages
            })
            
            fig = px.bar(df, x='Cup-Größe', y='Anzahl', text='Anzahl',
                         color='Cup-Größe', color_discrete_sequence=px.colors.qualitative.Pastel)
            
            fig.update_layout(
                title='Interaktive Darstellung der Cup-Größen-Verteilung',
                xaxis_title='Cup-
