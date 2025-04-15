"""
Visualization Module - Hauptmodul

Dieses Modul dient als Einstiegspunkt für alle Visualisierungsfunktionen und integriert
die spezialisierten Visualisierungsmodule. Es bietet eine einheitliche Schnittstelle zur
Erstellung verschiedener Arten von Visualisierungen basierend auf StashApp-Daten.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple

# Interne Importe
from core.stash_api import StashAPI
from core.data_models import Performer, Scene
from core.utils import ensure_dir
from analysis.statistics_module import StatisticsModule
from management.config_manager import ConfigManager

# Import der spezialisierten Visualisierungsmodule
from analysis.visualization_core import VisualizationCore
from analysis.visualization_performer import PerformerVisualization
from analysis.visualization_scenes import SceneVisualization
from analysis.visualization_correlations import CorrelationVisualization
from analysis.visualization_tags import TagVisualization
from analysis.visualization_o_counter import OCounterVisualization

# Logger konfigurieren
logger = logging.getLogger(__name__)

class VisualizationModule:
    """
    Hauptklasse zur Integration aller Visualisierungsfunktionen.
    
    Diese Klasse dient als Einstiegspunkt für die Erstellung verschiedener
    Visualisierungen und koordiniert den Zugriff auf die spezialisierten
    Visualisierungsmodule.
    """
    
    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        """
        Initialisiert das Visualisierungs-Hauptmodul und alle Submodule.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.stats_module = stats_module
        self.config = config
        
        # Basiskonfiguration laden
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')
        self.visualization_dir = self.config.get('Output', 'visualization_dir', 
                                                fallback=os.path.join(self.output_dir, 'graphs'))
        
        # Sicherstellen, dass das Ausgabeverzeichnis existiert
        ensure_dir(self.visualization_dir)
        
        # Kernmodul initialisieren
        self.core = VisualizationCore(api, stats_module, config)
        
        # Spezialisierte Visualisierungsmodule initialisieren
        self.performer_viz = PerformerVisualization(self.core)
        self.scene_viz = SceneVisualization(self.core)
        self.correlation_viz = CorrelationVisualization(self.core)
        self.tag_viz = TagVisualization(self.core)
        self.o_counter_viz = OCounterVisualization(self.core)
        
        logger.info("Visualisierungs-Hauptmodul initialisiert")
    
    def create_all_visualizations(self) -> List[str]:
        """
        Erstellt alle verfügbaren Visualisierungen und speichert sie im Ausgabeverzeichnis.
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle alle Visualisierungen...")
        
        # Stelle sicher, dass Statistiken verfügbar sind
        if not hasattr(self.stats_module, 'performer_stats') or not self.stats_module.performer_stats:
            logger.warning("Keine Performer-Statistiken verfügbar. Berechne Statistiken...")
            self.stats_module.calculate_all_statistics()
        
        # Liste der erstellten Visualisierungen
        created_visualizations = []
        
        # Performer-Visualisierungen
        logger.info("Erstelle Performer-Visualisierungen...")
        created_visualizations.extend(self.performer_viz.create_cup_size_visualizations())
        created_visualizations.extend(self.performer_viz.create_bmi_visualizations())
        created_visualizations.extend(self.performer_viz.create_age_visualizations())
        created_visualizations.extend(self.performer_viz.create_rating_visualizations())
        
        # Tag-Visualisierungen
        logger.info("Erstelle Tag-Visualisierungen...")
        created_visualizations.extend(self.tag_viz.create_tag_visualizations())
        
        # Szenen-Visualisierungen
        logger.info("Erstelle Szenen-Visualisierungen...")
        created_visualizations.extend(self.scene_viz.create_scene_rating_visualizations())
        created_visualizations.extend(self.scene_viz.create_time_series_visualizations())
        
        # O-Counter-Visualisierungen
        logger.info("Erstelle O-Counter-Visualisierungen...")
        created_visualizations.extend(self.o_counter_viz.create_o_counter_visualizations())
        
        # Korrelations-Visualisierungen
        logger.info("Erstelle Korrelations-Visualisierungen...")
        created_visualizations.extend(self.correlation_viz.create_correlation_visualizations())
        
        total_visualizations = len(created_visualizations)
        logger.info(f"{total_visualizations} Visualisierungen erfolgreich erstellt")
        
        return created_visualizations
    
    def create_visualization_category(self, category: str) -> List[str]:
        """
        Erstellt nur Visualisierungen einer bestimmten Kategorie.
        
        Args:
            category: Die Kategorie der zu erstellenden Visualisierungen 
                     ('performer', 'scene', 'tag', 'o_counter', 'correlation')
            
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info(f"Erstelle Visualisierungen der Kategorie '{category}'...")
        
        # Stelle sicher, dass Statistiken verfügbar sind
        if not hasattr(self.stats_module, 'performer_stats') or not self.stats_module.performer_stats:
            logger.warning("Keine Performer-Statistiken verfügbar. Berechne Statistiken...")
            self.stats_module.calculate_all_statistics()
        
        # Wähle die entsprechende Visualisierungskategorie
        if category.lower() == 'performer':
            return self._create_performer_visualizations()
        elif category.lower() == 'scene':
            return self._create_scene_visualizations()
        elif category.lower() == 'tag':
            return self.tag_viz.create_tag_visualizations()
        elif category.lower() == 'o_counter':
            return self.o_counter_viz.create_o_counter_visualizations()
        elif category.lower() == 'correlation':
            return self.correlation_viz.create_correlation_visualizations()
        else:
            logger.warning(f"Unbekannte Visualisierungskategorie: '{category}'")
            return []
    
    def _create_performer_visualizations(self) -> List[str]:
        """
        Erstellt alle Performer-bezogenen Visualisierungen.
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        visualizations = []
        visualizations.extend(self.performer_viz.create_cup_size_visualizations())
        visualizations.extend(self.performer_viz.create_bmi_visualizations())
        visualizations.extend(self.performer_viz.create_age_visualizations())
        visualizations.extend(self.performer_viz.create_rating_visualizations())
        return visualizations
    
    def _create_scene_visualizations(self) -> List[str]:
        """
        Erstellt alle Szenen-bezogenen Visualisierungen.
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        visualizations = []
        visualizations.extend(self.scene_viz.create_scene_rating_visualizations())
        visualizations.extend(self.scene_viz.create_time_series_visualizations())
        return visualizations
    
    def create_custom_visualization(self, 
                                  visualization_type: str, 
                                  params: Dict[str, Any] = None) -> Optional[str]:
        """
        Erstellt eine benutzerdefinierte Visualisierung mit angegebenen Parametern.
        
        Args:
            visualization_type: Der Typ der zu erstellenden Visualisierung
            params: Parameter für die Visualisierung
            
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        if params is None:
            params = {}
            
        logger.info(f"Erstelle benutzerdefinierte Visualisierung vom Typ '{visualization_type}'...")
        
        try:
            # Je nach Visualisierungstyp an das entsprechende Modul delegieren
            if visualization_type.startswith('performer_'):
                return self.performer_viz.create_custom_visualization(visualization_type, params)
            elif visualization_type.startswith('scene_'):
                return self.scene_viz.create_custom_visualization(visualization_type, params)
            elif visualization_type.startswith('tag_'):
                return self.tag_viz.create_custom_visualization(visualization_type, params)
            elif visualization_type.startswith('o_counter_'):
                return self.o_counter_viz.create_custom_visualization(visualization_type, params)
            elif visualization_type.startswith('correlation_'):
                return self.correlation_viz.create_custom_visualization(visualization_type, params)
            else:
                logger.warning(f"Unbekannter Visualisierungstyp: '{visualization_type}'")
                return None
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der benutzerdefinierten Visualisierung: {str(e)}")
            return None
