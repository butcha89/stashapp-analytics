"""
Data Models Module

Dieses Modul definiert die Datenmodelle für Performer, Szenen und andere Entitäten.
Es enthält auch Methoden zur Berechnung und Manipulation dieser Daten.
"""

import re
import math
import datetime
from typing import Dict, List, Any, Optional, Set, Tuple, Union
import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)

class Performer:
    """
    Datenmodell für einen Performer mit zusätzlichen Berechnungen und Attributen.
    """
    
    # Mapping für Cup-Größen-Umrechnung
    CUP_NUMERIC = {
        "A": 1, "B": 2, "C": 3, "D": 4, 
        "E": 5, "DD": 5, "F": 6, "DDD": 6, 
        "G": 7, "H": 8, "I": 9, "J": 10
    }
    
    # Umgekehrtes Mapping für die Anzeige
    CUP_NUMERIC_TO_LETTER = {
        1: "A", 2: "B", 3: "C", 4: "D", 
        5: "E", 6: "F", 7: "G", 8: "H",
        9: "I", 10: "J"
    }
    
    # Umrechnungstabelle für Unterbrustweiten
    BAND_CONVERSION = {
        28: 60, 30: 65, 32: 70, 34: 75, 36: 80, 
        38: 85, 40: 90, 42: 95, 44: 100, 46: 105
    }
    
    # Cup-Umrechnungstabelle (US/UK zu DE)
    CUP_CONVERSION = {
        "A": "A", "B": "B", "C": "C", "D": "D", 
        "DD": "E", "DDD": "F", "E": "E", "F": "F", 
        "G": "G", "H": "H"
    }
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialisiert einen Performer mit Rohdaten aus der API und berechnet zusätzliche Attribute.
        
        Args:
            data: Performer-Daten aus der StashApp API
        """
        # Kern-Attribute aus API-Daten
        self.raw_data = data
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.gender = data.get("gender", "")
        self.birthdate = data.get("birthdate", "")
        self.country = data.get("country", "")
        self.ethnicity = data.get("ethnicity", "")
        self.eye_color = data.get("eye_color", "")
        self.hair_color = data.get("hair_color", "")
        self.height_cm = data.get("height_cm", 0)
        self.weight = data.get("weight", 0)
        self.measurements = data.get("measurements", "")
        self.favorite = data.get("favorite", False)
        self.rating100 = data.get("rating100")
        self.scene_count = data.get("scene_count", 0)
        self.o_counter = data.get("o_counter", 0)
        self.tags = [tag.get("name", "") for tag in data.get("tags", [])]
        
        # Berechnete Attribute
        self.age = self._calculate_age()
        self.bmi = self._calculate_bmi()
        self.bmi_category = self._get_bmi_category()
        
        # BH-Größen-Berechnungen
        (
            self.us_bra_size, 
            self.german_bra_size, 
            self.cup_size, 
            self.band_size, 
            self.cup_numeric
        ) = self._parse_bra_size()
        
        # Erweiterte Kennzahlen
        self.bmi_to_cup_ratio = self._calculate_bmi_to_cup_ratio()
        self.height_to_cup_ratio = self._calculate_height_to_cup_ratio()
        
        # Rating auf 5er-Skala
        self.rating_5 = self._calculate_rating_5()
    
    def _calculate_age(self) -> Optional[int]:
        """
        Berechnet das Alter basierend auf dem Geburtsdatum.
        
        Returns:
            Optional[int]: Berechnetes Alter oder None, wenn kein Geburtsdatum vorhanden ist
        """
        if not self.birthdate:
            return None
            
        try:
            birth_date = datetime.datetime.strptime(self.birthdate, "%Y-%m-%d")
            today = datetime.datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        except Exception as e:
            logger.warning(f"Fehler bei der Altersberechnung für {self.name}: {str(e)}")
            return None
    
    def _calculate_bmi(self) -> Optional[float]:
        """
        Berechnet den BMI (Body Mass Index).
        
        Returns:
            Optional[float]: Berechneter BMI oder None, wenn Größe oder Gewicht fehlen
        """
        if not (self.height_cm and self.weight and self.height_cm > 0 and self.weight > 0):
            return None
            
        try:
            height_m = self.height_cm / 100
            weight_kg = float(self.weight)
            bmi = weight_kg / (height_m * height_m)
            return round(bmi, 1)
        except Exception as e:
            logger.warning(f"Fehler bei der BMI-Berechnung für {self.name}: {str(e)}")
            return None
    
    def _get_bmi_category(self) -> Optional[str]:
        """
        Bestimmt die BMI-Kategorie.
        
        Returns:
            Optional[str]: BMI-Kategorie oder None, wenn kein BMI berechnet wurde
        """
        if self.bmi is None:
            return None
            
        if self.bmi < 18.5:
            return "Untergewicht"
        elif self.bmi < 25:
            return "Normalgewicht"
        elif self.bmi < 30:
            return "Übergewicht"
        else:
            return "Adipositas"
    
    def _parse_bra_size(self) -> Tuple[str, str, str, str, int]:
        """
        Analysiert die BH-Größe aus dem Measurements-Feld.
        
        Returns:
            Tuple[str, str, str, str, int]: (US BH-Größe, DE BH-Größe, Cup-Größe, Unterbrustweite, Numerischer Cup-Wert)
        """
        if not self.measurements:
            return "", "", "", "", 0
        
        # Regex-Muster für BH-Größen
        match = re.search(r'(\d{2})([A-HJ-Z]+)', self.measurements)
        if not match:
            return "", "", "", "", 0
        
        us_band = int(match.group(1))
        us_cup = match.group(2)
        
        # Umrechnungen
        de_band = self.BAND_CONVERSION.get(us_band, round((us_band + 16) / 2) * 5)
        de_cup = self.CUP_CONVERSION.get(us_cup, us_cup)
        cup_numeric = self.CUP_NUMERIC.get(us_cup, 0)
        
        us_bra_size = f"{us_band}{us_cup}"
        german_bra_size = f"{de_band}{de_cup}"
        
        return us_bra_size, german_bra_size, us_cup, str(us_band), cup_numeric
    
    def _calculate_bmi_to_cup_ratio(self) -> Optional[float]:
        """
        Berechnet das Verhältnis von BMI zur Cup-Größe.
        
        Returns:
            Optional[float]: BMI zu Cup-Größe Verhältnis oder None, wenn Werte fehlen
        """
        if self.bmi and self.cup_numeric and self.cup_numeric > 0:
            return round(self.bmi / self.cup_numeric, 2)
        return None
    
    def _calculate_height_to_cup_ratio(self) -> Optional[float]:
        """
        Berechnet das Verhältnis von Körpergröße zur Cup-Größe.
        
        Returns:
            Optional[float]: Körpergröße zu Cup-Größe Verhältnis oder None, wenn Werte fehlen
        """
        if self.height_cm and self.cup_numeric and self.cup_numeric > 0:
            return round(self.height_cm / self.cup_numeric, 2)
        return None
    
    def _calculate_rating_5(self) -> Optional[float]:
        """
        Konvertiert rating100 in eine 5-Sterne-Skala.
        
        Returns:
            Optional[float]: Rating auf 5er-Skala oder None, wenn kein Rating vorhanden ist
        """
        if self.rating100 is not None:
            return round(self.rating100 / 20, 1)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert den Performer in ein Dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary mit allen Attributen
        """
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "birthdate": self.birthdate,
            "age": self.age,
            "country": self.country,
            "ethnicity": self.ethnicity,
            "eye_color": self.eye_color,
            "hair_color": self.hair_color,
            "height_cm": self.height_cm,
            "weight": self.weight,
            "measurements": self.measurements,
            "favorite": self.favorite,
            "rating100": self.rating100,
            "rating_5": self.rating_5,
            "scene_count": self.scene_count,
            "o_counter": self.o_counter,
            "tags": self.tags,
            "bmi": self.bmi,
            "bmi_category": self.bmi_category,
            "us_bra_size": self.us_bra_size,
            "german_bra_size": self.german_bra_size,
            "cup_size": self.cup_size,
            "band_size": self.band_size,
            "cup_numeric": self.cup_numeric,
            "bmi_to_cup_ratio": self.bmi_to_cup_ratio,
            "height_to_cup_ratio": self.height_to_cup_ratio
        }
    
    def __str__(self) -> str:
        """String-Repräsentation des Performers"""
        return f"{self.name} ({self.id})"


