#!/usr/bin/env python3
"""
StashApp Statistics - Hauptprogramm

Dieses Skript dient als Einstiegspunkt für die statistische Analyse
und Empfehlungsgenerierung der StashApp-Daten. Es wird zyklisch ausgeführt,
um Änderungen in der Datenbank zu erkennen und entsprechend zu verarbeiten.

Verwendung:
    python statistics_main.py [options]
"""

import os
import sys
import argparse
import logging
import json
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
import hashlib
from pathlib import Path

# Importieren der Module
try:
    from management.config_manager import ConfigManager
    from core.stash_api import StashAPI
    from analysis.statistics_module import StatisticsModule
    from analysis.visualization_module import VisualizationModule
    from recommendations.recommendation_performer import PerformerRecommendationModule
    from recommendations.recommendation_scenes import SceneRecommendationModule
    from output.discord_module import DiscordModule
    from management.updater_module import UpdaterModule
except ImportError as e:
    print(f"Fehler beim Importieren der Module: {e}")
    print("Bitte stellen Sie sicher, dass alle Module installiert sind.")
    sys.exit(1)

def setup_logging(config: ConfigManager) -> logging.Logger:
    """
    Richtet das Logging-System ein.
    
    Args:
        config: Konfigurationsobjekt
        
    Returns:
        logging.Logger: Konfigurierten Logger
    """
    log_level_str = config.get('Logging', 'log_level', fallback='INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    log_file = config.get('Logging', 'log_file', fallback='stashapp_analytics.log')
    log_format = config.get('Logging', 'log_format', 
                           fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_date_format = config.get('Logging', 'log_date_format', 
                                fallback='%Y-%m-%d %H:%M:%S')
    
    # Maximale Größe und Backup-Anzahl der Logdatei
    max_bytes = config.getint('Logging', 'log_file_max_size', fallback=10485760)  # 10 MB
    backup_count = config.getint('Logging', 'log_file_backup_count', fallback=3)
    
    # Logger konfigurieren
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Handler entfernen, falls bereits vorhanden
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler hinzufügen
    if log_file.lower() == 'console':
        # Nur Konsolenausgabe
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, log_date_format))
        logger.addHandler(console_handler)
    else:
        # Logdatei und Konsolenausgabe
        try:
            # Stelle sicher, dass Verzeichnis existiert
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # Rotating File Handler für automatische Rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(logging.Formatter(log_format, log_date_format))
            logger.addHandler(file_handler)
            
            # Zusätzlich Konsolenausgabe
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format, log_date_format))
            logger.addHandler(console_handler)
        except Exception as e:
            print(f"Fehler beim Einrichten der Logdatei: {e}")
            # Fallback zur Konsolenausgabe
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_format, log_date_format))
            logger.addHandler(console_handler)
    
    return logger

def create_output_directories(config: ConfigManager) -> None:
    """
    Erstellt die benötigten Ausgabeverzeichnisse.
    
    Args:
        config: Konfigurationsobjekt
    """
    # Verzeichnisse aus der Konfiguration laden
    output_dir = config.get('Output', 'output_dir', fallback='./output')
    visualization_dir = config.get('Output', 'visualization_dir', 
                                  fallback=os.path.join(output_dir, 'graphs'))
    
    # Verzeichnisse erstellen, falls nicht vorhanden
    for directory in [output_dir, visualization_dir]:
        os.makedirs(directory, exist_ok=True)

def calculate_data_hash(api: StashAPI) -> str:
    """
    Berechnet einen Hash-Wert der aktuellen Daten, um Änderungen zu erkennen.
    
    Args:
        api: API-Instanz
        
    Returns:
        str: Hash-Wert der Daten
    """
    # Sammeln von Daten für den Hash
    performers = api.get_all_performers()
    scenes = api.get_all_scenes()
    
    # Erstelle einen Hash aus den Daten
    hasher = hashlib.md5()
    
    # Füge performer-relevante Daten hinzu
    for performer in performers:
        performer_str = f"{performer.get('id')}:{performer.get('updated_at', '')}:{performer.get('o_counter', 0)}:{performer.get('rating100', 0)}"
        hasher.update(performer_str.encode('utf-8'))
    
    # Füge scene-relevante Daten hinzu
    for scene in scenes:
        scene_str = f"{scene.get('id')}:{scene.get('updated_at', '')}:{scene.get('o_counter', 0)}:{scene.get('rating100', 0)}"
        hasher.update(scene_str.encode('utf-8'))
    
    return hasher.hexdigest()

