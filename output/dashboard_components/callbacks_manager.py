"""
Dashboard Callbacks Manager

Dieses Modul registriert die Callbacks für die interaktiven Elemente des Dashboards.
"""

import logging
from typing import Dict, List, Any

import dash
from dash import dcc, html, Input, Output, State

from output.dashboard_components.layout_manager import render_page_content
from output.dashboard_components.callbacks import performer_callbacks, scene_callbacks, settings_callbacks

# Logger konfigurieren
logger = logging.getLogger(__name__)

def register_callbacks(app: dash.Dash, module_data: Dict[str, Any]) -> None:
    """
    Registriert die Callbacks für die Dash-App.
    
    Args:
        app: Die Dash-App
        module_data: Daten der verschiedenen Module
    """
    logger.info("Registriere Dashboard-Callbacks")
    
    # Callback für die Navigation
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname")
    )
    def update_page(pathname):
        """Aktualisiert den Seiteninhalt basierend auf dem aktuellen Pfad."""
        return render_page_content(pathname, module_data)
    
    # Performer-bezogene Callbacks registrieren
    performer_callbacks.register_callbacks(app, module_data)
    
    # Szenen-bezogene Callbacks registrieren
    scene_callbacks.register_callbacks(app, module_data)
    
    # Einstellungs-bezogene Callbacks registrieren
    settings_callbacks.register_callbacks(app, module_data)
    
    # Zusätzliche globale Callbacks
    register_global_callbacks(app, module_data)

def register_global_callbacks(app: dash.Dash, module_data: Dict[str, Any]) -> None:
    """
    Registriert globale Callbacks für die Dash-App.
    
    Args:
        app: Die Dash-App
        module_data: Daten der verschiedenen Module
    """
    # Beispiel für einen globalen Callback: Aktualisieren der Anzeige bei Klick auf einen Button
    @app.callback(
        Output("refresh-status", "children"),
        Input("refresh-button", "n_clicks")
    )
    def refresh_data(n_clicks):
        """Aktualisiert die Daten bei Klick auf den Refresh-Button."""
        if not n_clicks:
            return ""
        
        try:
            # Daten aktualisieren
            stats_module = module_data['stats_module']
            stats_module.calculate_all_statistics()
            
            return html.Div("Daten erfolgreich aktualisiert!", className="text-success")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Daten: {str(e)}")
            return html.Div(f"Fehler: {str(e)}", className="text-danger")