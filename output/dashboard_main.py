"""
dashboard_main.py - Hauptmodul für das Dashboard der Stasapp-Datenbank

Dieses Modul dient als Einstiegspunkt für das Dashboard-System. Es integriert
verschiedene Untermodule für Datenanalyse, Visualisierung und Empfehlungen.

Verwendung:
    python dashboard_main.py [options]

Optionen:
    --data-source    Pfad zur Datenquelle oder Datenbankverbindungsstring
    --output-dir     Verzeichnis für generierte Berichte und Visualisierungen
    --config         Pfad zur Konfigurationsdatei
"""

import os
import sys
import argparse
import logging
import json
import datetime
from typing import Dict, List, Any

# Import der Untermodule
from dashboard_data_loader import DataLoader
from dashboard_visualizer import DashboardVisualizer
from dashboard_analyzer import UserBehaviorAnalyzer
from dashboard_recommender import ContentRecommender
from dashboard_reporter import ReportGenerator
from dashboard_utils import setup_logging, load_config

def parse_arguments():
    """Kommandozeilenargumente parsen"""
    parser = argparse.ArgumentParser(description="Stasapp Dashboard System")
    parser.add_argument("--data-source", 
                        help="Pfad zur Datenquelle oder Datenbankverbindungsstring",
                        default="sqlite:///stasapp.db")
    parser.add_argument("--output-dir",
                        help="Verzeichnis für Ausgaben und Berichte",
                        default="./dashboard_output")
    parser.add_argument("--config",
                        help="Pfad zur Konfigurationsdatei",
                        default="./dashboard_config.json")
    parser.add_argument("--log-level",
                        help="Loglevel (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                        default="INFO")
    return parser.parse_args()

def main():
    """Hauptfunktion des Dashboard-Systems"""
    # Argumente einlesen
    args = parse_arguments()
    
    # Logging einrichten
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    logger.info(f"Starte Stasapp Dashboard am {datetime.datetime.now()}")
    
    try:
        # Konfiguration laden
        config = load_config(args.config)
        logger.info("Konfiguration erfolgreich geladen")
        
        # Ausgabeverzeichnis erstellen, wenn es nicht existiert
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Daten laden
        logger.info(f"Lade Daten aus {args.data_source}")
        data_loader = DataLoader(args.data_source)
        user_data = data_loader.load_user_data()
        content_data = data_loader.load_content_data()
        viewing_history = data_loader.load_viewing_history()
        
        # Datenanalyse durchführen
        logger.info("Analysiere Nutzungsverhalten")
        analyzer = UserBehaviorAnalyzer(user_data, viewing_history)
        usage_patterns = analyzer.analyze_patterns()
        user_segments = analyzer.segment_users()
        
        # Visualisierungen erstellen
        logger.info("Erstelle Visualisierungen")
        visualizer = DashboardVisualizer(args.output_dir)
        visualizer.create_usage_charts(usage_patterns)
        visualizer.create_user_segment_charts(user_segments)
        visualizer.create_content_popularity_charts(content_data, viewing_history)
        
        # Empfehlungen generieren
        logger.info("Generiere Empfehlungsvorschläge")
        recommender = ContentRecommender(content_data, viewing_history, user_segments)
        recommendations = recommender.generate_recommendations()
        
        # Berichte erstellen
        logger.info("Erstelle Berichte")
        reporter = ReportGenerator(args.output_dir)
        reporter.generate_summary_report(
            usage_patterns, 
            user_segments,
            recommendations
        )
        
        logger.info(f"Dashboard-Ausführung abgeschlossen. Ausgaben in {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Fehler bei der Dashboard-Ausführung: {str(e)}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
