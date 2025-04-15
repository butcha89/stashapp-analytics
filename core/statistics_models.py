"""
Statistics Models Module

Dieses Modul definiert Datenmodelle für die statistische Analyse
von StashApp-Daten. Es enthält Klassen zur Speicherung, Berechnung und 
Bereitstellung von statistischen Werten für Performer und Szenen.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import math
import datetime
from collections import Counter, defaultdict

from core.data_models import Performer, Scene

# Logger konfigurieren
logger = logging.getLogger(__name__)

class PerformerStats:
    """
    Statistikmodell für Performer-Daten.
    
    Diese Klasse speichert und berechnet statistische Werte für Performer,
    wie z.B. Durchschnittswerte, Verteilungen und Häufigkeiten.
    """
    
    def __init__(self, performers: List[Performer]):
        """
        Initialisiert das Performer-Statistikmodell und berechnet Basiswerte.
        
        Args:
            performers: Liste von Performer-Objekten
        """
        self.performers = performers
        self.total_count = len(performers)
        
        # Berechnete Statistiken
        self.favorited_count = 0
        self.rated_count = 0
        self.with_cup_size = 0
        self.with_bmi = 0
        self.with_age = 0
        
        # Verteilungen
        self.cup_distribution = {}
        self.bmi_distribution = {}
        self.age_distribution = {}
        self.rating_distribution = {}
        
        # Durchschnittswerte
        self.avg_cup_size = 0.0
        self.avg_cup_letter = ""
        self.avg_bmi = 0.0
        self.avg_age = 0.0
        self.avg_rating = 0.0
        self.avg_o_counter = 0.0
        
        # Tag-Statistiken
        self.tag_counts = {}
        
        # Berechne Statistiken
        self._calculate_basic_stats()
        self._calculate_distributions()
        self._calculate_tag_stats()
    
    def _calculate_basic_stats(self) -> None:
        """Berechnet grundlegende Statistiken über die Performer."""
        # Zähle verschiedene Performer-Gruppen
        self.favorited_count = sum(1 for p in self.performers if p.favorite)
        self.rated_count = sum(1 for p in self.performers if p.rating100 is not None)
        self.with_cup_size = sum(1 for p in self.performers if p.cup_numeric and p.cup_numeric > 0)
        self.with_bmi = sum(1 for p in self.performers if p.bmi is not None)
        self.with_age = sum(1 for p in self.performers if p.age is not None)
        
        # Berechne Durchschnittswerte
        cup_sizes = [p.cup_numeric for p in self.performers if p.cup_numeric and p.cup_numeric > 0]
        if cup_sizes:
            self.avg_cup_size = sum(cup_sizes) / len(cup_sizes)
            self.avg_cup_letter = Performer.CUP_NUMERIC_TO_LETTER.get(round(self.avg_cup_size), "?")
        
        bmis = [p.bmi for p in self.performers if p.bmi is not None]
        if bmis:
            self.avg_bmi = sum(bmis) / len(bmis)
        
        ages = [p.age for p in self.performers if p.age is not None]
        if ages:
            self.avg_age = sum(ages) / len(ages)
        
        ratings = [p.rating100 for p in self.performers if p.rating100 is not None]
        if ratings:
            self.avg_rating = sum(ratings) / len(ratings)
        
        o_counters = [p.o_counter for p in self.performers if p.o_counter > 0]
        if o_counters:
            self.avg_o_counter = sum(o_counters) / len(o_counters)
        
        logger.debug(f"Grundlegende Statistiken berechnet: {self.total_count} Performer, "
                    f"{self.favorited_count} favorisiert, {self.with_cup_size} mit Cup-Größe")
    
    def _calculate_distributions(self) -> None:
        """Berechnet Verteilungen für verschiedene Performer-Attribute."""
        # Cup-Größen-Verteilung
        cup_sizes = [p.cup_size for p in self.performers if p.cup_size]
        self.cup_distribution = dict(Counter(cup_sizes))
        
        # BMI-Kategorien-Verteilung
        bmi_categories = [p.bmi_category for p in self.performers if p.bmi_category]
        self.bmi_distribution = dict(Counter(bmi_categories))
        
        # Altersgruppen-Verteilung
        age_ranges = {
            "18-25": (18, 25),
            "26-30": (26, 30),
            "31-35": (31, 35),
            "36-40": (36, 40),
            "41-45": (41, 45),
            "46+": (46, 100)
        }
        
        age_groups = defaultdict(int)
        for p in self.performers:
            if p.age is not None:
                for range_name, (min_age, max_age) in age_ranges.items():
                    if min_age <= p.age <= max_age:
                        age_groups[range_name] += 1
                        break
        
        self.age_distribution = dict(age_groups)
        
        # Rating-Verteilung
        if any(p.rating100 is not None for p in self.performers):
            rating_stars = {}
            for p in self.performers:
                if p.rating100 is not None:
                    # Konvertiere zu 5-Sterne-Skala (gerundet)
                    stars = round(p.rating100 / 20)
                    rating_stars[stars] = rating_stars.get(stars, 0) + 1
            
            self.rating_distribution = rating_stars
        
        logger.debug("Attribut-Verteilungen berechnet")
    
    def _calculate_tag_stats(self) -> None:
        """Berechnet Statistiken zu Tags der Performer."""
        # Sammle alle Tags
        all_tags = []
        for p in self.performers:
            if hasattr(p, 'tags') and p.tags:
                all_tags.extend(p.tags)
        
        # Zähle Tag-Häufigkeiten
        self.tag_counts = dict(Counter(all_tags))
        
        logger.debug(f"{len(self.tag_counts)} verschiedene Tags gefunden")
    
    def get_top_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Gibt die häufigsten Tags zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Tags
            
        Returns:
            List[Tuple[str, int]]: Liste von (Tag, Häufigkeit) Tupeln
        """
        return Counter(self.tag_counts).most_common(limit)
    
    def get_top_rated_performers(self, limit: int = 10) -> List[Tuple[Performer, float]]:
        """
        Gibt die am höchsten bewerteten Performer zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Performer
            
        Returns:
            List[Tuple[Performer, float]]: Liste von (Performer, Rating) Tupeln
        """
        rated_performers = [(p, p.rating100) for p in self.performers if p.rating100 is not None]
        return sorted(rated_performers, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_top_o_counter_performers(self, limit: int = 10) -> List[Tuple[Performer, int]]:
        """
        Gibt die Performer mit dem höchsten O-Counter zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Performer
            
        Returns:
            List[Tuple[Performer, int]]: Liste von (Performer, O-Counter) Tupeln
        """
        countered_performers = [(p, p.o_counter) for p in self.performers if p.o_counter > 0]
        return sorted(countered_performers, key=lambda x: x[1], reverse=True)[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Statistiken in ein Dictionary zur einfachen Serialisierung.
        
        Returns:
            Dict[str, Any]: Dictionary mit allen Statistikwerten
        """
        return {
            "total_count": self.total_count,
            "favorited_count": self.favorited_count,
            "rated_count": self.rated_count,
            "with_cup_size": self.with_cup_size,
            "with_bmi": self.with_bmi,
            "with_age": self.with_age,
            
            "cup_distribution": self.cup_distribution,
            "bmi_distribution": self.bmi_distribution,
            "age_distribution": self.age_distribution,
            "rating_distribution": self.rating_distribution,
            
            "avg_cup_size": self.avg_cup_size,
            "avg_cup_letter": self.avg_cup_letter,
            "avg_bmi": self.avg_bmi,
            "avg_age": self.avg_age,
            "avg_rating": self.avg_rating,
            "avg_o_counter": self.avg_o_counter,
            
            "top_tags": dict(self.get_top_tags(20))
        }
        
class SceneStats:
    """
    Statistikmodell für Szenen-Daten.
    
    Diese Klasse speichert und berechnet statistische Werte für Szenen,
    wie z.B. Durchschnittswerte, Verteilungen und Häufigkeiten.
    """
    
    def __init__(self, scenes: List[Scene]):
        """
        Initialisiert das Szenen-Statistikmodell und berechnet Basiswerte.
        
        Args:
            scenes: Liste von Szenen-Objekten
        """
        self.scenes = scenes
        self.total_count = len(scenes)
        
        # Berechnete Statistiken
        self.rated_count = 0
        self.with_o_counter = 0
        self.with_date = 0
        
        # Verteilungen
        self.rating_distribution = {}
        self.duration_distribution = {}
        self.performer_count_distribution = {}
        self.studio_distribution = {}
        self.date_distribution = {}  # Nach Jahr/Monat
        
        # Durchschnittswerte
        self.avg_rating = 0.0
        self.avg_o_counter = 0.0
        self.avg_duration = 0.0
        self.avg_performer_count = 0.0
        
        # Tag-Statistiken
        self.tag_counts = {}
        
        # Berechne Statistiken
        self._calculate_basic_stats()
        self._calculate_distributions()
        self._calculate_tag_stats()
        self._calculate_time_stats()
    
    def _calculate_basic_stats(self) -> None:
        """Berechnet grundlegende Statistiken über die Szenen."""
        # Zähle verschiedene Szenengruppen
        self.rated_count = sum(1 for s in self.scenes if s.rating100 is not None)
        self.with_o_counter = sum(1 for s in self.scenes if s.o_counter > 0)
        self.with_date = sum(1 for s in self.scenes if s.date)
        
        # Berechne Durchschnittswerte
        ratings = [s.rating100 for s in self.scenes if s.rating100 is not None]
        if ratings:
            self.avg_rating = sum(ratings) / len(ratings)
        
        o_counters = [s.o_counter for s in self.scenes if s.o_counter > 0]
        if o_counters:
            self.avg_o_counter = sum(o_counters) / len(o_counters)
        
        durations = [s.duration for s in self.scenes if s.duration > 0]
        if durations:
            self.avg_duration = sum(durations) / len(durations)
        
        performer_counts = [len(s.performer_ids) for s in self.scenes if s.performer_ids]
        if performer_counts:
            self.avg_performer_count = sum(performer_counts) / len(performer_counts)
        
        logger.debug(f"Grundlegende Statistiken berechnet: {self.total_count} Szenen, "
                    f"{self.rated_count} bewertet, {self.with_o_counter} mit O-Counter")
    
    def _calculate_distributions(self) -> None:
        """Berechnet Verteilungen für verschiedene Szenen-Attribute."""
        # Rating-Verteilung
        if any(s.rating100 is not None for s in self.scenes):
            rating_stars = {}
            for s in self.scenes:
                if s.rating100 is not None:
                    # Konvertiere zu 5-Sterne-Skala (gerundet)
                    stars = round(s.rating100 / 20)
                    rating_stars[stars] = rating_stars.get(stars, 0) + 1
            
            self.rating_distribution = rating_stars
        
        # Dauer-Verteilung (in Minuten-Bereichen)
        duration_ranges = {
            "0-5 min": (0, 300),
            "5-10 min": (300, 600),
            "10-20 min": (600, 1200),
            "20-30 min": (1200, 1800),
            "30-60 min": (1800, 3600),
            "60+ min": (3600, float('inf'))
        }
        
        duration_groups = defaultdict(int)
        for s in self.scenes:
            if s.duration > 0:
                for range_name, (min_sec, max_sec) in duration_ranges.items():
                    if min_sec <= s.duration < max_sec:
                        duration_groups[range_name] += 1
                        break
        
        self.duration_distribution = dict(duration_groups)
        
        # Anzahl der Performer pro Szene
        performer_counts = {}
        for s in self.scenes:
            count = len(s.performer_ids) if s.performer_ids else 0
            performer_counts[count] = performer_counts.get(count, 0) + 1
        
        self.performer_count_distribution = performer_counts
        
        # Studio-Verteilung
        studios = [s.studio_name for s in self.scenes if s.studio_name]
        self.studio_distribution = dict(Counter(studios))
        
        logger.debug("Attribut-Verteilungen für Szenen berechnet")
    
    def _calculate_tag_stats(self) -> None:
        """Berechnet Statistiken zu Tags der Szenen."""
        # Sammle alle Tags
        all_tags = []
        for s in self.scenes:
            if hasattr(s, 'tags') and s.tags:
                all_tags.extend(s.tags)
        
        # Zähle Tag-Häufigkeiten
        self.tag_counts = dict(Counter(all_tags))
        
        logger.debug(f"{len(self.tag_counts)} verschiedene Tags in Szenen gefunden")
    
    def _calculate_time_stats(self) -> None:
        """Berechnet zeitbezogene Statistiken (nach Datum/Zeitraum)."""
        # Nur Szenen mit Datum berücksichtigen
        scenes_with_date = [s for s in self.scenes if s.date]
        if not scenes_with_date:
            return
        
        # Nach Jahr gruppieren
        year_groups = defaultdict(list)
        for s in scenes_with_date:
            try:
                date = datetime.datetime.strptime(s.date, "%Y-%m-%d")
                year = date.year
                year_groups[year].append(s)
            except ValueError:
                continue
        
        # Zeitliche Verteilung nach Jahr
        date_distribution = {}
        for year, scenes in year_groups.items():
            date_distribution[str(year)] = len(scenes)
        
        self.date_distribution = date_distribution
        
        logger.debug(f"Zeitliche Statistiken für {len(scenes_with_date)} Szenen berechnet")
    
    def get_top_tags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Gibt die häufigsten Tags zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Tags
            
        Returns:
            List[Tuple[str, int]]: Liste von (Tag, Häufigkeit) Tupeln
        """
        return Counter(self.tag_counts).most_common(limit)
    
    def get_top_rated_scenes(self, limit: int = 10) -> List[Tuple[Scene, float]]:
        """
        Gibt die am höchsten bewerteten Szenen zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Szenen
            
        Returns:
            List[Tuple[Scene, float]]: Liste von (Szene, Rating) Tupeln
        """
        rated_scenes = [(s, s.rating100) for s in self.scenes if s.rating100 is not None]
        return sorted(rated_scenes, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_top_o_counter_scenes(self, limit: int = 10) -> List[Tuple[Scene, int]]:
        """
        Gibt die Szenen mit dem höchsten O-Counter zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Szenen
            
        Returns:
            List[Tuple[Scene, int]]: Liste von (Szene, O-Counter) Tupeln
        """
        countered_scenes = [(s, s.o_counter) for s in self.scenes if s.o_counter > 0]
        return sorted(countered_scenes, key=lambda x: x[1], reverse=True)[:limit]
    
    def get_most_common_studios(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Gibt die häufigsten Studios zurück.
        
        Args:
            limit: Maximale Anzahl zurückzugebender Studios
            
        Returns:
            List[Tuple[str, int]]: Liste von (Studio, Häufigkeit) Tupeln
        """
        return Counter(self.studio_distribution).most_common(limit)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Statistiken in ein Dictionary zur einfachen Serialisierung.
        
        Returns:
            Dict[str, Any]: Dictionary mit allen Statistikwerten
        """
        return {
            "total_count": self.total_count,
            "rated_count": self.rated_count,
            "with_o_counter": self.with_o_counter,
            "with_date": self.with_date,
            
            "rating_distribution": self.rating_distribution,
            "duration_distribution": self.duration_distribution,
            "performer_count_distribution": self.performer_count_distribution,
            "studio_distribution": self.studio_distribution,
            "date_distribution": self.date_distribution,
            
            "avg_rating": self.avg_rating,
            "avg_o_counter": self.avg_o_counter,
            "avg_duration": self.avg_duration,
            "avg_performer_count": self.avg_performer_count,
            
            "top_tags": dict(self.get_top_tags(20)),
            "top_studios": dict(self.get_most_common_studios(10))
        }
