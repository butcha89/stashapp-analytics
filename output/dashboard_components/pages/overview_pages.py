"""
Dashboard Overview Page

Dieses Modul erstellt die Übersichtsseite des Dashboards.
"""

import logging
from typing import Dict, List, Any

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

from core.data_models import Performer
from output.dashboard_components.utils import get_performer_image_url, get_scene_image_url

# Logger konfigurieren
logger = logging.getLogger(__name__)

def create_page(module_data: Dict[str, Any]) -> html.Div:
    """
    Erstellt die Übersichtsseite des Dashboards.
    
    Args:
        module_data: Daten der verschiedenen Module
        
    Returns:
        html.Div: Die Übersichtsseite
    """
    try:
        # Extrahiere die benötigten Module aus den Daten
        api = module_data['api']
        stats_module = module_data['stats_module']
        performer_rec_module = module_data.get('performer_rec_module')
        scene_rec_module = module_data.get('scene_rec_module')
        
        # Lade zusammengefasste Statistiken
        stats = stats_module.get_summary_stats()
        
        # Erstelle die Übersichtsseite mit verschiedenen Komponenten
        return dbc.Container([
            # Header
            html.H1("Übersicht", className="mb-4"),
            
            # Aktualisierungsbutton
            dbc.Row([
                dbc.Col(
                    dbc.Button("Daten aktualisieren", id="refresh-button", color="primary", className="mb-3"),
                    width="auto"
                ),
                dbc.Col(
                    html.Div(id="refresh-status"),
                    width="auto"
                )
            ]),
            
            # Statistik-Karten
            create_stat_cards(stats),
            
            # Grafiken
            create_overview_graphs(stats),
            
            # Empfehlungsvorschau
            html.Hr(),
            html.H2("Letzte Empfehlungen", className="mb-3"),
            create_recommendation_preview(module_data)
        ])
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Übersichtsseite: {str(e)}")
        return html.Div([
            html.H1("Fehler beim Laden der Übersicht"),
            html.P(f"Details: {str(e)}")
        ])

def create_stat_cards(stats: Dict[str, Any]) -> dbc.Row:
    """
    Erstellt Karten für die wichtigsten Statistiken.
    
    Args:
        stats: Statistikdaten
        
    Returns:
        dbc.Row: Zeile mit Statistik-Karten
    """
    cards = []
    
    # Performer-Anzahl
    if "total_count" in stats:
        performer_card = dbc.Card(
            dbc.CardBody([
                html.H4("Performer", className="card-title"),
                html.H2(f"{stats['total_count']}", className="card-text text-center"),
                html.P("in der Datenbank", className="card-text text-muted")
            ]),
            className="mb-4 text-center border-primary"
        )
        cards.append(dbc.Col(performer_card, width=12, md=6, lg=3))
    
    # Durchschnittliche Cup-Größe
    if "avg_cup_size" in stats:
        avg_cup = stats.get("avg_cup_size", 0)
        avg_cup_letter = ""
        if avg_cup:
            avg_cup_letter = f" ({Performer.CUP_NUMERIC_TO_LETTER.get(round(avg_cup), '?')})"
        
        cup_card = dbc.Card(
            dbc.CardBody([
                html.H4("Ø Cup-Größe", className="card-title"),
                html.H2(f"{avg_cup:.2f}{avg_cup_letter}", className="card-text text-center"),
                html.P("aller Performer", className="card-text text-muted")
            ]),
            className="mb-4 text-center border-primary"
        )
        cards.append(dbc.Col(cup_card, width=12, md=6, lg=3))
    
    # Durchschnittlicher BMI
    if "avg_bmi" in stats:
        bmi_card = dbc.Card(
            dbc.CardBody([
                html.H4("Ø BMI", className="card-title"),
                html.H2(f"{stats.get('avg_bmi', 0):.1f}", className="card-text text-center"),
                html.P("aller Performer", className="card-text text-muted")
            ]),
            className="mb-4 text-center border-primary"
        )
        cards.append(dbc.Col(bmi_card, width=12, md=6, lg=3))
    
    # Durchschnittliches Rating
    if "avg_rating" in stats:
        rating_card = dbc.Card(
            dbc.CardBody([
                html.H4("Ø Rating", className="card-title"),
                html.H2(f"{stats.get('avg_rating', 0)/20:.1f}/5 ⭐", className="card-text text-center"),
                html.P("aller Performer", className="card-text text-muted")
            ]),
            className="mb-4 text-center border-primary"
        )
        cards.append(dbc.Col(rating_card, width=12, md=6, lg=3))
    
    return dbc.Row(cards)

