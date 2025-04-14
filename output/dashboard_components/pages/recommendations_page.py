import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import json
import os

# Annahme: Die Empfehlungsdateien befinden sich im './output/' Verzeichnis
OUTPUT_DIR = './output/'
PERFORMER_REC_FILE = os.path.join(OUTPUT_DIR, 'performer_recommendations.json')
SCENE_REC_FILE = os.path.join(OUTPUT_DIR, 'scene_recommendations.json')

def load_recommendations(filepath):
    """Lädt Empfehlungen aus der JSON-Datei."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Fehler: Empfehlungsdatei nicht gefunden: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Fehler: Fehler beim Decodieren der JSON-Datei: {filepath}")
        return None

def create_layout():
    """Erstellt das Layout für die Empfehlungsseite."""
    performer_recs = load_recommendations(PERFORMER_REC_FILE)
    scene_recs = load_recommendations(SCENE_REC_FILE)

    layout = html.Div([
        html.H1("Empfehlungen"),
        html.Br(),

        html.H2("Performer Empfehlungen"),
        html.Br(), # Hier war im vorherigen Code kein html.Br()
        if performer_recs:
            html.Ul([html.Li(rec) for rec in performer_recs]), # Annahme: performer_recs ist eine Liste von Strings
        else:
            html.P("Keine Performer-Empfehlungen verfügbar."),
        html.Br(),

        html.H2("Szenen Empfehlungen"),
        html.Br(), # Hier war im vorherigen Code kein html.Br()
        if scene_recs:
            html.Ul([html.Li(rec) for rec in scene_recs]), # Annahme: scene_recs ist eine Liste von Strings
        else:
            html.P("Keine Szenen-Empfehlungen verfügbar."),
        html.Br(),

        # Hier könnten weitere Details oder Visualisierungen hinzugefügt werden
    ])

    return layout

# Dies ist notwendig, damit Dash die Layout-Funktion erkennt
layout = create_layout()

if __name__ == '__main__':
    # Zum Testen der Layout-Generierung (optional)
    app = dash.Dash(__name__)
    app.layout = layout
    app.run_server(debug=True)
