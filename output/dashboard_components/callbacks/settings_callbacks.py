"""
Settings Callbacks

Dieses Modul enthält Callbacks für die Einstellungsseite des Dashboards.
"""

import logging
from typing import Dict, List, Any

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json

# Logger konfigurieren
logger = logging.getLogger(__name__)

def register_callbacks(app: dash.Dash, module_data: Dict[str, Any]) -> None:
    """
    Registriert Callbacks für die Einstellungsseite.
    
    Args:
        app: Die Dash-App
        module_data: Daten der verschiedenen Module
    """
    # Callback für den Verbindungstest zur StashApp-API
    @app.callback(
        Output("connection-test-result", "children"),
        Input("test-connection-btn", "n_clicks"),
        [State("stash-url", "value"),
         State("stash-api-key", "value"),
         State("stash-ssl-verify", "value")]
    )
    def test_connection(n_clicks, url, api_key, ssl_verify):
        """
        Testet die Verbindung zur StashApp-API.
        
        Args:
            n_clicks: Anzahl der Button-Klicks
            url: StashApp-URL
            api_key: API-Key
            ssl_verify: SSL-Überprüfung aktivieren
            
        Returns:
            html.Div: Das Testergebnis
        """
        if not n_clicks:
            return ""
        
        try:
            # Extrahiere die benötigten Module aus den Daten
            from core.stash_api import StashAPI
            
            # Erstelle temporäre API-Instanz
            temp_api = StashAPI(url, api_key, True if ssl_verify else False)
            
            # Teste Verbindung
            if temp_api.test_connection():
                return dbc.Alert("Verbindung erfolgreich hergestellt!", color="success")
            else:
                return dbc.Alert("Verbindung fehlgeschlagen. Bitte überprüfe die Einstellungen.", color="danger")
        except Exception as e:
            logger.error(f"Fehler beim Testen der Verbindung: {str(e)}")
            return dbc.Alert(f"Fehler: {str(e)}", color="danger")
    
    # Callback für den Discord-Test
    @app.callback(
        Output("discord-test-result", "children"),
        Input("test-discord-btn", "n_clicks"),
        [State("discord-webhook", "value"),
         State("enable-discord", "value")]
    )
    def test_discord(n_clicks, webhook_url, enable_discord):
        """
        Sendet eine Test-Nachricht an Discord.
        
        Args:
            n_clicks: Anzahl der Button-Klicks
            webhook_url: Discord-Webhook-URL
            enable_discord: Discord aktivieren
            
        Returns:
            html.Div: Das Testergebnis
        """
        if not n_clicks:
            return ""
        
        if not enable_discord:
            return dbc.Alert("Discord ist nicht aktiviert. Aktiviere es zuerst.", color="warning")
        
        if not webhook_url:
            return dbc.Alert("Keine Webhook-URL angegeben.", color="danger")
        
        try:
            # Sende Test-Nachricht
            data = {
                "content": "## StashApp Analytics Test\nDies ist eine Test-Nachricht vom Dashboard.",
                "username": "StashApp Analytics"
            }
            
            response = requests.post(
                webhook_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                return dbc.Alert("Test-Nachricht erfolgreich gesendet!", color="success")
            else:
                return dbc.Alert(f"Fehler beim Senden der Test-Nachricht. Status-Code: {response.status_code}", color="danger")
        except Exception as e:
            logger.error(f"Fehler beim Testen von Discord: {str(e)}")
            return dbc.Alert(f"Fehler: {str(e)}", color="danger")
    
    # Callback zum Speichern der Einstellungen
    @app.callback(
        Output("save-result", "children"),
        Input("save-settings-btn", "n_clicks"),
        [State("stash-url", "value"),
         State("stash-api-key", "value"),
         State("stash-ssl-verify", "value"),
         State("output-dir", "value"),
         State("visualization-dir", "value"),
         State("dashboard-port", "value"),
         State("min-similarity", "value"),
         State("max-recommendations", "value"),
         State("include-zero-counter", "value"),
         State("weight-cup-size", "value"),
         State("weight-bmi", "value"),
         State("weight-height", "value"),
         State("enable-discord", "value"),
         State("discord-webhook", "value"),
         State("discord-schedule", "value")]
    )
    def save_settings(n_clicks, stash_url, api_key, ssl_verify, output_dir, visualization_dir,
                      dashboard_port, min_similarity, max_recommendations, include_zero_counter,
                      weight_cup_size, weight_bmi, weight_height, enable_discord, discord_webhook,
                      discord_schedule):
        """
        Speichert die Einstellungen in der Konfigurationsdatei.
        
        Args:
            Verschiedene Einstellungen aus den Formularfeldern
            
        Returns:
            html.Div: Das Speicherergebnis
        """
        if not n_clicks:
            return ""
        
        try:
            # Extrahiere die benötigten Module aus den Daten
            config = module_data['config']
            
            # Aktualisiere die Konfiguration
            # StashApp-Einstellungen
            config.set('StashApp', 'url', stash_url)
            config.set('StashApp', 'api_key', api_key)
            config.set('StashApp', 'ssl_verify', str(bool(ssl_verify)))
            
            # Ausgabeeinstellungen
            config.set('Output', 'output_dir', output_dir)
            config.set('Output', 'visualization_dir', visualization_dir)
            config.set('Output', 'dashboard_port', str(dashboard_port))
            
            # Empfehlungseinstellungen
            config.set('Recommendations', 'min_similarity_score', str(min_similarity))
            config.set('Recommendations', 'max_recommendations', str(max_recommendations))
            config.set('Recommendations', 'include_zero_counter', str(bool(include_zero_counter)))
            config.set('Recommendations', 'weight_cup_size', str(weight_cup_size))
            config.set('Recommendations', 'bmi_cup_size', str(weight_bmi))
            config.set('Recommendations', 'height_cup_size', str(weight_height))
            
            # Discord-Einstellungen
            config.set('Discord', 'enable_discord', str(bool(enable_discord)))
            config.set('Discord', 'webhook_url', discord_webhook)
            config.set('Discord', 'post_schedule', discord_schedule)
            
            # Speichere die Konfiguration
            config.save()
            
            logger.info("Konfiguration erfolgreich gespeichert")
            return dbc.Alert("Einstellungen erfolgreich gespeichert! Starte das Dashboard neu, um alle Änderungen zu übernehmen.", color="success")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            return dbc.Alert(f"Fehler beim Speichern: {str(e)}", color="danger")