class Scene:
    """
    Datenmodell für eine Szene mit zusätzlichen Berechnungen und Attributen.
    """
    
    def __init__(self, data: Dict[str, Any], performers: Optional[List[Performer]] = None):
        """
        Initialisiert eine Szene mit Rohdaten aus der API und berechnet zusätzliche Attribute.
        
        Args:
            data: Szenen-Daten aus der StashApp API
            performers: Optionale Liste von Performer-Objekten für erweiterte Berechnungen
        """
        # Kern-Attribute aus API-Daten
        self.raw_data = data
        self.id = data.get("id", "")
        self.title = data.get("title", "")
        self.details = data.get("details", "")
        self.url = data.get("url", "")
        self.date = data.get("date", "")
        self.rating100 = data.get("rating100")
        self.o_counter = data.get("o_counter", 0)
        self.organized = data.get("organized", False)
        self.interactive = data.get("interactive", False)
        
        # Listen von assoziierten Objekten
        self.performer_ids = [p.get("id", "") for p in data.get("performers", [])]
        self.performer_names = [p.get("name", "") for p in data.get("performers", [])]
        self.has_favorite_performers = any(p.get("favorite", False) for p in data.get("performers", []))
        self.tags = [tag.get("name", "") for tag in data.get("tags", [])]
        
        # Informationen zum Studio
        studio_data = data.get("studio", {})
        self.studio_id = studio_data.get("id", "") if studio_data else ""
        self.studio_name = studio_data.get("name", "") if studio_data else ""
        
        # Zeitstempel
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        
        # Datei-Metadaten
        file_data = data.get("file", {})
        self.duration = file_data.get("duration", 0) if file_data else 0
        self.size = file_data.get("size", 0) if file_data else 0
        self.resolution = (file_data.get("width", 0), file_data.get("height", 0)) if file_data else (0, 0)
        
        # Berechnete Attribute
        self.rating_5 = self._calculate_rating_5()
        self.age_days = self._calculate_age_days()
        
        # Erweiterte Performer-bezogene Berechnungen
        if performers:
            self._calculate_performer_attributes(performers)
    
    def _calculate_rating_5(self) -> Optional[float]:
        """
        Konvertiert rating100 in eine 5-Sterne-Skala.
        
        Returns:
            Optional[float]: Rating auf 5er-Skala oder None, wenn kein Rating vorhanden ist
        """
        if self.rating100 is not None:
            return round(self.rating100 / 20, 1)
        return None
    
    def _calculate_age_days(self) -> Optional[int]:
        """
        Berechnet das Alter der Szene in Tagen.
        
        Returns:
            Optional[int]: Alter in Tagen oder None, wenn kein Datum vorhanden ist
        """
        if not self.date:
            return None
            
        try:
            scene_date = datetime.datetime.strptime(self.date, "%Y-%m-%d")
            today = datetime.datetime.now()
            delta = today - scene_date
            return delta.days
        except Exception as e:
            logger.warning(f"Fehler bei der Altersberechnung für Szene {self.title}: {str(e)}")
            return None
    
    def _calculate_performer_attributes(self, performers: List[Performer]) -> None:
        """
        Berechnet zusätzliche Attribute basierend auf den Performern in der Szene.
        
        Args:
            performers: Liste von Performer-Objekten
        """
        scene_performers = [p for p in performers if p.id in self.performer_ids]
        
        if not scene_performers:
            self.avg_cup_size = None
            self.avg_bmi = None
            self.avg_age = None
            self.avg_rating = None
            self.has_high_rated_performers = False
            return
        
        # Durchschnittliche Cup-Größe
        cup_sizes = [p.cup_numeric for p in scene_performers if p.cup_numeric > 0]
        self.avg_cup_size = round(sum(cup_sizes) / len(cup_sizes), 1) if cup_sizes else None
        
        # Durchschnittlicher BMI
        bmis = [p.bmi for p in scene_performers if p.bmi is not None]
        self.avg_bmi = round(sum(bmis) / len(bmis), 1) if bmis else None
        
        # Durchschnittsalter
        ages = [p.age for p in scene_performers if p.age is not None]
        self.avg_age = round(sum(ages) / len(ages), 1) if ages else None
        
        # Durchschnittliches Rating der Performer
        ratings = [p.rating100 for p in scene_performers if p.rating100 is not None]
        self.avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
        
        # Hat hochbewertete Performer (>= 80)
        self.has_high_rated_performers = any(p.rating100 is not None and p.rating100 >= 80 for p in scene_performers)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Szene in ein Dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary mit allen Attributen
        """
        result = {
            "id": self.id,
            "title": self.title,
            "details": self.details,
            "url": self.url,
            "date": self.date,
            "rating100": self.rating100,
            "rating_5": self.rating_5,
            "o_counter": self.o_counter,
            "organized": self.organized,
            "interactive": self.interactive,
            "performer_ids": self.performer_ids,
            "performer_names": self.performer_names,
            "has_favorite_performers": self.has_favorite_performers,
            "tags": self.tags,
            "studio_id": self.studio_id,
            "studio_name": self.studio_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration": self.duration,
            "size": self.size,
            "resolution": self.resolution,
            "age_days": self.age_days
        }
        
        # Füge berechnete Performer-Attribute hinzu, wenn vorhanden
        if hasattr(self, 'avg_cup_size'):
            result.update({
                "avg_cup_size": self.avg_cup_size,
                "avg_bmi": self.avg_bmi,
                "avg_age": self.avg_age,
                "avg_rating": self.avg_rating,
                "has_high_rated_performers": self.has_high_rated_performers
            })
        
        return result
    
    def __str__(self) -> str:
        """String-Repräsentation der Szene"""
        return f"{self.title} ({self.id})"


class PerformerStats:
    """
    Klasse zur Berechnung und Verwaltung von Performer-Statistiken.
    """
    
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
        self.avg_cup_size = self._calculate_avg_cup_size()
        self.avg_bmi = self._calculate_avg_bmi()
        self.avg_age = self._calculate_avg_age()
        self.avg_rating = self._calculate_avg_rating()
        self.avg_o_counter = self._calculate_avg_o_counter()
        
        # Cup-Size Statistiken
        self.cup_stats = self._calculate_cup_stats()
    
    def _calculate_cup_distribution(self) -> Dict[str, int]:
        """
        Berechnet die Verteilung der Cup-Größen.
        
        Returns:
            Dict[str, int]: Anzahl der Performer pro Cup-Größe
        """
        distribution = {}
        for p in self.performers:
            if p.cup_size:
                distribution[p.cup_size] = distribution.get(p.cup_size, 0) + 1
        return distribution
    
    def _calculate_bmi_distribution(self) -> Dict[str, int]:
        """
        Berechnet die Verteilung der BMI-Kategorien.
        
        Returns:
            Dict[str, int]: Anzahl der Performer pro BMI-Kategorie
        """
        distribution = {}
        for p in self.performers:
            if p.bmi_category:
                distribution[p.bmi_category] = distribution.get(p.bmi_category, 0) + 1
        return distribution
    
    def _calculate_rating_distribution(self) -> Dict[int, int]:
        """
        Berechnet die Verteilung der Bewertungen (in Sternen).
        
        Returns:
            Dict[int, int]: Anzahl der Performer pro Bewertungsstufe (1-5 Sterne)
        """
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for p in self.performers:
            if p.rating100 is not None:
                stars = min(5, max(1, int(round(p.rating100 / 20))))
                distribution[stars] = distribution.get(stars, 0) + 1
        return distribution
    
    def _calculate_age_distribution(self) -> Dict[str, int]:
        """
        Berechnet die Verteilung der Altersgruppen.
        
        Returns:
            Dict[str, int]: Anzahl der Performer pro Altersgruppe
        """
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
        """
        Berechnet die Verteilung der O-Counter-Werte.
        
        Returns:
            Dict[int, int]: Anzahl der Performer pro O-Counter-Wert
        """
        distribution = {}
        for p in self.performers:
            if p.o_counter > 0:
                distribution[p.o_counter] = distribution.get(p.o_counter, 0) + 1
        return distribution
    
    def _calculate_avg_cup_size(self) -> Optional[float]:
        """
        Berechnet die durchschnittliche Cup-Größe (numerisch).
        
        Returns:
            Optional[float]: Durchschnittliche Cup-Größe oder None, wenn keine Daten vorhanden sind
        """
        cup_values = [p.cup_numeric for p in self.performers if p.cup_numeric > 0]
        return round(sum(cup_values) / len(cup_values), 2) if cup_values else None
    
    def _calculate_avg_bmi(self) -> Optional[float]:
        """
        Berechnet den durchschnittlichen BMI.
        
        Returns:
            Optional[float]: Durchschnittlicher BMI oder None, wenn keine Daten vorhanden sind
        """
        bmi_values = [p.bmi for p in self.performers if p.bmi is not None]
        return round(sum(bmi_values) / len(bmi_values), 2) if bmi_values else None
    
    def _calculate_avg_age(self) -> Optional[float]:
        """
        Berechnet das Durchschnittsalter.
        
        Returns:
            Optional[float]: Durchschnittsalter oder None, wenn keine Daten vorhanden sind
        """
        age_values = [p.age for p in self.performers if p.age is not None]
        return round(sum(age_values) / len(age_values), 2) if age_values else None
    
    def _calculate_avg_rating(self) -> Optional[float]:
        """
        Berechnet die durchschnittliche Bewertung.
        
        Returns:
            Optional[float]: Durchschnittliche Bewertung oder None, wenn keine Daten vorhanden sind
        """
        rating_values = [p.rating100 for p in self.performers if p.rating100 is not None]
        return round(sum(rating_values) / len(rating_values), 2) if rating_values else None
    
    def _calculate_avg_o_counter(self) -> Optional[float]:
        """
        Berechnet den durchschnittlichen O-Counter.
        
        Returns:
            Optional[float]: Durchschnittlicher O-Counter oder None, wenn keine Daten vorhanden sind
        """
        counter_values = [p.o_counter for p in self.performers if p.o_counter > 0]
        return round(sum(counter_values) / len(counter_values), 2) if counter_values else None
    
    def _calculate_cup_stats(self) -> Dict[str, Any]:
        """
        Berechnet detaillierte Statistiken für Cup-Größen.
        
        Returns:
            Dict[str, Any]: Dictionary mit Cup-Size-Statistiken
        """
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
    
    def get_top_o_counter_by_cup_size(self) -> Dict[str, List[Performer]]:
        """
        Ermittelt die Performer mit dem höchsten O-Counter für jede Cup-Größe.
        
        Returns:
            Dict[str, List[Performer]]: Top-Performer nach Cup-Größe
        """
        result = {}
        performers_by_cup = {}
        
        # Gruppiere Performer nach Cup-Größe
        for p in self.performers:
            if p.cup_size and p.o_counter > 0:
                if p.cup_size not in performers_by_cup:
                    performers_by_cup[p.cup_size] = []
                performers_by_cup[p.cup_size].append(p)
        
        # Sortiere nach O-Counter und wähle Top-3
        for cup, cup_performers in performers_by_cup.items():
            sorted_performers = sorted(cup_performers, key=lambda p: p.o_counter, reverse=True)
            result[cup] = sorted_performers[:3]
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert alle Statistiken in ein Dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary mit allen Statistiken
        """
        result = {
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
        
        return result


class SceneStats:
    """
    Klasse zur Berechnung und Verwaltung von Szenen-Statistiken.
    """
    
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
        self.avg_rating = self._calculate_avg_rating()
        self.avg_o