def should_process_data(api: StashAPI, config: ConfigManager, logger: logging.Logger) -> bool:
    """
    Überprüft, ob die Daten verarbeitet werden sollten (basierend auf Änderungen).
    
    Args:
        api: API-Instanz
        config: Konfigurationsobjekt
        logger: Logger-Instanz
        
    Returns:
        bool: True, wenn Daten verarbeitet werden sollten
    """
    # Berechne Hash der aktuellen Daten
    current_hash = calculate_data_hash(api)
    
    # Dateipfad für den gespeicherten Hash
    output_dir = config.get('Output', 'output_dir', fallback='./output')
    hash_file = os.path.join(output_dir, '.data_hash')
    
    # Force-Update-Intervall in Tagen
    force_update_interval = config.getint('Advanced', 'force_update_interval_days', fallback=7)
    
    # Prüfen, ob die Hash-Datei existiert
    if os.path.exists(hash_file):
        try:
            # Lese den gespeicherten Hash und Timestamp
            with open(hash_file, 'r') as f:
                content = f.read().strip().split('|')
                stored_hash = content[0]
                
                # Prüfen, ob Zeitstempel vorhanden ist
                if len(content) > 1:
                    last_update_str = content[1]
                    last_update = datetime.datetime.fromisoformat(last_update_str)
                    
                    # Prüfen, ob ein Force-Update notwendig ist
                    days_since_update = (datetime.datetime.now() - last_update).days
                    if days_since_update >= force_update_interval:
                        logger.info(f"Force-Update nach {days_since_update} Tagen (Intervall: {force_update_interval} Tage)")
                        update_hash_file(hash_file, current_hash)
                        return True
                
                # Vergleichen der Hashes
                if stored_hash == current_hash:
                    logger.info("Keine Änderungen in den Daten festgestellt.")
                    return False
                else:
                    logger.info("Änderungen in den Daten festgestellt.")
                    update_hash_file(hash_file, current_hash)
                    return True
        except Exception as e:
            logger.warning(f"Fehler beim Lesen der Hash-Datei: {e}")
            update_hash_file(hash_file, current_hash)
            return True
    else:
        # Keine Hash-Datei gefunden, erstelle eine neue
        logger.info("Keine vorherige Hash-Datei gefunden. Führe initiale Verarbeitung durch.")
        update_hash_file(hash_file, current_hash)
        return True

def update_hash_file(hash_file: str, current_hash: str) -> None:
    """
    Aktualisiert die Hash-Datei mit dem aktuellen Hash und Zeitstempel.
    
    Args:
        hash_file: Pfad zur Hash-Datei
        current_hash: Aktueller Hash-Wert
    """
    try:
        # Erstelle Verzeichnis, falls nicht vorhanden
        os.makedirs(os.path.dirname(hash_file), exist_ok=True)
        
        # Speichere Hash und aktuellen Zeitstempel
        timestamp = datetime.datetime.now().isoformat()
        with open(hash_file, 'w') as f:
            f.write(f"{current_hash}|{timestamp}")
    except Exception as e:
        print(f"Fehler beim Schreiben der Hash-Datei: {e}")

