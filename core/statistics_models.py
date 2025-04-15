"""
Statistics Models Module

Dieses Modul enthält Klassen zur Berechnung und Verwaltung von Statistiken
für Performer und Szenen.
"""

import math
import datetime
from typing import Dict, List, Any, Optional, Set, Tuple, Union
import logging

from .data_models import Performer, Scene

# Logger konfigurieren
logger = logging.getLogger(__name__)

class PerformerStats:
    """Klasse zur Berechnung und Verwaltung von Performer-Statistiken."""
    
    def __init__(self, performers: List[Performer]):
        """
        Initialisiert die Statistikklasse mit einer Liste von Performern.
        
        Args:
            performers: Liste von Performer-Objekten
        """
        self.performers = performers
        self.total_count = len(performers)
        
        # Berechnete Statistiken
        self.cup_distribution = self._calculate_cup_distribution()
        self.bmi_distribution = self._calculate_bmi_distribution()
        self.rating_distribution = self._calculate_rating_distribution()
        self.age_distribution = self._calculate_age_distribution()
        self.o_counter_distribution = self._calculate_o_counter_distribution()
        
        # Durchschnittswerte
        self.avg_cup_size = self._calculate_avg(
            [p.cup_numeric for p in performers if p.cup_numeric > 0]
        )
        self.avg_bmi = self._calculate_avg(
            [p.bmi for p in performers if p.bmi is not None]
        )
        self.avg_age = self._calculate_avg(
            [p.age for p in performers if p.age is not None]
        )
        self.avg_rating = self._calculate_avg(
            [p.rating100 for p in performers if p.rating100 is not None]
        )
        self.avg_o_counter = self._calculate_avg(
            [p.o_counter for p in performers if p.o_counter > 0]
        )
        
        # Cup-Size Statistiken
        self.cup_stats = self._calculate_cup_stats()
    
    @staticmethod
    def _calculate_avg(values: List[Union[int, float]]) -> Optional[float]:
        """Berechnet den Durchschnitt einer Liste von Werten."""
        return round(sum(values) / len(values), 2) if values else None
    
    def _calculate_cup_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung der Cup-Größen."""
        distribution = {}
        for p in self.performers:
            if p.cup_size:
                distribution[p.cup_size] = distribution.get(p.cup_size, 0) + 1
        return distribution
    
    def _calculate_bmi_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung der BMI-Kategorien."""
        distribution = {}
        for p in self.performers:
            if p.bmi_category:
                distribution[p.bmi_category] = distribution.get(p.bmi_category, 0) + 1
        return distribution
    
    def _calculate_rating_distribution(self) -> Dict[int, int]:
        """Berechnet die Verteilung der Bewertungen (in Sternen)."""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for p in self.performers:
            if p.rating100 is not None:
                stars = min(5, max(1, int(round(p.rating100 / 20))))
                distribution[stars] = distribution.get(stars, 0) + 1
        return distribution
    
    def _calculate_age_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung der Altersgruppen."""
        distribution = {}
        age_groups = {
            "18-25": (18, 25),
            "26-30": (26, 30),
            "31-35": (31, 35),
            "36-40": (36, 40),
            "41-45": (41, 45),
            "46+": (46, 100)
        }
        
        for p in self.performers:
            if p.age is not None:
                for group, (min_age, max_age) in age_groups.items():
                    if min_age <= p.age <= max_age:
                        distribution[group] = distribution.get(group, 0) + 1
                        break
        
        return distribution
    
    def _calculate_o_counter_distribution(self) -> Dict[int, int]:
        """Berechnet die Verteilung der O-Counter-Werte."""
        distribution = {}
        for p in self.performers:
            if p.o_counter > 0:
                distribution[p.o_counter] = distribution.get(p.o_counter, 0) + 1
        return distribution
    
    def _calculate_cup_stats(self) -> Dict[str, Any]:
        """Berechnet detaillierte Statistiken für Cup-Größen."""
        cup_sizes = [p.cup_numeric for p in self.performers if p.cup_numeric > 0]
        if not cup_sizes:
            return {}
        
        # Sortierte Versionen für konsistente Ausgabe
        sorted_cup_sizes = sorted(self.cup_distribution.keys(), key=lambda x: (len(x), x))
        
        # Mittelwert und Standardabweichung
        mean = sum(cup_sizes) / len(cup_sizes)
        variance = sum((x - mean) ** 2 for x in cup_sizes) / len(cup_sizes)
        std_dev = math.sqrt(variance)
        
        # Häufigste Cup-Größe
        most_common_cup = max(self.cup_distribution.items(), key=lambda x: x[1])
        
        return {
            "mean": round(mean, 2),
            "mean_letter": Performer.CUP_NUMERIC_TO_LETTER.get(round(mean), "?"),
            "std_dev": round(std_dev, 2),
            "min": min(cup_sizes),
            "min_letter": Performer.CUP_NUMERIC_TO_LETTER.get(min(cup_sizes), "?"),
            "max": max(cup_sizes),
            "max_letter": Performer.CUP_NUMERIC_TO_LETTER.get(max(cup_sizes), "?"),
            "most_common": most_common_cup[0],
            "most_common_count": most_common_cup[1],
            "sorted_cup_sizes": sorted_cup_sizes,
            "numeric_cup_values": cup_sizes
        }
    
    def get_top_o_counter_performers(self, limit: int = 10) -> List[Performer]:
        """Ermittelt die Performer mit dem höchsten O-Counter."""
        sorted_performers = sorted(
            [p for p in self.performers if p.o_counter > 0],
            key=lambda p: p.o_counter,
            reverse=True
        )
        return sorted_performers[:limit]
    
    def get_similar_performers(self, performer: Performer, 
                               min_similarity: float = 0.7, 
                               max_results: int = 10) -> List[Tuple[Performer, float]]:
        """
        Findet ähnliche Performer basierend auf Cup-Größe, BMI und anderen Faktoren.
        
        Args:
            performer: Der Performer, zu dem ähnliche gefunden werden sollen
            min_similarity: Minimaler Ähnlichkeitswert (0-1)
            max_results: Maximale Anzahl an Ergebnissen
            
        Returns:
            List[Tuple[Performer, float]]: Liste von (Performer, Ähnlichkeitswert) Tupeln
        """
        if not performer.cup_numeric or performer.cup_numeric <= 0:
            return []
        
        similarities = []
        
        for p in self.performers:
            if p.id == performer.id or not p.cup_numeric or p.cup_numeric <= 0:
                continue
                
            # Cup-Größen-Ähnlichkeit (0-1)
            cup_diff = abs(performer.cup_numeric - p.cup_numeric)
            cup_similarity = max(0, 1 - (cup_diff / 5))  # Maximal 5 Cup-Größen Unterschied
            
            # BMI-Ähnlichkeit, falls verfügbar (0-1)
            bmi_similarity = 0
            if performer.bmi is not None and p.bmi is not None:
                bmi_diff = abs(performer.bmi - p.bmi)
                bmi_similarity = max(0, 1 - (bmi_diff / 10))  # Maximal 10 BMI Punkte Unterschied
            
            # Alters-Ähnlichkeit, falls verfügbar (0-1)
            age_similarity = 0
            if performer.age is not None and p.age is not None:
                age_diff = abs(performer.age - p.age)
                age_similarity = max(0, 1 - (age_diff / 20))  # Maximal 20 Jahre Unterschied
            
            # Tag-Ähnlichkeit (0-1)
            common_tags = set(performer.tags).intersection(set(p.tags))
            all_tags = set(performer.tags).union(set(p.tags))
            tag_similarity = len(common_tags) / max(1, len(all_tags))
            
            # Gewichtete Gesamtähnlichkeit
            total_similarity = (
                0.4 * cup_similarity + 
                0.2 * bmi_similarity + 
                0.2 * age_similarity + 
                0.2 * tag_similarity
            )
            
            if total_similarity >= min_similarity:
                similarities.append((p, total_similarity))
        
        # Sortieren nach Ähnlichkeit und Begrenzung der Ergebnisse
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:max_results]
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert alle Statistiken in ein Dictionary."""
        return {
            "total_count": self.total_count,
            "cup_distribution": self.cup_distribution,
            "bmi_distribution": self.bmi_distribution,
            "rating_distribution": self.rating_distribution,
            "age_distribution": self.age_distribution,
            "o_counter_distribution": self.o_counter_distribution,
            "avg_cup_size": self.avg_cup_size,
            "avg_bmi": self.avg_bmi,
            "avg_age": self.avg_age,
            "avg_rating": self.avg_rating,
            "avg_o_counter": self.avg_o_counter,
            "cup_stats": self.cup_stats
        }


