"""
dashboard_utils.py - Hilfsfunktionen für das Stasapp Dashboard

Dieses Modul enthält Hilfsfunktionen, die von verschiedenen Teilen des
Dashboard-Systems verwendet werden, wie Logging-Setup, Konfigurationshandling
und allgemeine Utility-Funktionen.
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Richtet die Logging-Konfiguration für das Dashboard-System ein.
    
    Args:
        log_level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Pfad zur Log-Datei (falls None, wird nur auf die Konsole geloggt)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Ungültiges log-level: {log_level}")
    
    # Basis-Logging-Konfiguration
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
    )
    
    # Optional: Logging in Datei
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Lädt die Konfiguration aus einer JSON-Datei.
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Returns:
        Dict mit der Konfiguration
        
    Raises:
        FileNotFoundError: Wenn die Konfigurationsdatei nicht existiert
        json.JSONDecodeError: Wenn die Datei kein gültiges JSON enthält
    """
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.warning(f"Konfigurationsdatei {config_path} nicht gefunden. Verwende Standardkonfiguration.")
        return create_default_config(config_path)
    except json.JSONDecodeError as e:
        logging.error(f"Fehler beim Lesen der Konfigurationsdatei: {str(e)}")
        raise

def create_default_config(config_path: str) -> Dict[str, Any]:
    """
    Erstellt eine Standard-Konfiguration und speichert sie.
    
    Args:
        config_path: Pfad, unter dem die Konfiguration gespeichert werden soll
        
    Returns:
        Dict mit der Standardkonfiguration
    """
    default_config = {
        "database": {
            "use_cache": True,
            "cache_timeout": 3600,  # in Sekunden (1 Stunde)
        },
        "analytics": {
            "min_data_points": 100,
            "segment_count": 5,
            "trending_threshold": 0.2
        },
        "visualization": {
            "color_palette": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "plot_size": [10, 6],
            "dpi": 100,
            "font_size": 12
        },
        "recommendations": {
            "max_recommendations": 10,
            "novelty_weight": 0.3,
            "relevance_weight": 0.7,
            "min_confidence": 0.6
        },
        "reporting": {
            "include_charts": True,
            "include_raw_data": False,
            "formats": ["html", "pdf"]
        }
    }
    
    # Konfiguration speichern
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as config_file:
        json.dump(default_config, config_file, indent=4)
    
    logging.info(f"Standardkonfiguration unter {config_path} erstellt.")
    return default_config

def format_timestamp(timestamp: float) -> str:
    """
    Formatiert einen Unix-Timestamp als lesbare Zeichenkette.
    
    Args:
        timestamp: Unix-Timestamp
        
    Returns:
        Formatierte Zeichenkette (z.B. "2025-04-14 15:30:45")
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def calculate_change_percentage(old_value: float, new_value: float) -> float:
    """
    Berechnet die prozentuale Änderung zwischen zwei Werten.
    
    Args:
        old_value: Alter Wert
        new_value: Neuer Wert
        
    Returns:
        Prozentuale Änderung (z.B. 0.25 für 25% Wachstum)
    """
    if old_value == 0:
        return float('inf') if new_value > 0 else 0.0
    
    return (new_value - old_value) / abs(old_value)

def group_by_property(items: List[Dict[str, Any]], property_name: str) -> Dict[Any, List[Dict[str, Any]]]:
    """
    Gruppiert eine Liste von Dictionaries nach einem bestimmten Schlüssel.
    
    Args:
        items: Liste von Dictionaries
        property_name: Name des Schlüssels, nach dem gruppiert werden soll
        
    Returns:
        Dictionary mit Gruppen
    """
    result = {}
    for item in items:
        key = item.get(property_name)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result

def sanitize_filename(filename: str) -> str:
    """
    Säubert einen Dateinamen von unerlaubten Zeichen.
    
    Args:
        filename: Originaler Dateiname
        
    Returns:
        Gesäuberter Dateiname
    """
    # Unerlaubte Zeichen durch Unterstrich ersetzen
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
