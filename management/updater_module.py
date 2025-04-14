"""
Updater Module

Dieses Modul ist verantwortlich für die Aktualisierung von Performer-Metadaten in StashApp
basierend auf berechneten Werten aus dem Statistikmodul.
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Union
import re

from core.stash_api import StashAPI
from core.data_models import Performer
from analysis.statistics_module import StatisticsModule
from management.config_manager import ConfigManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class UpdaterModule:
    """
    Klasse zur Aktualisierung von Performer-Metadaten in StashApp basierend auf 
    berechneten Statistiken und Messungen.
    """
    
    def __init__(self, api: StashAPI, stats_module: StatisticsModule, config: ConfigManager):
        """
        Initialisiert das Updater-Modul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.stats_module = stats_module
        self.config = config
        
        # Lade Konfigurationsoptionen
        self.update_bra_sizes = self.config.getboolean('Updater', 'update_bra_sizes', fallback=True)
        self.update_bmi_categories = self.config.getboolean('Updater', 'update_bmi_categories', fallback=True)
        self.update_ratios = self.config.getboolean('Updater', 'update_ratios', fallback=True)
        self.create_missing_tags = self.config.getboolean('Updater', 'create_missing_tags', fallback=True)
        self.dry_run = self.config.getboolean('Updater', 'dry_run', fallback=False)
        self.rate_limit_delay = self.config.getfloat('Updater', 'rate_limit_delay', fallback=0.5)
        
        # Cache für Tag-IDs, um wiederholte API-Abfragen zu vermeiden
        self.tag_id_cache = {}
        
        logger.info("Updater-Modul initialisiert")
    
    def update_all(self) -> Dict[str, int]:
        """
        Führt alle konfigurierten Updates durch.
        
        Returns:
            Dict[str, int]: Statistik über die Anzahl der durchgeführten Updates
        """
        if self.dry_run:
            logger.info("DRY RUN MODUS: Es werden keine tatsächlichen Änderungen vorgenommen")
        
        stats = {
            "total_performers": len(self.stats_module.performers),
            "updated_performers": 0,
            "bra_sizes_updated": 0,
            "bmi_categories_updated": 0,
            "ratios_updated": 0,
            "tags_created": 0,
            "tags_assigned": 0,
            "errors": 0
        }
        
        performers = self.stats_module.performers
        logger.info(f"Starte Update für {len(performers)} Performer")
        
        for i, performer in enumerate(performers):
            try:
                # Fortschritt anzeigen
                if (i + 1) % 10 == 0 or i + 1 == len(performers):
                    logger.info(f"Fortschritt: {i+1}/{len(performers)} Performer verarbeitet")
                
                # Updates für diesen Performer durchführen
                updated = self._update_performer(performer)
                
                if updated:
                    stats["updated_performers"] += 1
                
                # Kurze Pause, um API-Rate-Limits zu beachten
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Fehler beim Aktualisieren von {performer.name}: {str(e)}")
                stats["errors"] += 1
        
        # Abschlussbericht
        logger.info("Update abgeschlossen. Zusammenfassung:")
        logger.info(f"- Insgesamt verarbeitet: {stats['total_performers']} Performer")
        logger.info(f"- Aktualisierte Performer: {stats['updated_performers']}")
        logger.info(f"- BH-Größen aktualisiert: {stats['bra_sizes_updated']}")
        logger.info(f"- BMI-Kategorien aktualisiert: {stats['bmi_categories_updated']}")
        logger.info(f"- Verhältnisse aktualisiert: {stats['ratios_updated']}")
        logger.info(f"- Tags erstellt: {stats['tags_created']}")
        logger.info(f"- Tags zugewiesen: {stats['tags_assigned']}")
        logger.info(f"- Fehler: {stats['errors']}")
        
        return stats
    
    def _update_performer(self, performer: Performer) -> bool:
        """
        Aktualisiert die Metadaten eines einzelnen Performers.
        
        Args:
            performer: Der zu aktualisierende Performer
            
        Returns:
            bool: True, wenn Updates durchgeführt wurden, sonst False
        """
        updates_performed = False
        
        # BH-Größen aktualisieren
        if self.update_bra_sizes and performer.german_bra_size:
            bra_tag_name = f"BH-Größe: {performer.german_bra_size}"
            cup_tag_name = f"Cup: {performer.cup_size}"
            band_tag_name = f"Unterbrustweite: {performer.band_size}"
            
            # BH-Größen-Tag hinzufügen
            if self._add_tag_to_performer(performer, bra_tag_name):
                updates_performed = True
            
            # Cup-Größen-Tag hinzufügen
            if performer.cup_size and self._add_tag_to_performer(performer, cup_tag_name):
                updates_performed = True
            
            # Unterbrustweiten-Tag hinzufügen
            if performer.band_size and self._add_tag_to_performer(performer, band_tag_name):
                updates_performed = True
        
        # BMI-Kategorien aktualisieren
        if self.update_bmi_categories and performer.bmi_category:
            bmi_tag_name = f"BMI: {performer.bmi_category}"
            
            # BMI-Kategorie-Tag hinzufügen
            if self._add_tag_to_performer(performer, bmi_tag_name):
                updates_performed = True
        
        # Verhältnisse aktualisieren
        if self.update_ratios:
            # BMI zu Cup-Größe Verhältnis
            if performer.bmi_to_cup_ratio:
                ratio_value = performer.bmi_to_cup_ratio
                ratio_range = self._get_ratio_range(ratio_value)
                bmi_cup_tag_name = f"BMI/Cup: {ratio_range}"
                
                if self._add_tag_to_performer(performer, bmi_cup_tag_name):
                    updates_performed = True
            
            # Größe zu Cup-Größe Verhältnis
            if performer.height_to_cup_ratio:
                ratio_value = performer.height_to_cup_ratio
                ratio_range = self._get_ratio_range(ratio_value, step=10)
                height_cup_tag_name = f"Größe/Cup: {ratio_range}"
                
                if self._add_tag_to_performer(performer, height_cup_tag_name):
                    updates_performed = True
        
        return updates_performed
    
    def _add_tag_to_performer(self, performer: Performer, tag_name: str) -> bool:
        """
        Fügt einem Performer einen Tag hinzu, erstellt den Tag falls nötig.
        
        Args:
            performer: Der Performer, dem der Tag hinzugefügt werden soll
            tag_name: Der Name des Tags
            
        Returns:
            bool: True, wenn der Tag hinzugefügt wurde, False wenn der Tag bereits vorhanden war oder ein Fehler auftrat
        """
        # Prüfen, ob der Performer den Tag bereits hat
        if tag_name in performer.tags:
            logger.debug(f"Tag '{tag_name}' bereits bei {performer.name} vorhanden")
            return False
        
        # Im Dry-Run-Modus nur loggen
        if self.dry_run:
            logger.info(f"DRY RUN: Würde Tag '{tag_name}' zu {performer.name} hinzufügen")
            return True
        
        try:
            # Tag-ID abrufen oder Tag erstellen
            tag_id = self._get_or_create_tag(tag_name)
            
            if not tag_id:
                logger.warning(f"Konnte Tag '{tag_name}' nicht finden oder erstellen")
                return False
            
            # Tag zum Performer hinzufügen
            result = self.api.add_tag_to_performer(performer.id, tag_id)
            
            if result:
                logger.info(f"Tag '{tag_name}' erfolgreich zu {performer.name} hinzugefügt")
                return True
            else:
                logger.warning(f"Fehler beim Hinzufügen des Tags '{tag_name}' zu {performer.name}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Tags '{tag_name}' zu {performer.name}: {str(e)}")
            return False
    
    def _get_or_create_tag(self, tag_name: str) -> Optional[str]:
        """
        Ruft die ID eines Tags ab oder erstellt einen neuen Tag, wenn er nicht existiert.
        
        Args:
            tag_name: Der Name des gesuchten Tags
            
        Returns:
            Optional[str]: Die ID des Tags oder None bei Fehler
        """
        # Prüfen, ob die Tag-ID bereits im Cache ist
        if tag_name in self.tag_id_cache:
            return self.tag_id_cache[tag_name]
        
        # Tag-ID abrufen
        tag_id = self.api.get_tag_id_by_name(tag_name)
        
        # Falls Tag nicht existiert und create_missing_tags aktiviert ist, Tag erstellen
        if not tag_id and self.create_missing_tags:
            logger.info(f"Tag '{tag_name}' nicht gefunden, erstelle neu")
            tag_id = self.api.create_tag(tag_name)
            
            if tag_id:
                logger.info(f"Tag '{tag_name}' erfolgreich erstellt, ID: {tag_id}")
            else:
                logger.warning(f"Fehler beim Erstellen des Tags '{tag_name}'")
        
        # Tag-ID im Cache speichern
        if tag_id:
            self.tag_id_cache[tag_name] = tag_id
        
        return tag_id
    
    def _get_ratio_range(self, ratio: float, step: float = 1.0) -> str:
        """
        Ermittelt den Bereich für ein Verhältnis (z.B. "5.0-6.0").
        
        Args:
            ratio: Der Verhältniswert
            step: Die Schrittweite für die Bereiche
            
        Returns:
            str: Der Bereichsname (z.B. "5.0-6.0")
        """
        # Untergrenze bestimmen (auf step gerundet)
        lower_bound = int(ratio / step) * step
        upper_bound = lower_bound + step
        
        return f"{lower_bound:.1f}-{upper_bound:.1f}"
    
    def update_bra_sizes_only(self) -> Dict[str, int]:
        """
        Aktualisiert nur die BH-Größen-Tags.
        
        Returns:
            Dict[str, int]: Statistik über die Anzahl der durchgeführten Updates
        """
        # Temporär nur BH-Größen-Updates aktivieren
        original_bmi = self.update_bmi_categories
        original_ratios = self.update_ratios
        
        self.update_bmi_categories = False
        self.update_ratios = False
        
        result = self.update_all()
        
        # Ursprüngliche Einstellungen wiederherstellen
        self.update_bmi_categories = original_bmi
        self.update_ratios = original_ratios
        
        return result
    
    def update_bmi_categories_only(self) -> Dict[str, int]:
        """
        Aktualisiert nur die BMI-Kategorie-Tags.
        
        Returns:
            Dict[str, int]: Statistik über die Anzahl der durchgeführten Updates
        """
        # Temporär nur BMI-Kategorien-Updates aktivieren
        original_bra = self.update_bra_sizes
        original_ratios = self.update_ratios
        
        self.update_bra_sizes = False
        self.update_ratios = False
        
        result = self.update_all()
        
        # Ursprüngliche Einstellungen wiederherstellen
        self.update_bra_sizes = original_bra
        self.update_ratios = original_ratios
        
        return result
    
    def update_ratios_only(self) -> Dict[str, int]:
        """
        Aktualisiert nur die Verhältnis-Tags.
        
        Returns:
            Dict[str, int]: Statistik über die Anzahl der durchgeführten Updates
        """
        # Temporär nur Verhältnis-Updates aktivieren
        original_bra = self.update_bra_sizes
        original_bmi = self.update_bmi_categories
        
        self.update_bra_sizes = False
        self.update_bmi_categories = False
        
        result = self.update_all()
        
        # Ursprüngliche Einstellungen wiederherstellen
        self.update_bra_sizes = original_bra
        self.update_bmi_categories = original_bmi
        
        return result
    
    def test_run(self) -> Dict[str, List[str]]:
        """
        Führt einen Testlauf durch, ohne tatsächliche Änderungen vorzunehmen.
        
        Returns:
            Dict[str, List[str]]: Liste der zu erstellenden Tags und der Performer-Tag-Zuordnungen
        """
        original_dry_run = self.dry_run
        self.dry_run = True
        
        performers = self.stats_module.performers
        
        # Listen für die Ergebnisse
        results = {
            "to_create_tags": set(),
            "performer_tag_assignments": []
        }
        
        for performer in performers:
            # BH-Größen
            if self.update_bra_sizes and performer.german_bra_size:
                bra_tag_name = f"BH-Größe: {performer.german_bra_size}"
                cup_tag_name = f"Cup: {performer.cup_size}"
                band_tag_name = f"Unterbrustweite: {performer.band_size}"
                
                if bra_tag_name not in performer.tags:
                    results["to_create_tags"].add(bra_tag_name)
                    results["performer_tag_assignments"].append(f"{performer.name} -> {bra_tag_name}")
                
                if performer.cup_size and cup_tag_name not in performer.tags:
                    results["to_create_tags"].add(cup_tag_name)
                    results["performer_tag_assignments"].append(f"{performer.name} -> {cup_tag_name}")
                
                if performer.band_size and band_tag_name not in performer.tags:
                    results["to_create_tags"].add(band_tag_name)
                    results["performer_tag_assignments"].append(f"{performer.name} -> {band_tag_name}")
            
            # BMI-Kategorien
            if self.update_bmi_categories and performer.bmi_category:
                bmi_tag_name = f"BMI: {performer.bmi_category}"
                
                if bmi_tag_name not in performer.tags:
                    results["to_create_tags"].add(bmi_tag_name)
                    results["performer_tag_assignments"].append(f"{performer.name} -> {bmi_tag_name}")
            
            # Verhältnisse
            if self.update_ratios:
                # BMI zu Cup-Größe Verhältnis
                if performer.bmi_to_cup_ratio:
                    ratio_value = performer.bmi_to_cup_ratio
                    ratio_range = self._get_ratio_range(ratio_value)
                    bmi_cup_tag_name = f"BMI/Cup: {ratio_range}"
                    
                    if bmi_cup_tag_name not in performer.tags:
                        results["to_create_tags"].add(bmi_cup_tag_name)
                        results["performer_tag_assignments"].append(f"{performer.name} -> {bmi_cup_tag_name}")
                
                # Größe zu Cup-Größe Verhältnis
                if performer.height_to_cup_ratio:
                    ratio_value = performer.height_to_cup_ratio
                    ratio_range = self._get_ratio_range(ratio_value, step=10)
                    height_cup_tag_name = f"Größe/Cup: {ratio_range}"
                    
                    if height_cup_tag_name not in performer.tags:
                        results["to_create_tags"].add(height_cup_tag_name)
                        results["performer_tag_assignments"].append(f"{performer.name} -> {height_cup_tag_name}")
        
        # Ursprüngliche Einstellung wiederherstellen
        self.dry_run = original_dry_run
        
        # Konvertiere Sets zu geordneten Listen für bessere Lesbarkeit
        results["to_create_tags"] = sorted(list(results["to_create_tags"]))
        
        return results
