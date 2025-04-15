"""
Data Processor Module

Dieses Modul ist verantwortlich für die Verarbeitung, Transformation und
Aufbereitung der Rohdaten aus StashApp für die weitere Analyse.
Es dient als zentrale Datenschnittstelle zwischen der API und den Analysemodulen.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import concurrent.futures
import pandas as pd
import numpy as np

from core.stash_api import StashAPI
from core.data_models import Performer, Scene
from core.utils import ensure_dir

# Logger konfigurieren
logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Verarbeitet und transformiert Rohdaten aus der StashApp API
    für die weitere Analyse und Statistikgenerierung.
    """
    
    def __init__(self, api: StashAPI, max_workers: int = 4):
        """
        Initialisiert den Datenprozessor.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            max_workers: Maximale Anzahl paralleler Worker für die Datenverarbeitung
        """
        self.api = api
        self.max_workers = max_workers
        
        # Daten-Container
        self.performers = []
        self.scenes = []
        self.raw_performers = []
        self.raw_scenes = []
        self.raw_tags = []
        
        # Hilfsvariablen für die Datenverarbeitung
        self.performer_map = {}  # id -> Performer
        self.scene_map = {}  # id -> Scene
        self.tag_map = {}  # id -> Tag
        
        logger.info("DataProcessor initialisiert")
    
    def load_all_data(self) -> Tuple[int, int, int]:
        """
        Lädt alle relevanten Daten aus der StashApp API.
        
        Returns:
            Tuple[int, int, int]: Anzahl von (Performern, Szenen, Tags)
        """
        logger.info("Lade Daten von StashApp...")
        
        # Daten laden
        self.raw_performers = self.api.get_all_performers()
        self.raw_scenes = self.api.get_all_scenes()
        self.raw_tags = self.api.get_all_tags()
        
        # Daten konvertieren und aufbereiten
        self._process_performers()
        self._process_scenes()
        self._process_tags()
        
        # Zusätzliche Datenverknüpfungen
        self._link_performers_to_scenes()
        self._calculate_custom_metrics()
        
        logger.info(f"Daten geladen: {len(self.performers)} Performer, {len(self.scenes)} Szenen, {len(self.raw_tags)} Tags")
        return len(self.performers), len(self.scenes), len(self.raw_tags)
    
    def _process_performers(self) -> None:
        """
        Verarbeitet die rohen Performer-Daten und erstellt Performer-Objekte.
        """
        logger.info("Verarbeite Performer-Daten...")
        
        # Performer-Objekte erstellen
        self.performers = [Performer(p) for p in self.raw_performers]
        
        # Performer-Map erstellen
        self.performer_map = {p.id: p for p in self.performers}
        
        logger.info(f"{len(self.performers)} Performer verarbeitet")
    
    def _process_scenes(self) -> None:
        """
        Verarbeitet die rohen Szenen-Daten und erstellt Szenen-Objekte.
        """
        logger.info("Verarbeite Szenen-Daten...")
        
        # Szenen-Objekte erstellen
        self.scenes = []
        
        # Verarbeite Szenen für effizienten Zugriff in ggf. mehreren Threads
        if self.max_workers > 1 and len(self.raw_scenes) > 100:
            # Parallele Verarbeitung für große Datenmengen
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                self.scenes = list(executor.map(
                    lambda s: Scene(s, self.performers), 
                    self.raw_scenes
                ))
        else:
            # Sequentielle Verarbeitung
            self.scenes = [Scene(s, self.performers) for s in self.raw_scenes]
        
        # Szenen-Map erstellen
        self.scene_map = {s.id: s for s in self.scenes}
        
        logger.info(f"{len(self.scenes)} Szenen verarbeitet")
    
    def _process_tags(self) -> None:
        """
        Verarbeitet die rohen Tag-Daten für einfacheren Zugriff.
        """
        logger.info("Verarbeite Tag-Daten...")
        
        # Tag-Map erstellen
        self.tag_map = {tag['id']: tag for tag in self.raw_tags}
        
        logger.info(f"{len(self.tag_map)} Tags verarbeitet")
    
    def _link_performers_to_scenes(self) -> None:
        """
        Erstellt Verknüpfungen zwischen Performern und ihren Szenen.
        """
        logger.info("Verknüpfe Performer mit Szenen...")
        
        # Erstelle für jeden Performer eine Liste seiner Szenen
        performer_scenes = {p.id: [] for p in self.performers}
        
        for scene in self.scenes:
            for performer_id in scene.performer_ids:
                if performer_id in performer_scenes:
                    performer_scenes[performer_id].append(scene)
        
        # Verknüpfe die Szenen mit dem Performer-Objekt
        for performer in self.performers:
            performer.scenes = performer_scenes.get(performer.id, [])
            
            # Berechne zusätzliche Szenen-abhängige Metriken
            scene_count = len(performer.scenes)
            performer.scene_count = scene_count
            
            # Durchschnittliche Szenen-Bewertung
            if scene_count > 0:
                rated_scenes = [s for s in performer.scenes if s.rating100 is not None]
                if rated_scenes:
                    performer.avg_scene_rating = sum(s.rating100 for s in rated_scenes) / len(rated_scenes)
        
        logger.info("Performer-Szenen-Verknüpfungen erstellt")
    
    def _calculate_custom_metrics(self) -> None:
        """
        Berechnet benutzerdefinierte Metriken für Performer und Szenen.
        """
        logger.info("Berechne benutzerdefinierte Metriken...")
        
        # Berechne Metriken für Performer
        for performer in self.performers:
            # Beispiel: Cup-Größe zu BMI-Verhältnis für Proportionsanalyse
            if performer.cup_numeric and performer.cup_numeric > 0 and performer.bmi:
                performer.cup_to_bmi_ratio = performer.cup_numeric / performer.bmi
            
            # Beispiel: Bewertungs-Popularitäts-Verhältnis
            if performer.rating100 is not None and performer.scene_count > 0:
                performer.rating_to_scenes_ratio = performer.rating100 / performer.scene_count
        
        # Berechne Metriken für Szenen
        for scene in self.scenes:
            # Beispiel: Durchschnittliche Cup-Größe der Performer in der Szene
            scene_performers = [self.performer_map.get(p_id) for p_id in scene.performer_ids]
            scene_performers = [p for p in scene_performers if p]
            
            cup_sizes = [p.cup_numeric for p in scene_performers if p.cup_numeric and p.cup_numeric > 0]
            if cup_sizes:
                scene.avg_cup_size = sum(cup_sizes) / len(cup_sizes)
            
            # Beispiel: Szene hat favorisierten Performer
            scene.has_favorite = any(getattr(p, 'favorite', False) for p in scene_performers)
        
        logger.info("Benutzerdefinierte Metriken berechnet")
    
    def get_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        Erstellt pandas DataFrames aus den verarbeiteten Daten.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mit DataFrames für Performer, Szenen etc.
        """
        # Performer DataFrame
        performer_data = [p.to_dict() for p in self.performers]
        performer_df = pd.DataFrame(performer_data)
        
        # Szenen DataFrame
        scene_data = [s.to_dict() for s in self.scenes]
        scene_df = pd.DataFrame(scene_data)
        
        # Performer-Scene Beziehungen als DataFrame
        relationships = []
        for scene in self.scenes:
            for performer_id in scene.performer_ids:
                relationships.append({
                    'scene_id': scene.id,
                    'performer_id': performer_id,
                    'scene_rating': scene.rating100,
                    'scene_o_counter': scene.o_counter
                })
        relationship_df = pd.DataFrame(relationships)
        
        # Tag-Statistiken
        tag_stats = []
        for tag_id, tag in self.tag_map.items():
            tag_stats.append({
                'tag_id': tag_id,
                'name': tag.get('name', 'Unknown'),
                'scene_count': tag.get('scene_count', 0),
                'performer_count': tag.get('performer_count', 0)
            })
        tag_df = pd.DataFrame(tag_stats)
        
        return {
            'performers': performer_df,
            'scenes': scene_df,
            'relationships': relationship_df,
            'tags': tag_df
        }
    
    def filter_performers(self, **filter_args) -> List[Performer]:
        """
        Filtert Performer nach verschiedenen Kriterien.
        
        Args:
            **filter_args: Filter-Argumente, z.B. cup_size='D', favorite=True
            
        Returns:
            List[Performer]: Gefilterte Performer-Liste
        """
        filtered = self.performers
        
        for key, value in filter_args.items():
            filtered = [p for p in filtered if hasattr(p, key) and getattr(p, key) == value]
        
        return filtered
    
    def filter_scenes(self, **filter_args) -> List[Scene]:
        """
        Filtert Szenen nach verschiedenen Kriterien.
        
        Args:
            **filter_args: Filter-Argumente, z.B. o_counter=0, has_favorite=True
            
        Returns:
            List[Scene]: Gefilterte Szenen-Liste
        """
        filtered = self.scenes
        
        for key, value in filter_args.items():
            filtered = [s for s in filtered if hasattr(s, key) and getattr(s, key) == value]
        
        return filtered
