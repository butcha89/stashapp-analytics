"""
Performer Callbacks

Dieses Modul enthält Callbacks für die Performer-bezogenen Komponenten des Dashboards.
"""

import logging
from typing import Dict, List, Any

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

# Logger konfigurieren
logger = logging.getLogger(__name__)

def register_callbacks(app: dash.Dash, module_data: Dict[str, Any]) -> None:
    """
    Registriert Callbacks für Performer-bezogene Komponenten.
    
    Args:
        app: Die Dash-App
        module_data: Daten der verschiedenen Module
    """
    # Callback für Performer-Filter auf der Statistikseite
    @app.callback(
        Output("performer-table-container", "children"),
        [Input("cup-filter", "value"),
         Input("bmi-filter", "value"),
         Input("age-filter", "value")]
    )
    def update_performer_table(cup_sizes, bmi_categories, age_groups):
        """
        Aktualisiert die Performer-Tabelle basierend auf den Filtereinstellungen.
        
        Args:
            cup_sizes: Ausgewählte Cup-Größen
            bmi_categories: Ausgewählte BMI-Kategorien
            age_groups: Ausgewählte Altersgruppen
            
        Returns:
            html.Div: Die aktualisierte Tabelle
        """
        try:
            # Extrahiere die benötigten Module aus den Daten
            stats_module = module_data['stats_module']
            
            # Hole alle Performer
            performers = stats_module.performers
            
            # Filtere basierend auf den Einstellungen
            filtered_performers = performers
            
            if cup_sizes:
                filtered_performers = [p for p in filtered_performers if p.cup_size in cup_sizes]
                
            if bmi_categories:
                filtered_performers = [p for p in filtered_performers if p.bmi_category in bmi_categories]
                
            if age_groups:
                # Altersgruppen-Bereiche bestimmen
                age_ranges = {
                    "18-25": (18, 25),
                    "26-30": (26, 30),
                    "31-35": (31, 35),
                    "36-40": (36, 40),
                    "41-45": (41, 45),
                    "46+": (46, 100)
                }
                
                # Performer filtern, die in eine der ausgewählten Altersgruppen fallen
                filtered_performers = [
                    p for p in filtered_performers 
                    if any(
                        p.age is not None and 
                        low <= p.age <= high 
                        for group in age_groups 
                        for low, high in [age_ranges.get(group, (0, 100))]
                    )
                ]
            
            # Wenn keine Performer übrig bleiben
            if not filtered_performers:
                return html.Div("Keine Performer mit diesen Filterkriterien gefunden.")
            
            # Erstelle eine Tabelle mit den gefilterten Performern
            table_data = []
            for p in filtered_performers[:100]:  # Begrenze auf 100 für Performance
                table_data.append({
                    "Name": p.name,
                    "Cup-Größe": p.cup_size or "N/A",
                    "BH-Größe": p.german_bra_size or "N/A",
                    "BMI": f"{p.bmi:.1f}" if p.bmi else "N/A",
                    "Alter": str(p.age) if p.age else "N/A",
                    "Rating": f"{p.rating_5:.1f}/5" if p.rating_5 else "N/A",
                    "O-Counter": str(p.o_counter)
                })
            
            # Erstelle ein DataFrame für die Tabelle
            df = pd.DataFrame(table_data)
            
            # Erstelle die Tabelle
            table = dbc.Table.from_dataframe(
                df, 
                striped=True, 
                bordered=True, 
                hover=True,
                responsive=True,
                className="mt-3"
            )
            
            return html.Div([
                html.P(f"Gefunden: {len(filtered_performers)} Performer" + 
                       (f" (zeige die ersten 100)" if len(filtered_performers) > 100 else "")),
                table
            ])
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Performer-Tabelle: {str(e)}")
            return html.Div(f"Fehler: {str(e)}")
    
    # Callback für Performer-Empfehlungen nach Typ
    @app.callback(
        Output("performer-recommendations-container", "children"),
        [Input("performer-rec-filter", "value"),
         Input("performer-rec-count", "value")]
    )
    def update_performer_recommendations(filter_type, count):
        """
        Aktualisiert die Performer-Empfehlungen basierend auf den Filtereinstellungen.
        
        Args:
            filter_type: Art der Empfehlung
            count: Anzahl der anzuzeigenden Empfehlungen
            
        Returns:
            html.Div: Die aktualisierten Empfehlungen
        """
        try:
            # Extrahiere die benötigten Module aus den Daten
            performer_rec_module = module_data.get('performer_rec_module')
            
            if not performer_rec_module:
                return html.Div("Keine Empfehlungen verfügbar. Führe zuerst das Empfehlungsmodul aus.")
            
            # Hole die Empfehlungen nach Typ
            recommendations = []
            if hasattr(performer_rec_module, 'get_recommendations_by_type'):
                recommendations = performer_rec_module.get_recommendations_by_type(filter_type, count)
            else:
                # Fallback zu allgemeinen Empfehlungen
                recommendations = performer_rec_module.get_top_recommendations(count)
            
            # Erstelle die Empfehlungskarten
            from output.dashboard_components.pages.recommendations_page import create_performer_recommendation_cards
            return create_performer_recommendation_cards(recommendations, module_data)
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Performer-Empfehlungen: {str(e)}")
            return html.Div(f"Fehler: {str(e)}")