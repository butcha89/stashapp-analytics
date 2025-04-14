"""
Data Models Module

Dieses Modul definiert die grundlegenden Datenmodelle für Performer und Szenen.
"""

import re
import math
import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)

class Performer:
    """Datenmodell für einen Performer mit zusätzlichen Berechnungen und Attributen."""
    
    # Mappings für Cup-Größen und Umrechnungen
    CUP_NUMERIC = {
        "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "DD": 5, 
        "F": 6, "DDD": 6, "G": 7, "H": 8, "I": 9, "J": 10
    }
    
    CUP_NUMERIC_TO_LETTER = {
        1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 
        6: "F", 7: "G", 8: "H", 9: "I", 10: "J"
    }
    
    BAND_CONVERSION = {
        28: 60, 30: 65, 32: 70, 34: 75, 36: 80, 
        38: 85, 40: 90, 42: 95, 44: 100, 46: 105
    }
    
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
        self.bmi_to_cup_ratio = self._calculate_ratio(self.bmi, self.cup_numeric)
        self.height_to_cup_ratio = self._calculate_ratio(self.height_cm, self.cup_numeric)
        
        # Rating auf 5er-Skala
        self.rating_5 = round(self.rating100 / 20, 1) if self.rating100 is not None else None
    
    def _calculate_age(self) -> Optional[int]:
        """Berechnet das Alter basierend auf dem Geburtsdatum."""
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
        """Berechnet den BMI (Body Mass Index)."""
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
        """Bestimmt die BMI-Kategorie."""
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
        """Analysiert die BH-Größe aus dem Measurements-Feld."""
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
    
    @staticmethod
    def _calculate_ratio(value1: Optional[float], value2: Optional[int]) -> Optional[float]:
        """Berechnet das Verhältnis zweier Werte."""
        if value1 and value2 and value2 > 0:
            return round(value1 / value2, 2)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert den Performer in ein Dictionary."""
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
    """Datenmodell für eine Szene mit zusätzlichen Berechnungen und Attributen."""
    
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
        self.rating_5 = round(self.rating100 / 20, 1) if self.rating100 is not None else None
        self.age_days = self._calculate_age_days()
        
        # Erweiterte Performer-bezogene Berechnungen
        if performers:
            self._calculate_performer_attributes(performers)
    
    def _calculate_age_days(self) -> Optional[int]:
        """Berechnet das Alter der Szene in Tagen."""
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
        """Berechnet zusätzliche Attribute basierend auf den Performern in der Szene."""
        scene_performers = [p for p in performers if p.id in self.performer_ids]
        
        if not scene_performers:
            self.avg_cup_size = None
            self.avg_bmi = None
            self.avg_age = None
            self.avg_rating = None
            self.has_high_rated_performers = False
            return
        
        # Durchschnittswerte berechnen
        self._calculate_averages(scene_performers)
        
        # Hat hochbewertete Performer (>= 80)
        self.has_high_rated_performers = any(
            p.rating100 is not None and p.rating100 >= 80 for p in scene_performers
        )
    
    def _calculate_averages(self, performers: List[Performer]) -> None:
        """Berechnet Durchschnittswerte für verschiedene Performer-Attribute."""
        # Cup-Größe
        cup_sizes = [p.cup_numeric for p in performers if p.cup_numeric > 0]
        self.avg_cup_size = round(sum(cup_sizes) / len(cup_sizes), 1) if cup_sizes else None
        
        # BMI
        bmis = [p.bmi for p in performers if p.bmi is not None]
        self.avg_bmi = round(sum(bmis) / len(bmis), 1) if bmis else None
        
        # Alter
        ages = [p.age for p in performers if p.age is not None]
        self.avg_age = round(sum(ages) / len(ages), 1) if ages else None
        
        # Rating
        ratings = [p.rating100 for p in performers if p.rating100 is not None]
        self.avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Szene in ein Dictionary."""
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
