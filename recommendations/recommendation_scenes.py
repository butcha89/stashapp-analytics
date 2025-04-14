
# recommendations_scenes.py

"""
Scene Recommendation Module

Dieses Modul implementiert Algorithmen zur Erzeugung von Szenen-Empfehlungen
basierend auf Nutzerpräferenzen, Tag-Ähnlichkeiten, beteiligten Performern,
Qualität, Neuheit und O-Counter-Statistiken.
"""

import os
import json
import logging
import random
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

# Modulimporte (assuming these exist in the project structure)
from core.stash_api import StashAPI
# Assuming a Scene data model exists, similar to Performer
from core.data_models import Scene, Performer
from analysis.statistics_module import StatisticsModule
from management.config_manager import ConfigManager
from core.utils import save_json, ensure_dir

# Logger konfigurieren
logger = logging.getLogger(__name__)

class SceneRecommendationModule:
    """
    Klasse zur Generierung von Szenen-Empfehlungen basierend auf
    Nutzerpräferenzen und Szenenattributen.
    """

    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        """
        Initialisiert das Szenen-Empfehlungsmodul.

        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp.
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
                          (inkl. Szenen- und Performer-Daten).
            config: ConfigManager-Instanz mit der Konfiguration.
        """
        self.api = api
        self.stats_module = stats_module
        self.config = config

        # Hole alle Szenen und Performer aus dem Statistik-Modul
        self.scenes = self.stats_module.scenes if self.stats_module else []
        self.performers = self.stats_module.performers if self.stats_module else []

        # Identifiziere Nutzerpräferenzen
        self._build_preference_profile() # Defines self.preferred_tags, self.favorite_performer_ids etc.

        # Lade Konfigurationsoptionen für Szenen-Empfehlungen
        self.max_recommendations = self.config.getint('SceneRecommendations', 'max_recommendations', fallback=15)
        self.min_scene_rating = self.config.getint('SceneRecommendations', 'min_scene_rating', fallback=60)
        self.novelty_timeframe = self.config.getint('SceneRecommendations', 'novelty_timeframe', fallback=30) # Days
        self.min_tag_similarity_score = self.config.getfloat('SceneRecommendations', 'min_tag_similarity_score', fallback=0.3) # Lower threshold might be suitable for tags

        # Aktiviere/Deaktiviere Kriterien und deren Gewichtungen
        self.enable_tag_similarity = self.config.getboolean('SceneRecommendations', 'enable_tag_similarity', fallback=True)
        self.weight_tag_similarity = self.config.getfloat('SceneRecommendations', 'weight_tag_similarity', fallback=0.7)

        self.enable_performer_match = self.config.getboolean('SceneRecommendations', 'enable_performer_match', fallback=True)
        self.weight_performer_match = self.config.getfloat('SceneRecommendations', 'weight_performer_match', fallback=0.8) # High weight for favorite performers

        self.enable_studio_match = self.config.getboolean('SceneRecommendations', 'enable_studio_match', fallback=True)
        self.weight_studio_match = self.config.getfloat('SceneRecommendations', 'weight_studio_match', fallback=0.3)

        self.enable_high_quality = self.config.getboolean('SceneRecommendations', 'enable_high_quality', fallback=True)
        self.weight_high_quality = self.config.getfloat('SceneRecommendations', 'weight_high_quality', fallback=0.5)

        self.enable_novelty = self.config.getboolean('SceneRecommendations', 'enable_novelty', fallback=True)
        self.weight_novelty = self.config.getfloat('SceneRecommendations', 'weight_novelty', fallback=0.4)

        self.enable_low_o_counter_boost = self.config.getboolean('SceneRecommendations', 'enable_low_o_counter_boost', fallback=True)
        self.weight_low_o_counter = self.config.getfloat('SceneRecommendations', 'weight_low_o_counter', fallback=0.2) # Small boost for unwatched high-rated scenes


        # Ausgabeverzeichnis
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')

        # Empfehlungskategorien und Ergebnisse
        self.recommendation_categories = {
            "tag_similarity": [],
            "favorite_performers": [],
            "preferred_studios": [],
            "high_quality_unwatched": [],
            "novelty_unwatched": [],
            "top_unwatched_overall": [] # Based on rating, for discovery
        }

        # Map category keys to their weight attributes for aggregation
        self.category_weight_map = {
            "tag_similarity": self.weight_tag_similarity,
            "favorite_performers": self.weight_performer_match,
            "preferred_studios": self.weight_studio_match,
            "high_quality_unwatched": self.weight_high_quality,
            "novelty_unwatched": self.weight_novelty,
            "top_unwatched_overall": self.weight_low_o_counter # Use this weight for the discovery category
        }

        # Top-Empfehlungen
        self.top_recommendations = []

        logger.info("Szenen-Empfehlungsmodul initialisiert")

    def _build_preference_profile(self) -> None:
        """
        Analysiert Nutzerdaten (favorisierte Performer, gesehene/bewertete Szenen),
        um bevorzugte Tags, Performer und Studios zu identifizieren.
        """
        logger.debug("Erstelle Nutzerpräferenz-Profil...")
        self.favorite_performer_ids: Set[str] = {p.id for p in self.performers if p.favorite}
        self.watched_scene_ids: Set[str] = set()
        self.high_rated_scene_ids: Set[str] = set()
        self.preferred_tags: Dict[str, int] = {} # tag_id -> count
        self.preferred_studios: Dict[str, int] = {} # studio_id -> count

        # Szenen analysieren, die gesehen wurden (O-Counter > 0) oder hoch bewertet wurden
        min_rating_for_pref = self.config.getint('SceneRecommendations', 'min_rating_for_preference', fallback=75)
        min_plays_for_pref = self.config.getint('SceneRecommendations', 'min_plays_for_preference', fallback=1)

        for scene in self.scenes:
            if not hasattr(scene, 'id'): continue

            is_watched = hasattr(scene, 'o_counter') and scene.o_counter >= min_plays_for_pref
            is_high_rated = hasattr(scene, 'rating100') and scene.rating100 is not None and scene.rating100 >= min_rating_for_pref

            if is_watched:
                self.watched_scene_ids.add(scene.id)
            if is_high_rated:
                 self.high_rated_scene_ids.add(scene.id)

            # Extrahiere Features aus relevanten Szenen (gesehen ODER hoch bewertet)
            if is_watched or is_high_rated:
                # Tags sammeln
                if hasattr(scene, 'tags') and scene.tags:
                    for tag in scene.tags:
                        if isinstance(tag, dict) and 'id' in tag:
                            tag_id = tag['id']
                            self.preferred_tags[tag_id] = self.preferred_tags.get(tag_id, 0) + 1

                # Studio sammeln
                if hasattr(scene, 'studio') and scene.studio and isinstance(scene.studio, dict) and 'id' in scene.studio:
                     studio_id = scene.studio['id']
                     self.preferred_studios[studio_id] = self.preferred_studios.get(studio_id, 0) + 1

        # Optional: Filtere Tags/Studios, die nur selten vorkommen
        min_occurrence = self.config.getint('SceneRecommendations', 'min_preference_occurrence', fallback=2)
        self.preferred_tags = {tag_id: count for tag_id, count in self.preferred_tags.items() if count >= min_occurrence}
        self.preferred_studios = {studio_id: count for studio_id, count in self.preferred_studios.items() if count >= min_occurrence}

        logger.info(f"Präferenz-Profil erstellt: {len(self.favorite_performer_ids)} favorisierte Performer, "
                    f"{len(self.watched_scene_ids)} gesehene Szenen, {len(self.preferred_tags)} bevorzugte Tags, "
                    f"{len(self.preferred_studios)} bevorzugte Studios.")

        if not self.favorite_performer_ids and not self.watched_scene_ids and not self.high_rated_scene_ids:
             logger.warning("Keine ausreichenden Nutzerdaten (Favoriten, gesehene/bewertete Szenen) gefunden, um ein detailliertes Profil zu erstellen. Empfehlungen basieren möglicherweise auf globalen Metriken.")


    def generate_recommendations(self, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, List[Tuple[Scene, float]]]:
        """
        Generiert Szenen-Empfehlungen basierend auf verschiedenen Kriterien.

        Args:
            custom_weights: Optionales Dictionary mit benutzerdefinierten Gewichtungen.

        Returns:
            Dict[str, List[Tuple[Scene, float]]]: Empfehlungen nach Kategorien sortiert.
        """
        logger.info("Generiere Szenen-Empfehlungen...")

        if custom_weights:
            self._apply_custom_weights(custom_weights)

        # Kandidaten für Empfehlungen identifizieren (primär: ungesehene Szenen)
        candidates = self._get_recommendation_candidates()

        if not candidates:
            logger.warning("Keine geeigneten Kandidaten (ungesehene Szenen) für Empfehlungen gefunden.")
            return {}

        # --- Empfehlungen nach verschiedenen Kriterien generieren ---
        if self.enable_tag_similarity and self.preferred_tags:
            self._generate_by_tags(candidates)

        if self.enable_performer_match and self.favorite_performer_ids:
            self._generate_by_performers(candidates)

        if self.enable_studio_match and self.preferred_studios:
             self._generate_by_studios(candidates)

        if self.enable_high_quality:
             self._generate_by_quality(candidates) # Focus on high quality among unwatched

        if self.enable_novelty:
             self._generate_by_novelty(candidates) # Focus on novelty among unwatched

        # Zusätzliche Kategorie für Entdeckung: Top bewertete ungesehene Szenen
        # (Kann Szenen hervorheben, die nicht stark auf die *persönlichen* Präferenzen passen, aber generell gut sind)
        if self.enable_low_o_counter_boost:
            self._generate_top_unwatched_by_rating(candidates)


        # Top-Empfehlungen übergreifend erstellen
        self._generate_top_recommendations()

        logger.info("Szenen-Empfehlungen erfolgreich generiert")

        # Optional: Save results automatically
        # self.save_recommendations()

        return self.recommendation_categories

    def _apply_custom_weights(self, custom_weights: Dict[str, float]) -> None:
        """ Wendet benutzerdefinierte Gewichtungen an. """
        # (Implementation similar to PerformerRecommendationModule._apply_custom_weights)
        for key, value in custom_weights.items():
            # Check if the key corresponds to a weight attribute
            if key.startswith('weight_') and hasattr(self, key):
                try:
                    setattr(self, key, float(value))
                    logger.debug(f"Benutzerdefinierte Gewichtung angewendet: {key} = {value}")
                    # Update the category weight map as well
                    category_key = key.replace('weight_', '')
                    # Map specific weights to category keys if names differ
                    category_mapping = {
                         "tag_similarity": "tag_similarity",
                         "performer_match": "favorite_performers",
                         "studio_match": "preferred_studios",
                         "high_quality": "high_quality_unwatched",
                         "novelty": "novelty_unwatched",
                         "low_o_counter": "top_unwatched_overall"
                    }
                    mapped_key = category_mapping.get(category_key)
                    if mapped_key and mapped_key in self.category_weight_map:
                         self.category_weight_map[mapped_key] = float(value)

                except ValueError:
                     logger.warning(f"Ungültiger Wert für Gewichtung {key}: {value}")
            # Allow overriding other numeric/boolean config values too (add if needed)


    def _get_recommendation_candidates(self) -> List[Scene]:
        """
        Identifiziert geeignete Kandidaten für Empfehlungen.
        Primär: Szenen mit O-Counter = 0.

        Returns:
            List[Scene]: Liste geeigneter Kandidaten-Szenen.
        """
        # Filtere alle Szenen, die bereits gesehen wurden (O-Counter > 0)
        # Oder Szenen, die explizit als "watched" markiert sind, falls O-Counter nicht zuverlässig ist
        candidates = [
            scene for scene in self.scenes
            if hasattr(scene, 'o_counter') and scene.o_counter == 0 and scene.id not in self.watched_scene_ids
        ]

        # Zusätzliche Filter könnten hier angewendet werden:
        # - Mindestauflösung?
        # - Mindestdauer?
        # - Blockierte Tags/Performer/Studios?
        # Example: Filter out scenes with rating below a very low threshold
        # min_candidate_rating = self.config.getint('SceneRecommendations', 'min_candidate_rating', fallback=20)
        # candidates = [s for s in candidates if (getattr(s, 'rating100', 100) or 100) >= min_candidate_rating]

        logger.info(f"{len(candidates)} Kandidaten (ungesehene Szenen) für Empfehlungen identifiziert.")
        return candidates

    def _generate_by_tags(self, candidates: List[Scene]) -> None:
        """ Generiert Empfehlungen basierend auf Tag-Ähnlichkeit zu bevorzugten Tags. """
        logger.info("Generiere Szenen-Empfehlungen nach Tag-Ähnlichkeit...")
        if not self.preferred_tags:
             logger.warning("Keine bevorzugten Tags im Profil gefunden. Überspringe Tag-basierte Empfehlungen.")
             return

        tag_recommendations = []
        preferred_tag_set = set(self.preferred_tags.keys())

        for scene in candidates:
            if not hasattr(scene, 'tags') or not scene.tags:
                continue

            scene_tag_set = set(tag['id'] for tag in scene.tags if isinstance(tag, dict) and 'id' in tag)
            if not scene_tag_set:
                continue

            # Jaccard-Ähnlichkeit
            common_tags = preferred_tag_set.intersection(scene_tag_set)
            all_tags = preferred_tag_set.union(scene_tag_set)

            if not all_tags: continue
            similarity = len(common_tags) / len(all_tags)

            # Optional: Gewichtung nach Häufigkeit der Tags im Nutzerprofil? (Komplexer)
            # score = similarity # Einfache Jaccard-Ähnlichkeit

            if similarity >= self.min_tag_similarity_score:
                tag_recommendations.append((scene, similarity))

        tag_recommendations.sort(key=lambda x: x[1], reverse=True)
        self.recommendation_categories["tag_similarity"] = tag_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['tag_similarity'])} Empfehlungen nach Tag-Ähnlichkeit generiert.")

    def _generate_by_performers(self, candidates: List[Scene]) -> None:
        """ Generiert Empfehlungen basierend auf favorisierten Performern in der Szene. """
        logger.info("Generiere Szenen-Empfehlungen nach favorisierten Performern...")
        if not self.favorite_performer_ids:
            logger.warning("Keine favorisierten Performer gefunden. Überspringe Performer-basierte Empfehlungen.")
            return

        performer_recommendations = []
        for scene in candidates:
            if not hasattr(scene, 'performers') or not scene.performers:
                continue

            scene_performer_ids = set(p['id'] for p in scene.performers if isinstance(p, dict) and 'id' in p)
            common_performers = self.favorite_performer_ids.intersection(scene_performer_ids)

            if common_performers:
                # Score based on number of favorite performers? Or fixed score?
                # Simple approach: Score = 1.0 if any favorite is present, maybe higher if multiple.
                score = 1.0 # * len(common_performers) # Example: scale by count
                performer_recommendations.append((scene, score))

        # Sortieren (optional, da Score oft gleich ist, vielleicht nach Rating sekundär sortieren?)
        performer_recommendations.sort(key=lambda x: (x[1], getattr(x[0], 'rating100', 0) or 0), reverse=True)
        self.recommendation_categories["favorite_performers"] = performer_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['favorite_performers'])} Empfehlungen nach favorisierten Performern generiert.")


    def _generate_by_studios(self, candidates: List[Scene]) -> None:
        """ Generiert Empfehlungen basierend auf bevorzugten Studios. """
        logger.info("Generiere Szenen-Empfehlungen nach bevorzugten Studios...")
        if not self.preferred_studios:
            logger.warning("Keine bevorzugten Studios im Profil gefunden. Überspringe Studio-basierte Empfehlungen.")
            return

        studio_recommendations = []
        preferred_studio_set = set(self.preferred_studios.keys())

        for scene in candidates:
             if hasattr(scene, 'studio') and scene.studio and isinstance(scene.studio, dict) and 'id' in scene.studio:
                 studio_id = scene.studio['id']
                 if studio_id in preferred_studio_set:
                      # Score could be based on preference frequency, or just fixed
                      score = 1.0 # Simple approach
                      studio_recommendations.append((scene, score))

        # Sortieren (optional, vielleicht nach Rating sekundär sortieren?)
        studio_recommendations.sort(key=lambda x: (x[1], getattr(x[0], 'rating100', 0) or 0), reverse=True)
        self.recommendation_categories["preferred_studios"] = studio_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['preferred_studios'])} Empfehlungen nach bevorzugten Studios generiert.")

    def _generate_by_quality(self, candidates: List[Scene]) -> None:
        """ Generiert Empfehlungen für hoch bewertete ungesehene Szenen. """
        logger.info("Generiere Empfehlungen für hoch bewertete ungesehene Szenen...")
        quality_recommendations = []
        for scene in candidates:
            rating = getattr(scene, 'rating100', None)
            if rating is not None and rating >= self.min_scene_rating:
                 # Score is the normalized rating
                 score = rating / 100.0
                 quality_recommendations.append((scene, score))

        quality_recommendations.sort(key=lambda x: x[1], reverse=True)
        self.recommendation_categories["high_quality_unwatched"] = quality_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['high_quality_unwatched'])} Empfehlungen für hoch bewertete ungesehene Szenen generiert.")

    def _generate_by_novelty(self, candidates: List[Scene]) -> None:
        """ Generiert Empfehlungen für kürzlich hinzugefügte ungesehene Szenen. """
        logger.info("Generiere Empfehlungen für neue ungesehene Szenen...")
        novelty_recommendations = []
        now = datetime.now().astimezone()
        timeframe_limit = now - timedelta(days=self.novelty_timeframe)

        for scene in candidates:
            created_at_str = getattr(scene, 'created_at', None) # Assuming Scene model has created_at
            if not created_at_str:
                 # Fallback to file creation time if available?
                 if hasattr(scene, 'file') and scene.file and isinstance(scene.file, dict) and 'created_at' in scene.file:
                      created_at_str = scene.file['created_at']
                 else:
                      continue # Skip if no creation date found

            try:
                 created_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                 if created_date >= timeframe_limit:
                    days_old = (now - created_date).total_seconds() / (24 * 3600)
                    novelty_score = max(0.0, 1.0 - (days_old / self.novelty_timeframe)) if self.novelty_timeframe > 0 else 1.0
                    novelty_recommendations.append((scene, novelty_score))
            except ValueError as e:
                 logger.warning(f"Fehler beim Parsen des Erstellungsdatums '{created_at_str}' für Szene {getattr(scene, 'title', scene.id)}: {e}")
            except Exception as e:
                 logger.error(f"Unerwarteter Fehler bei Neuheitsprüfung für Szene {getattr(scene, 'title', scene.id)}: {e}")


        novelty_recommendations.sort(key=lambda x: x[1], reverse=True)
        self.recommendation_categories["novelty_unwatched"] = novelty_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.recommendation_categories['novelty_unwatched'])} Empfehlungen für neue ungesehene Szenen generiert.")

    def _generate_top_unwatched_by_rating(self, candidates: List[Scene]) -> None:
        """ Generiert eine Liste der Top-bewerteten ungesehenen Szenen (für Entdeckung). """
        logger.info("Generiere Top-Liste ungesehener Szenen nach Rating...")
        discovery_recommendations = []
        for scene in candidates:
             rating = getattr(scene, 'rating100', None)
             if rating is not None and rating > 0: # Include any rated scene
                 score = rating / 100.0
                 discovery_recommendations.append((scene, score))

        discovery_recommendations.sort(key=lambda x: x[1], reverse=True)
        self.recommendation_categories["top_unwatched_overall"] = discovery_recommendations[:self.max_recommendations * 2] # Show more for discovery?
        logger.info(f"{len(self.recommendation_categories['top_unwatched_overall'])} Top ungesehene Szenen nach Rating generiert.")


    def _generate_top_recommendations(self) -> None:
        """
        Kombiniert die Ergebnisse aus allen aktivierten Kategorien zu einer
        gewichteten Gesamtliste der Top-Empfehlungen für Szenen.
        """
        logger.info("Generiere übergreifende Top-Szenen-Empfehlungen...")
        combined_scores: Dict[str, float] = {} # scene_id -> combined_score
        scene_map: Dict[str, Scene] = {} # scene_id -> scene_object

        # Iterate through each category and its recommendations
        for category_key, recommendations in self.recommendation_categories.items():
            category_weight = self.category_weight_map.get(category_key, 0)
            if category_weight <= 0 or not recommendations:
                 continue

            logger.debug(f"Aggregiere Szenen-Kategorie '{category_key}' mit Gewicht {category_weight}")

            for scene, score in recommendations:
                 if not scene or not hasattr(scene, 'id'): continue
                 scene_id = scene.id

                 if scene_id not in scene_map:
                     scene_map[scene_id] = scene

                 current_score = combined_scores.get(scene_id, 0.0)
                 combined_scores[scene_id] = current_score + (score * category_weight)

        # Convert to list and sort
        aggregated_recommendations = [
            (scene_map[scene_id], total_score)
            for scene_id, total_score in combined_scores.items() if scene_id in scene_map
        ]
        aggregated_recommendations.sort(key=lambda x: x[1], reverse=True)

        self.top_recommendations = aggregated_recommendations[:self.max_recommendations]
        logger.info(f"{len(self.top_recommendations)} übergreifende Top-Szenen-Empfehlungen generiert")

        # Log top 5 for quick check
        for i, (s, score) in enumerate(self.top_recommendations[:5]):
            title = getattr(s, 'title', None) or f"Scene ID: {s.id}"
            logger.debug(f"Top {i+1}: {title} (Score: {score:.4f})")


    def get_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
         """
         Gibt die generierten Szenen-Empfehlungen in einem serialisierbaren Format zurück.

         Returns:
             Dict[str, List[Dict[str, Any]]]: Empfehlungen nach Kategorie und Top-Liste.
         """
         output_data = {}
         # Convert category recommendations
         for category, recs in self.recommendation_categories.items():
             output_data[category] = [
                 {"id": s.id, "title": getattr(s, 'title', 'N/A'), "score": float(score)}
                 for s, score in recs if s
             ]
         # Convert top recommendations
         output_data["top_recommendations"] = [
             {"id": s.id, "title": getattr(s, 'title', 'N/A'), "score": float(score)}
             for s, score in self.top_recommendations if s
         ]
         return output_data

    def save_recommendations(self, filename: str = "scene_recommendations.json") -> None:
        """
        Speichert die generierten Szenen-Empfehlungen in einer JSON-Datei.

        Args:
            filename: Name der Ausgabedatei.
        """
        ensure_dir(self.output_dir)
        output_path = os.path.join(self.output_dir, filename)
        recommendations_data = self.get_recommendations()

        try:
            save_json(recommendations_data, output_path)
            logger.info(f"Szenen-Empfehlungen erfolgreich gespeichert unter: {output_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Szenen-Empfehlungen: {e}")


