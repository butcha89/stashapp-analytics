"""
Scene Callbacks

Dieses Modul enthält Callbacks für die Szenen-bezogenen Komponenten des Dashboards.
"""

import logging
from typing import Dict, List, Any

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Logger konfigurieren
logger = logging.getLogger(__name__)

def register_callbacks(app: dash.Dash, module_data: Dict[str, Any]) -> None:
    """
    Registriert Callbacks für Szenen-bezogene Komponenten.
    
    Args:
        app: Die Dash-App
        module_data: Daten der verschiedenen Module
    """
    # Callback für Szenen-Empfehlungen nach Typ
    @app.callback(
        Output("scene-recommendations-container", "children"),
        [Input("scene-rec-filter", "value"),
         Input("scene-rec-count", "value")]
    )
    def update_scene_recommendations(filter_type, count):
        """
        Aktualisiert die Szenen-Empfehlungen basierend auf den Filtereinstellungen.
        
        Args:
            filter_type: Art der Empfehlung
            count: Anzahl der anzuzeigenden Empfehlungen
            
        Returns:
            html.Div: Die aktualisierten Empfehlungen
        """
        try:
            # Extrahiere die benötigten Module aus den Daten
            scene_rec_module = module_data.get('scene_rec_module')
            
            if not scene_rec_module:
                return html.Div("Keine Empfehlungen verfügbar. Führe zuerst das Empfehlungsmodul aus.")
            
            # Hole die Empfehlungen nach Typ
            recommendations = []
            if hasattr(scene_rec_module, 'get_recommendations_by_type'):
                recommendations = scene_rec_module.get_recommendations_by_type(filter_type, count)
            else:
                # Fallback zu allgemeinen Empfehlungen
                recommendations = scene_rec_module.get_top_recommendations(count)
            
            # Erstelle die Empfehlungskarten
            from output.dashboard_components.pages.recommendations_page import create_scene_recommendation_cards
            return create_scene_recommendation_cards(recommendations, module_data)
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Szenen-Empfehlungen: {str(e)}")
            return html.Div(f"Fehler: {str(e)}")
    
    # Callback für Tag-Filter
    @app.callback(
        Output("scene-tag-filter-result", "children"),
        [Input("scene-tag-filter", "value"),
         Input("scene-tag-min-count", "value")]
    )
    def update_scene_tag_filter(tags, min_count):
        """
        Filtert Szenen nach Tags und Mindesthäufigkeit.
        
        Args:
            tags: Ausgewählte Tags
            min_count: Mindesthäufigkeit für Szenen
            
        Returns:
            html.Div: Die gefilterten Szenen
        """
        try:
            # Extrahiere die benötigten Module aus den Daten
            stats_module = module_data['stats_module']
            
            # Wenn keine Tags ausgewählt wurden
            if not tags:
                return html.Div("Bitte wähle mindestens einen Tag aus.")
            
            # Hole alle Szenen
            scenes = stats_module.scenes
            
            # Filtere Szenen, die alle ausgewählten Tags enthalten
            filtered_scenes = [
                s for s in scenes 
                if all(tag in s.tags for tag in tags) and s.o_counter >= min_count
            ]
            
            # Wenn keine Szenen übrig bleiben
            if not filtered_scenes:
                return html.Div("Keine Szenen mit diesen Tags und Mindesthäufigkeit gefunden.")
            
            # Sortiere nach O-Counter
            filtered_scenes.sort(key=lambda s: s.o_counter, reverse=True)
            
            # Erstelle Karten für die gefilterten Szenen (max. 20)
            scene_cards = []
            for scene in filtered_scenes[:20]:
                # Performer-Namen für die Anzeige vorbereiten
                performer_text = ", ".join(scene.performer_names[:3])
                if len(scene.performer_names) > 3:
                    performer_text += f" und {len(scene.performer_names) - 3} weitere"
                
                card = dbc.Card(
                    dbc.CardBody([
                        html.H5(scene.title or "Unbenannte Szene", className="card-title"),
                        html.Div([
                            html.Span("Performer: ", className="font-weight-bold"),
                            html.Span(performer_text)
                        ], className="card-text"),
                        html.Div([
                            html.Span("O-Counter: ", className="font-weight-bold"),
                            html.Span(str(scene.o_counter))
                        ], className="card-text"),
                        html.Div([
                            html.Span("Rating: ", className="font-weight-bold"),
                            html.Span(f"{scene.rating_5:.1f}/5 ⭐" if scene.rating_5 else "N/A")
                        ], className="card-text")
                    ]),
                    className="mb-3"
                )
                scene_cards.append(card)
            
            return html.Div([
                html.P(f"Gefunden: {len(filtered_scenes)} Szenen" + 
                      (f" (zeige die ersten 20)" if len(filtered_scenes) > 20 else "")),
                *scene_cards
            ])
            
        except Exception as e:
            logger.error(f"Fehler beim Filtern der Szenen nach Tags: {str(e)}")
            return html.Div(f"Fehler: {str(e)}")