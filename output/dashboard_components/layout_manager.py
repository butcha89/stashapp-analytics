"""
Dashboard Layout Manager

Dieses Modul ist verantwortlich für die Erstellung des Layouts
des Dashboards und seiner verschiedenen Seiten.
"""

import os
import logging
from typing import Dict, List, Any, Optional

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

from output.dashboard_components.pages import overview_page, performer_stats_page, scene_stats_page, recommendations_page, settings_page

# Logger konfigurieren
logger = logging.getLogger(__name__)

def create_layout(module_data: Dict[str, Any]) -> html.Div:
    """
    Erstellt das Hauptlayout des Dashboards.
    
    Args:
        module_data: Daten der verschiedenen Module
        
    Returns:
        html.Div: Das Hauptlayout der Dash-App
    """
    logger.info("Erstelle Dashboard-Layout")
    
    # Erstelle die Navigationsleiste
    navbar = create_navbar()
    
    # Erstelle den Container für den Inhaltsbereich
    content = dbc.Container(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-content"),
        ],
        fluid=True,
        className="mt-4",
    )
    
    # Setze das Layout der App
    return html.Div([navbar, content])

def create_navbar() -> dbc.Navbar:
    """
    Erstellt die Navigationsleiste des Dashboards.
    
    Returns:
        dbc.Navbar: Die Navigationsleiste der Dash-App
    """
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("StashApp Analytics", className="ms-2"),
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Übersicht", href="#overview", id="nav-overview")),
                        dbc.NavItem(dbc.NavLink("Performer-Statistiken", href="#performer-stats", id="nav-performer-stats")),
                        dbc.NavItem(dbc.NavLink("Szenen-Statistiken", href="#scene-stats", id="nav-scene-stats")),
                        dbc.NavItem(dbc.NavLink("Empfehlungen", href="#recommendations", id="nav-recommendations")),
                        dbc.NavItem(dbc.NavLink("Einstellungen", href="#settings", id="nav-settings")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
            ]
        ),
        color="primary",
        dark=True,
        className="mb-4",
    )

def render_page_content(pathname: str, module_data: Dict[str, Any]) -> html.Div:
    """
    Rendert den Inhalt basierend auf dem aktuellen Pfad.
    
    Args:
        pathname: Der aktuelle Pfad
        module_data: Daten der verschiedenen Module
        
    Returns:
        html.Div: Der gerenderte Seiteninhalt
    """
    try:
        # Extrahiere die benötigten Module aus den Daten
        api = module_data['api']
        stats_module = module_data['stats_module']
        performer_rec_module = module_data.get('performer_rec_module')
        scene_rec_module = module_data.get('scene_rec_module')
        config = module_data['config']
        
        # Standardmäßig die Übersichtsseite anzeigen
        if pathname is None or pathname == "/" or "#overview" in pathname:
            return overview_page.create_page(module_data)
        elif "#performer-stats" in pathname:
            return performer_stats_page.create_page(module_data)
        elif "#scene-stats" in pathname:
            return scene_stats_page.create_page(module_data)
        elif "#recommendations" in pathname:
            return recommendations_page.create_page(module_data)
        elif "#settings" in pathname:
            return settings_page.create_page(module_data)
            
        # Bei unbekanntem Pfad zur Übersichtsseite umleiten
        return overview_page.create_page(module_data)
        
    except Exception as e:
        logger.error(f"Fehler beim Rendern der Seite: {str(e)}")
        return html.Div([
            html.H1("Fehler beim Laden der Seite"),
            html.P(f"Details: {str(e)}")
        ])