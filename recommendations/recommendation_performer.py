# source: 1
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

# Modulimporte (assuming these exist in the project structure)
from core.stash_api import StashAPI
from core.data_models import Performer # Assuming Performer class has relevant attributes like name, cup_numeric, bmi_to_cup_ratio, height_to_cup_ratio, tags, age, rating100, o_counter, favorite, scenes, raw_data{'created_at'} etc.
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

    # source: 2
    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        # source: 3
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

        # source: 4
        # Hole alle Performer aus dem Statistik-Modul
        self.performers = self.stats_module.performers if self.stats_module else []
        self.favorited_performers = [p for p in self.performers if p.favorite]

        # Lade Konfigurationsoptionen für Empfehlungen
        self.min_similarity_score = self.config.getfloat('Recommendations', 'min_similarity_score', fallback=0.75)
        self.max_recommendations = self.config.getint('Recommendations', 'max_recommendations', fallback=10)
        self.include_zero_counter = self.config.getboolean('Recommendations', 'include_zero_counter', fallback=True)

        # source: 5
        # Gewichtungen für Ähnlichkeitskriterien
        self.weight_cup_size = self.config.getfloat('Recommendations', 'weight_cup_size', fallback=0.4)
        self.bmi_cup_size = self.config.getfloat('Recommendations', 'bmi_cup_size', fallback=0.2)
        self.height_cup_size = self.config.getfloat('Recommendations', 'height_cup_size', fallback=0.2)

        # Zusätzliche Empfehlungskriterien
        self.enable_tag_similarity = self.config.getboolean('Recommendations', 'enable_tag_similarity', fallback=True)
        self.weight_tag_similarity = self.config.getfloat('Recommendations', 'weight_tag_similarity', fallback=0.6)

        # source: 6
        self.enable_scene_types = self.config.getboolean('Recommendations', 'enable_scene_types', fallback=True) # Note: Scene types are mentioned but not implemented in the provided snippet. Assuming similar logic to tags or versatility might apply. Add weight if needed.
        self.weight_scene_types = self.config.getfloat('Recommendations', 'weight_scene_types', fallback=0.5) # Added weight based on requirements

        self.enable_age_range = self.config.getboolean('Recommendations', 'enable_age_range', fallback=True)
        self.age_range_tolerance = self.config.getint('Recommendations', 'age_range_tolerance', fallback=5)
        self.weight_age_similarity = self.config.getfloat('Recommendations', 'weight_age_similarity', fallback=0.4)

        self.enable_novelty = self.config.getboolean('Recommendations', 'enable_novelty', fallback=True)
        # source: 7
        self.novelty_timeframe = self.config.getint('Recommendations', 'novelty_timeframe', fallback=30) # Days
        self.weight_novelty = self.config.getfloat('Recommendations', 'weight_novelty', fallback=0.3)

        self.enable_scene_quality = self.config.getboolean('Recommendations', 'enable_scene_quality', fallback=True)
        self.min_scene_rating = self.config.getint('Recommendations', 'min_scene_rating', fallback=60) # Assuming this refers to performer's average scene rating or overall rating
        self.weight_scene_quality = self.config.getfloat('Recommendations', 'weight_scene_quality', fallback=0.5)

        self.enable_versatility = self.config.getboolean('Recommendations', 'enable_versatility', fallback=True)
        self.weight_versatility = self.config.getfloat('Recommendations', 'weight_versatility', fallback=0.4)

        # source: 8
        self.enable_similar_to_favorites = self.config.getboolean('Recommendations', 'enable_similar_to_favorites', fallback=True)
        self.favorite_similarity_threshold = self.config.getfloat('Recommendations', 'favorite_similarity_threshold', fallback=0.7)
        self.weight_favorite_similarity = self.config.getfloat('Recommendations', 'weight_favorite_similarity', fallback=0.7)

        # Ausgabeverzeichnis
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')

        # Empfehlungskategorien und Ergebnisse
        self.recommendation_categories = {
            # source: 9
            "similar_cup_size": [],
            "similar_proportions": [],
            "similar_tags": [],
            # "similar_scene_types": [], # Added based on requirements
            "similar_age": [],
            "high_quality": [],
            "novelty": [],
            "versatile": [],
            "similar_to_favorites": [],
             # source: 10
            "zero_counter": [] # Performers with low O-Counter
        }

        # Map category keys to their weight attributes for easier aggregation
        self.category_weight_map = {
            "similar_cup_size": self.weight_cup_size,
            "similar_proportions": (self.bmi_cup_size + self.height_cup_size) / 2, # Average weight for proportion similarity
            "similar_tags": self.weight_tag_similarity,
            # "similar_scene_types": self.weight_scene_types, # Add if implemented
            "similar_age": self.weight_age_similarity,
            "high_quality": self.weight_scene_quality,
            "novelty": self.weight_novelty,
            "versatile": self.weight_versatility,
            "similar_to_favorites": self.weight_favorite_similarity,
            "zero_counter": 0.1 # Give a small boost to unrated performers, adjust as needed
        }


        # Top-Empfehlungen
        self.top_recommendations = []

        logger.info("Performer-Empfehlungsmodul initialisiert")

    # source: 11
    def generate_recommendations(self, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, List[Tuple[Performer, float]]]:
        """
        Generiert Performer-Empfehlungen basierend auf verschiedenen Kriterien.

        Args:
            custom_weights: Optionales Dictionary mit benutzerdefinierten Gewichtungen

        Returns:
            Dict[str, List[Tuple[Performer, float]]]: Empfehlungen nach Kategorien sortiert
        """
        logger.info("Generiere Performer-Empfehlungen...")

        # source: 12
        if custom_weights:
            self._apply_custom_weights(custom_weights)

        # Keine Favoriten vorhanden? Verwende Top-bewertete Performer
        if not self.favorited_performers:
            logger.warning("Keine favorisierten Performer gefunden. Verwende Top-bewertete Performer als Referenz.")
            # source: 13
            self.favorited_performers = sorted(
                [p for p in self.performers if p.rating100 is not None],
                key=lambda p: p.rating100 or 0,
                reverse=True
            )[:5] # Take top 5 rated as reference

        # Wenn immer noch keine Referenz-Performer vorhanden sind, können keine Empfehlungen generiert werden
        if not self.favorited_performers:
            # source: 14
            logger.error("Keine Referenz-Performer gefunden. Empfehlungen können nicht generiert werden.")
            return {}

        # Kandidaten für Empfehlungen identifizieren
        candidates = self._get_recommendation_candidates()

        if not candidates:
            logger.warning("Keine geeigneten Kandidaten für Empfehlungen gefunden.")
            # source: 15
            return {}

        # --- Empfehlungen nach verschiedenen Kriterien generieren ---
        self._generate_recommendations_by_cup_size(candidates)
        self._generate_recommendations_by_proportions(candidates)

        if self.enable_tag_similarity:
            self._generate_recommendations_by_tags(candidates)

        # if self.enable_scene_types: # Add if implementing scene type similarity
        #     self._generate_recommendations_by_scene_types(candidates)

        if self.enable_age_range:
            self._generate_recommendations_by_age(candidates)

        # source: 16
        if self.enable_scene_quality:
            self._generate_recommendations_by_quality(candidates)

        if self.enable_novelty:
            self._generate_recommendations_by_novelty(candidates)

        if self.enable_versatility:
            self._generate_recommendations_by_versatility(candidates)

        # source: 17
        if self.enable_similar_to_favorites:
             # This might be computationally more expensive, run after simpler criteria
            self._generate_recommendations_by_favorite_similarity(candidates)

        # Always generate this list if enabled, even if filtering happens in _get_recommendation_candidates
        if self.include_zero_counter:
            self._generate_recommendations_for_zero_counter(candidates)


        # Top-Empfehlungen übergreifend erstellen
        self._generate_top_recommendations()

        logger.info("Performer-Empfehlungen erfolgreich generiert")

        # Optional: Save results automatically
        # self.save_recommendations()

        # source: 18
        return self.recommendation_categories

    # source: 19
    def _apply_custom_weights(self, custom_weights: Dict[str, float]) -> None:
        """
        Wendet benutzerdefinierte Gewichtungen an.

        Args:
            custom_weights: Dictionary mit benutzerdefinierten Gewichtungen
        """
        for key, value in custom_weights.items():
            # Check if the key corresponds to a weight attribute
            if key.startswith('weight_') and hasattr(self, key):
                try:
                    setattr(self, key, float(value))
                    logger.debug(f"Benutzerdefinierte Gewichtung angewendet: {key} = {value}")
                    # Update the category weight map as well
                    category_key = key.replace('weight_', '')
                    if category_key in self.category_weight_map:
                         self.category_weight_map[category_key] = float(value)
                    elif category_key == "bmi_cup_size" or category_key == "height_cup_size":
                         # Update the average weight for proportions
                         self.category_weight_map["similar_proportions"] = (self.bmi_cup_size + self.height_cup_size) / 2

                except ValueError:
                     logger.warning(f"Ungültiger Wert für Gewichtung {key}: {value}")
            elif hasattr(self, key) and isinstance(getattr(self, key), (float, int, bool)):
                 # Allow overriding other numeric/boolean config values too
                 try:
                     if isinstance(getattr(self, key), bool):
                         setattr(self, key, str(value).lower() in ['true', '1', 'yes'])
                     elif isinstance(getattr(self, key), int):
                          setattr(self, key, int(value))
                     else: # float
                          setattr(self, key, float(value))
                     logger.debug(f"Benutzerdefinierte Konfiguration angewendet: {key} = {getattr(self, key)}")
                 except ValueError:
                     logger.warning(f"Ungültiger Wert für Konfiguration {key}: {value}")


    # source: 20
    def _get_recommendation_candidates(self) -> List[Performer]:
        """
        Identifiziert geeignete Kandidaten für Empfehlungen.
        Filtert Favoriten und optional Performer mit O-Counter > 0 heraus.

        Returns:
            List[Performer]: Liste geeigneter Kandidaten
        """
        # source: 21
        # Alle Performer, die nicht favorisiert sind
        favorite_ids = {p.id for p in self.favorited_performers} # Use set for faster lookup
        non_favorites = [p for p in self.performers if p.id not in favorite_ids]

        # Grundlegende Filterung: Z.B. Performer mit mindestens einer Szene oder gültigen Daten
        # This depends heavily on the Performer data model and what defines a "valid" performer
        candidates = [p for p in non_favorites if p.cup_numeric and p.cup_numeric > 0] # Example: require valid cup size

        # source: 22
        # Wenn konfiguriert, entferne Performer mit O-Counter > 0
        # The requirement description is ambiguous:
        # "Performer mit niedrigem O-Counter: Potentiell interessante Performer, die noch nicht oft angesehen wurden"
        # "include_zero_counter" config option
        # Interpretation: If include_zero_counter is FALSE, we ONLY recommend those with O-Counter = 0.
        # If include_zero_counter is TRUE, we consider ALL non-favorites, but might give a boost or have a separate category for O-Counter = 0.
        # The current code filters OUT O-Counter > 0 if include_zero_counter is FALSE.
        if not self.include_zero_counter:
            candidates = [p for p in candidates if hasattr(p, 'o_counter') and p.o_counter == 0]

        logger.info(f"{len(candidates)} Kandidaten für Empfehlungen identifiziert.")
        return candidates

    # source: 23
    def _generate_recommendations_by_cup_size(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichen Cup-Größen.

        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Cup-Größe...")

        # Berechne durchschnittliche Cup-Größe der Favoriten
        fav_cup_sizes = [p.cup_numeric for p in self.favorited_performers if p.cup_numeric and p.cup_numeric > 0]
        if not fav_cup_sizes:
            logger.warning("Keine gültigen Cup-Größen bei Favoriten gefunden für Cup-Größen-Vergleich.")
            return
        # source: 24
        avg_fav_cup = sum(fav_cup_sizes) / len(fav_cup_sizes)

        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_cup_performers = []
        for candidate in candidates:
            # source: 25
            if not candidate.cup_numeric or candidate.cup_numeric <= 0:
                continue

            # Berechne Ähnlichkeit (0-1) basierend auf Cup-Größen-Differenz
            # Higher difference = lower similarity
            # Max difference considered relevant could be ~4 sizes (e.g., A vs DD)
            max_relevant_diff = 4.0
            cup_diff = abs(candidate.cup_numeric - avg_fav_cup)
            similarity = max(0.0, 1.0 - (cup_diff / max_relevant_diff))

            # source: 26
            if similarity >= self.min_similarity_score:
                similar_cup_performers.append((candidate, similarity))

        # Sortieren nach Ähnlichkeit (absteigend)
        similar_cup_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_cup_size"] = similar_cup_performers[:self.max_recommendations]
        # source: 27
        logger.info(f"{len(self.recommendation_categories['similar_cup_size'])} Empfehlungen nach Cup-Größe generiert")

    # source: 28
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

        # source: 29
        if not fav_bmi_cup_ratios or not fav_height_cup_ratios:
            logger.warning("Nicht genügend Daten für Proportionsvergleich bei Favoriten vorhanden.")
            return

        avg_bmi_cup = sum(fav_bmi_cup_ratios) / len(fav_bmi_cup_ratios)
        avg_height_cup = sum(fav_height_cup_ratios) / len(fav_height_cup_ratios)

        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_proportion_performers = []
        # source: 30
        for candidate in candidates:
            if not candidate.bmi_to_cup_ratio or not candidate.height_to_cup_ratio:
                continue

            # BMI/Cup-Verhältnis Ähnlichkeit - Normalize based on expected range/variation
            # Assuming a max relevant difference of ~5 units for BMI/Cup ratio
            max_relevant_bmi_cup_diff = 5.0
            bmi_cup_diff = abs(candidate.bmi_to_cup_ratio - avg_bmi_cup)
             # source: 31
            bmi_cup_similarity = max(0.0, 1.0 - (bmi_cup_diff / max_relevant_bmi_cup_diff))

            # Größe/Cup-Verhältnis Ähnlichkeit - Normalize based on expected range/variation
            # Assuming a max relevant difference of ~50 units for Height/Cup ratio
            max_relevant_height_cup_diff = 50.0
            height_cup_diff = abs(candidate.height_to_cup_ratio - avg_height_cup)
            height_cup_similarity = max(0.0, 1.0 - (height_cup_diff / max_relevant_height_cup_diff))

            # Gewichtete Gesamtähnlichkeit for proportions category
            # source: 32
            # Use the specific weights for this category's score
            total_similarity = (
                self.bmi_cup_size * bmi_cup_similarity +
                self.height_cup_size * height_cup_similarity
            )
            # Normalize by the sum of weights used, in case they don't add up to 1
            weight_sum = self.bmi_cup_size + self.height_cup_size
            if weight_sum > 0:
                total_similarity /= weight_sum
            else:
                total_similarity = 0 # Avoid division by zero if both weights are 0

            # source: 33
            if total_similarity >= self.min_similarity_score:
                similar_proportion_performers.append((candidate, total_similarity))

        # Sortieren nach Ähnlichkeit (absteigend)
        similar_proportion_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_proportions"] = similar_proportion_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['similar_proportions'])} Empfehlungen nach Körperproportionen generiert")

    # source: 34
    def _generate_recommendations_by_tags(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichen Tags (Jaccard-Ähnlichkeit).

        Args:
            candidates: Liste möglicher Kandidaten
        """
        # source: 35
        logger.info("Generiere Empfehlungen nach Tag-Ähnlichkeit...")

        # Sammle alle eindeutigen Tag-IDs der Favoriten
        fav_tags = set()
        for p in self.favorited_performers:
            # Assuming p.tags is a list of tag objects or dicts with an 'id'
            if hasattr(p, 'tags') and p.tags:
                 fav_tags.update(tag['id'] for tag in p.tags if isinstance(tag, dict) and 'id' in tag) # Adapt if tag structure is different

        # source: 36
        if not fav_tags:
            logger.warning("Keine Tags bei Favoriten für Tag-Vergleich gefunden.")
            return

        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_tag_performers = []
        for candidate in candidates:
             # source: 37
            if not hasattr(candidate, 'tags') or not candidate.tags:
                continue

            candidate_tags = set(tag['id'] for tag in candidate.tags if isinstance(tag, dict) and 'id' in tag) # Adapt if tag structure is different
            if not candidate_tags:
                continue

            # Jaccard-Ähnlichkeit: |Intersection| / |Union|
            common_tags = fav_tags.intersection(candidate_tags)
            all_tags = fav_tags.union(candidate_tags)

             # source: 38
            if not all_tags: # Should not happen if candidate_tags is not empty, but safety check
                continue

            similarity = len(common_tags) / len(all_tags)

            # Verwende einen möglicherweise angepassten Schwellenwert für Tags
            tag_similarity_threshold = self.min_similarity_score * 0.8 # Example: Allow slightly lower score for tag match
            if similarity >= tag_similarity_threshold:
                similar_tag_performers.append((candidate, similarity))

        # source: 39
        # Sortieren nach Ähnlichkeit (absteigend)
        similar_tag_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_tags"] = similar_tag_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['similar_tags'])} Empfehlungen nach Tag-Ähnlichkeit generiert")

    # source: 40
    def _generate_recommendations_by_age(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf ähnlichem Alter, innerhalb einer Toleranz.

        Args:
            candidates: Liste möglicher Kandidaten
        """
        # source: 41
        logger.info("Generiere Empfehlungen nach Altersähnlichkeit...")

        # Berechne durchschnittliches Alter der Favoriten
        fav_ages = [p.age for p in self.favorited_performers if hasattr(p, 'age') and p.age is not None and p.age > 0]
        if not fav_ages:
            logger.warning("Kein Alter bei Favoriten für Altersvergleich gefunden.")
            return
        # source: 42
        avg_fav_age = sum(fav_ages) / len(fav_ages)

        # Berechne Ähnlichkeit für jeden Kandidaten
        similar_age_performers = []
        for candidate in candidates:
            # source: 43
            if not hasattr(candidate, 'age') or candidate.age is None or candidate.age <= 0:
                continue

            # Altersunterschied in Jahren
            age_diff = abs(candidate.age - avg_fav_age)

            # Wenn innerhalb der Toleranz, berechne Ähnlichkeitswert (1 = exact match, 0 = at tolerance boundary)
            if age_diff <= self.age_range_tolerance:
                # source: 44
                # Avoid division by zero if tolerance is 0
                similarity = 1.0 - (age_diff / self.age_range_tolerance) if self.age_range_tolerance > 0 else 1.0
                similar_age_performers.append((candidate, similarity))

        # Sortieren nach Ähnlichkeit (absteigend)
        similar_age_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_age"] = similar_age_performers[:self.max_recommendations]
        # source: 45
        logger.info(f"{len(self.recommendation_categories['similar_age'])} Empfehlungen nach Altersähnlichkeit generiert")

    # source: 46
    def _generate_recommendations_by_quality(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf hoher Qualität (Performer-Rating).

        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Qualität (Performer-Rating)...")

        # Filtere nach Mindesbewertung und sortiere nach Rating
        high_quality_performers = []
        for candidate in candidates:
            # source: 47
            # Use rating100 if available, otherwise maybe fallback to another quality metric?
            if not hasattr(candidate, 'rating100') or candidate.rating100 is None or candidate.rating100 < self.min_scene_rating:
                continue

            # Normalisiere Rating auf 0-1 (assuming rating100 is 0-100)
            # Use the rating directly as the 'score' for this category
            normalized_rating = candidate.rating100 / 100.0
            high_quality_performers.append((candidate, normalized_rating))

        # source: 48
        # Sortieren nach Rating (absteigend)
        high_quality_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["high_quality"] = high_quality_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['high_quality'])} Empfehlungen nach Qualität generiert")

    # source: 49
    def _generate_recommendations_by_novelty(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf Neuheit (kürzlich hinzugefügt).

        Args:
            candidates: Liste möglicher Kandidaten
        """
        # source: 50
        logger.info("Generiere Empfehlungen nach Neuheit...")

        # Aktuelles Datum und Zeitrahmen
        now = datetime.now().astimezone() # Use timezone-aware datetime
        timeframe_limit = now - timedelta(days=self.novelty_timeframe)

        # Filtere nach kürzlich hinzugefügten Performern
        # source: 51
        novelty_performers = []
        for candidate in candidates:
            # source: 52
            # Assume raw_data contains the original Stash performer data including 'created_at'
            if not hasattr(candidate, 'raw_data') or not candidate.raw_data or 'created_at' not in candidate.raw_data:
                continue

            created_at_str = candidate.raw_data.get('created_at')
            if not created_at_str:
                continue

            try:
                # Parse the ISO 8601 timestamp from Stash (usually includes 'Z' or timezone offset)
                # source: 53
                created_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))

                # Check if within the timeframe
                if created_date >= timeframe_limit:
                    # source: 55
                    # Calculate score: linear decay from 1 (just created) to 0 (at timeframe boundary)
                    days_old = (now - created_date).total_seconds() / (24 * 3600)
                    # Avoid division by zero if timeframe is 0 or less
                    novelty_score = max(0.0, 1.0 - (days_old / self.novelty_timeframe)) if self.novelty_timeframe > 0 else 1.0
                    novelty_performers.append((candidate, novelty_score))

            # source: 56
            except ValueError as e:
                logger.warning(f"Fehler beim Parsen des Erstellungsdatums '{created_at_str}' für Performer {getattr(candidate, 'name', candidate.id)}: {e}")
            except Exception as e: # Catch other potential errors
                 logger.error(f"Unerwarteter Fehler bei Neuheitsprüfung für Performer {getattr(candidate, 'name', candidate.id)}: {e}")


        # Sortieren nach Score (absteigend, newest first)
        novelty_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["novelty"] = novelty_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['novelty'])} Empfehlungen nach Neuheit generiert")

    def _generate_recommendations_by_versatility(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf Vielseitigkeit (z.B. Anzahl verschiedener Tags oder Szenenkategorien).
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen nach Vielseitigkeit...")
        versatile_performers = []

        max_unique_tags = 1 # To avoid division by zero if no performer has tags

        # First pass to find the maximum number of unique tags among candidates
        for candidate in candidates:
             if hasattr(candidate, 'tags') and candidate.tags:
                  unique_tags = len(set(tag['id'] for tag in candidate.tags if isinstance(tag, dict) and 'id' in tag))
                  if unique_tags > max_unique_tags:
                      max_unique_tags = unique_tags

        # Second pass to calculate normalized versatility score
        for candidate in candidates:
            unique_tags = 0
            if hasattr(candidate, 'tags') and candidate.tags:
                unique_tags = len(set(tag['id'] for tag in candidate.tags if isinstance(tag, dict) and 'id' in tag))

            # Normalize score (0-1 based on max found tags)
            versatility_score = (unique_tags / max_unique_tags) if max_unique_tags > 0 else 0
            # Maybe apply a non-linear scale or require a minimum number of tags?
            # For now, simple normalization.
            if versatility_score > 0: # Only recommend if they have at least some tags
                 versatile_performers.append((candidate, versatility_score))

        # Sortieren nach Vielseitigkeit (absteigend)
        versatile_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["versatile"] = versatile_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['versatile'])} Empfehlungen nach Vielseitigkeit generiert")


    def _calculate_performer_similarity(self, p1: Performer, p2: Performer) -> float:
        """
        Hilfsfunktion zur Berechnung einer Gesamtähnlichkeit zwischen zwei Performern
        basierend auf verschiedenen Attributen (Cup, Proportionen, Alter, Tags).
        Verwendet die konfigurierten Gewichtungen.

        Args:
            p1: Erster Performer
            p2: Zweiter Performer

        Returns:
            float: Gesamtähnlichkeitswert (0-1)
        """
        total_similarity = 0.0
        total_weight = 0.0

        # 1. Cup Size Similarity
        if p1.cup_numeric and p1.cup_numeric > 0 and p2.cup_numeric and p2.cup_numeric > 0:
             max_relevant_diff = 4.0
             cup_diff = abs(p1.cup_numeric - p2.cup_numeric)
             cup_similarity = max(0.0, 1.0 - (cup_diff / max_relevant_diff))
             total_similarity += cup_similarity * self.weight_cup_size
             total_weight += self.weight_cup_size

        # 2. Proportions Similarity (BMI/Cup + Height/Cup)
        bmi_cup_similarity = 0.0
        height_cup_similarity = 0.0
        prop_weight = 0.0
        if p1.bmi_to_cup_ratio and p2.bmi_to_cup_ratio:
            max_relevant_bmi_cup_diff = 5.0
            bmi_cup_diff = abs(p1.bmi_to_cup_ratio - p2.bmi_to_cup_ratio)
            bmi_cup_similarity = max(0.0, 1.0 - (bmi_cup_diff / max_relevant_bmi_cup_diff))
            total_similarity += bmi_cup_similarity * self.bmi_cup_size
            prop_weight += self.bmi_cup_size
        if p1.height_to_cup_ratio and p2.height_to_cup_ratio:
            max_relevant_height_cup_diff = 50.0
            height_cup_diff = abs(p1.height_to_cup_ratio - p2.height_to_cup_ratio)
            height_cup_similarity = max(0.0, 1.0 - (height_cup_diff / max_relevant_height_cup_diff))
            total_similarity += height_cup_similarity * self.height_cup_size
            prop_weight += self.height_cup_size
        if prop_weight > 0:
             total_weight += prop_weight # Add the actual used weight

        # 3. Age Similarity
        if hasattr(p1, 'age') and p1.age and hasattr(p2, 'age') and p2.age:
             age_diff = abs(p1.age - p2.age)
             if age_diff <= self.age_range_tolerance:
                  age_similarity = 1.0 - (age_diff / self.age_range_tolerance) if self.age_range_tolerance > 0 else 1.0
                  total_similarity += age_similarity * self.weight_age_similarity
                  total_weight += self.weight_age_similarity

        # 4. Tag Similarity (Jaccard)
        if self.enable_tag_similarity and hasattr(p1, 'tags') and p1.tags and hasattr(p2, 'tags') and p2.tags:
            tags1 = set(tag['id'] for tag in p1.tags if isinstance(tag, dict) and 'id' in tag)
            tags2 = set(tag['id'] for tag in p2.tags if isinstance(tag, dict) and 'id' in tag)
            if tags1 and tags2:
                common_tags = tags1.intersection(tags2)
                all_tags = tags1.union(tags2)
                if all_tags:
                    tag_similarity = len(common_tags) / len(all_tags)
                    total_similarity += tag_similarity * self.weight_tag_similarity
                    total_weight += self.weight_tag_similarity

        # Normalize final similarity score by total weight used
        if total_weight == 0:
            return 0.0
        return total_similarity / total_weight


    def _generate_recommendations_by_favorite_similarity(self, candidates: List[Performer]) -> None:
        """
        Generiert Empfehlungen basierend auf der Gesamtähnlichkeit zu den favorisierten Performern.
        Args:
            candidates: Liste möglicher Kandidaten
        """
        logger.info("Generiere Empfehlungen basierend auf Ähnlichkeit zu Favoriten...")
        favorite_similar_performers = []

        for candidate in candidates:
            max_similarity_to_any_favorite = 0.0
            # Calculate similarity to each favorite performer
            for favorite in self.favorited_performers:
                similarity = self._calculate_performer_similarity(candidate, favorite)
                if similarity > max_similarity_to_any_favorite:
                    max_similarity_to_any_favorite = similarity

            # Check against the specific threshold for this category
            if max_similarity_to_any_favorite >= self.favorite_similarity_threshold:
                 favorite_similar_performers.append((candidate, max_similarity_to_any_favorite))

        # Sortieren nach Ähnlichkeit (absteigend)
        favorite_similar_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["similar_to_favorites"] = favorite_similar_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['similar_to_favorites'])} Empfehlungen basierend auf Favoriten-Ähnlichkeit generiert")


    def _generate_recommendations_for_zero_counter(self, candidates: List[Performer]) -> None:
        """
        Erstellt eine Liste von interessanten Performern, die noch nicht oft angesehen wurden (O-Counter = 0).
        Sortiert diese z.B. nach Rating oder Neuheit.
        Args:
            candidates: Liste möglicher Kandidaten (könnte bereits gefiltert sein, je nach include_zero_counter)
        """
        logger.info("Generiere Empfehlungen für Performer mit niedrigem O-Counter...")
        zero_counter_performers = []

        for candidate in candidates:
             # Check if o_counter attribute exists and is 0
             if hasattr(candidate, 'o_counter') and candidate.o_counter == 0:
                  # Use a simple score, e.g., normalized rating, or just 1 if no rating exists
                  score = (candidate.rating100 / 100.0) if hasattr(candidate, 'rating100') and candidate.rating100 else 0.5
                  zero_counter_performers.append((candidate, score)) # Score here represents potential interest

        # Sortieren (z.B. nach Rating absteigend, oder nach Name)
        zero_counter_performers.sort(key=lambda x: x[1], reverse=True)

        # Speichere die Top-N Ergebnisse
        self.recommendation_categories["zero_counter"] = zero_counter_performers[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['zero_counter'])} Empfehlungen für Performer mit niedrigem O-Counter generiert")


    def _generate_top_recommendations(self) -> None:
        """
        Kombiniert die Ergebnisse aus allen aktivierten Kategorien zu einer
        gewichteten Gesamtliste der Top-Empfehlungen.
        """
        logger.info("Generiere übergreifende Top-Empfehlungen...")
        combined_scores: Dict[str, float] = {} # performer_id -> combined_score
        performer_map: Dict[str, Performer] = {} # performer_id -> performer_object

        # Iterate through each category and its recommendations
        for category_key, recommendations in self.recommendation_categories.items():
            # Check if this category contributes to the overall score (has a weight > 0)
            category_weight = self.category_weight_map.get(category_key, 0)
            if category_weight <= 0 or not recommendations:
                 continue # Skip categories with zero weight or no recommendations

            logger.debug(f"Aggregiere Kategorie '{category_key}' mit Gewicht {category_weight}")

            # Add weighted score for each performer in the category list
            for performer, score in recommendations:
                 if not performer or not hasattr(performer, 'id'): continue

                 performer_id = performer.id
                 # Store performer object if not already seen
                 if performer_id not in performer_map:
                     performer_map[performer_id] = performer

                 # Add weighted score to the performer's total score
                 current_score = combined_scores.get(performer_id, 0.0)
                 combined_scores[performer_id] = current_score + (score * category_weight)

        # Convert the combined scores dictionary into a list of (Performer, total_score) tuples
        aggregated_recommendations = []
        for performer_id, total_score in combined_scores.items():
             if performer_id in performer_map:
                  # Optional: Normalize score? The current score depends on how many lists a performer appears in and the weights.
                  # For simplicity, we use the raw aggregated score for ranking.
                  aggregated_recommendations.append((performer_map[performer_id], total_score))

        # Sort the final list by the combined score (descending)
        aggregated_recommendations.sort(key=lambda x: x[1], reverse=True)

        # Store the top N overall recommendations
        self.top_recommendations = aggregated_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.top_recommendations)} übergreifende Top-Empfehlungen generiert")

        # Log top 5 for quick check
        for i, (p, s) in enumerate(self.top_recommendations[:5]):
            logger.debug(f"Top {i+1}: {getattr(p, 'name', p.id)} (Score: {s:.4f})")


    def get_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
         """
         Gibt die generierten Empfehlungen in einem serialisierbaren Format zurück.

         Returns:
             Dict[str, List[Dict[str, Any]]]: Empfehlungen nach Kategorie und Top-Liste.
         """
         output_data = {}
         # Convert category recommendations
         for category, recs in self.recommendation_categories.items():
             output_data[category] = [
                 {"id": p.id, "name": getattr(p, 'name', 'N/A'), "score": float(score)}
                 for p, score in recs if p
             ]
         # Convert top recommendations
         output_data["top_recommendations"] = [
             {"id": p.id, "name": getattr(p, 'name', 'N/A'), "score": float(score)}
             for p, score in self.top_recommendations if p
         ]
         return output_data

    def save_recommendations(self, filename: str = "performer_recommendations.json") -> None:
        """
        Speichert die generierten Empfehlungen in einer JSON-Datei im Output-Verzeichnis.

        Args:
            filename: Name der Ausgabedatei.
        """
        ensure_dir(self.output_dir)
        output_path = os.path.join(self.output_dir, filename)
        recommendations_data = self.get_recommendations()

        try:
            save_json(recommendations_data, output_path)
            logger.info(f"Empfehlungen erfolgreich gespeichert unter: {output_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Empfehlungen: {e}")


# --- Example Usage (Simulated - requires actual StashAPI, Stats, Config) ---
if __name__ == '__main__':
    # This is a placeholder for testing; replace with actual initialization
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starte Beispiel für PerformerRecommendationModule...")

    # --- Mock Objects (Replace with real instances) ---
    class MockStashAPI:
        pass # Implement necessary methods if needed

    class MockPerformer:
        def __init__(self, id, name, favorite=False, cup_numeric=None, bmi_cup_ratio=None, height_cup_ratio=None, tags=None, age=None, rating100=None, o_counter=0, created_at=None, raw_data=None):
            self.id = id
            self.name = name
            self.favorite = favorite
            self.cup_numeric = cup_numeric
            self.bmi_to_cup_ratio = bmi_cup_ratio # Calculated externally?
            self.height_to_cup_ratio = height_cup_ratio # Calculated externally?
            self.tags = tags if tags else [] # List of {'id': 'tag_id', 'name': 'tag_name'}
            self.age = age
            self.rating100 = rating100
            self.o_counter = o_counter
            self.raw_data = raw_data if raw_data else {'created_at': created_at}

    class MockStatisticsModule:
        def __init__(self, performers):
            self.performers = performers

    class MockConfigManager:
        def __init__(self, config_dict=None):
            self.config = config_dict if config_dict else {}

        def get(self, section, option, fallback=None):
            return self.config.get(section, {}).get(option, fallback)
        def getint(self, section, option, fallback=None):
            try: return int(self.get(section, option, fallback=fallback))
            except (ValueError, TypeError): return fallback
        def getfloat(self, section, option, fallback=None):
            try: return float(self.get(section, option, fallback=fallback))
            except (ValueError, TypeError): return fallback
        def getboolean(self, section, option, fallback=None):
            val = str(self.get(section, option, fallback=fallback)).lower()
            return val in ['true', '1', 'yes', 'on']

    # --- Create Mock Data ---
    now = datetime.now().astimezone()
    performers_data = [
        # Favorites
        MockPerformer(id='fav1', name='Favorite Alice', favorite=True, cup_numeric=3.0, bmi_cup_ratio=7.0, height_cup_ratio=55.0, tags=[{'id': 'tag1', 'name': 'Blonde'}, {'id': 'tag2', 'name': 'Solo'}], age=25, rating100=90, o_counter=10, created_at=(now - timedelta(days=300)).isoformat()),
        MockPerformer(id='fav2', name='Favorite Betty', favorite=True, cup_numeric=4.0, bmi_cup_ratio=6.0, height_cup_ratio=45.0, tags=[{'id': 'tag1', 'name': 'Blonde'}, {'id': 'tag3', 'name': 'Lesbian'}], age=30, rating100=85, o_counter=15, created_at=(now - timedelta(days=400)).isoformat()),
        # Candidates
        MockPerformer(id='cand1', name='Candidate Carla', cup_numeric=3.0, bmi_cup_ratio=7.2, height_cup_ratio=56.0, tags=[{'id': 'tag1', 'name': 'Blonde'}, {'id': 'tag4', 'name': 'Anal'}], age=26, rating100=80, o_counter=0, created_at=(now - timedelta(days=10)).isoformat()), # Similar cup, props, age, tags; recent; zero counter
        MockPerformer(id='cand2', name='Candidate Diana', cup_numeric=5.0, bmi_cup_ratio=5.5, height_cup_ratio=40.0, tags=[{'id': 'tag3', 'name': 'Lesbian'}, {'id': 'tag5', 'name': 'Brunette'}], age=32, rating100=88, o_counter=5, created_at=(now - timedelta(days=50)).isoformat()), # Similar age, tags; high quality
        MockPerformer(id='cand3', name='Candidate Eva', cup_numeric=2.0, bmi_cup_ratio=8.0, height_cup_ratio=60.0, tags=[{'id': 'tag6', 'name': 'Teen'}], age=19, rating100=70, o_counter=0, created_at=(now - timedelta(days=5)).isoformat()), # Different; young; recent; zero counter
        MockPerformer(id='cand4', name='Candidate Fiona', cup_numeric=3.5, bmi_cup_ratio=6.5, height_cup_ratio=50.0, tags=[{'id': 'tag1', 'name':'Blonde'}, {'id': 'tag2','name':'Solo'}, {'id':'tag3','name':'Lesbian'}, {'id':'tag4','name':'Anal'}], age=28, rating100=95, o_counter=2, created_at=(now - timedelta(days=200)).isoformat()), # Similar, versatile, high quality
        MockPerformer(id='cand5', name='Candidate Gina (No Cup)', cup_numeric=None, age=40, rating100=60, o_counter=1, created_at=(now - timedelta(days=60)).isoformat()), # Invalid for some criteria
    ]

    mock_api = MockStashAPI()
    mock_stats = MockStatisticsModule(performers_data)
    # Use default config values by providing an empty dict or load from a file/dict
    mock_config = MockConfigManager({
        'Recommendations': {
            'max_recommendations': 3, # Keep lists short for example
            'weight_cup_size': 0.4,
            'bmi_cup_size': 0.2,
            'height_cup_size': 0.2,
            'weight_tag_similarity': 0.6,
            'weight_scene_types': 0.5, # Make sure mapping exists if used
            'weight_age_similarity': 0.4,
            'weight_novelty': 0.3,
            'weight_scene_quality': 0.5,
            'weight_versatility': 0.4,
            'weight_favorite_similarity': 0.7,
            'favorite_similarity_threshold': 0.6, # Lower threshold for example
            'min_similarity_score': 0.5, # Lower threshold for example categories
            'include_zero_counter': True,
            'enable_tag_similarity': True,
            'enable_age_range': True,
            'enable_novelty': True,
            'enable_scene_quality': True,
            'enable_versatility': True,
            'enable_similar_to_favorites': True,
            'novelty_timeframe': 60 # 60 days
        },
        'Output': {
             'output_dir': './output_recommendations'
        }
    })

    # --- Instantiate and Run ---
    recommender = PerformerRecommendationModule(mock_api, mock_stats, mock_config)
    recommendations = recommender.generate_recommendations()

    # --- Print Results ---
    print("\n--- Generated Recommendations ---")
    for category, recs in recommendations.items():
        print(f"\nCategory: {category}")
        if recs:
             for i, (p, score) in enumerate(recs):
                 print(f"  {i+1}. {getattr(p, 'name', p.id)} (Score: {score:.4f})")
        else:
             print("  No recommendations found.")

    print("\n--- Top Overall Recommendations ---")
    if recommender.top_recommendations:
         for i, (p, score) in enumerate(recommender.top_recommendations):
             print(f"  {i+1}. {getattr(p, 'name', p.id)} (Score: {score:.4f})")
    else:
         print("  No top recommendations generated.")

    # --- Save Results ---
    recommender.save_recommendations()
