"""
Dashboard Utilities

Dieses Modul enthält Hilfsfunktionen für das Dashboard-System.
"""

import os
import logging
from typing import List, Optional

from core.data_models import Performer, Scene

# Logger konfigurieren
logger = logging.getLogger(__name__)

def ensure_directories(directories: List[str]) -> None:
    """
    Stellt sicher, dass die angegebenen Verzeichnisse existieren.
    
    Args:
        directories: Liste von Verzeichnispfaden
    """
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Verzeichnis erstellt: {directory}")

def get_performer_image_url(performer: Performer, api_url: str) -> Optional[str]:
    """
    Ermittelt die URL zum Bild eines Performers.
    
    Args:
        performer: Performer-Objekt
        api_url: Basis-URL der StashApp-API
        
    Returns:
        Optional[str]: Bild-URL oder None, wenn kein Bild vorhanden
    """
    if performer.raw_data and "image_path" in performer.raw_data:
        image_path = performer.raw_data["image_path"]
        if image_path:
            return f"{api_url}/performer/{performer.id}/image"
    return None

def get_scene_image_url(scene: Scene, api_url: str) -> Optional[str]:
    """
    Ermittelt die URL zum Screenshot einer Szene.
    
    Args:
        scene: Szene-Objekt
        api_url: Basis-URL der StashApp-API
        
    Returns:
        Optional[str]: Screenshot-URL oder None, wenn kein Screenshot vorhanden
    """
    if scene.raw_data and "paths" in scene.raw_data:
        paths = scene.raw_data["paths"]
        if paths and "screenshot" in paths:
            screenshot_path = paths["screenshot"]
            if screenshot_path:
                return f"{api_url}/scene/{scene.id}/screenshot"
    return None

def format_duration(seconds: float) -> str:
    """
    Formatiert eine Zeitdauer in Sekunden als lesbare Zeichenkette.
    
    Args:
        seconds: Zeitdauer in Sekunden
        
    Returns:
        str: Formatierte Zeitdauer (z.B. "1:23:45")
    """
    if seconds <= 0:
        return "0:00"
    
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Kürzt einen Text auf die angegebene Länge und fügt '...' hinzu.
    
    Args:
        text: Der zu kürzende Text
        max_length: Maximale Länge des Textes
        
    Returns:
        str: Gekürzter Text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    Wandelt ein verschachteltes Dictionary in ein flaches Dictionary um.
    
    Args:
        d: Verschachteltes Dictionary
        parent_key: Schlüssel des Elternelements (für Rekursion)
        sep: Trennzeichen für verschachtelte Schlüssel
        
    Returns:
        dict: Flaches Dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)