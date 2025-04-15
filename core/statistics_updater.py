"""
Statistics Updater Module

Dieses Modul enthält Funktionen zum effizienten Aktualisieren der Statistikdaten,
indem es Änderungen an der Datenbank seit der letzten Aktualisierung erkennt
und nur die betroffenen Daten neu berechnet.
"""

import os
import logging
import json
import time
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

from core.stash_api import StashAPI
from core.data_models import Performer, Scene
from management.config_manager import ConfigManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class StatisticsUpdater:
    """
    Klasse zur effizienten Aktualisierung von Statistikdaten.
    """
    
    def __init__(self, api: StashAPI, config: ConfigManager):
        """
        Initialisiert den Statistik-Updater.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.config = config
        
        # Ausgabeverzeichnis
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')
        self.cache_dir = os.path.join(self.output_dir, '.cache')
        
        # Stellen sicher, dass das Cache-Verzeichnis existiert
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Konfiguration für die Aktualisierung
        self.force_update_interval = self.config.getint('Advanced', 'force_update_interval_days', fallback=7)
        self.cache_ttl = self.config.getint('Advanced', 'cache_ttl', fallback=3600)  # Sekunden
        self.enable_cache = self.config.getboolean('Advanced', 'enable_cache', fallback=True)
        
        # Hash-Datei und Statusdateien
        self.hash_file = os.path.join(self.cache_dir, 'data_hash.json')
        self.last_update_file = os.path.join(self.cache_dir, 'last_update.json')
        
        # Cache für Performer und Szenen
        self.performer_cache = {}
        self.scene_cache = {}
        
        logger.info("StatisticsUpdater initialisiert")
    
    def calculate_data_hash(self) -> Dict[str, str]:
        """
        Berechnet Hash-Werte für verschiedene Datengruppen, um Änderungen zu erkennen.
        
        Returns:
            Dict[str, str]: Dictionary mit Hash-Werten für verschiedene Datengruppen
        """
        # Sammeln von Daten für die Hashes
        performers = self.api.get_all_performers()
        scenes = self.api.get_all_scenes()
        tags = self.api.get_all_tags()
        
        # Erstelle Hasher für verschiedene Datengruppen
        performer_hasher = hashlib.md5()
        scene_hasher = hashlib.md5()
        tag_hasher = hashlib.md5()
        
        # Performer-Hash
        for performer in performers:
            # Relevant: ID, Aktualisierungsdatum, O-Counter, Rating, Favorit-Status
            performer_str = (
                f"{performer.get('id')}:{performer.get('updated_at', '')}:"
                f"{performer.get('o_counter', 0)}:{performer.get('rating100', 0)}:"
                f"{1 if performer.get('favorite', False) else 0}"
            )
            performer_hasher.update(performer_str.encode('utf-8'))
        
        # Szenen-Hash
        for scene in scenes:
            # Relevant: ID, Aktualisierungsdatum, O-Counter, Rating
            scene_str = (
                f"{scene.get('id')}:{scene.get('updated_at', '')}:"
                f"{scene.get('o_counter', 0)}:{scene.get('rating100', 0)}"
            )
            scene_hasher.update(scene_str.encode('utf-8'))
        
        # Tag-Hash
        for tag in tags:
            # Relevant: ID, Aktualisierungsdatum, Szenen-Anzahl, Performer-Anzahl
            tag_str = (
                f"{tag.get('id')}:{tag.get('updated_at', '')}:"
                f"{tag.get('scene_count', 0)}:{tag.get('performer_count', 0)}"
            )
            tag_hasher.update(tag_str.encode('utf-8'))
        
        # Gesamthash berechnen
        all_hasher = hashlib.md5()
        all_hasher.update(performer_hasher.hexdigest().encode('utf-8'))
        all_hasher.update(scene_hasher.hexdigest().encode('utf-8'))
        all_hasher.update(tag_hasher.hexdigest().encode('utf-8'))
        
        return {
            'all': all_hasher.hexdigest(),
            'performers': performer_hasher.hexdigest(),
            'scenes': scene_hasher.hexdigest(),
            'tags': tag_hasher.hexdigest()
        }
    
    def check_for_changes(self) -> Tuple[bool, Dict[str, bool]]:
        """
        Überprüft, ob Änderungen an den Daten vorliegen.
        
        Returns:
            Tuple[bool, Dict[str, bool]]: 
                - Ob Änderungen vorliegen
                - Dictionary mit Flags für die einzelnen Datengruppen
        """
        # Aktuelle Hashes berechnen
        current_hashes = self.calculate_data_hash()
        
        # Änderungsstatus für verschiedene Datengruppen
        changes = {
            'performers': False,
            'scenes': False,
            'tags': False,
            'force_update': False
        }
        
        # Prüfen, ob die Hash-Datei existiert
        if os.path.exists(self.hash_file):
            try:
                # Lade die gespeicherten Hashes
                with open(self.hash_file, 'r') as f:
                    stored_data = json.load(f)
                    stored_hashes = stored_data.get('hashes', {})
                    last_update_timestamp = stored_data.get('timestamp')
                
                # Prüfen, ob ein Force-Update notwendig ist
                if last_update_timestamp:
                    last_update = datetime.datetime.fromisoformat(last_update_timestamp)
                    days_since_update = (datetime.datetime.now() - last_update).days
                    
                    if days_since_update >= self.force_update_interval:
                        logger.info(f"Force-Update nach {days_since_update} Tagen (Intervall: {self.force_update_interval} Tage)")
                        changes['force_update'] = True
                        self._update_hash_file(current_hashes)
                        return True, changes
                
                # Vergleiche die Hashes
                if stored_hashes.get('all') != current_hashes.get('all'):
                    # Detaillierte Änderungen prüfen
                    changes['performers'] = stored_hashes.get('performers') != current_hashes.get('performers')
                    changes['scenes'] = stored_hashes.get('scenes') != current_hashes.get('scenes')
                    changes['tags'] = stored_hashes.get('tags') != current_hashes.get('tags')
                    
                    logger.info("Änderungen in den Daten festgestellt.")
                    if changes['performers']:
                        logger.info("Änderungen bei Performern festgestellt.")
                    if changes['scenes']:
                        logger.info("Änderungen bei Szenen festgestellt.")
                    if changes['tags']:
                        logger.info("Änderungen bei Tags festgestellt.")
                    
                    self._update_hash_file(current_hashes)
                    return True, changes
                else:
                    logger.info("Keine Änderungen in den Daten festgestellt.")
                    return False, changes
                    
            except Exception as e:
                logger.warning(f"Fehler beim Lesen der Hash-Datei: {e}")
                self._update_hash_file(current_hashes)
                return True, {k: True for k in changes}  # Alle als geändert markieren
        else:
            # Keine Hash-Datei gefunden, erstelle eine neue
            logger.info("Keine vorherige Hash-Datei gefunden. Führe initiale Verarbeitung durch.")
            self._update_hash_file(current_hashes)
            return True, {k: True for k in changes}  # Alle als geändert markieren
    
    def _update_hash_file(self, hashes: Dict[str, str]) -> None:
        """
        Aktualisiert die Hash-Datei mit den aktuellen Hashes und Zeitstempel.
        
        Args:
            hashes: Aktuelle Hash-Werte
        """
        try:
            # Aktuellen Zeitstempel hinzufügen
            data = {
                'hashes': hashes,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Hashfile speichern
            with open(self.hash_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug("Hash-Datei aktualisiert")
        except Exception as e:
            logger.error(f"Fehler beim Schreiben der Hash-Datei: {e}")
    
    def save_update_status(self, status: Dict[str, Any]) -> None:
        """
        Speichert den aktuellen Aktualisierungsstatus.
        
        Args:
            status: Statusdaten
        """
        try:
            # Status mit Zeitstempel
            status['timestamp'] = datetime.datetime.now().isoformat()
            
            # Status speichern
            with open(self.last_update_file, 'w') as f:
                json.dump(status, f, indent=2)
                
            logger.debug("Aktualisierungsstatus gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Aktualisierungsstatus: {e}")
    
    def get_last_update_status(self) -> Dict[str, Any]:
        """
        Lädt den Status der letzten Aktualisierung.
        
        Returns:
            Dict[str, Any]: Statusdaten oder leeres Dictionary, falls nicht verfügbar
        """
        if not os.path.exists(self.last_update_file):
            return {}
            
        try:
            with open(self.last_update_file, 'r') as f:
                status = json.load(f)
                return status
        except Exception as e:
            logger.warning(f"Fehler beim Laden des Aktualisierungsstatus: {e}")
            return {}
    
    def get_changed_performers(self) -> List[str]:
        """
        Ermittelt die IDs der geänderten Performer seit der letzten Aktualisierung.
        
        Returns:
            List[str]: Liste der Performer-IDs
        """
        # Diese Methode könnte erweitert werden, um spezifischere Änderungen zu erkennen
        # und nur die tatsächlich geänderten Performer zurückzugeben
        performers = self.api.get_all_performers()
        return [p.get('id') for p in performers if p.get('id')]
    
    def get_changed_scenes(self) -> List[str]:
        """
        Ermittelt die IDs der geänderten Szenen seit der letzten Aktualisierung.
        
        Returns:
            List[str]: Liste der Szenen-IDs
        """
        # Diese Methode könnte erweitert werden, um spezifischere Änderungen zu erkennen
        # und nur die tatsächlich geänderten Szenen zurückzugeben
        scenes = self.api.get_all_scenes()
        return [s.get('id') for s in scenes if s.get('id')]
    
    def cache_performers(self, performers: List[Performer]) -> None:
        """
        Speichert Performer-Objekte im Cache.
        
        Args:
            performers: Liste von Performer-Objekten
        """
        if not self.enable_cache:
            return
            
        for performer in performers:
            self.performer_cache[performer.id] = performer
    
    def cache_scenes(self, scenes: List[Scene]) -> None:
        """
        Speichert Szenen-Objekte im Cache.
        
        Args:
            scenes: Liste von Szenen-Objekten
        """
        if not self.enable_cache:
            return
            
        for scene in scenes:
            self.scene_cache[scene.id] = scene
    
    def clear_cache(self) -> None:
        """
        Löscht den Cache.
        """
        self.performer_cache = {}
        self.scene_cache = {}
        logger.debug("Cache gelöscht")
    
    def should_process_data(self, force: bool = False) -> Tuple[bool, Dict[str, bool]]:
        """
        Überprüft, ob die Daten verarbeitet werden sollten.
        
        Args:
            force: Erzwingt die Verarbeitung unabhängig von Änderungen
            
        Returns:
            Tuple[bool, Dict[str, bool]]: 
                - Ob Daten verarbeitet werden sollten
                - Dictionary mit Flags für die einzelnen Datengruppen
        """
        if force:
            logger.info("Verarbeitung erzwungen")
            changes = {
                'performers': True,
                'scenes': True,
                'tags': True,
                'force_update': True
            }
            # Aktualisiere die Hash-Datei, damit der nächste reguläre Lauf
            # Änderungen gegenüber dem aktuellen Stand erkennt
            self._update_hash_file(self.calculate_data_hash())
            return True, changes
        
        # Normale Änderungsprüfung
        return self.check_for_changes()
    
    def update_statistics_incrementally(self, stats_module, changes: Dict[str, bool]) -> bool:
        """
        Aktualisiert Statistiken inkrementell basierend auf erkannten Änderungen.
        
        Args:
            stats_module: Statistikmodul
            changes: Dictionary mit Flags für geänderte Datengruppen
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            # Wenn keine spezifischen Änderungen oder Force-Update, alles neu berechnen
            if changes.get('force_update') or all(changes.values()):
                logger.info("Vollständige Neuberechnung der Statistiken")
                stats_module.calculate_all_statistics()
                return True
            
            # Inkrementelle Aktualisierung
            if changes.get('performers'):
                logger.info("Aktualisiere Performer-Statistiken")
                if hasattr(stats_module, 'update_performer_stats'):
                    stats_module.update_performer_stats()
                else:
                    # Fallback: volle Neuberechnung
                    stats_module.calculate_all_statistics()
                    return True
            
            if changes.get('scenes'):
                logger.info("Aktualisiere Szenen-Statistiken")
                if hasattr(stats_module, 'update_scene_stats'):
                    stats_module.update_scene_stats()
                else:
                    # Fallback: volle Neuberechnung
                    stats_module.calculate_all_statistics()
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der inkrementellen Aktualisierung: {e}")
            
            # Bei Fehler: vollständige Neuberechnung
            try:
                logger.info("Fallback: Vollständige Neuberechnung der Statistiken")
                stats_module.calculate_all_statistics()
                return True
            except Exception as e2:
                logger.error(f"Fehler bei der vollständigen Neuberechnung: {e2}")
                return False
                
    def log_update_summary(self, start_time: float, changes: Dict[str, bool]) -> None:
        """
        Loggt eine Zusammenfassung der Aktualisierung.
        
        Args:
            start_time: Startzeit der Aktualisierung
            changes: Dictionary mit Flags für geänderte Datengruppen
        """
        end_time = time.time()
        runtime = end_time - start_time
        
        # Zusammenfassung erstellen
        summary = {
            'runtime_seconds': round(runtime, 2),
            'changes': changes,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        # Status speichern
        self.save_update_status(summary)
        
        # Log-Ausgabe
        logger.info(f"Aktualisierung abgeschlossen in {runtime:.2f} Sekunden")
        if changes.get('performers'):
            logger.info("Performer-Daten wurden aktualisiert")
        if changes.get('scenes'):
            logger.info("Szenen-Daten wurden aktualisiert")
        if changes.get('tags'):
            logger.info("Tag-Daten wurden aktualisiert")
        if changes.get('force_update'):
            logger.info("Vollständige Aktualisierung (Force-Update)")
