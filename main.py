#!/usr/bin/env python3
"""
StashApp Analytics - Hauptprogramm

Dieses Skript dient als Einstiegspunkt für das StashApp Analytics-Tool.
Es lädt die Konfiguration, initialisiert die Verbindung zur StashApp API
und bietet ein CLI-Interface zur Ausführung verschiedener Funktionen.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import time
import traceback

# Pfad zum übergeordneten Verzeichnis hinzufügen, um Importe zu ermöglichen
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import der Module
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
    print("Bitte stellen Sie sicher, dass alle Module installiert sind und die Verzeichnisstruktur korrekt ist.")
    print("Führen Sie 'pip install -r requirements.txt' aus, um alle Abhängigkeiten zu installieren.")
    sys.exit(1)

def setup_logging(config):
    """
    Konfiguriert das Logging-System basierend auf den Einstellungen in der Konfigurationsdatei.
    
    Args:
        config: ConfigManager-Instanz mit geladener Konfiguration
    """
    log_level_str = config.get('Logging', 'log_level', fallback='INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_format = config.get('Logging', 'log_format', 
                           fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_date_format = config.get('Logging', 'log_date_format', 
                                fallback='%Y-%m-%d %H:%M:%S')
    
    log_file = config.get('Logging', 'log_file', fallback='stashapp_analytics.log')
    
    # Logger konfigurieren
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=log_date_format,
        handlers=[
            logging.FileHandler(log_file) if log_file.lower() != 'console' else logging.StreamHandler()
        ]
    )
    
    # Root-Logger abrufen
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Konsolenausgabe hinzufügen, wenn eine Logdatei verwendet wird
    if log_file.lower() != 'console':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(log_format, log_date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    logging.info(f"Logging initialisiert mit Level: {log_level_str}")

def create_output_directories(config):
    """
    Erstellt die in der Konfiguration angegebenen Ausgabeverzeichnisse, falls sie nicht existieren.
    
    Args:
        config: ConfigManager-Instanz mit geladener Konfiguration
    """
    output_dir = config.get('Output', 'output_dir', fallback='./output')
    visualization_dir = config.get('Output', 'visualization_dir', fallback='./output/graphs')
    
    # Verzeichnisse erstellen
    for directory in [output_dir, visualization_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Verzeichnis erstellt: {directory}")

def run_statistics(api, config):
    """
    Führt die statistischen Analysen aus.
    
    Args:
        api: StashAPI-Instanz
        config: ConfigManager-Instanz
    
    Returns:
        StatisticsModule-Instanz mit berechneten Statistiken
    """
    logging.info("Starte statistische Analyse...")
    
    stats_module = StatisticsModule(api, config)
    stats_module.calculate_all_statistics()
    stats_module.save_statistics()
    
    logging.info("Statistische Analyse abgeschlossen")
    return stats_module

def run_visualizations(api, stats_module, config):
    """
    Erstellt Visualisierungen basierend auf den berechneten Statistiken.
    
    Args:
        api: StashAPI-Instanz
        stats_module: StatisticsModule-Instanz mit berechneten Statistiken
        config: ConfigManager-Instanz
    """
    logging.info("Erstelle Visualisierungen...")
    
    vis_module = VisualizationModule(api, stats_module, config)
    vis_module.create_all_visualizations()
    
    logging.info("Visualisierungen erfolgreich erstellt")

def run_performer_recommendations(api, stats_module, config):
    """
    Generiert Performer-Empfehlungen.
    
    Args:
        api: StashAPI-Instanz
        stats_module: StatisticsModule-Instanz mit berechneten Statistiken
        config: ConfigManager-Instanz
    
    Returns:
        PerformerRecommendationModule-Instanz mit Empfehlungen
    """
    logging.info("Generiere Performer-Empfehlungen...")
    
    rec_module = PerformerRecommendationModule(api, stats_module, config)
    rec_module.generate_recommendations()
    rec_module.save_recommendations()
    
    logging.info("Performer-Empfehlungen erfolgreich generiert")
    return rec_module

def run_scene_recommendations(api, stats_module, performer_rec_module, config):
    """
    Generiert Szenen-Empfehlungen.
    
    Args:
        api: StashAPI-Instanz
        stats_module: StatisticsModule-Instanz mit berechneten Statistiken
        performer_rec_module: PerformerRecommendationModule-Instanz mit Empfehlungen
        config: ConfigManager-Instanz
    
    Returns:
        SceneRecommendationModule-Instanz mit Empfehlungen
    """
    logging.info("Generiere Szenen-Empfehlungen...")
    
    rec_module = SceneRecommendationModule(api, stats_module, performer_rec_module, config)
    rec_module.generate_recommendations()
    rec_module.save_recommendations()
    
    logging.info("Szenen-Empfehlungen erfolgreich generiert")
    return rec_module

def run_discord_updates(api, stats_module, performer_rec_module, scene_rec_module, config):
    """
    Sendet Updates an Discord.
    
    Args:
        api: StashAPI-Instanz
        stats_module: StatisticsModule-Instanz mit berechneten Statistiken
        performer_rec_module: PerformerRecommendationModule-Instanz mit Empfehlungen
        scene_rec_module: SceneRecommendationModule-Instanz mit Empfehlungen
        config: ConfigManager-Instanz
    """
    if not config.getboolean('Discord', 'enable_discord', fallback=False):
        logging.info("Discord-Integration ist deaktiviert")
        return
    
    logging.info("Sende Updates an Discord...")
    
    discord_module = DiscordModule(api, stats_module, performer_rec_module, scene_rec_module, config)
    discord_module.send_all_updates()
    
    logging.info("Discord-Updates erfolgreich gesendet")

def run_updater(api, stats_module, config):
    """
    Aktualisiert Performer-Metadaten basierend auf Berechnungen.
    
    Args:
        api: StashAPI-Instanz
        stats_module: StatisticsModule-Instanz mit berechneten Statistiken
        config: ConfigManager-Instanz
    """
    logging.info("Starte Updater-Modul...")
    
    updater = UpdaterModule(api, stats_module, config)
    updater.update_all()
    
    logging.info("Aktualisierungen erfolgreich abgeschlossen")

def parse_arguments():
    """
    Parst Kommandozeilenargumente.
    
    Returns:
        argparse.Namespace: Geparste Argumente
    """
    parser = argparse.ArgumentParser(description='StashApp Analytics Tool')
    
    parser.add_argument('-c', '--config', 
                       help='Pfad zur Konfigurationsdatei (Standard: configuration.ini)', 
                       default='configuration.ini')
    
    parser.add_argument('--stats', action='store_true',
                       help='Führe Statistikanalyse aus')
    
    parser.add_argument('--vis', action='store_true',
                       help='Erstelle Visualisierungen')
    
    parser.add_argument('--rec-performers', action='store_true',
                       help='Generiere Performer-Empfehlungen')
    
    parser.add_argument('--rec-scenes', action='store_true',
                       help='Generiere Szenen-Empfehlungen')
    
    parser.add_argument('--discord', action='store_true',
                       help='Sende Updates an Discord')
    
    parser.add_argument('--update', action='store_true',
                       help='Aktualisiere Performer-Metadaten')
    
    parser.add_argument('--all', action='store_true',
                       help='Führe alle Aktionen aus')
    
    return parser.parse_args()

def main():
    """
    Hauptfunktion des Programms.
    """
    start_time = time.time()
    
    # Kommandozeilenargumente parsen
    args = parse_arguments()
    
    try:
        # Konfiguration laden
        config = ConfigManager(args.config)
        
        # Logging einrichten
        setup_logging(config)
        
        # Ausgabeverzeichnisse erstellen
        create_output_directories(config)
        
        # Versionsinfo loggen
        logging.info(f"StashApp Analytics Tool gestartet")
        logging.info(f"Konfiguration geladen aus: {args.config}")
        
        # StashAPI-Client initialisieren
        stash_url = config.get('StashApp', 'url')
        api_key = config.get('StashApp', 'api_key')
        ssl_verify = config.getboolean('StashApp', 'ssl_verify', fallback=False)
        
        api = StashAPI(stash_url, api_key, ssl_verify)
        logging.info(f"Verbindung zu StashApp hergestellt: {stash_url}")
        
        # Bestimmen, welche Aktionen ausgeführt werden sollen
        run_all = args.all
        run_statistics_flag = args.stats or run_all
        run_visualizations_flag = args.vis or run_all
        run_performer_recommendations_flag = args.rec_performers or run_all
        run_scene_recommendations_flag = args.rec_scenes or run_all
        run_discord_updates_flag = args.discord or run_all
        run_updater_flag = args.update or run_all
        
        # Wenn keine spezifischen Aktionen angegeben wurden, Hilfe anzeigen
        if not any([run_statistics_flag, run_visualizations_flag, 
                  run_performer_recommendations_flag, run_scene_recommendations_flag,
                  run_discord_updates_flag, run_updater_flag]):
            print("Keine Aktion angegeben. Nutze --help für eine Liste der verfügbaren Aktionen.")
            return
        
        # Aktionen ausführen
        stats_module = None
        performer_rec_module = None
        scene_rec_module = None
        
        if run_statistics_flag:
            stats_module = run_statistics(api, config)
        
        if run_visualizations_flag:
            if not stats_module:
                stats_module = run_statistics(api, config)
            run_visualizations(api, stats_module, config)
        
        if run_performer_recommendations_flag:
            if not stats_module:
                stats_module = run_statistics(api, config)
            performer_rec_module = run_performer_recommendations(api, stats_module, config)
        
        if run_scene_recommendations_flag:
            if not stats_module:
                stats_module = run_statistics(api, config)
            if not performer_rec_module:
                performer_rec_module = run_performer_recommendations(api, stats_module, config)
            scene_rec_module = run_scene_recommendations(api, stats_module, performer_rec_module, config)
        
        if run_updater_flag:
            if not stats_module:
                stats_module = run_statistics(api, config)
            run_updater(api, stats_module, config)
        
        if run_discord_updates_flag:
            if not stats_module:
                stats_module = run_statistics(api, config)
            if not performer_rec_module:
                performer_rec_module = run_performer_recommendations(api, stats_module, config)
            if not scene_rec_module:
                scene_rec_module = run_scene_recommendations(api, stats_module, performer_rec_module, config)
            run_discord_updates(api, stats_module, performer_rec_module, scene_rec_module, config)
        
        # Laufzeit berechnen
        end_time = time.time()
        runtime = end_time - start_time
        logging.info(f"Programm erfolgreich beendet. Laufzeit: {runtime:.2f} Sekunden")
        
    except Exception as e:
        logging.error(f"Ein Fehler ist aufgetreten: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"Ein Fehler ist aufgetreten: {str(e)}")
        print("Weitere Details finden Sie in der Logdatei.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
