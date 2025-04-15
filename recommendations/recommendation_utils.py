"""
Recommendation Utilities Module

Dieses Modul enthält gemeinsame Funktionen und Hilfsklassen für die 
Empfehlungsmodule (Performer und Szenen).
"""

import os
import logging
import math
import json
from typing import List, Dict, Tuple, Any, Set, Optional, Union
from datetime import datetime, timedelta

from core.utils import calculate_jaccard_similarity

# Logger konfigurieren
logger = logging.getLogger(__name__)

def calculate_normalized_similarity(value1: float, value2: float, 
                                  max_diff: float, 
                                  invert: bool = False) -> float:
    """
    Berechnet einen normalisierten Ähnlichkeitswert zwischen zwei numerischen Werten.
    
    Args:
        value1: Erster Wert
        value2: Zweiter Wert
        max_diff: Maximale Differenz, die als relevant betrachtet wird
                 (Differenzen größer als max_diff ergeben eine Ähnlichkeit von 0)
        invert: Wenn True, wird die Ähnlichkeit invertiert (1 - Ähnlichkeit)
                Nützlich, wenn größere Differenz = größere Ähnlichkeit sein soll
    
    Returns:
        float: Ähnlichkeitswert zwischen 0 und 1
    """
    diff = abs(value1 - value2)
    
    # Verhindere Division durch Null
    if max_diff <= 0:
        similarity = 1.0 if diff == 0 else 0.0
    else:
        similarity = max(0.0, 1.0 - (diff / max_diff))
    
    return 1.0 - similarity if invert else similarity

def calculate_tag_similarity(tags1: Set[str], tags2: Set[str]) -> float:
    """
    Berechnet die Tag-Ähnlichkeit mit dem Jaccard-Index.
    
    Args:
        tags1: Erste Menge von Tags
        tags2: Zweite Menge von Tags
    
    Returns:
        float: Jaccard-Ähnlichkeitswert (0 = keine Überlappung, 1 = identisch)
    """
    if not tags1 or not tags2:
        return 0.0
    
    return calculate_jaccard_similarity(tags1, tags2)

def parse_iso_date(date_str: str) -> Optional[datetime]:
    """
    Parst ein ISO-8601-Datumsobjekt aus einem String.
    
    Args:
        date_str: Datum im ISO-8601-Format (z.B. "2023-04-12T15:30:45Z")
    
    Returns:
        Optional[datetime]: DateTime-Objekt oder None bei Fehler
    """
    try:
        # Behandelt Zeitzoneninformation (Z, +00:00, etc.)
        date_str = date_str.replace('Z', '+00:00')
        if '+' not in date_str and '-' not in date_str[-6:]:
            # Wenn keine Zeitzone angegeben ist, nehmen wir UTC an
            date_str += '+00:00'
        
        return datetime.fromisoformat(date_str)
    except ValueError as e:
        logger.warning(f"Fehler beim Parsen des Datums '{date_str}': {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Parsen des Datums '{date_str}': {str(e)}")
        return None

def calculate_age_days(date_str: str) -> Optional[int]:
    """
    Berechnet das Alter in Tagen von einem Datum bis heute.
    
    Args:
        date_str: Datum im ISO-8601-Format
    
    Returns:
        Optional[int]: Alter in Tagen oder None bei Fehler
    """
    date = parse_iso_date(date_str)
    if not date:
        return None
    
    now = datetime.now().astimezone()
    delta = now - date
    return delta.days

def calculate_novelty_score(created_date: str, timeframe_days: int = 30) -> Optional[float]:
    """
    Berechnet einen Neuheits-Score basierend auf dem Erstellungsdatum.
    
    Args:
        created_date: Erstellungsdatum im ISO-8601-Format
        timeframe_days: Zeitraum in Tagen, der für "neu" betrachtet wird
    
    Returns:
        Optional[float]: Neuheits-Score (1 = gerade erstellt, 0 = älter als der Zeitraum)
    """
    age_days = calculate_age_days(created_date)
    if age_days is None:
        return None
    
    # Linearer Abfall von 1 (neu) zu 0 (am Ende des Zeitraums)
    return max(0.0, 1.0 - (age_days / timeframe_days)) if timeframe_days > 0 else 0.0

