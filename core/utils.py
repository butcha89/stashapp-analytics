"""
Utilities Module

Dieses Modul enthält allgemeine Hilfsfunktionen, die von verschiedenen
Teilen der Anwendung verwendet werden.
"""

import os
import re
import json
import csv
import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)

def safe_filename(filename: str) -> str:
    """
    Ersetzt ungültige Zeichen in Dateinamen.
    
    Args:
        filename: Der zu bereinigende Dateiname
        
    Returns:
        str: Bereinigter Dateiname ohne ungültige Zeichen
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def ensure_dir(directory: str) -> bool:
    """
    Stellt sicher, dass das angegebene Verzeichnis existiert.
    
    Args:
        directory: Der Pfad zum zu überprüfenden/erstellenden Verzeichnis
        
    Returns:
        bool: True, wenn das Verzeichnis existiert (oder erstellt wurde), sonst False
    """
    if not directory:
        return False
        
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Verzeichnisses '{directory}': {str(e)}")
        return False

def format_filesize(size_bytes: int) -> str:
    """
    Formatiert eine Dateigröße in Bytes in eine menschenlesbare Form.
    
    Args:
        size_bytes: Größe in Bytes
        
    Returns:
        str: Formatierte Größe (z.B. "4.2 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"
        
def format_duration(seconds: float) -> str:
    """
    Formatiert eine Dauer in Sekunden in ein menschenlesbares Format.
    
    Args:
        seconds: Dauer in Sekunden
        
    Returns:
        str: Formatierte Dauer (z.B. "2h 15m 30s")
    """
    if seconds <= 0:
        return "0s"
        
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    result = ""
    if hours > 0:
        result += f"{hours}h "
    if minutes > 0 or hours > 0:
        result += f"{minutes}m "
    
    result += f"{seconds}s"
    return result.strip()

def format_date(date_str: str, input_format: str = "%Y-%m-%d", output_format: str = "%d.%m.%Y") -> str:
    """
    Formatiert ein Datum in ein neues Format.
    
    Args:
        date_str: Das zu formatierende Datum
        input_format: Das Format der Eingabe
        output_format: Das gewünschte Ausgabeformat
        
    Returns:
        str: Das formatierte Datum oder eine leere Zeichenkette bei Fehler
    """
    if not date_str:
        return ""
        
    try:
        date_obj = datetime.datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except Exception as e:
        logger.warning(f"Fehler beim Formatieren des Datums '{date_str}': {str(e)}")
        return date_str

def calculate_age(birthdate: str, format: str = "%Y-%m-%d") -> Optional[int]:
    """
    Berechnet das Alter basierend auf dem Geburtsdatum.
    
    Args:
        birthdate: Das Geburtsdatum als String
        format: Das Format des Geburtsdatums
        
    Returns:
        Optional[int]: Das berechnete Alter oder None bei Fehler
    """
    if not birthdate:
        return None
        
    try:
        birth_date = datetime.datetime.strptime(birthdate, format)
        today = datetime.datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except Exception as e:
        logger.warning(f"Fehler bei der Altersberechnung für '{birthdate}': {str(e)}")
        return None

def save_json(data: Any, file_path: str, indent: int = 4) -> bool:
    """
    Speichert Daten als JSON-Datei.
    
    Args:
        data: Die zu speichernden Daten
        file_path: Der Pfad zur Ausgabedatei
        indent: Einrückung für die JSON-Datei
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        directory = os.path.dirname(file_path)
        ensure_dir(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        logger.info(f"Daten erfolgreich als JSON in '{file_path}' gespeichert")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der JSON-Datei '{file_path}': {str(e)}")
        return False

def load_json(file_path: str) -> Optional[Any]:
    """
    Lädt Daten aus einer JSON-Datei.
    
    Args:
        file_path: Der Pfad zur JSON-Datei
        
    Returns:
        Optional[Any]: Die geladenen Daten oder None bei Fehler
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"JSON-Datei '{file_path}' nicht gefunden")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Daten erfolgreich aus JSON-Datei '{file_path}' geladen")
        return data
    except Exception as e:
        logger.error(f"Fehler beim Laden der JSON-Datei '{file_path}': {str(e)}")
        return None

