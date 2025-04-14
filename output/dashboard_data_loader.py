"""
dashboard_data_loader.py - Datenlademodul für das Stasapp Dashboard

Dieses Modul ist verantwortlich für das Laden von Daten aus verschiedenen Quellen
in das Dashboard-System. Es unterstützt verschiedene Datenbankanbindungen sowie
das Laden aus Dateien.
"""

import os
import json
import sqlite3
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import pickle
import datetime

# Cache-Dictionary für geladene Daten
_data_cache = {}
_cache_timestamps = {}

class DataLoader:
    """Klasse zum Laden von Daten für das Dashboard"""
    
    def __init__(self, data_source: str, cache_timeout: int = 3600):
        """
        Initialisiert den DataLoader.
        
        Args:
            data_source: Pfad zur Datenquelle oder Datenbankverbindungsstring
            cache_timeout: Cache-Timeout in Sekunden (Standard: 1 Stunde)
        """
        self.logger = logging.getLogger(__name__)
        self.data_source = data_source
        self.cache_timeout = cache_timeout
        self.engine = None
        self.Session = None
        
        # Datenbankverbindung einrichten, wenn es sich um eine Datenbank handelt
        if data_source.startswith(('sqlite://', 'mysql://', 'postgresql://')):
            self.engine = sa.create_engine(data_source)
            self.Session = sessionmaker(bind=self.engine)
            self.logger.info(f"Datenbankverbindung zu {data_source} hergestellt")
        else:
            self.logger.info(f"Verwende Dateiquelle: {data_source}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Überprüft, ob ein Cache-Eintrag noch gültig ist.
        
        Args:
            cache_key: Schlüssel des Cache-Eintrags
            
        Returns:
            True, wenn der Cache-Eintrag gültig ist, sonst False
        """
        if cache_key not in _cache_timestamps:
            return False
        
        cache_time = _cache_timestamps[cache_key]
        current_time = datetime.datetime.now().timestamp()
        
        return (current_time - cache_time) < self.cache_timeout
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        Lädt Daten aus dem Cache.
        
        Args:
            cache_key: Schlüssel des Cache-Eintrags
            
        Returns:
            Daten aus dem Cache oder None, falls nicht vorhanden oder veraltet
        """
        if cache_key in _data_cache and self._is_cache_valid(cache_key):
            self.logger.debug(f"Daten für {cache_key} aus Cache geladen")
            return _data_cache[cache_key]
        
        return None
    
    def _store_in_cache(self, cache_key: str, data: Any) -> None:
        """
        Speichert Daten im Cache.
        
        Args:
            cache_key: Schlüssel des Cache-Eintrags
            data: Zu speichernde Daten
        """
        _data_cache[cache_key] = data
        _cache_timestamps[cache_key] = datetime.datetime.now().timestamp()
        self.logger.debug(f"Daten für {cache_key} im Cache gespeichert")
    
    def load_user_data(self) -> pd.DataFrame:
        """
        Lädt Nutzerdaten.
        
        Returns:
            DataFrame mit Nutzerdaten
        """
        cache_key = f"{self.data_source}:user_data"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        self.logger.info("Lade Nutzerdaten")
        
        try:
            if self.engine:
                # Laden aus Datenbank
                query = "SELECT * FROM users"
                df = pd.read_sql(query, self.engine)
            else:
                # Laden aus Datei (z.B. CSV oder JSON)
                if os.path.isdir(self.data_source):
                    file_path = os.path.join(self.data_source, "users.csv")
                    if os.path.exists(file_path):
                        df = pd.read_csv(file_path)
                    else:
                        file_path = os.path.join(self.data_source, "users.json")
                        if os.path.exists(file_path):
                            df = pd.read_json(file_path)
                        else:
                            raise FileNotFoundError("Keine Nutzerdaten gefunden")
                else:
                    raise ValueError(f"Ungültige Datenquelle: {self.data_source}")
            
            self.logger.info(f"{len(df)} Nutzereinträge geladen")
            self._store_in_cache(cache_key, df)
            return df
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Nutzerdaten: {str(e)}")
            # Fallback zu leeren Daten
            return pd.DataFrame()
    
    def load_content_data(self) -> pd.DataFrame:
        """
        Lädt Inhaltsdaten.
        
        Returns:
            DataFrame mit Inhaltsdaten
        """
        cache_key = f"{self.data_source}:content_data"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        self.logger.info("Lade Inhaltsdaten")
        
        try:
            if self.engine:
                # Laden aus Datenbank
                query = "SELECT * FROM content"
                df = pd.read_sql(query, self.engine)
            else:
                # Laden aus Datei (z.B. CSV oder JSON)
                if os.path.isdir(self.data_source):
                    file_path = os.path.join(self.data_source, "content.csv")
                    if os.path.exists(file_path):
                        df = pd.read_csv(file_path)
                    else:
                        file_path = os.path.join(self.data_source, "content.json")
                        if os.path.exists(file_path):
                            df = pd.read_json(file_path)
                        else:
                            raise FileNotFoundError("Keine Inhaltsdaten gefunden")
                else:
                    raise ValueError(f"Ungültige Datenquelle: {self.data_source}")
            
            self.logger.info(f"{len(df)} Inhaltseinträge geladen")
            self._store_in_cache(cache_key, df)
            return df
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Inhaltsdaten: {str(e)}")
            # Fallback zu leeren Daten
            return pd.DataFrame()
    
    def load_viewing_history(self) -> pd.DataFrame:
        """
        Lädt Sehgewohnheiten / Nutzungsdaten.
        
        Returns:
            DataFrame mit Nutzungshistorie
        """
        cache_key = f"{self.data_source}:viewing_history"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        self.logger.info("Lade Nutzungshistorie")
        
        try:
            if self.engine:
                # Laden aus Datenbank
                query = """
                SELECT * FROM viewing_history 
                ORDER BY user_id, timestamp
                """
                df = pd.read_sql(query, self.engine)
            else:
                # Laden aus Datei (z.B. CSV oder JSON)
                if os.path.isdir(self.data_source):
                    file_path = os.path.join(self.data_source, "viewing_history.csv")
                    if os.path.exists(file_path):
                        df = pd.read_csv(file_path)
                    else:
                        file_path = os.path.join(self.data_source, "viewing_history.json")
                        if os.path.exists(file_path):
                            df = pd.read_json(file_path)
                        else:
                            raise FileNotFoundError("Keine Nutzungshistorie gefunden")
                else:
                    raise ValueError(f"Ungültige Datenquelle: {self.data_source}")
            
            # Konvertiere Timestamp zu datetime, falls notwendig
            if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            self.logger.info(f"{len(df)} Einträge in der Nutzungshistorie geladen")
            self._store_in_cache(cache_key, df)
            return df
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Nutzungshistorie: {str(e)}")
            # Fallback zu leeren Daten
            return pd.DataFrame()
    
    def load_custom_data(self, query_or_file: str) -> pd.DataFrame:
        """
        Lädt benutzerdefinierte Daten mit einer SQL-Abfrage oder aus einer Datei.
        
        Args:
            query_or_file: SQL-Abfrage oder Dateipfad
            
        Returns:
            DataFrame mit den abgefragten Daten
        """
        cache_key = f"{self.data_source}:{hash(query_or_file)}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        self.logger.info(f"Lade benutzerdefinierte Daten: {query_or_file[:50]}...")
        
        try:
            if self.engine and (query_or_file.strip().upper().startswith("SELECT") or 
                               query_or_file.strip().upper().startswith("WITH")):
                # Annahme: Bei SQL-Engine und SELECT-Statement ist es eine SQL-Abfrage
                df = pd.read_sql(query_or_file, self.engine)
                self.logger.info(f"{len(df)} Einträge mit benutzerdefinierter Abfrage geladen")
            else:
                # Ansonsten als Dateipfad interpretieren
                file_path = query_or_file
                if not os.path.isabs(file_path) and os.path.isdir(self.data_source):
                    # Relativer Pfad zur Datenquelle
                    file_path = os.path.join(self.data_source, file_path)
                
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.csv':
                    df = pd.read_csv(file_path)
                elif ext == '.json':
                    df = pd.read_json(file_path)
                elif ext == '.xlsx' or ext == '.xls':
                    df = pd.read_excel(file_path)
                elif ext == '.parquet':
                    df = pd.read_parquet(file_path)
                elif ext == '.pickle' or ext == '.pkl':
                    with open(file_path, 'rb') as f:
                        df = pickle.load(f)
                else:
                    raise ValueError(f"Nicht unterstütztes Dateiformat: {ext}")
                
                self.logger.info(f"{len(df)} Einträge aus {file_path} geladen")
            
            self._store_in_cache(cache_key, df)
            return df
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden benutzerdefinierter Daten: {str(e)}")
            # Fallback zu leeren Daten
            return pd.DataFrame()
    
    def clear_cache(self, key: Optional[str] = None) -> None:
        """
        Löscht Einträge aus dem Cache.
        
        Args:
            key: Optionaler Schlüssel, der gelöscht werden soll. 
                 Wenn None, wird der gesamte Cache gelöscht.
        """
        global _data_cache, _cache_timestamps
        
        if key is None:
            # Gesamten Cache löschen
            _data_cache = {}
            _cache_timestamps = {}
            self.logger.info("Gesamter Cache gelöscht")
        elif key in _data_cache:
            # Nur den angegebenen Schlüssel löschen
            del _data_cache[key]
            if key in _cache_timestamps:
                del _cache_timestamps[key]
            self.logger.info(f"Cache-Eintrag für {key} gelöscht")
        else:
            self.logger.warning(f"Cache-Eintrag für {key} nicht gefunden")
