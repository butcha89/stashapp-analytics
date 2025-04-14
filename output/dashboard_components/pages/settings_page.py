"""
Dashboard Settings Page

Dieses Modul erstellt die Einstellungsseite des Dashboards.
"""

import logging
from typing import Dict, List, Any

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Logger konfigurieren
logger = logging.getLogger(__name__)

def create_page(module_data: Dict[str, Any]) -> html.Div:
    """
    Erstellt die Einstellungsseite des Dashboards.
    
    Args:
        module_data: Daten der verschiedenen Module
        
    Returns:
        html.Div: Die Einstellungsseite
    """
    try:
        # Extrahiere die benötigten Module aus den Daten
        config = module_data['config']
        
        # Lade aktuelle Konfiguration
        config_values = {}
        for section in config.get_all_sections():
            config_values[section] = config.get_section_dict(section)
        
        # Erstelle Formulare für die verschiedenen Konfigurationsabschnitte
        sections = []
        
        # StashApp-Einstellungen
        stash_section = html.Div([
            html.H2("StashApp-Verbindung", className="mb-3"),
            dbc.Form([
                dbc.FormGroup([
                    dbc.Label("URL:"),
                    dbc.Input(
                        id="stash-url",
                        type="text",
                        value=config_values.get("StashApp", {}).get("url", ""),
                        placeholder="http://localhost:9999"
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("API-Key:"),
                    dbc.Input(
                        id="stash-api-key",
                        type="password",
                        value=config_values.get("StashApp", {}).get("api_key", ""),
                        placeholder="Dein API-Key"
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("SSL-Überprüfung:"),
                    dbc.Checklist(
                        id="stash-ssl-verify",
                        options=[{"label": "SSL-Zertifikate überprüfen", "value": True}],
                        value=[True] if config_values.get("StashApp", {}).get("ssl_verify", "False").lower() == "true" else []
                    )
                ]),
                dbc.Button("Verbindung testen", id="test-connection-btn", color="primary")
            ]),
            html.Div(id="connection-test-result", className="mt-3")
        ])
        sections.append(stash_section)
        
        # Ausgabeeinstellungen
        output_section = html.Div([
            html.H2("Ausgabeeinstellungen", className="mb-3 mt-4"),
            dbc.Form([
                dbc.FormGroup([
                    dbc.Label("Ausgabeverzeichnis:"),
                    dbc.Input(
                        id="output-dir",
                        type="text",
                        value=config_values.get("Output", {}).get("output_dir", "./output")
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Visualisierungsverzeichnis:"),
                    dbc.Input(
                        id="visualization-dir",
                        type="text",
                        value=config_values.get("Output", {}).get("visualization_dir", "./output/graphs")
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Dashboard-Port:"),
                    dbc.Input(
                        id="dashboard-port",
                        type="number",
                        min=1000,
                        max=65535,
                        value=config_values.get("Output", {}).get("dashboard_port", 8080)
                    )
                ])
            ])
        ])
        sections.append(output_section)
        
        # Empfehlungseinstellungen
        rec_section = html.Div([
            html.H2("Empfehlungseinstellungen", className="mb-3 mt-4"),
            dbc.Form([
                dbc.FormGroup([
                    dbc.Label("Minimaler Ähnlichkeitswert:"),
                    dcc.Slider(
                        id="min-similarity",
                        min=0.1,
                        max=1.0,
                        step=0.05,
                        marks={i/10: str(i/10) for i in range(1, 11)},
                        value=float(config_values.get("Recommendations", {}).get("min_similarity_score", 0.75))
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Maximale Anzahl an Empfehlungen:"),
                    dbc.Input(
                        id="max-recommendations",
                        type="number",
                        min=1,
                        max=100,
                        value=config_values.get("Recommendations", {}).get("max_recommendations", 10)
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Auch Performer mit O-Counter = 0 empfehlen:"),
                    dbc.Checklist(
                        id="include-zero-counter",
                        options=[{"label": "Einschließen", "value": True}],
                        value=[True] if config_values.get("Recommendations", {}).get("include_zero_counter", "True").lower() == "true" else []
                    )
                ]),
                html.H5("Gewichtungen:", className="mt-3"),
                dbc.Row([
                    dbc.Col(
                        dbc.FormGroup([
                            dbc.Label("Cup-Größe:"),
                            dcc.Slider(
                                id="weight-cup-size",
                                min=0.0,
                                max=1.0,
                                step=0.1,
                                marks={i/10: str(i/10) for i in range(0, 11)},
                                value=float(config_values.get("Recommendations", {}).get("weight_cup_size", 0.4))
                            )
                        ]),
                        width=12, md=4
                    ),
                    dbc.Col(
                        dbc.FormGroup([
                            dbc.Label("BMI:"),
                            dcc.Slider(
                                id="weight-bmi",
                                min=0.0,
                                max=1.0,
                                step=0.1,
                                marks={i/10: str(i/10) for i in range(0, 11)},
                                value=float(config_values.get("Recommendations", {}).get("bmi_cup_size", 0.2))
                            )
                        ]),
                        width=12, md=4
                    ),
                    dbc.Col(
                        dbc.FormGroup([
                            dbc.Label("Größe:"),
                            dcc.Slider(
                                id="weight-height",
                                min=0.0,
                                max=1.0,
                                step=0.1,
                                marks={i/10: str(i/10) for i in range(0, 11)},
                                value=float(config_values.get("Recommendations", {}).get("height_cup_size", 0.2))
                            )
                        ]),
                        width=12, md=4
                    )
                ])
            ])
        ])
        sections.append(rec_section)
        
        # Discord-Einstellungen
        discord_section = html.Div([
            html.H2("Discord-Integration", className="mb-3 mt-4"),
            dbc.Form([
                dbc.FormGroup([
                    dbc.Label("Discord aktivieren:"),
                    dbc.Checklist(
                        id="enable-discord",
                        options=[{"label": "Aktivieren", "value": True}],
                        value=[True] if config_values.get("Discord", {}).get("enable_discord", "False").lower() == "true" else []
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Webhook URL:"),
                    dbc.Input(
                        id="discord-webhook",
                        type="text",
                        value=config_values.get("Discord", {}).get("webhook_url", ""),
                        placeholder="https://discord.com/api/webhooks/..."
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Post-Zeitplan:"),
                    dbc.Select(
                        id="discord-schedule",
                        options=[
                            {"label": "Täglich", "value": "daily"},
                            {"label": "Wöchentlich", "value": "weekly"},
                            {"label": "Monatlich", "value": "monthly"}
                        ],
                        value=config_values.get("Discord", {}).get("post_schedule", "daily")
                    )
                ]),
                dbc.Button("Discord-Test senden", id="test-discord-btn", color="primary")
            ]),
            html.Div(id="discord-test-result", className="mt-3")
        ])
        sections.append(discord_section)
        
        # Speichern-Button
        save_section = html.Div([
            html.Hr(),
            dbc.Button("Einstellungen speichern", id="save-settings-btn", color="success", size="lg", className="mt-3"),
            html.Div(id="save-result", className="mt-3")
        ])
        sections.append(save_section)
        
        return dbc.Container([
            html.H1("Einstellungen", className="mb-4"),
            *sections
        ])
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Einstellungsseite: {str(e)}")
        return html.Div([
            html.H1("Fehler beim Laden der Einstellungen"),
            html.P(f"Details: {str(e)}")
        ])