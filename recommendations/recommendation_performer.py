"""
Recommendation Performer Module

Dieses Modul implementiert Algorithmen zur Erzeugung von Performer-Empfehlungen
basierend auf verschiedenen Ähnlichkeitskriterien wie Cup-Größe, BMI-Verhältnisse,
Tag-Ähnlichkeiten und Nutzerpräferenzen.
"""

import os
import json
import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta

# Modulimporte
from core.stash_api import StashAPI
from core.data_models import Performer
from analysis.statistics_module import StatisticsModule
from management.config_manager import ConfigManager
from core.utils import save_json, ensure_dir

# Logger konfigurieren
logger = logging.getLogger(__name__)

class PerformerRecommendationModule:
    """
    Klasse zur Generierung von Performer-Empfehlungen basierend auf 
    verschiedenen Ähnlichkeitskriterien und Nutzerpräferenzen.
    """
    
    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        """
        Initialisiert das Performer-Empfehlungsmodul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.stats_module = stats_module
        self.config = config
        
        # Hole alle Performer aus dem Statistik-Modul
        self.performers = self.stats_module.performers if self.stats_module else []
        self.favorited_performers = [p for p in self.performers if p.favorite]
        
        # Lade Konfigurationsoptionen für Empfehlungen
        self.min_similarity_score = self.config.getfloat('Recommendations', 'min_similarity_score', fallback=0.75)
        self.max_recommendations = self.config.getint('Recommendations', 'max_recommendations', fallback=10)
        self.include_zero_counter = self.config.getboolean('Recommendations', 'include_zero_counter', fallback=True)
        
        # Gewichtungen für Ähnlichkeitskriterien
        self.weight_cup_size = self.config.getfloat('Recommendations', 'weight_cup_size', fallback=0.4)
        self.bmi_cup_size = self.config.getfloat('Recommendations', 'bmi_cup_size', fallback=0.2)
        self.height_cup_size = self.config.getfloat('Recommendations', 'height_cup_size', fallback=0.2)
        
        # Zusätzliche Empfehlungskriterien
        self.enable_tag_similarity = self.config.getboolean('Recommendations', 'enable_tag_similarity', fallback=True)
        self.weight_tag_similarity = self.config.getfloat('Recommendations', 'weight_tag_similarity', fallback=0.6)
        
        self.enable_scene_types = self.config.getboolean('Recommendations', 'enable_scene_types', fallback=True)
        self.weight_scene_types = self.config.getfloat('Recommendations', 'weight_scene_types', fallback=0.5)
        
        self.enable_age_range = self.config.getboolean('Recommendations', 'enable_age_range', fallback=True)
        self.age_range_tolerance = self.config.getint('Recommendations', 'age_range_tolerance', fallback=5)
        self.weight_age_similarity = self.config.getfloat('Recommendations', 'weight_age_similarity', fallback=0.4)
        
        self.enable_novelty = self.config.getboolean('Recommendations', 'enable_novelty', fallback=True)
        self.novelty_timeframe = self.config.getint('Recommendations', 'novelty_timeframe', fallback=30)
        self.weight_novelty = self.config.getfloat('Recommendations', 'weight_novelty', fallback=0.3)
        
        self.enable_scene_quality = self.config.getboolean('Recommendations', 'enable_scene_quality', fallback=True)
        self.min_scene_rating = self.config.getint('Recommendations', 'min_scene_rating', fallback=60)
        self.weight_scene_quality = self.config.getfloat('Recommendations', 'weight_scene_quality', fallback=0.5)
        
        self.enable_versatility = self.config.getboolean('Recommendations', 'enable_versatility', fallback=True)
        self.weight_versatility = self.config.getfloat('Recommendations', 'weight_versatility', fallback=0.4)
        
        self.enable_similar_to_favorites = self.config.getboolean('Recommendations', 'enable_similar_to_favorites', fallback=True)
        self.favorite_similarity_threshold = self.config.getfloat('Recommendations', 'favorite_similarity_threshold', fallback=0.7)
        self.weight_favorite_similarity = self.config.getfloat('Recommendations', 'weight_favorite_similarity', fallback=0.7)
        
        # Ausgabeverzeichnis
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')
        
        # Empfehlungskategorien und Ergebnisse
        self.recommendation_categories = {
            "similar_cup_size": [],
            "similar_proportions": [],
            "similar_tags": [],
            "similar_age": [],
            "high_quality": [],
            "novelty": [],
            "versatile": [],
            "similar_to_favorites": [],
            "zero_counter": []
        }
        
        # Top-Empfehlungen
        self.top_recommendations = []
        
        logger.info("Performer-Empfehlungsmodul initialisiert")
    
    def generate_recommendations(self, custom_weights: Dict[str, float] = None) -> Dict[str, List[Tuple[Performer, float]]]:
        """
        Generiert Performer-Empfehlungen basierend auf verschiedenen Kriterien.
        
        Args:
            custom_weights: Optionales Dictionary mit benutzerdefinierten Gewichtungen
            
        Returns:
            Dict[str, List[Tuple[Performer, float]]]: Empfehlungen nach Kategorien sortiert
        """
        logger.info("Generiere Performer-Empfehlungen...")
        
        # Anwenden benutzerdefinierter Gewichtungen, falls vorhanden
        if custom_weights:
            self._apply_custom_weights(custom_weights)
        
        # Keine Favoriten vorhanden? Verwende Top-bewertete Performer
        if not self.favorited_performers:
            logger.warning("Keine favorisierten Performer gefunden. Verwende Top-bewertete Performer als Referenz.")
            self.favorited_performers = sorted(
                [p for p in self.performers if p.rating100 is not None], 
                key=lambda p: p.rating100 or 0, 
                reverse=True
            )[:5]
        
        # Wenn immer noch keine Referenz-Performer vorhanden sind, können keine Empfehlungen generiert werden
        if not self.favorited_performers:
            logger.error("Keine Referenz-Performer gefunden. Empfehlungen können nicht generiert werden.")
            return {}
        
        # Kandidaten für Empfehlungen identifizieren
        candidates = self._get_recommendation_candidates()
        
        if not candidates:
            logger.warning("Keine geeigneten Kandidaten für Empfehlungen gefunden.")
            return {}
        
        # Empfehlungen nach verschiedenen Kriterien generieren
        self._generate_recommendations_by_cup_size(candidates)
        self._generate_recommendations_by_proportions(candidates)
        
        if self.enable_tag_similarity:
            self._generate_recommendations_by_tags(candidates)
        
        if self.enable_age_range:
            self._generate_recommendations_by_age(candidates)
        
        if self.enable_scene_quality:
            self._generate_recommendations_by_quality(candidates)
        
        if self.enable_novelty:
            self._generate_recommendations_by_novelty(candidates)
        
        if self.enable_versatility:
            self._generate_recommendations_by_versatility(candidates)
        
        if self.enable_similar_to_favorites:
            self._generate_recommendations_by_favorite_similarity(candidates)
        
        if self.include_zero_counter:
            self._generate_recommendations_for_zero_counter(candidates)
        
        # Top-Empfehlungen übergreifend erstellen
        self._generate_top_recommendations()
        
        logger.info("Performer-Empfehlungen erfolgreich generiert")
        
        return self.recommendation_categories
    
    def _apply_custom_weights(self, custom_weights: Dict[str, float]) -> None:
        """
        Wendet benutzerdefinierte Gewichtungen an.
        
        Args:
            custom_weights: Dictionary mit benutzerdefinierten Gewichtungen
        """
        for key, value in custom_weights.items():
            if hasattr(self, key) and isinstance(getattr(self, key), float):
                setattr(self, key, float(value))
                logger.debug(f"Benutzerdefinierte Gewichtung für {key} = {value}")
    
    def _get_recommendation_candidates(self) -> List[Performer]:
        """
        Identifiziert geeignete Kandidaten für Empfehlungen.
        
        Returns:
            List[Performer]: Liste geeigneter Kandidaten
        """
        # Alle Performer, die nicht favorisiert sind
        non_favorites = [p for p in self.performers if not p.favorite]
        
        # Grundlegende Filterung: Performer mit gültigen Cup-Größen
        candidates = [p for p in non_favorites if p.cup_numeric and p.cup_numeric > 0]
        
        # Wenn konfiguriert, entferne Performer mit O-Counter > 0
        if not self.include_zero_counter:
            candidates = [p for p in candidates if p.o_counter == 0]
        
        return candidates
    
    def _generate_recommendations_by_cup_size(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichen Cup-Größen.
        
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Cup-Größe...")
        
        # Berechne durchschnittliche Cup-Größe der Favoriten
        fav_cup_sizes = [p.cup_numeric for p in self.favorited_performers if p.cup_numeric > 0]
        if not fav_cup_sizes:
            return
            
        avg_fav_cup = sum(fav_cup_sizes) / len(fav_cup_sizes)
        
        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_cup_performers = []
        
        for candidate in candidates:
            if not candidate.cup_numeric or candidate.cup_numeric <= 0:
                continue
                
            # Berechne Ähnlichkeit (0-1) basierend auf Cup-Größen-Differenz
            cup_diff = abs(candidate.cup_numeric - avg_fav_cup)
            similarity = max(0, 1 - (cup_diff / 4))  # Normalisiert auf 0-1, max 4 Cup-Größen Unterschied
            
            if similarity >= self.min_similarity_score:
                similar_cup_performers.append((candidate, similarity))
        
        # Sortieren nach Ähnlichkeit (absteigend)
        similar_cup_performers.sort(key=lambda x: x[1], reverse=True)
        
        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_cup_size"] = similar_cup_performers[:self.max_recommendations]
        
        logger.info(f"{len(self.recommendation_categories['similar_cup_size'])} Empfehlungen nach Cup-Größe generiert")
    
    def _generate_recommendations_by_proportions(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichen Körperproportionen (BMI/Cup, Größe/Cup).
        
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Körperproportionen...")
        
        # Sammle Verhältniswerte der Favoriten
        fav_bmi_cup_ratios = [p.bmi_to_cup_ratio for p in self.favorited_performers if p.bmi_to_cup_ratio]
        fav_height_cup_ratios = [p.height_to_cup_ratio for p in self.favorited_performers if p.height_to_cup_ratio]
        
        if not fav_bmi_cup_ratios or not fav_height_cup_ratios:
            return
            
        avg_bmi_cup = sum(fav_bmi_cup_ratios) / len(fav_bmi_cup_ratios)
        avg_height_cup = sum(fav_height_cup_ratios) / len(fav_height_cup_ratios)
        
        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_proportion_performers = []
        
        for candidate in candidates:
            if not candidate.bmi_to_cup_ratio or not candidate.height_to_cup_ratio:
                continue
                
            # BMI/Cup-Verhältnis Ähnlichkeit
            bmi_cup_diff = abs(candidate.bmi_to_cup_ratio - avg_bmi_cup)
            bmi_cup_similarity = max(0, 1 - (bmi_cup_diff / 5))  # Normalisiert auf 0-1
            
            # Größe/Cup-Verhältnis Ähnlichkeit
            height_cup_diff = abs(candidate.height_to_cup_ratio - avg_height_cup)
            height_cup_similarity = max(0, 1 - (height_cup_diff / 50))  # Normalisiert auf 0-1
            
            # Gewichtete Gesamtähnlichkeit
            total_similarity = (
                self.bmi_cup_size * bmi_cup_similarity + 
                self.height_cup_size * height_cup_similarity
            ) / (self.bmi_cup_size + self.height_cup_size)
            
            if total_similarity >= self.min_similarity_score:
                similar_proportion_performers.append((candidate, total_similarity))
        
        # Sortieren nach Ähnlichkeit (absteigend)
        similar_proportion_performers.sort(key=lambda x: x[1], reverse=True)
        
        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_proportions"] = similar_proportion_performers[:self.max_recommendations]
        
        logger.info(f"{len(self.recommendation_categories['similar_proportions'])} Empfehlungen nach Körperproportionen generiert")
    
    def _generate_recommendations_by_tags(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichen Tags.
        
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Tag-Ähnlichkeit...")
        
        # Sammle alle Tags der Favoriten
        fav_tags = set()
        for p in self.favorited_performers:
            fav_tags.update(p.tags)
        
        if not fav_tags:
            return
        
        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_tag_performers = []
        
        for candidate in candidates:
            if not candidate.tags:
                continue
                
            # Jaccard-Ähnlichkeit: Überschneidung / Vereinigung
            candidate_tags = set(candidate.tags)
            common_tags = fav_tags.intersection(candidate_tags)
            all_tags = fav_tags.union(candidate_tags)
            
            if not all_tags:
                continue
                
            similarity = len(common_tags) / len(all_tags)
            
            if similarity >= self.min_similarity_score * 0.8:  # Etwas niedrigerer Schwellenwert für Tags
                similar_tag_performers.append((candidate, similarity))
        
        # Sortieren nach Ähnlichkeit (absteigend)
        similar_tag_performers.sort(key=lambda x: x[1], reverse=True)
        
        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_tags"] = similar_tag_performers[:self.max_recommendations]
        
        logger.info(f"{len(self.recommendation_categories['similar_tags'])} Empfehlungen nach Tag-Ähnlichkeit generiert")
    
    def _generate_recommendations_by_age(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichem Alter.
        
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Altersähnlichkeit...")
        
        # Berechne durchschnittliches Alter der Favoriten
        fav_ages = [p.age for p in self.favorited_performers if p.age is not None]
        if not fav_ages:
            return
            
        avg_fav_age = sum(fav_ages) / len(fav_ages)
        
        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_age_performers = []
        
        for candidate in candidates:
            if candidate.age is None:
                continue
                
            # Altersunterschied in Jahren
            age_diff = abs(candidate.age - avg_fav_age)
            
            # Wenn innerhalb der Toleranz, berechne Ähnlichkeitswert
            if age_diff <= self.age_range_tolerance:
                similarity = 1 - (age_diff / self.age_range_tolerance)
                similar_age_performers.append((candidate, similarity))
        
        # Sortieren nach Ähnlichkeit (absteigend)
        similar_age_performers.sort(key=lambda x: x[1], reverse=True)
        
        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_age"] = similar_age_performers[:self.max_recommendations]
        
        logger.info(f"{len(self.recommendation_categories['similar_age'])} Empfehlungen nach Altersähnlichkeit generiert")
    
    def _generate_recommendations_by_quality(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf hoher Qualität (Rating).
        
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Qualität...")
        
        # Filtere nach Mindesbewertung und sortiere nach Rating
        high_quality_performers = []
        
        for candidate in candidates:
            if candidate.rating100 is None or candidate.rating100 < self.min_scene_rating:
                continue
                
            # Normalisiere Rating auf 0-1
            normalized_rating = candidate.rating100 / 100
            
            high_quality_performers.append((candidate, normalized_rating))
        
        # Sortieren nach Rating (absteigend)
        high_quality_performers.sort(key=lambda x: x[1], reverse=True)
        
        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["high_quality"] = high_quality_performers[:self.max_recommendations]
        
        logger.info(f"{len(self.recommendation_categories['high_quality'])} Empfehlungen nach Qualität generiert")
    
    def _generate_recommendations_by_novelty(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf Neuheit (kürzlich hinzugefügt).
        
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Neuheit...")
        
        # Aktuelles Datum und Zeitrahmen
        now = datetime.now()
        timeframe_days = self.novelty_timeframe
        
        # Filtere nach kürzlich hinzugefügten Performern
        novelty_performers = []
        
        for candidate in candidates:
            if not hasattr(candidate, 'raw_data') or not candidate.raw_data:
                continue
                
            # Hole created_at aus den Rohdaten
            created_at = candidate.raw_data.get('created_at')
            if not created_at:
                continue
                
            try:
                # Parse das Datum (Format kann variieren)
                if 'T' in created_at:
                    # ISO-Format: 2023-01-01T12:34:56Z
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    # Einfaches Datum: 2023-01-01
                    created_date = datetime.strptime(created_at, "%Y-%m-%d")
                
                # Berechne Alter in Tagen
                days_old = (now - created_date).days
                
                # Wenn innerhalb des Zeitrahmens, füge zur Liste hinzu
                if days_old <= timeframe_days:
                    # Je neuer, desto höher der Score
                    novelty_score = 1 - (days_old / timeframe_days)
                    novelty_performers.append((candidate, novelty_score))
            except Exception as e:
                logger.warning(f"Fehler beim Parsen des Erstellungsda
