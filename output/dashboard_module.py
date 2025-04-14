"""
Dashboard Module

Dieses Modul bietet ein interaktives Web-Dashboard zur Anzeige von Statistiken und
Empfehlungen aus der StashApp-Datenbank. Es dient als Hauptmodul, das andere
Dashboard-Komponenten integriert und koordiniert.
"""

import os
import logging
import threading
import webbrowser
import time
from typing import Dict, List, Any, Optional, Union

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

from core.stash_api import StashAPI
from analysis.statistics_module import StatisticsModule
from recommendations.recommendation_performer import PerformerRecommendationModule
from recommendations.recommendation_scenes import SceneRecommendationModule
from management.config_manager import ConfigManager

# Import der Dashboard-Untermodule
from output.dashboard_components.layout_manager import create_layout
from output.dashboard_components.callbacks_manager import register_callbacks
from output.dashboard_components.utils import ensure_directories, get_performer_image_url, get_scene_image_url

# Logger konfigurieren
logger = logging.getLogger(__name__)

class DashboardModule:
    """
    Klasse zur Bereitstellung eines interaktiven Web-Dashboards zur Anzeige von
    Statistiken und Empfehlungen aus StashApp.
    """
    
    def __init__(self, api: StashAPI, 
                 stats_module: StatisticsModule, 
                 performer_rec_module: Optional[PerformerRecommendationModule] = None, 
                 scene_rec_module: Optional[SceneRecommendationModule] = None, 
                 config: ConfigManager = None):
        """
        Initialisiert das Dashboard-Modul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
            performer_rec_module: Optional, PerformerRecommendationModule-Instanz mit Empfehlungen
            scene_rec_module: Optional, SceneRecommendationModule-Instanz mit Empfehlungen
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.stats_module = stats_module
        self.performer_rec_module = performer_rec_module
        self.scene_rec_module = scene_rec_module
        self.config = config
        
        # Lade Konfigurationsoptionen
        self.output_dir = self.config.get('Output', 'output_dir', fallback='./output')
        self.visualization_dir = self.config.get('Output', 'visualization_dir', fallback='./output/graphs')
        self.port = self.config.getint('Output', 'dashboard_port', fallback=8080)
        self.host = self.config.get('Output', 'dashboard_host', fallback='0.0.0.0')
        self.debug = self.config.getboolean('Output', 'dashboard_debug', fallback=False)
        self.open_browser = self.config.getboolean('Output', 'open_browser', fallback=True)
        
        # Erstelle Verzeichnisse, falls sie nicht existieren
        ensure_directories([self.output_dir, self.visualization_dir])
        
        # Initialisiere die Dash-App
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        # Setze den Seitentitel
        self.app.title = 'StashApp Analytics Dashboard'
        
        # Module-Daten für den Layout-Manager und Callback-Manager
        self.module_data = {
            'api': self.api,
            'stats_module': self.stats_module,
            'performer_rec_module': self.performer_rec_module,
            'scene_rec_module': self.scene_rec_module,
            'config': self.config,
            'output_dir': self.output_dir,
            'visualization_dir': self.visualization_dir
        }
        
        # Setze das Layout der App
        self.app.layout = create_layout(self.module_data)
        
        # Registriere Callbacks
        register_callbacks(self.app, self.module_data)
        
        logger.info("Dashboard-Modul initialisiert")
    
    def run(self):
        """Startet das Dashboard."""
        logger.info(f"Starte Dashboard auf http://{self.host}:{self.port}")
        
        # Öffne den Browser, falls konfiguriert
        if self.open_browser:
            # Starte den Browser in einem separaten Thread
            threading.Timer(
                1.5, 
                lambda: webbrowser.open(f"http://{'localhost' if self.host == '0.0.0.0' else self.host}:{self.port}")
            ).start()
        
        # Starte den Dash-Server
        self.app.run_server(
            host=self.host,
            port=self.port,
            debug=self.debug
        )
