import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import json
import os

# Annahme: Die Statistikdateien befinden sich im './output/' Verzeichnis
OUTPUT_DIR = './output/'
SCENE_STATS_FILE = os.path.join(OUTPUT_DIR, 'scene_statistics.json')

def load_scene_stats():
    """Lädt die Szenen-Statistiken aus der JSON-Datei."""
    try:
        with open(SCENE_STATS_FILE, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Fehler: Statistikdatei nicht gefunden: {SCENE_STATS_FILE}")
        return None
    except json.JSONDecodeError:
        print(f"Fehler: Fehler beim Decodieren der JSON-Datei: {SCENE_STATS_FILE}")
        return None

def create_layout():
    """Erstellt das Layout für die Szenen-Statistikseite."""
    data = load_scene_stats()

    if data is None:
        return html.Div("Fehler beim Laden der Szenen-Statistiken.")

    # Annahme: Die JSON-Datei enthält eine Liste von Szenen-Objekten
    # mit verschiedenen Statistikfeldern (z.B. 'id', 'duration', 'rating', 'performer_count').
    # Passe diese Felder entsprechend deiner tatsächlichen Daten an.

    # Beispielhafte Visualisierungen:

    # 1. Histogramm der Szenendauer
    fig_duration = px.histogram(data, x='duration', nbins=50, title='Verteilung der Szenendauer (in Sekunden)')

    # 2. Balkendiagramm der Anzahl der Szenen pro Bewertung (falls Bewertung vorhanden)
    fig_rating_count = None
    if all('rating' in scene for scene in data):
        rating_counts = {}
        for scene in data:
            rating = scene.get('rating')
            if rating is not None:
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
        ratings = list(rating_counts.keys())
        counts = list(rating_counts.values())
        fig_rating_count = px.bar(x=ratings, y=counts, title='Anzahl der Szenen pro Bewertung')

    layout = html.Div([
        html.H1("Szenen Statistiken"),
        html.Br(),

        html.Div([
            dcc.Graph(figure=fig_duration) if fig_duration else html.P("Keine Daten zur Szenendauer verfügbar."),
        ]),
        html.Br(),

        html.Div([
            dcc.Graph(figure=fig_rating_count) if fig_rating_count else html.P("Keine Daten zur Szenenbewertung verfügbar."),
        ]),
        html.Br(),

        # Hier könnten weitere Visualisierungen und Informationen hinzugefügt werden
    ])

    return layout

# Dies ist notwendig, damit Dash die Layout-Funktion erkennt
layout = create_layout()

if __name__ == '__main__':
    # Zum Testen der Layout-Generierung (optional)
    app = dash.Dash(__name__)
    app.layout = layout
    app.run_server(debug=True)