def save_csv(data: List[Dict[str, Any]], file_path: str, fieldnames: Optional[List[str]] = None) -> bool:
    """
    Speichert Daten als CSV-Datei.
    
    Args:
        data: Die zu speichernden Daten (Liste von Dictionaries)
        file_path: Der Pfad zur Ausgabedatei
        fieldnames: Die Spaltenüberschriften (falls None, werden sie aus den Daten extrahiert)
        
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        if not data:
            logger.warning(f"Keine Daten zum Speichern in '{file_path}' vorhanden")
            return False
            
        directory = os.path.dirname(file_path)
        ensure_dir(directory)
        
        # Spaltenüberschriften ermitteln, falls nicht angegeben
        if fieldnames is None:
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(list(fieldnames))
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Daten erfolgreich als CSV in '{file_path}' gespeichert")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der CSV-Datei '{file_path}': {str(e)}")
        return False

def load_csv(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Lädt Daten aus einer CSV-Datei.
    
    Args:
        file_path: Der Pfad zur CSV-Datei
        
    Returns:
        Optional[List[Dict[str, Any]]]: Die geladenen Daten oder None bei Fehler
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"CSV-Datei '{file_path}' nicht gefunden")
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]
        
        logger.info(f"Daten erfolgreich aus CSV-Datei '{file_path}' geladen")
        return data
    except Exception as e:
        logger.error(f"Fehler beim Laden der CSV-Datei '{file_path}': {str(e)}")
        return None

def convert_bra_size(size_str: str, to_eu: bool = True) -> Optional[str]:
    """
    Konvertiert BH-Größen zwischen US/UK und EU-Format.
    
    Args:
        size_str: Die zu konvertierende BH-Größe (z.B. "34C" oder "75D")
        to_eu: True für Konvertierung nach EU, False für Konvertierung nach US/UK
        
    Returns:
        Optional[str]: Die konvertierte BH-Größe oder None bei Fehler
    """
    # Umrechnungstabellen
    band_us_to_eu = {
        28: 60, 30: 65, 32: 70, 34: 75, 36: 80, 
        38: 85, 40: 90, 42: 95, 44: 100, 46: 105
    }
    
    band_eu_to_us = {v: k for k, v in band_us_to_eu.items()}
    
    cup_us_to_eu = {
        "A": "A", "B": "B", "C": "C", "D": "D", 
        "DD": "E", "DDD": "F", "E": "E", "F": "F", 
        "G": "G", "H": "H"
    }
    
    cup_eu_to_us = {
        "A": "A", "B": "B", "C": "C", "D": "D", 
        "E": "DD", "F": "DDD", "G": "G", "H": "H"
    }
    
    try:
        if to_eu:
            # US/UK zu EU konvertieren
            match = re.match(r'(\d{2})([A-HJ-Z]+)', size_str)
            if not match:
                return None
                
            us_band = int(match.group(1))
            us_cup = match.group(2)
            
            eu_band = band_us_to_eu.get(us_band, round((us_band + 16) / 2) * 5)
            eu_cup = cup_us_to_eu.get(us_cup, us_cup)
            
            return f"{eu_band}{eu_cup}"
        else:
            # EU zu US/UK konvertieren
            match = re.match(r'(\d{2,3})([A-HJ-Z]+)', size_str)
            if not match:
                return None
                
            eu_band = int(match.group(1))
            eu_cup = match.group(2)
            
            us_band = band_eu_to_us.get(eu_band, round(eu_band * 2 - 16))
            us_cup = cup_eu_to_us.get(eu_cup, eu_cup)
            
            return f"{us_band}{us_cup}"
    except Exception as e:
        logger.warning(f"Fehler bei der Konvertierung der BH-Größe '{size_str}': {str(e)}")
        return None

def get_cup_numeric(cup: str) -> int:
    """
    Konvertiert eine Cup-Größe in einen numerischen Wert.
    
    Args:
        cup: Die Cup-Größe (z.B. "C", "DD")
        
    Returns:
        int: Numerischer Wert der Cup-Größe oder 0 bei Fehler
    """
    cup_mapping = {
        "A": 1, "B": 2, "C": 3, "D": 4, 
        "E": 5, "DD": 5, "F": 6, "DDD": 6, 
        "G": 7, "H": 8, "I": 9, "J": 10
    }
    
    return cup_mapping.get(cup, 0)

def get_cup_letter(numeric: int) -> str:
    """
    Konvertiert einen numerischen Cup-Wert in eine Buchstabenbezeichnung.
    
    Args:
        numeric: Der numerische Cup-Wert
        
    Returns:
        str: Buchstabenbezeichnung der Cup-Größe oder "?" bei Fehler
    """
    cup_mapping = {
        1: "A", 2: "B", 3: "C", 4: "D", 
        5: "E", 6: "F", 7: "G", 8: "H",
        9: "I", 10: "J"
    }
    
    return cup_mapping.get(numeric, "?")

def calculate_bmi(height_cm: float, weight_kg: float) -> Optional[float]:
    """
    Berechnet den BMI (Body Mass Index).
    
    Args:
        height_cm: Körpergröße in Zentimetern
        weight_kg: Gewicht in Kilogramm
        
    Returns:
        Optional[float]: Berechneter BMI oder None bei ungültigen Werten
    """
    if not (height_cm and weight_kg and height_cm > 0 and weight_kg > 0):
        return None
        
    try:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        return round(bmi, 1)
    except Exception as e:
        logger.warning(f"Fehler bei der BMI-Berechnung: {str(e)}")
        return None

def get_bmi_category(bmi: float) -> str:
    """
    Bestimmt die BMI-Kategorie.
    
    Args:
        bmi: Der BMI-Wert
        
    Returns:
        str: Die BMI-Kategorie
    """
    if bmi < 18.5:
        return "Untergewicht"
    elif bmi < 25:
        return "Normalgewicht"
    elif bmi < 30:
        return "Übergewicht"
    else:
        return "Adipositas"

def normalize_tags(tags: List[str]) -> List[str]:
    """
    Normalisiert Tags (Kleinschreibung, Entfernung von Sonderzeichen, etc.).
    
    Args:
        tags: Liste von Tags
        
    Returns:
        List[str]: Normalisierte Liste von Tags
    """
    result = []
    
    for tag in tags:
        # Entferne führende/nachfolgende Leerzeichen
        tag = tag.strip()
        
        # Überspringe leere Tags
        if not tag:
            continue
            
        # Konvertiere zu Kleinbuchstaben
        tag = tag.lower()
        
        # Ersetze Leerzeichen und Sonderzeichen durch Unterstriche
        tag = re.sub(r'[^a-z0-9]', '_', tag)
        
        # Entferne doppelte Unterstriche
        tag = re.sub(r'_+', '_', tag)
        
        # Entferne führende/nachfolgende Unterstriche
        tag = tag.strip('_')
        
        # Füge den normalisierten Tag hinzu
        if tag:
            result.append(tag)
    
    return result

def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Berechnet die Jaccard-Ähnlichkeit zweier Sets.
    
    Args:
        set1: Erstes Set
        set2: Zweites Set
        
    Returns:
        float: Jaccard-Ähnlichkeit (0-1)
    """
    if not set1 or not set2:
        return 0.0
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Berechnet die Levenshtein-Distanz zwischen zwei Strings.
    
    Args:
        s1: Erster String
        s2: Zweiter String
        
    Returns:
        int: Levenshtein-Distanz
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
        
    if len(s2) == 0:
        return len(s1)
        
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def string_similarity(s1: str, s2: str) -> float:
    """
    Berechnet die Ähnlichkeit zwischen zwei Strings (0-1).
    
    Args:
        s1: Erster String
        s2: Zweiter String
        
    Returns:
        float: Ähnlichkeit (0-1)
    """
    if not s1 or not s2:
        return 0.0
        
    # Konvertiere zu Kleinbuchstaben
    s1, s2 = s1.lower(), s2.lower()
    
    # Berechne Levenshtein-Distanz
    distance = levenshtein_distance(s1, s2)
    
    # Normalisiere auf Bereich 0-1
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
        
    return 1.0 - (distance / max_len)