def parse_arguments():
    """
    Parst die Kommandozeilenargumente.
    
    Returns:
        argparse.Namespace: Die geparsten Argumente
    """
    parser = argparse.ArgumentParser(description='StashApp Statistik-Tool')
    
    parser.add_argument('-c', '--config', 
                       help='Pfad zur Konfigurationsdatei (Standard: configuration.ini)', 
                       default='configuration.ini')
    
    parser.add_argument('--force', action='store_true',
                       help='Erzwingt die Ausführung, ignoriert Hash-Prüfung')
    
    parser.add_argument('--no-stats', action='store_true',
                       help='Statistikanalyse überspringen')
    
    parser.add_argument('--no-vis', action='store_true',
                       help='Visualisierung überspringen')
    
    parser.add_argument('--no-rec', action='store_true',
                       help='Empfehlungsgenerierung überspringen')
    
    parser.add_argument('--no-discord', action='store_true',
                       help='Discord-Updates überspringen')
    
    parser.add_argument('--no-update', action='store_true',
                       help='Metadaten-Updates überspringen')
    
    parser.add_argument('--output-dir',
                       help='Ausgabeverzeichnis (überschreibt Konfiguration)')
    
    return parser.parse_args()

def generate_metadata_summary(stats_module: StatisticsModule, performer_rec_module: Optional[PerformerRecommendationModule], scene_rec_module: Optional[SceneRecommendationModule], output_dir: str, logger: logging.Logger) -> None:
    """
    Generiert eine Zusammenfassung der Metadaten und speichert sie im Ausgabeverzeichnis.
    
    Args:
        stats_module: Statistikmodul
        performer_rec_module: Performer-Empfehlungsmodul (oder None)
        scene_rec_module: Szenen-Empfehlungsmodul (oder None)
        output_dir: Ausgabeverzeichnis
        logger: Logger-Instanz
    """
    try:
        # Statistikzusammenfassung erstellen
        stats_summary = {
            "total_performers": len(stats_module.performers),
            "total_scenes": len(stats_module.scenes),
            "favorited_performers": len([p for p in stats_module.performers if p.favorite]),
            "rated_performers": len([p for p in stats_module.performers if p.rating100 is not None]),
            "rated_scenes": len([s for s in stats_module.scenes if s.rating100 is not None]),
            "total_o_counter": sum(p.o_counter for p in stats_module.performers),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Empfehlungszusammenfassung, falls verfügbar
        recommendation_summary = {}
        if performer_rec_module:
            recommendation_summary["performer_recommendations"] = {
                "total_categories": len(performer_rec_module.recommendation_categories),
                "total_recommendations": sum(len(recs) for recs in performer_rec_module.recommendation_categories.values()),
                "top_recommendations": len(performer_rec_module.top_recommendations)
            }
        
        if scene_rec_module:
            recommendation_summary["scene_recommendations"] = {
                "total_categories": len(scene_rec_module.recommendation_categories),
                "total_recommendations": sum(len(recs) for recs in scene_rec_module.recommendation_categories.values()),
                "top_recommendations": len(scene_rec_module.top_recommendations)
            }
        
        # Gesamtzusammenfassung
        summary = {
            "statistics": stats_summary,
            "recommendations": recommendation_summary,
            "generated_at": datetime.datetime.now().isoformat()
        }
        
        # Als JSON speichern
        summary_file = os.path.join(output_dir, "metadata_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metadaten-Zusammenfassung gespeichert: {summary_file}")
    except Exception as e:
        logger.error(f"Fehler beim Generieren der Metadaten-Zusammenfassung: {e}")

def main():
    """
    Hauptfunktion.
    """
    start_time = time.time()
    
    # Kommandozeilenargumente parsen
    args = parse_arguments()
    
    try:
        # Konfiguration laden
        config = ConfigManager(args.config)
        
        # Logging einrichten
        logger = setup_logging(config)
        
        # Programmstart loggen
        logger.info("StashApp Statistik-Tool gestartet")
        logger.info(f"Konfiguration geladen aus: {args.config}")
        
        # Ausgabeverzeichnis überschreiben, falls angegeben
        if args.output_dir:
            config.set('Output', 'output_dir', args.output_dir)
            logger.info(f"Ausgabeverzeichnis überschrieben: {args.output_dir}")
        
        # Ausgabeverzeichnisse erstellen
        create_output_directories(config)
        
        # StashAPI-Client initialisieren
        stash_url = config.get('StashApp', 'url')
        api_key = config.get('StashApp', 'api_key')
        ssl_verify = config.getboolean('StashApp', 'ssl_verify', fallback=False)
        
        try:
            api = StashAPI(stash_url, api_key, ssl_verify)
            logger.info(f"Verbindung zu StashApp hergestellt: {stash_url}")
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zu StashApp: {e}")
            return 1
        
        # Prüfen, ob die Daten verarbeitet werden sollten
        if args.force or should_process_data(api, config, logger):
            # Statistikmodule initialisieren
            stats_module = None
            performer_rec_module = None
            scene_rec_module = None
            
            output_dir = config.get('Output', 'output_dir')
            
            # Ausführungsoptionen aus Argumenten oder Konfiguration
            run_stats = not args.no_stats
            run_vis = not args.no_vis
            run_rec = not args.no_rec
            run_discord = not args.no_discord and config.getboolean('Discord', 'enable_discord', fallback=False)
            run_update = not args.no_update
            
            # Statistikanalyse durchführen
            if run_stats:
                logger.info("Starte Statistikanalyse...")
                stats_module = StatisticsModule(api, config)
                stats_module.calculate_all_statistics()
                stats_module.save_statistics()
                logger.info("Statistikanalyse abgeschlossen")
                
                # Visualisierungen erstellen
                if run_vis:
                    logger.info("Erstelle Visualisierungen...")
                    vis_module = VisualizationModule(api, stats_module, config)
                    vis_module.create_all_visualizations()
                    logger.info("Visualisierungen erstellt")
            else:
                logger.info("Statistikanalyse übersprungen")
            
            # Empfehlungen generieren
            if run_rec and stats_module:
                logger.info("Generiere Empfehlungen...")
                
                # Performer-Empfehlungen
                try:
                    performer_rec_module = PerformerRecommendationModule(api, stats_module, config)
                    performer_rec_module.generate_recommendations()
                    performer_rec_module.save_recommendations()
                    logger.info("Performer-Empfehlungen generiert")
                except Exception as e:
                    logger.error(f"Fehler bei der Generierung von Performer-Empfehlungen: {e}")
                
                # Szenen-Empfehlungen
                try:
                    scene_rec_module = SceneRecommendationModule(api, stats_module, config)
                    scene_rec_module.generate_recommendations()
                    scene_rec_module.save_recommendations()
                    logger.info("Szenen-Empfehlungen generiert")
                except Exception as e:
                    logger.error(f"Fehler bei der Generierung von Szenen-Empfehlungen: {e}")
            else:
                logger.info("Empfehlungsgenerierung übersprungen")
            
            # Metadaten-Update durchführen
            if run_update and stats_module:
                logger.info("Starte Metadaten-Update...")
                updater = UpdaterModule(api, stats_module, config)
                update_stats = updater.update_all()
                logger.info(f"Metadaten-Update abgeschlossen: {update_stats}")
            else:
                logger.info("Metadaten-Update übersprungen")
            
            # Discord-Updates senden
            if run_discord and stats_module:
                logger.info("Sende Discord-Updates...")
                discord_module = DiscordModule(api, stats_module, performer_rec_module, scene_rec_module, config)
                discord_module.send_all_updates()
                logger.info("Discord-Updates gesendet")
            else:
                logger.info("Discord-Updates übersprungen")
            
            # Metadaten-Zusammenfassung generieren
            generate_metadata_summary(stats_module, performer_rec_module, scene_rec_module, output_dir, logger)
            
            # Abschluss
            end_time = time.time()
            runtime = end_time - start_time
            logger.info(f"Programm erfolgreich beendet. Laufzeit: {runtime:.2f} Sekunden")
        else:
            logger.info("Keine Verarbeitung notwendig, da keine Änderungen festgestellt wurden.")
    
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        try:
            logger.error(f"Ein Fehler ist aufgetreten: {e}", exc_info=True)
        except:
            pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