class SceneStats:
    """Klasse zur Berechnung und Verwaltung von Szenen-Statistiken."""
    
    def __init__(self, scenes: List[Scene]):
        """
        Initialisiert die Statistikklasse mit einer Liste von Szenen.
        
        Args:
            scenes: Liste von Szenen-Objekten
        """
        self.scenes = scenes
        self.total_count = len(scenes)
        
        # Berechnete Statistiken
        self.rating_distribution = self._calculate_rating_distribution()
        self.o_counter_distribution = self._calculate_o_counter_distribution()
        self.tag_distribution = self._calculate_tag_distribution()
        self.studio_distribution = self._calculate_studio_distribution()
        self.age_distribution = self._calculate_age_distribution()
        
        # Durchschnittswerte
        self.avg_rating = self._calculate_avg(
            [s.rating100 for s in scenes if s.rating100 is not None]
        )
        self.avg_o_counter = self._calculate_avg(
            [s.o_counter for s in scenes if s.o_counter > 0]
        )
        self.avg_duration = self._calculate_avg(
            [s.duration for s in scenes if s.duration > 0]
        )
        
        # O-Counter-bezogene Statistiken
        self.popular_tags_in_high_o_counter = self._calculate_popular_tags_in_high_o_counter()
    
    @staticmethod
    def _calculate_avg(values: List[Union[int, float]]) -> Optional[float]:
        """Berechnet den Durchschnitt einer Liste von Werten."""
        return round(sum(values) / len(values), 2) if values else None
    
    def _calculate_rating_distribution(self) -> Dict[int, int]:
        """Berechnet die Verteilung der Bewertungen (in Sternen)."""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for s in self.scenes:
            if s.rating100 is not None:
                stars = min(5, max(1, round(s.rating100 / 20)))
                distribution[stars] = distribution.get(stars, 0) + 1
        return distribution
    
    def _calculate_o_counter_distribution(self) -> Dict[int, int]:
        """Berechnet die Verteilung der O-Counter-Werte."""
        distribution = {}
        for s in self.scenes:
            if s.o_counter > 0:
                distribution[s.o_counter] = distribution.get(s.o_counter, 0) + 1
        return distribution
    
    def _calculate_tag_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung der Tags."""
        distribution = {}
        for s in self.scenes:
            for tag in s.tags:
                distribution[tag] = distribution.get(tag, 0) + 1
        return distribution
    
    def _calculate_studio_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung der Studios."""
        distribution = {}
        for s in self.scenes:
            if s.studio_name:
                distribution[s.studio_name] = distribution.get(s.studio_name, 0) + 1
        return distribution
    
    def _calculate_age_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung des Alters der Szenen (in Monaten)."""
        distribution = {}
        for s in self.scenes:
            if s.date:
                try:
                    date = datetime.datetime.strptime(s.date, "%Y-%m-%d")
                    now = datetime.datetime.now()
                    age_months = (now.year - date.year) * 12 + now.month - date.month
                    age_group = f"{age_months // 6 * 6}-{(age_months // 6 + 1) * 6}" # 6-Monats-Intervalle
                    distribution[age_group] = distribution.get(age_group, 0) + 1
                except ValueError:
                    # Ungültiges Datumsformat
                    pass
        return distribution
    
    def _calculate_popular_tags_in_high_o_counter(self) -> Dict[str, int]:
        """Berechnet die häufigsten Tags in Szenen mit hohem O-Counter."""
        # Szenen mit O-Counter im obersten Quartil
        o_counters = [s.o_counter for s in self.scenes if s.o_counter > 0]
        if not o_counters:
            return {}
        
        threshold = sorted(o_counters)[int(len(o_counters) * 0.75)]
        high_o_counter_scenes = [s for s in self.scenes if s.o_counter >= threshold]
        
        # Tags in diesen Szenen zählen
        tag_counts = {}
        for s in high_o_counter_scenes:
            for tag in s.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return tag_counts
    
    def get_scenes_by_performer(self, performer_id: str) -> List[Scene]:
        """Gibt alle Szenen eines bestimmten Performers zurück."""
        return [s for s in self.scenes if performer_id in s.performer_ids]
    
    def get_most_watched_scenes(self, limit: int = 10) -> List[Scene]:
        """Gibt die am meisten gesehenen Szenen zurück (nach O-Counter)."""
        sorted_scenes = sorted(
            [s for s in self.scenes if s.o_counter > 0],
            key=lambda s: s.o_counter,
            reverse=True
        )
        return sorted_scenes[:limit]
    
    def get_highest_rated_scenes(self, limit: int = 10) -> List[Scene]:
        """Gibt die am höchsten bewerteten Szenen zurück."""
        sorted_scenes = sorted(
            [s for s in self.scenes if s.rating100 is not None],
            key=lambda s: s.rating100,
            reverse=True
        )
        return sorted_scenes[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert alle Statistiken in ein Dictionary."""
        return {
            "total_count": self.total_count,
            "rating_distribution": self.rating_distribution,
            "o_counter_distribution": self.o_counter_distribution,
            "tag_distribution": {k: v for k, v in sorted(self.tag_distribution.items(), 
                                                        key=lambda x: x[1], 
                                                        reverse=True)[:20]}, # Top 20 Tags
            "studio_distribution": {k: v for k, v in sorted(self.studio_distribution.items(), 
                                                           key=lambda x: x[1], 
                                                           reverse=True)[:20]}, # Top 20 Studios
            "age_distribution": self.age_distribution,
            "avg_rating": self.avg_rating,
            "avg_o_counter": self.avg_o_counter,
            "avg_duration": self.avg_duration,
            "popular_tags_in_high_o_counter": {k: v for k, v in sorted(self.popular_tags_in_high_o_counter.items(), 
                                                                    key=lambda x: x[1], 
                                                                    reverse=True)[:10]} # Top 10 Tags
        }