def apply_weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Wendet gewichtete Scores an und kombiniert sie zu einem Gesamtscore.
    
    Args:
        scores: Dictionary mit Scores pro Kriterium
        weights: Dictionary mit Gewichtungen pro Kriterium
    
    Returns:
        float: Gewichteter Gesamtscore (0-1)
    """
    total_score = 0.0
    total_weight = 0.0
    
    for criterion, score in scores.items():
        if criterion in weights and weights[criterion] > 0:
            weight = weights[criterion]
            total_score += score * weight
            total_weight += weight
    
    # Normalisieren, falls Gewichte nicht auf 1 summieren
    if total_weight > 0:
        return total_score / total_weight
    else:
        return 0.0

def save_recommendations_json(recommendations: Dict[str, List[Dict[str, Any]]], 
                             filepath: str) -> bool:
    """
    Speichert Empfehlungen im JSON-Format.
    
    Args:
        recommendations: Die zu speichernden Empfehlungen
        filepath: Pfad zur Ausgabedatei
    
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Empfehlungen erfolgreich gespeichert unter '{filepath}'")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Empfehlungen unter '{filepath}': {str(e)}")
        return False

class RecommendationRegistry:
    """
    Hilfsklasse zur Speicherung von Zwischenergebnissen verschiedener 
    Empfehlungsalgorithmen.
    """
    
    def __init__(self, max_items_per_category: int = 10):
        """
        Initialisiert das Empfehlungsregister.
        
        Args:
            max_items_per_category: Maximale Anzahl der zu speichernden Items pro Kategorie
        """
        self.categories = {}  # Dict[str, List[Tuple[Any, float]]]
        self.max_items = max_items_per_category
    
    def add_recommendation(self, category: str, item: Any, score: float) -> None:
        """
        Fügt eine Empfehlung zu einer Kategorie hinzu.
        
        Args:
            category: Kategoriename
            item: Das zu empfehlende Item (z.B. Performer oder Szene)
            score: Ähnlichkeits- oder Empfehlungswert (0-1)
        """
        # Erstelle Kategorie, falls nicht vorhanden
        if category not in self.categories:
            self.categories[category] = []
        
        # Füge Item hinzu
        self.categories[category].append((item, score))
        
        # Sortiere und begrenze die Anzahl
        self.categories[category].sort(key=lambda x: x[1], reverse=True)
        self.categories[category] = self.categories[category][:self.max_items]
    
    def get_recommendations(self, category: str) -> List[Tuple[Any, float]]:
        """
        Gibt die Empfehlungen einer Kategorie zurück.
        
        Args:
            category: Kategoriename
        
        Returns:
            List[Tuple[Any, float]]: Liste von (Item, Score) Tupeln
        """
        return self.categories.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """
        Gibt alle verfügbaren Kategorien zurück.
        
        Returns:
            List[str]: Liste der Kategorienamen
        """
        return list(self.categories.keys())
    
    def get_all_recommendations(self) -> Dict[str, List[Tuple[Any, float]]]:
        """
        Gibt alle Empfehlungen nach Kategorien zurück.
        
        Returns:
            Dict[str, List[Tuple[Any, float]]]: Dictionary mit Empfehlungen pro Kategorie
        """
        return self.categories
    
    def aggregate_recommendations(self, weights: Dict[str, float], 
                                max_results: int = 10) -> List[Tuple[Any, float]]:
        """
        Aggregiert Empfehlungen aus allen Kategorien zu einer Gesamtliste.
        
        Args:
            weights: Gewichtungen pro Kategorie
            max_results: Maximale Anzahl der Gesamtergebnisse
        
        Returns:
            List[Tuple[Any, float]]: Aggregierte Liste von (Item, Score) Tupeln
        """
        # Sammle alle Items mit ihren gewichteten Scores
        item_scores = {}  # Dict[item_id, total_score]
        item_map = {}  # Dict[item_id, item]
        
        for category, items in self.categories.items():
            if category not in weights or weights[category] <= 0:
                continue
            
            weight = weights[category]
            for item, score in items:
                # Verwende die ID des Items als Schlüssel
                item_id = getattr(item, 'id', str(item))
                
                # Speichere das Item-Objekt
                item_map[item_id] = item
                
                # Addiere gewichteten Score zum Gesamtscore
                current_score = item_scores.get(item_id, 0.0)
                item_scores[item_id] = current_score + (score * weight)
        
        # Konvertiere zu Liste und sortiere
        aggregated = [
            (item_map[item_id], score)
            for item_id, score in item_scores.items()
        ]
        aggregated.sort(key=lambda x: x[1], reverse=True)
        
        return aggregated[:max_results]