def create_overview_graphs(stats: Dict[str, Any]) -> dbc.Row:
    """
    Erstellt Grafiken für die Übersichtsseite.
    
    Args:
        stats: Statistikdaten
        
    Returns:
        dbc.Row: Zeile mit Grafiken
    """
    graphs = []
    
    # Cup-Größen-Verteilung
    if "cup_distribution" in stats:
        cup_dist = stats["cup_distribution"]
        # Sortiere nach Cup-Größe
        sorted_cups = sorted(cup_dist.keys(), key=lambda x: Performer.CUP_NUMERIC.get(x, 0))
        
        cup_fig = px.bar(
            x=sorted_cups,
            y=[cup_dist[cup] for cup in sorted_cups],
            labels={"x": "Cup-Größe", "y": "Anzahl"},
            title="Verteilung der Cup-Größen"
        )
        cup_graph = dcc.Graph(figure=cup_fig)
        graphs.append(dbc.Col(cup_graph, width=12, lg=6, className="mb-4"))
    
    # BMI-Kategorien
    if "bmi_distribution" in stats:
        bmi_dist = stats["bmi_distribution"]
        # Sortiere nach BMI-Kategorie
        sorted_categories = ["Untergewicht", "Normalgewicht", "Übergewicht", "Adipositas"]
        sorted_bmi = []
        sorted_counts = []
        
        for cat in sorted_categories:
            if cat in bmi_dist:
                sorted_bmi.append(cat)
                sorted_counts.append(bmi_dist[cat])
        
        bmi_fig = px.pie(
            names=sorted_bmi,
            values=sorted_counts,
            title="Verteilung der BMI-Kategorien"
        )
        bmi_graph = dcc.Graph(figure=bmi_fig)
        graphs.append(dbc.Col(bmi_graph, width=12, lg=6, className="mb-4"))
    
    return dbc.Row(graphs)

def create_recommendation_preview(module_data: Dict[str, Any]) -> html.Div:
    """
    Erstellt eine Vorschau der letzten Empfehlungen.
    
    Args:
        module_data: Daten der verschiedenen Module
        
    Returns:
        html.Div: Die Empfehlungsvorschau
    """
    try:
        # Extrahiere die benötigten Module aus den Daten
        api = module_data['api']
        performer_rec_module = module_data.get('performer_rec_module')
        scene_rec_module = module_data.get('scene_rec_module')
        
        recommendations = []
        
        # Füge Performer-Empfehlungen hinzu, falls vorhanden
        if performer_rec_module:
            performer_recs = performer_rec_module.get_top_recommendations(3)
            if performer_recs:
                performer_cards = dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardImg(src=get_performer_image_url(p, api.url), top=True) 
                            if get_performer_image_url(p, api.url) else None,
                            dbc.CardBody([
                                html.H5(p.name, className="card-title"),
                                html.P(f"Cup: {p.cup_size}" if p.cup_size else "", className="card-text"),
                                html.P(f"Score: {score:.2f}", className="card-text text-muted"),
                            ])
                        ]),
                        width=12, md=4, className="mb-4"
                    ) for p, score in performer_recs
                ])
                
                recommendations.append(html.Div([
                    html.H3("Top Performer", className="mb-3"),
                    performer_cards
                ]))
        
        # Füge Szenen-Empfehlungen hinzu, falls vorhanden
        if scene_rec_module:
            scene_recs = scene_rec_module.get_top_recommendations(3)
            if scene_recs:
                scene_cards = dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardImg(src=get_scene_image_url(s, api.url), top=True) 
                            if get_scene_image_url(s, api.url) else None,
                            dbc.CardBody([
                                html.H5(s.title or "Unbenannte Szene", className="card-title"),
                                html.P(", ".join(s.performer_names[:2]) + (", ..." if len(s.performer_names) > 2 else ""), 
                                      className="card-text"),
                                html.P(f"Score: {score:.2f}", className="card-text text-muted"),
                            ])
                        ]),
                        width=12, md=4, className="mb-4"
                    ) for s, score in scene_recs
                ])
                
                recommendations.append(html.Div([
                    html.H3("Top Szenen", className="mb-3"),
                    scene_cards
                ]))
        
        if not recommendations:
            return html.P("Keine Empfehlungen verfügbar. Führe zuerst das Empfehlungsmodul aus.")
        
        return html.Div(recommendations)
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Empfehlungsvorschau: {str(e)}")
        return html.P(f"Fehler beim Laden der Empfehlungen: {str(e)}")