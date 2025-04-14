import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import json
import os

# Annahme: Die Statistikdateien befinden sich im './output/' Verzeichnis
OUTPUT_DIR = './output/'
PERFORMER_STATS_FILE = os.path.join(OUTPUT_DIR, 'performer_statistics.json')

def load_performer_stats():
    """Lädt die Performer-Statistiken aus der JSON-Datei."""
    try:
        with open(PERFORMER_STATS_FILE, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Fehler: Statistikdatei nicht gefunden: {PERFORMER_STATS_FILE}")
        return None
    except json.JSONDecodeError:
        print(f"Fehler: Fehler beim Decodieren der JSON-Datei: {PERFORMER_STATS_FILE}")
        return None

def create_layout():
    """Erstellt das Layout für die Performer-Statistikseite."""
    data = load_performer_stats()

    if data is None:
        return html.Div("Fehler beim Laden der Performer-Statistiken.")

    # Annahme: Die JSON-Datei enthält eine Liste von Performer-Objekten
    # mit verschiedenen Statistikfeldern (z.B. 'name', 'scene_count', 'average_rating').
    # Passe diese Felder entsprechend deiner tatsächlichen Daten an.

    # Beispielhafte Visualisierungen:

    # 1. Balkendiagramm der Top-Performer nach Szenenanzahl
    top_performers_scenes = sorted(data, key=lambda x: x.get('scene_count', 0), reverse=True)[:10]
    fig_scenes = px.bar(top_performers_scenes, x='name', y='scene_count',
                        title='Top 10 Performer nach Anzahl der Szenen')

    # 2. Streudiagramm: Durchschnittliche Bewertung vs. Szenenanzahl (falls Bewertung vorhanden)
    fig_rating_scenes = None
    if all('average_rating' in performer for performer in data):
        fig_rating_scenes = px.scatter(data, x='scene_count', y='average_rating', hover_name='name',
                                    title='Durchschnittliche Bewertung vs. Anzahl der Szenen')

    layout = html.Div([
        html.H1("Performer Statistiken"),
        html.Br(),

        html.Div([
            dcc.Graph(figure=fig_scenes) if fig_scenes else html.P("Keine Daten zur Szenenanzahl verfügbar."),
        ]),
        html.Br(),

        html.Div([
            dcc.Graph(figure=fig_rating_scenes) if fig_rating_scenes else html.P("Keine Daten zur durchschnittlichen Bewertung verfügbar."),
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
