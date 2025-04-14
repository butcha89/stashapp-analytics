"""
Statistics Module

Dieses Modul ist verantwortlich für die Berechnung und Analyse aller statistischen
Daten aus den StashApp-Daten. Es verarbeitet Performer- und Szenen-Daten und 
berechnet Statistiken wie Durchschnittswerte, Verteilungen und Korrelationen.
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
from collections import Counter, defaultdict

# Interne Importe
from core.stash_api import StashAPI
from core.data_models import Performer, Scene
from core.utils import save_json, ensure_dir, calculate_jaccard_similarity
from core.statistics_models import PerformerStats, SceneStats
from management.config_manager import ConfigManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class StatisticsModule:
    """
    Klasse zur Berechnung von Statistiken aus StashApp-Daten.
    
    Diese Klasse ist verantwortlich für:
    - Laden von Daten aus der StashApp API
    - Konvertierung in Performer- und Szenen-Objekte
    - Berechnung verschiedener Statistiken
    - Speichern der Ergebnisse
    """
    
    def __init__(self, api: StashAPI, config: ConfigManager):
        """
        Initialisiert das Statistik-Modul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.config = config
        
        # Daten-Container
        self.performers = []
        self.scenes = []
        self.raw_performers = []
        self.raw_scenes = []
        
        # Statistische Objekte
        self.performer_stats = None
        self.scene_stats = None
        self.correlation_stats = {}
        
        # Kategorische Daten
        self.cup_size_groups = {}
        self.bmi_groups = {}
        self.age_groups = {}
        self.tag_frequency = {}
        
        # Zeitliche Daten
        self.time_series_data = {}
        self.seasonal_data = {}
        
        # Ausgabe-Konfiguration
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')
        self.decimal_places = self.config.getint('Statistics', 'decimal_places', fallback=2)
        self.min_data_points = self.config.getint('Statistics', 'min_data_points', fallback=5)
        
        # Statistik-Optionen
        self.calculate_cup_stats = self.config.getboolean('Statistics', 'calculate_cup_stats', fallback=True)
        self.calculate_bmi_stats = self.config.getboolean('Statistics', 'calculate_bmi_stats', fallback=True)
        self.calculate_rating_stats = self.config.getboolean('Statistics', 'calculate_rating_stats', fallback=True)
        self.calculate_o_counter_stats = self.config.getboolean('Statistics', 'calculate_o_counter_stats', fallback=True)
        self.calculate_age_stats = self.config.getboolean('Statistics', 'calculate_age_stats', fallback=True)
        self.calculate_correlations = self.config.getboolean('Statistics', 'calculate_correlations', fallback=True)
        
        # Ausreißerbehandlung
        self.outlier_detection = self.config.get('Statistics', 'outlier_detection', fallback='IQR')
        
        logger.info("Statistik-Modul initialisiert")
    
    def load_data(self) -> Tuple[int, int]:
        """
        Lädt Performer- und Szenen-Daten aus der StashApp API.
        
        Returns:
            Tuple[int, int]: Anzahl von geladenen (Performern, Szenen)
        """
        logger.info("Lade Daten von StashApp...")
        
        # Performer laden
        start_time = time.time()
        self.raw_performers = self.api.get_all_performers()
        self.performers = [Performer(p) for p in self.raw_performers]
        performer_load_time = time.time() - start_time
        logger.info(f"{len(self.performers)} Performer in {performer_load_time:.2f} Sekunden geladen")
        
        # Szenen laden
        start_time = time.time()
        self.raw_scenes = self.api.get_all_scenes()
        self.scenes = [Scene(s, self.performers) for s in self.raw_scenes]
        scene_load_time = time.time() - start_time
        logger.info(f"{len(self.scenes)} Szenen in {scene_load_time:.2f} Sekunden geladen")
        
        return len(self.performers), len(self.scenes)
    
    def get_favorite_performers(self) -> List[Performer]:
        """
        Gibt eine Liste der favorisierten Performer zurück.
        
        Returns:
            List[Performer]: Liste der favorisierten Performer
        """
        return [p for p in self.performers if p.favorite]
    
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
        o_counter_performers = [(p, p.o_counter) for p in self.performers if p.o_counter > 0]
        return sorted(o_counter_performers, key=lambda x: x[1], reverse=True)[:limit]
    
    def calculate_all_statistics(self) -> Dict[str, Any]:
        """
        Berechnet alle konfigurierten Statistiken.
        
        Returns:
            Dict[str, Any]: Dictionary mit allen berechneten Statistiken
        """
        if not self.performers:
            self.load_data()
        
        logger.info("Berechne Statistiken...")
        start_time = time.time()
        
        # Performer-Statistiken berechnen
        self.performer_stats = PerformerStats(self.performers)
        
        # Szenen-Statistiken berechnen
        self.scene_stats = SceneStats(self.scenes)
        
        # Kategorische Daten berechnen
        if self.calculate_cup_stats:
            self._calculate_cup_size_stats()
            
        if self.calculate_bmi_stats:
            self._calculate_bmi_stats()
            
        if self.calculate_age_stats:
            self._calculate_age_stats()
        
        # Zeitliche Daten berechnen
        self._calculate_time_series()
        
        # Tag-Frequenzen berechnen
        self._calculate_tag_frequencies()
        
        # Korrelationen berechnen
        if self.calculate_correlations:
            self._calculate_correlations()
        
        total_time = time.time() - start_time
        logger.info(f"Alle Statistiken in {total_time:.2f} Sekunden berechnet")
        
        # Statistik-Ergebnisse zusammenstellen
        stats_results = {
            "general": self._get_general_stats(),
            "performers": self.performer_stats.to_dict() if self.performer_stats else {},
            "scenes": self.scene_stats.to_dict() if self.scene_stats else {},
            "cup_sizes": self.cup_size_groups,
            "bmi": self.bmi_groups,
            "age": self.age_groups,
            "tags": self.tag_frequency,
            "time_series": self.time_series_data,
            "seasonal": self.seasonal_data,
            "correlations": self.correlation_stats
        }
        
        return stats_results
    
    def _calculate_cup_size_stats(self) -> None:
        """
        Berechnet detaillierte Statistiken über Cup-Größen.
        """
        logger.info("Berechne Cup-Größen-Statistiken...")
        
        # Performer mit gültigen Cup-Größen filtern
        performers_with_cups = [p for p in self.performers if p.cup_numeric > 0]
        
        if len(performers_with_cups) < self.min_data_points:
            logger.warning(f"Zu wenige Performer mit Cup-Größen ({len(performers_with_cups)}/{self.min_data_points})")
            return
        
        # Gruppieren nach Cup-Größe
        cup_size_groups = defaultdict(list)
        for p in performers_with_cups:
            cup_size_groups[p.cup_size].append(p)
        
        # Statistiken pro Cup-Größe
        cup_stats = {}
        for cup, performers in cup_size_groups.items():
            if not cup:
                continue
                
            # BMI-Verteilung pro Cup-Größe
            bmis = [p.bmi for p in performers if p.bmi is not None]
            
            # Rating-Verteilung pro Cup-Größe
            ratings = [p.rating100 for p in performers if p.rating100 is not None]
            
            # O-Counter-Verteilung pro Cup-Größe
            o_counters = [p.o_counter for p in performers if p.o_counter > 0]
            
            # Durchschnittswerte berechnen
            cup_stats[cup] = {
                "count": len(performers),
                "avg_bmi": self._safe_avg(bmis),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "performer_ids": [p.id for p in performers]
            }
        
        # Zusammenfassung für alle Cup-Größen
        all_cup_numeric = [p.cup_numeric for p in performers_with_cups]
        
        summary = {
            "total_count": len(performers_with_cups),
            "avg_cup_numeric": self._safe_avg(all_cup_numeric),
            "avg_cup_letter": Performer.CUP_NUMERIC_TO_LETTER.get(
                round(self._safe_avg(all_cup_numeric) or 0), "?"
            ),
            "cup_distribution": dict(sorted(Counter([p.cup_size for p in performers_with_cups]).items())),
            "most_common": Counter([p.cup_size for p in performers_with_cups]).most_common(3)
        }
        
        # Zusätzliche Analysen für Cup-Größen
        if len(performers_with_cups) >= 10:
            # Durchschnittliche Cup-Größe nach Ländern
            countries = defaultdict(list)
            for p in performers_with_cups:
                if p.country:
                    countries[p.country].append(p.cup_numeric)
            
            country_cup_avg = {}
            for country, cups in countries.items():
                if len(cups) >= 5:  # Mindestens 5 Performer pro Land
                    country_cup_avg[country] = {
                        "avg_cup_numeric": self._safe_avg(cups),
                        "avg_cup_letter": Performer.CUP_NUMERIC_TO_LETTER.get(
                            round(self._safe_avg(cups) or 0), "?"
                        ),
                        "count": len(cups)
                    }
            
            summary["country_averages"] = country_cup_avg
        
        # Speichere die Ergebnisse
        self.cup_size_groups = {
            "per_cup_size": cup_stats,
            "summary": summary
        }
        
        logger.info(f"Cup-Größen-Statistiken für {len(cup_stats)} verschiedene Cup-Größen berechnet")
    
    def _calculate_bmi_stats(self) -> None:
        """
        Berechnet detaillierte Statistiken über BMI-Werte.
        """
        logger.info("Berechne BMI-Statistiken...")
        
        # Performer mit gültigen BMI-Werten filtern
        performers_with_bmi = [p for p in self.performers if p.bmi is not None]
        
        if len(performers_with_bmi) < self.min_data_points:
            logger.warning(f"Zu wenige Performer mit BMI-Werten ({len(performers_with_bmi)}/{self.min_data_points})")
            return
        
        # Gruppieren nach BMI-Kategorie
        bmi_groups = defaultdict(list)
        for p in performers_with_bmi:
            bmi_groups[p.bmi_category].append(p)
        
        # Statistiken pro BMI-Kategorie
        bmi_stats = {}
        for category, performers in bmi_groups.items():
            if not category:
                continue
                
            # Cup-Größen-Verteilung pro BMI-Kategorie
            cups = [p.cup_numeric for p in performers if p.cup_numeric > 0]
            
            # Rating-Verteilung pro BMI-Kategorie
            ratings = [p.rating100 for p in performers if p.rating100 is not None]
            
            # O-Counter-Verteilung pro BMI-Kategorie
            o_counters = [p.o_counter for p in performers if p.o_counter > 0]
            
            # Durchschnittswerte berechnen
            bmi_stats[category] = {
                "count": len(performers),
                "avg_cup_numeric": self._safe_avg(cups),
                "avg_cup_letter": Performer.CUP_NUMERIC_TO_LETTER.get(
                    round(self._safe_avg(cups) or 0), "?"
                ),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "performer_ids": [p.id for p in performers]
            }
        
        # Zusammenfassung für alle BMI-Werte
        all_bmi = [p.bmi for p in performers_with_bmi]
        bmi_categories = [p.bmi_category for p in performers_with_bmi if p.bmi_category]
        
        # Entferne potenzielle Ausreißer für eine robustere Statistik
        filtered_bmi = self._filter_outliers(all_bmi) if self.outlier_detection else all_bmi
        
        summary = {
            "total_count": len(performers_with_bmi),
            "avg_bmi": self._safe_avg(filtered_bmi),
            "min_bmi": min(filtered_bmi) if filtered_bmi else None,
            "max_bmi": max(filtered_bmi) if filtered_bmi else None,
            "median_bmi": self._safe_median(filtered_bmi),
            "category_distribution": dict(sorted(Counter(bmi_categories).items())),
            "most_common_category": Counter(bmi_categories).most_common(1)[0][0] if bmi_categories else None
        }
        
        # Speichere die Ergebnisse
        self.bmi_groups = {
            "per_category": bmi_stats,
            "summary": summary
        }
        
        logger.info(f"BMI-Statistiken für {len(bmi_stats)} verschiedene BMI-Kategorien berechnet")
    
    def _calculate_age_stats(self) -> None:
        """
        Berechnet detaillierte Statistiken über Altersverteilungen.
        """
        logger.info("Berechne Alters-Statistiken...")
        
        # Performer mit gültigem Alter filtern
        performers_with_age = [p for p in self.performers if p.age is not None]
        
        if len(performers_with_age) < self.min_data_points:
            logger.warning(f"Zu wenige Performer mit Altersangaben ({len(performers_with_age)}/{self.min_data_points})")
            return
        
        # Altersgruppen definieren
        age_ranges = {
            "18-25": (18, 25),
            "26-30": (26, 30),
            "31-35": (31, 35),
            "36-40": (36, 40),
            "41-45": (41, 45),
            "46+": (46, 100)
        }
        
        # Performer in Altersgruppen einteilen
        age_groups = defaultdict(list)
        for p in performers_with_age:
            for range_name, (min_age, max_age) in age_ranges.items():
                if min_age <= p.age <= max_age:
                    age_groups[range_name].append(p)
                    break
        
        # Statistiken pro Altersgruppe
        age_stats = {}
        for range_name, performers in age_groups.items():
            # Cup-Größen-Verteilung pro Altersgruppe
            cups = [p.cup_numeric for p in performers if p.cup_numeric > 0]
            
            # BMI-Verteilung pro Altersgruppe
            bmis = [p.bmi for p in performers if p.bmi is not None]
            
            # Rating-Verteilung pro Altersgruppe
            ratings = [p.rating100 for p in performers if p.rating100 is not None]
            
            # O-Counter-Verteilung pro Altersgruppe
            o_counters = [p.o_counter for p in performers if p.o_counter > 0]
            
            # Durchschnittswerte berechnen
            age_stats[range_name] = {
                "count": len(performers),
                "avg_cup_numeric": self._safe_avg(cups),
                "avg_cup_letter": Performer.CUP_NUMERIC_TO_LETTER.get(
                    round(self._safe_avg(cups) or 0), "?"
                ),
                "avg_bmi": self._safe_avg(bmis),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "performer_ids": [p.id for p in performers]
            }
        
        # Zusammenfassung für alle Altersangaben
        all_ages = [p.age for p in performers_with_age]
        
        # Entferne potenzielle Ausreißer für eine robustere Statistik
        filtered_ages = self._filter_outliers(all_ages) if self.outlier_detection else all_ages
        
        summary = {
            "total_count": len(performers_with_age),
            "avg_age": self._safe_avg(filtered_ages),
            "min_age": min(filtered_ages) if filtered_ages else None,
            "max_age": max(filtered_ages) if filtered_ages else None,
            "median_age": self._safe_median(filtered_ages),
            "age_distribution": {range_name: len(performers) for range_name, performers in age_groups.items()}
        }
        
        # Speichere die Ergebnisse
        self.age_groups = {
            "per_range": age_stats,
            "summary": summary
        }
        
        logger.info(f"Alters-Statistiken für {len(age_stats)} verschiedene Altersgruppen berechnet")
    
    def _calculate_time_series(self) -> None:
        """
        Berechnet Zeitreihenanalysen für Szenen und Performer.
        """
        logger.info("Berechne Zeitreihenanalysen...")
        
        # Szenen mit gültigem Datum filtern
        scenes_with_date = [s for s in self.scenes if s.date]
        
        if len(scenes_with_date) < self.min_data_points:
            logger.warning(f"Zu wenige Szenen mit Datumsangaben ({len(scenes_with_date)}/{self.min_data_points})")
            return
        
        # Gruppieren nach Jahr und Monat
        monthly_data = defaultdict(list)
        yearly_data = defaultdict(list)
        
        for scene in scenes_with_date:
            try:
                date = datetime.datetime.strptime(scene.date, "%Y-%m-%d")
                year_key = date.year
                month_key = f"{date.year}-{date.month:02d}"
                
                yearly_data[year_key].append(scene)
                monthly_data[month_key].append(scene)
            except Exception as e:
                logger.warning(f"Fehler bei der Datumsverarbeitung für Szene {scene.id}: {str(e)}")
        
        # Monatliche Statistiken
        monthly_stats = {}
        for month_key, scenes in sorted(monthly_data.items()):
            ratings = [s.rating100 for s in scenes if s.rating100 is not None]
            o_counters = [s.o_counter for s in scenes if s.o_counter > 0]
            
            monthly_stats[month_key] = {
                "scene_count": len(scenes),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "total_o_counter": sum(s.o_counter for s in scenes)
            }
        
        # Jährliche Statistiken
        yearly_stats = {}
        for year_key, scenes in sorted(yearly_data.items()):
            ratings = [s.rating100 for s in scenes if s.rating100 is not None]
            o_counters = [s.o_counter for s in scenes if s.o_counter > 0]
            
            yearly_stats[year_key] = {
                "scene_count": len(scenes),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "total_o_counter": sum(s.o_counter for s in scenes)
            }
        
        # Saisonale Statistiken (nach Monaten)
        monthly_aggregated = defaultdict(list)
        for scene in scenes_with_date:
            try:
                date = datetime.datetime.strptime(scene.date, "%Y-%m-%d")
                month = date.month
                monthly_aggregated[month].append(scene)
            except Exception:
                pass
        
        seasonal_stats = {}
        for month, scenes in sorted(monthly_aggregated.items()):
            ratings = [s.rating100 for s in scenes if s.rating100 is not None]
            o_counters = [s.o_counter for s in scenes if s.o_counter > 0]
            
            seasonal_stats[month] = {
                "scene_count": len(scenes),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "total_o_counter": sum(s.o_counter for s in scenes)
            }
        
        # Speichere die Ergebnisse
        self.time_series_data = {
            "monthly": monthly_stats,
            "yearly": yearly_stats
        }
        
        self.seasonal_data = seasonal_stats
        
        logger.info(f"Zeitreihenanalysen für {len(monthly_stats)} Monate und {len(yearly_stats)} Jahre berechnet")
    
    def _calculate_tag_frequencies(self) -> None:
        """
        Berechnet Häufigkeitsverteilungen und Statistiken für Tags.
        """
        logger.info("Berechne Tag-Frequenzen...")
        
        # Tags von Performern sammeln
        performer_tags = []
        for p in self.performers:
            performer_tags.extend(p.tags)
        
        # Tags von Szenen sammeln
        scene_tags = []
        for s in self.scenes:
            scene_tags.extend(s.tags)
        
        # Häufigkeiten berechnen
        performer_tag_freq = Counter(performer_tags)
        scene_tag_freq = Counter(scene_tags)
        
        # Top-Tags bestimmen
        top_performer_tags = performer_tag_freq.most_common(20)
        top_scene_tags = scene_tag_freq.most_common(20)
        
        # Tag-Statistiken nach Kategorie
        tag_stats = {}
        
        # Für Performer-Tags: Rating und O-Counter durchschnitte
        for tag, _ in top_performer_tags:
            performers_with_tag = [p for p in self.performers if tag in p.tags]
            
            # Statistische Daten sammeln
            ratings = [p.rating100 for p in performers_with_tag if p.rating100 is not None]
            o_counters = [p.o_counter for p in performers_with_tag if p.o_counter > 0]
            cups = [p.cup_numeric for p in performers_with_tag if p.cup_numeric > 0]
            
            tag_stats[tag] = {
                "count": len(performers_with_tag),
                "avg_rating": self._safe_avg(ratings),
                "avg_o_counter": self._safe_avg(o_counters),
                "avg_cup_numeric": self._safe_avg(cups),
                "avg_cup_letter": Performer.CUP_NUMERIC_TO_LETTER.get(
                    round(self._safe_avg(cups) or 0), "?"
                )
            }
        
        # Speichere die Ergebnisse
        self.tag_frequency = {
            "performer_tags": {tag: count for tag, count in top_performer_tags},
            "scene_tags": {tag: count for tag, count in top_scene_tags},
            "tag_stats": tag_stats
        }
        
        logger.info(f"Tag-Frequenzen für {len(performer_tag_freq)} Performer-Tags und {len(scene_tag_freq)} Szenen-Tags berechnet")
    
    def _calculate_correlations(self) -> None:
        """
        Berechnet Korrelationen zwischen verschiedenen Attributen.
        
        Untersucht Zusammenhänge zwischen:
        - Cup-Größe und Rating
        - Cup-Größe und O-Counter
        - BMI und Rating
        - Alter und Rating
        - Szenen-Rating und O-Counter
        - Szenen-Dauer und Rating
        - Szenen-Alter und Rating
        """
        logger.info("Berechne Korrelationen zwischen Attributen...")
        
        # Korrelationen für Performer-Attribute
        performer_correlations = {}
        
        # Cup-Größe vs. Rating
        cup_rating_data = [
            (p.cup_numeric, p.rating100) 
            for p in self.performers 
            if p.cup_numeric > 0 and p.rating100 is not None
        ]
        
        if len(cup_rating_data) >= self.min_data_points:
            cup_data = [d[0] for d in cup_rating_data]
            rating_data = [d[1] for d in cup_rating_data]
            
            correlation = self._calculate_correlation(cup_data, rating_data)
            performer_correlations["cup_size_vs_rating"] = {
                "correlation": correlation,
                "n": len(cup_rating_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # Cup-Größe vs. O-Counter
        cup_ocounter_data = [
            (p.cup_numeric, p.o_counter) 
            for p in self.performers 
            if p.cup_numeric > 0 and p.o_counter > 0
        ]
        
        if len(cup_ocounter_data) >= self.min_data_points:
            cup_data = [d[0] for d in cup_ocounter_data]
            ocounter_data = [d[1] for d in cup_ocounter_data]
            
            correlation = self._calculate_correlation(cup_data, ocounter_data)
            performer_correlations["cup_size_vs_o_counter"] = {
                "correlation": correlation,
                "n": len(cup_ocounter_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # BMI vs. Rating
        bmi_rating_data = [
            (p.bmi, p.rating100) 
            for p in self.performers 
            if p.bmi is not None and p.rating100 is not None
        ]
        
        if len(bmi_rating_data) >= self.min_data_points:
            bmi_data = [d[0] for d in bmi_rating_data]
            rating_data = [d[1] for d in bmi_rating_data]
            
            correlation = self._calculate_correlation(bmi_data, rating_data)
            performer_correlations["bmi_vs_rating"] = {
                "correlation": correlation,
                "n": len(bmi_rating_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # Alter vs. Rating
        age_rating_data = [
            (p.age, p.rating100) 
            for p in self.performers 
            if p.age is not None and p.rating100 is not None
        ]
        
        if len(age_rating_data) >= self.min_data_points:
            age_data = [d[0] for d in age_rating_data]
            rating_data = [d[1] for d in age_rating_data]
            
            correlation = self._calculate_correlation(age_data, rating_data)
            performer_correlations["age_vs_rating"] = {
                "correlation": correlation,
                "n": len(age_rating_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # Korrelationen für Szenen-Attribute
        scene_correlations = {}
        
        # Rating vs. O-Counter
        scene_rating_ocounter_data = [
            (s.rating100, s.o_counter) 
            for s in self.scenes 
            if s.rating100 is not None and s.o_counter > 0
        ]
        
        if len(scene_rating_ocounter_data) >= self.min_data_points:
            rating_data = [d[0] for d in scene_rating_ocounter_data]
            ocounter_data = [d[1] for d in scene_rating_ocounter_data]
            
            correlation = self._calculate_correlation(rating_data, ocounter_data)
            scene_correlations["rating_vs_o_counter"] = {
                "correlation": correlation,
                "n": len(scene_rating_ocounter_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # Dauer vs. Rating
        duration_rating_data = [
            (s.duration, s.rating100) 
            for s in self.scenes 
            if s.duration > 0 and s.rating100 is not None
        ]
        
        if len(duration_rating_data) >= self.min_data_points:
            duration_data = [d[0] for d in duration_rating_data]
            rating_data = [d[1] for d in duration_rating_data]
            
            correlation = self._calculate_correlation(duration_data, rating_data)
            scene_correlations["duration_vs_rating"] = {
                "correlation": correlation,
                "n": len(duration_rating_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # Szenen-Alter vs. Rating (falls "age_days" berechnet wurde)
        age_rating_data = [
            (s.age_days, s.rating100) 
            for s in self.scenes 
            if hasattr(s, "age_days") and s.age_days is not None and s.rating100 is not None
        ]
        
        if len(age_rating_data) >= self.min_data_points:
            age_data = [d[0] for d in age_rating_data]
            rating_data = [d[1] for d in age_rating_data]
            
            correlation = self._calculate_correlation(age_data, rating_data)
            scene_correlations["age_vs_rating"] = {
                "correlation": correlation,
                "n": len(age_rating_data),
                "interpretation": self._interpret_correlation(correlation)
            }
        
        # Speichere die Ergebnisse
        self.correlation_stats = {
            "performer_correlations": performer_correlations,
            "scene_correlations": scene_correlations
        }
        
        logger.info(f"Korrelationen für {len(performer_correlations)} Performer-Attribute und {len(scene_correlations)} Szenen-Attribute berechnet")
    
    def get_data_for_analysis(self) -> Dict[str, pd.DataFrame]:
        """
        Erstellt Pandas-DataFrames für weitergehende Analysen.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mit verschiedenen DataFrames
        """
        # Performer-DataFrame erstellen
        performer_data = []
        for p in self.performers:
            performer_dict = p.to_dict()
            performer_data.append(performer_dict)
        
        # Scene-DataFrame erstellen
        scene_data = []
        for s in self.scenes:
            scene_dict = s.to_dict()
            scene_data.append(scene_dict)
        
        # DataFrames erstellen
        performer_df = pd.DataFrame(performer_data)
        scene_df = pd.DataFrame(scene_data)
        
        # Für Zeitreihenanalyse: Szenen-DataFrame mit Datum-Index
        time_series_df = None
        if 'date' in scene_df.columns:
            try:
                time_series_df = scene_df.copy()
                time_series_df['date'] = pd.to_datetime(time_series_df['date'])
                time_series_df.set_index('date', inplace=True)
                time_series_df.sort_index(inplace=True)
            except Exception as e:
                logger.warning(f"Fehler bei der Erstellung des Zeitreihen-DataFrame: {str(e)}")
        
        return {
            "performers": performer_df,
            "scenes": scene_df,
            "time_series": time_series_df
        }
    
    def save_statistics(self) -> bool:
        """
        Speichert alle berechneten Statistiken in JSON-Dateien.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info("Speichere Statistiken...")
        
        if not self.performer_stats or not self.scene_stats:
            logger.warning("Keine Statistiken zum Speichern verfügbar")
            return False
        
        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        if not ensure_dir(self.output_dir):
            logger.error(f"Konnte Ausgabeverzeichnis '{self.output_dir}' nicht erstellen")
            return False
        
        # Speicherpfade definieren
        stats_path = os.path.join(self.output_dir, "statistics.json")
        performer_stats_path = os.path.join(self.output_dir, "performer_statistics.json")
        scene_stats_path = os.path.join(self.output_dir, "scene_statistics.json")
        
        # Alle Statistiken in einer Datei speichern
        all_stats = {
            "general": self._get_general_stats(),
            "performers": self.performer_stats.to_dict() if self.performer_stats else {},
            "scenes": self.scene_stats.to_dict() if self.scene_stats else {},
            "cup_sizes": self.cup_size_groups,
            "bmi": self.bmi_groups,
            "age": self.age_groups,
            "tags": self.tag_frequency,
            "time_series": self.time_series_data,
            "seasonal": self.seasonal_data,
            "correlations": self.correlation_stats
        }
        
        success = save_json(all_stats, stats_path)
        
        if success:
            logger.info(f"Alle Statistiken erfolgreich in '{stats_path}' gespeichert")
        else:
            logger.error(f"Fehler beim Speichern der Statistiken in '{stats_path}'")
            return False
        
        # Performer-Statistiken separat speichern
        if self.performer_stats:
            if save_json(self.performer_stats.to_dict(), performer_stats_path):
                logger.info(f"Performer-Statistiken erfolgreich in '{performer_stats_path}' gespeichert")
            else:
                logger.warning(f"Fehler beim Speichern der Performer-Statistiken in '{performer_stats_path}'")
        
        # Szenen-Statistiken separat speichern
        if self.scene_stats:
            if save_json(self.scene_stats.to_dict(), scene_stats_path):
                logger.info(f"Szenen-Statistiken erfolgreich in '{scene_stats_path}' gespeichert")
            else:
                logger.warning(f"Fehler beim Speichern der Szenen-Statistiken in '{scene_stats_path}'")
        
        return True
    
    def _get_general_stats(self) -> Dict[str, Any]:
        """
        Erstellt eine Übersicht mit allgemeinen Statistiken.
        
        Returns:
            Dict[str, Any]: Dictionary mit allgemeinen Statistiken
        """
        stats = {
            "total_performers": len(self.performers),
            "total_scenes": len(self.scenes),
            "favorited_performers": len([p for p in self.performers if p.favorite]),
            "total_o_counter": sum(p.o_counter for p in self.performers),
            "performers_with_ratings": len([p for p in self.performers if p.rating100 is not None]),
            "scenes_with_ratings": len([s for s in self.scenes if s.rating100 is not None]),
            "calculated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Durchschnittswerte
        cup_sizes = [p.cup_numeric for p in self.performers if p.cup_numeric > 0]
        if cup_sizes:
            stats["avg_cup_size"] = self._safe_avg(cup_sizes)
            stats["avg_cup_letter"] = Performer.CUP_NUMERIC_TO_LETTER.get(
                round(stats["avg_cup_size"]), "?"
            )
        
        bmis = [p.bmi for p in self.performers if p.bmi is not None]
        if bmis:
            stats["avg_bmi"] = self._safe_avg(bmis)
        
        ages = [p.age for p in self.performers if p.age is not None]
        if ages:
            stats["avg_age"] = self._safe_avg(ages)
        
        return stats
    
    def _safe_avg(self, values: List[Union[int, float]]) -> Optional[float]:
        """
        Berechnet sicher den Durchschnitt einer Liste von Werten.
        
        Args:
            values: Liste von Werten
            
        Returns:
            Optional[float]: Durchschnittswert oder None bei leerer Liste
        """
        if not values:
            return None
            
        return round(sum(values) / len(values), self.decimal_places)
    
    def _safe_median(self, values: List[Union[int, float]]) -> Optional[float]:
        """
        Berechnet sicher den Median einer Liste von Werten.
        
        Args:
            values: Liste von Werten
            
        Returns:
            Optional[float]: Median oder None bei leerer Liste
        """
        if not values:
            return None
            
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return round((sorted_values[n//2 - 1] + sorted_values[n//2]) / 2, self.decimal_places)
        else:
            return round(sorted_values[n//2], self.decimal_places)
    
    def _filter_outliers(self, values: List[Union[int, float]], method: str = None) -> List[Union[int, float]]:
        """
        Entfernt Ausreißer aus einer Liste von Werten.
        
        Args:
            values: Liste von Werten
            method: Methode zur Ausreißererkennung ('IQR' oder 'zscore')
            
        Returns:
            List[Union[int, float]]: Liste ohne Ausreißer
        """
        if not values or len(values) < 4:
            return values
            
        method = method or self.outlier_detection
        
        if method == 'IQR':
            # Interquartile Range (IQR) Methode
            values = sorted(values)
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            return [x for x in values if lower_bound <= x <= upper_bound]
            
        elif method == 'zscore':
            # Z-Score Methode
            mean = sum(values) / len(values)
            std_dev = np.std(values)
            
            if std_dev == 0:
                return values
                
            threshold = 3.0  # Standard-Z-Score-Schwellenwert
            
            return [x for x in values if abs((x - mean) / std_dev) <= threshold]
            
        else:
            return values
    
    def _calculate_correlation(self, x_values: List[Union[int, float]], y_values: List[Union[int, float]]) -> float:
        """
        Berechnet den Pearson-Korrelationskoeffizienten zwischen zwei Wertelisten.
        
        Args:
            x_values: Erste Werteliste
            y_values: Zweite Werteliste
            
        Returns:
            float: Korrelationskoeffizient (-1 bis 1)
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
            
        try:
            # Numpy's corrcoef gibt eine Matrix zurück; wir benötigen nur den Wert [0, 1]
            correlation_matrix = np.corrcoef(x_values, y_values)
            correlation = correlation_matrix[0, 1]
            
            # Runden auf die konfigurierte Anzahl von Dezimalstellen
            return round(correlation, self.decimal_places)
        except Exception as e:
            logger.warning(f"Fehler bei der Korrelationsberechnung: {str(e)}")
            return 0.0
    
    def _interpret_correlation(self, correlation: float) -> str:
        """
        Interpretiert den Korrelationskoeffizienten als Text.
        
        Args:
            correlation: Korrelationskoeffizient (-1 bis 1)
            
        Returns:
            str: Textuelle Interpretation der Korrelation
        """
        abs_corr = abs(correlation)
        
        if abs_corr < 0.1:
            strength = "keine"
        elif abs_corr < 0.3:
            strength = "schwache"
        elif abs_corr < 0.5:
            strength = "moderate"
        elif abs_corr < 0.7:
            strength = "starke"
        else:
            strength = "sehr starke"
        
        direction = "positive" if correlation >= 0 else "negative"
        
        return f"{strength} {direction} Korrelation"