# --- Example Usage (Simulated) ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starte Beispiel für SceneRecommendationModule...")

    # --- Mock Objects (Assume Scene model and others are defined appropriately) ---
    class MockStashAPI: pass
    class MockPerformer: # Simplified from previous example
        def __init__(self, id, name, favorite=False):
            self.id = id; self.name = name; self.favorite = favorite
    class MockScene:
        def __init__(self, id, title, tags=None, performers=None, studio=None, rating100=None, o_counter=0, created_at=None):
            self.id = id; self.title = title
            self.tags = tags if tags else [] # List of {'id': 'tag_id'}
            self.performers = performers if performers else [] # List of {'id': 'perf_id'}
            self.studio = studio # Dict {'id': 'studio_id'} or None
            self.rating100 = rating100; self.o_counter = o_counter
            self.created_at = created_at # ISO string

    class MockStatisticsModule:
        def __init__(self, scenes, performers):
            self.scenes = scenes; self.performers = performers

    class MockConfigManager: # Simplified from previous example
        def __init__(self, config_dict=None): self.config = config_dict or {}
        def get(self, section, option, fallback=None): return self.config.get(section, {}).get(option, fallback)
        def getint(self, section, option, fallback=None): return int(self.get(section, option, fallback=fallback) or fallback)
        def getfloat(self, section, option, fallback=None): return float(self.get(section, option, fallback=fallback) or fallback)
        def getboolean(self, section, option, fallback=None): return str(self.get(section, option, fallback=fallback)).lower() in ['true', '1', 'yes']

    # --- Create Mock Data ---
    now_iso = datetime.now().astimezone().isoformat()
    p1 = MockPerformer(id='p1', name='Alice', favorite=True)
    p2 = MockPerformer(id='p2', name='Betty', favorite=True)
    p3 = MockPerformer(id='p3', name='Carla', favorite=False)

    scenes_data = [
        MockScene(id='s1', title='Watched Scene A', tags=[{'id':'t1'}, {'id':'t2'}], performers=[{'id':'p1'}], studio={'id':'st1'}, rating100=90, o_counter=2, created_at=now_iso),
        MockScene(id='s2', title='Watched Scene B', tags=[{'id':'t2'}, {'id':'t3'}], performers=[{'id':'p3'}], studio={'id':'st2'}, rating100=80, o_counter=1, created_at=now_iso),
        MockScene(id='s3', title='Unwatched Fav Perf', tags=[{'id':'t4'}], performers=[{'id':'p1'}, {'id':'p2'}], studio={'id':'st1'}, rating100=85, o_counter=0, created_at=now_iso),
        MockScene(id='s4', title='Unwatched Similar Tag', tags=[{'id':'t1'}, {'id':'t3'}], performers=[{'id':'p3'}], studio={'id':'st3'}, rating100=75, o_counter=0, created_at=now_iso),
        MockScene(id='s5', title='Unwatched High Rated', tags=[{'id':'t5'}], performers=[{'id':'p3'}], studio={'id':'st2'}, rating100=95, o_counter=0, created_at=now_iso),
        MockScene(id='s6', title='Unwatched New', tags=[{'id':'t6'}], performers=[{'id':'p3'}], studio={'id':'st3'}, rating100=70, o_counter=0, created_at=(datetime.now().astimezone() - timedelta(days=5)).isoformat()),
        MockScene(id='s7', title='Unwatched Old Low Rated', tags=[{'id':'t7'}], performers=[{'id':'p3'}], studio={'id':'st3'}, rating100=40, o_counter=0, created_at=(datetime.now().astimezone() - timedelta(days=100)).isoformat()),
    ]
    performers_data = [p1, p2, p3]

    mock_api = MockStashAPI()
    mock_stats = MockStatisticsModule(scenes_data, performers_data)
    mock_config = MockConfigManager({
        'SceneRecommendations': { # Use defaults or override here
             'max_recommendations': 5,
             'min_scene_rating': 60,
             'min_tag_similarity_score': 0.2,
             'weight_tag_similarity': 0.6,
             'weight_performer_match': 0.9,
             'weight_high_quality': 0.5,
             'weight_novelty': 0.3,
             'weight_low_o_counter': 0.2, # For the discovery list
             'enable_tag_similarity': True,
             'enable_performer_match': True,
             'enable_high_quality': True,
             'enable_novelty': True,
             'enable_low_o_counter_boost': True,
             'min_preference_occurrence': 1 # For mock data simplicity
        },
        'Output': { 'output_dir': './output_recommendations' }
    })

    # --- Instantiate and Run ---
    scene_recommender = SceneRecommendationModule(mock_api, mock_stats, mock_config)
    recommendations = scene_recommender.generate_recommendations()

    # --- Print Results ---
    print("\n--- Generated Scene Recommendations ---")
    for category, recs in recommendations.items():
        print(f"\nCategory: {category}")
        if recs:
             for i, (s, score) in enumerate(recs):
                 print(f"  {i+1}. {getattr(s, 'title', s.id)} (Score: {score:.4f})")
        else:
             print("  No recommendations found.")

    print("\n--- Top Overall Scene Recommendations ---")
    if scene_recommender.top_recommendations:
         for i, (s, score) in enumerate(scene_recommender.top_recommendations):
             print(f"  {i+1}. {getattr(s, 'title', s.id)} (Score: {score:.4f})")
    else:
         print("  No top recommendations generated.")

    # --- Save Results ---
    scene_recommender.save_recommendations()
