"""
Visualization Core Module

Dieses Modul bietet die grundlegenden Funktionen und gemeinsamen Komponenten
für alle Visualisierungsmodule. Es dient als Basis für spezialisierte
Visualisierungsmodule und kümmert sich um Konfigurationsmanagement,
Diagrammspeicherung, Farbpaletten und Stildefinitionen.
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

class VisualizationCore:
    """
    Kernklasse für Visualisierungen mit gemeinsamen Funktionen und Konfigurationen.
    
    Diese Klasse stellt die grundlegenden Funktionen für alle Visualisierungsmodule
    bereit und verwaltet die gemeinsame Konfiguration, Stile und Speichermethoden.
    """
    
    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        """
        Initialisiert das Visualisierungs-Kernmodul.
        
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
        self.interactive_mode = self.config.getboolean('Visualization', 'interactive_mode', fallback=True)
        self.save_interactive = self.config.getboolean('Visualization', 'save_interactive', fallback=True)
        
        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        ensure_dir(self.visualization_dir)
        
        # Seaborn-Style setzen
        self._configure_styles()
        
        # Farbpaletten definieren
        self._define_color_palettes()
        
        logger.info("Visualisierungs-Kernmodul initialisiert")
    
    def _configure_styles(self) -> None:
        """
        Konfiguriert die Matplotlib- und Seaborn-Stile.
        """
        # Seaborn-Style
        style = "whitegrid" if self.show_grid else "white"
        sns.set_style(style)
        sns.set_context("notebook", font_scale=1.1)
        
        # Matplotlib globale Einstellungen
        plt.rcParams['figure.figsize'] = (self.figure_width, self.figure_height)
        plt.rcParams['font.size'] = self.label_fontsize
        plt.rcParams['axes.labelsize'] = self.label_fontsize
        plt.rcParams['axes.titlesize'] = self.title_fontsize
        plt.rcParams['xtick.labelsize'] = self.label_fontsize - 2
        plt.rcParams['ytick.labelsize'] = self.label_fontsize - 2
        plt.rcParams['legend.fontsize'] = self.legend_fontsize
        plt.rcParams['figure.titlesize'] = self.title_fontsize + 2
        
        # Weitere Einstellungen
        plt.rcParams['axes.grid'] = self.show_grid
        plt.rcParams['axes.axisbelow'] = True  # Grid hinter den Daten
        plt.rcParams['figure.autolayout'] = True  # Automatisches Layout
        
        # Sorge für bessere Darstellung bei hochauflösenden Displays
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = self.image_dpi
    
    def _define_color_palettes(self) -> None:
        """
        Definiert verschiedene Farbpaletten für die Visualisierungen.
        """
        # Farbpaletten für verschiedene Visualisierungstypen
        self.palettes = {
            'categorical': sns.color_palette(self.color_scheme, 10),
            'sequential': sns.color_palette(f"{self.color_scheme}_r", 10),
            'diverging': sns.diverging_palette(240, 10, n=10),
            'pastel': sns.color_palette("pastel", 10),
            'dark': sns.color_palette("dark", 10),
            'bright': sns.color_palette("bright", 10),
            'muted': sns.color_palette("muted", 10),
            'colorblind': sns.color_palette("colorblind", 10)
        }
        
        # Aufgabenspezifische Paletten
        self.palettes['cup_sizes'] = sns.color_palette("coolwarm", 10)  # von klein nach groß
        self.palettes['bmi'] = sns.color_palette("RdYlGn_r", 4)  # für BMI-Kategorien
        self.palettes['ratings'] = sns.color_palette("YlOrRd", 5)  # für Bewertungen
        self.palettes['age'] = sns.color_palette("viridis", 6)  # für Altersgruppen
        self.palettes['o_counter'] = sns.color_palette("plasma", 10)  # für O-Counter
        self.palettes['correlation'] = sns.diverging_palette(240, 10, as_cmap=True)  # für Korrelationen
    
    def save_figure(self, fig, filename: str, tight_layout: bool = True) -> str:
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
    
    def save_plotly_figure(self, fig, filename: str) -> str:
        """
        Speichert eine Plotly-Figur im Ausgabeverzeichnis.
        
        Args:
            fig: Plotly-Figur
            filename: Dateiname (ohne Pfad und Erweiterung)
            
        Returns:
            str: Vollständiger Pfad zur gespeicherten Datei
        """
        if not self.save_interactive:
            return ""
            
        # Pfad zur HTML-Ausgabedatei erstellen
        html_path = os.path.join(self.visualization_dir, f"{filename}.html")
        
        # Plotly-Figur als HTML speichern
        try:
            fig.write_html(html_path)
            logger.info(f"Interaktive Visualisierung gespeichert: {html_path}")
            
            # Optional auch als statisches Bild speichern
            try:
                img_path = os.path.join(self.visualization_dir, f"{filename}.{self.image_format}")
                fig.write_image(img_path, scale=2)
                logger.info(f"Statisches Bild der interaktiven Visualisierung gespeichert: {img_path}")
            except Exception as img_error:
                logger.warning(f"Konnte kein statisches Bild speichern: {str(img_error)}")
            
            return html_path
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Plotly-Visualisierung '{filename}': {str(e)}")
            return ""
    
    def create_figure(self, width_factor: float = 1.0, height_factor: float = 1.0) -> plt.Figure:
        """
        Erstellt eine neue Matplotlib-Figur mit den konfigurierten Abmessungen.
        
        Args:
            width_factor: Multiplikator für die Breite
            height_factor: Multiplikator für die Höhe
            
        Returns:
            plt.Figure: Neue Matplotlib-Figur
        """
        width = self.figure_width * width_factor
        height = self.figure_height * height_factor
        return plt.figure(figsize=(width, height))
    
    def format_axes(self, ax, title: str, xlabel: str = "", ylabel: str = "",
                   xticks_rotation: int = 0, yticks_rotation: int = 0) -> None:
        """
        Formatiert die Achsen einer Matplotlib-Figur mit den konfigurierten Einstellungen.
        
        Args:
            ax: Matplotlib-Axes-Objekt
            title: Diagrammtitel
            xlabel: Beschriftung der X-Achse
            ylabel: Beschriftung der Y-Achse
            xticks_rotation: Rotation der X-Achsenbeschriftungen in Grad
            yticks_rotation: Rotation der Y-Achsenbeschriftungen in Grad
        """
        # Titel und Achsenbeschriftungen
        ax.set_title(title, fontsize=self.title_fontsize)
        ax.set_xlabel(xlabel, fontsize=self.label_fontsize)
        ax.set_ylabel(ylabel, fontsize=self.label_fontsize)
        
        # Achsenbeschriftungen rotieren
        plt.setp(ax.get_xticklabels(), rotation=xticks_rotation, ha='right' if xticks_rotation > 0 else 'center')
        plt.setp(ax.get_yticklabels(), rotation=yticks_rotation)
        
        # Grid anzeigen, falls konfiguriert
        ax.grid(self.show_grid, alpha=0.3)
    
    def add_value_labels(self, ax, bars, fontsize: int = None, fmt: str = "{:.1f}", 
                         xpos: str = 'center', offset_y: float = 3) -> None:
        """
        Fügt Wertbeschriftungen zu Balkendiagrammen hinzu.
        
        Args:
            ax: Matplotlib-Axes-Objekt
            bars: Die Balkenobjekte aus dem Balkendiagramm
            fontsize: Schriftgröße (falls None, wird label_fontsize - 2 verwendet)
            fmt: Formatierungsstring für die Werte
            xpos: Position der Beschriftung ('center', 'left', 'right')
            offset_y: Vertikaler Offset für die Beschriftung
        """
        if fontsize is None:
            fontsize = self.label_fontsize - 2
            
        # Mapping von xpos auf horizontale Ausrichtung
        ha_dict = {'center': 'center', 'left': 'left', 'right': 'right'}
        
        # Werte zu jedem Balken hinzufügen
        for bar in bars:
            height = bar.get_height()
            x_pos = bar.get_x() + (bar.get_width() / 2 if xpos == 'center' else 
                                 (bar.get_width() * 0.05 if xpos == 'left' else 
                                  bar.get_width() * 0.95))
            
            y_pos = height + offset_y
            
            # Textformatierung
            ax.annotate(fmt.format(height),
                       xy=(x_pos, height),
                       xytext=(0, offset_y),
                       textcoords="offset points",
                       ha=ha_dict.get(xpos, 'center'), 
                       va='bottom',
                       fontsize=fontsize)
    
    def filter_outliers(self, data: List[float], method: str = 'IQR', 
                      threshold: float = 1.5) -> List[float]:
        """
        Filtert Ausreißer aus einer Datenliste.
        
        Args:
            data: Liste von Datenwerten
            method: Methode zur Ausreißererkennung ('IQR' oder 'zscore')
            threshold: Schwellenwert für die Ausreißererkennung
            
        Returns:
            List[float]: Gefilterte Datenliste ohne Ausreißer
        """
        if len(data) < 4:  # Zu wenig Daten für sinnvolle Filterung
            return data
            
        if method.upper() == 'IQR':
            # Interquartile Range Methode
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            return [x for x in data if lower_bound <= x <= upper_bound]
            
        elif method.upper() == 'ZSCORE':
            # Z-Score Methode
            mean = np.mean(data)
            std = np.std(data)
            
            if std == 0:  # Verhindere Division durch Null
                return data
                
            return [x for x in data if abs((x - mean) / std) <= threshold]
            
        else:
            logger.warning(f"Unbekannte Ausreißererkennungsmethode: {method}")
            return data
    
    def get_color_for_value(self, value: float, vmin: float, vmax: float, 
                          cmap_name: str = None) -> Tuple[float, float, float, float]:
        """
        Gibt eine Farbe basierend auf einem Wert in einem Bereich zurück.
        
        Args:
            value: Der Wert, für den die Farbe bestimmt werden soll
            vmin: Untere Grenze des Wertebereichs
            vmax: Obere Grenze des Wertebereichs
            cmap_name: Name der Farbpalette (falls None, wird color_scheme verwendet)
            
        Returns:
            Tuple[float, float, float, float]: RGBA-Farbtupel
        """
        if cmap_name is None:
            cmap_name = self.color_scheme
            
        # Normalisiere den Wert auf den Bereich [0, 1]
        if vmax == vmin:
            normalized = 0.5  # Vermeide Division durch Null
        else:
            normalized = (value - vmin) / (vmax - vmin)
        
        # Begrenze auf [0, 1]
        normalized = max(0, min(1, normalized))
        
        # Holen der Farbpalette und Konvertierung des Werts in eine Farbe
        cmap = plt.get_cmap(cmap_name)
        return cmap(normalized)
    
    def get_performer_data_as_df(self) -> pd.DataFrame:
        """
        Konvertiert die Performer-Daten in einen pandas DataFrame für einfachere Analyse.
        
        Returns:
            pd.DataFrame: DataFrame mit Performer-Daten
        """
        performer_data = []
        for p in self.stats_module.performers:
            # Grundlegende Daten extrahieren
            performer_dict = {
                'id': p.id,
                'name': p.name,
                'cup_size': p.cup_size,
                'cup_numeric': p.cup_numeric,
                'rating': p.rating100,
                'bmi': p.bmi,
                'age': p.age,
                'height': p.height_cm,
                'weight': p.weight,
                'o_counter': p.o_counter,
                'favorite': p.favorite,
                'bmi_category': p.bmi_category,
                'scene_count': p.scene_count
            }
            performer_data.append(performer_dict)
        
        return pd.DataFrame(performer_data)
    
    def get_scene_data_as_df(self) -> pd.DataFrame:
        """
        Konvertiert die Szenen-Daten in einen pandas DataFrame für einfachere Analyse.
        
        Returns:
            pd.DataFrame: DataFrame mit Szenen-Daten
        """
        scene_data = []
        for s in self.stats_module.scenes:
            scene_dict = {
                'id': s.id,
                'title': s.title,
                'date': s.date,
                'rating': s.rating100,
                'o_counter': s.o_counter,
                'studio': s.studio_name,
                'performer_count': len(s.performer_ids),
                'duration': s.duration
            }
            
            # Füge erweiterte Attribute hinzu, falls verfügbar
            if hasattr(s, 'avg_cup_size'):
                scene_dict['avg_cup_size'] = s.avg_cup_size
                
            if hasattr(s, 'avg_age'):
                scene_dict['avg_performer_age'] = s.avg_age
                
            if hasattr(s, 'avg_bmi'):
                scene_dict['avg_bmi'] = s.avg_bmi
                
            scene_data.append(scene_dict)
        
        # Konvertiere zu DataFrame
        df = pd.DataFrame(scene_data)
        
        # Konvertiere Datum zu datetime, falls vorhanden
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
        return df
