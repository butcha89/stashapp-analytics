# StashApp Analytics

Ein modulares System zur Datenanalyse und Empfehlung für [StashApp](https://github.com/stashapp/stash), das umfangreiche Statistiken, personalisierte Empfehlungen und Visualisierungen bietet.

## Funktionen

- **Statistikanalyse**: Detaillierte Analyse von Performer-Daten und Cup-Größen-Verteilungen
- **Visuelle Darstellungen**: Grafische Darstellung von statistischen Daten in verschiedenen Diagrammtypen
- **Performer-Empfehlungen**: Intelligente Vorschläge basierend auf Ähnlichkeiten zu Favoriten
- **Szenen-Empfehlungen**: Szenenvorschläge basierend auf Tags und O-Counter-Statistiken
- **Dashboard**: Interaktives Web-Dashboard zur Anzeige aller Daten und Empfehlungen 
- **Discord-Integration**: Automatischer Versand von Updates und Empfehlungen an Discord
- **Metadaten-Aktualisierung**: Automatisches Tagging basierend auf berechneten Werten

## Modulare Struktur

Das Projekt ist in mehrere Module aufgeteilt, um die Wartbarkeit und Erweiterbarkeit zu verbessern:

### Core-Module:
- **stash_api.py**: API-Kommunikation mit StashApp
- **data_models.py**: Datenmodelle für Performer und Szenen
- **utils.py**: Allgemeine Hilfsfunktionen

### Analyse-Module:
- **statistics_module.py**: Statistische Berechnungen
- **visualization_module.py**: Erstellung von Diagrammen und Grafiken

### Empfehlungs-Module:
- **recommendation_performer.py**: Algorithmen für Performer-Empfehlungen
- **recommendation_scenes.py**: Algorithmen für Szenen-Empfehlungen

### Ausgabe-Module:
- **dashboard_module.py**: Interaktives Web-Dashboard
- **discord_module.py**: Discord-Integration 

### Verwaltungs-Module:
- **updater_module.py**: Aktualisierung von Metadaten in StashApp
- **config_manager.py**: Verwaltung der Konfigurationsoptionen

## Installation

1. **Repository klonen**
   ```bash
   git clone https://github.com/dein-benutzername/stashapp-analytics.git
   cd stashapp-analytics
   ```

2. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfiguration einrichten**
   ```bash
   cp configuration.ini.example configuration.ini
   # Öffne configuration.ini und passe die Einstellungen an
   ```

## Verwendung

### Alle Funktionen ausführen
```bash
python main.py --all
```

### Nur bestimmte Funktionen ausführen
```bash
# Nur Statistiken berechnen 
python main.py --stats

# Statistiken berechnen und visualisieren
python main.py --stats --vis

# Dashboard starten
python main.py --dashboard

# Empfehlungen generieren
python main.py --rec-performers --rec-scenes

# Discord-Updates senden  
python main.py --discord
```

## Konfiguration

Die Konfiguration erfolgt über die `configuration.ini` Datei. Hier sind die wichtigsten Einstellungen:

### StashApp-Verbindung
```ini 
[StashApp]
url = http://localhost:9999  
api_key = DEIN_API_KEY
ssl_verify = False
```

### Empfehlungseinstellungen
```ini
[Recommendations] 
min_similarity_score = 0.75
max_recommendations = 10 
include_zero_counter = True
weight_cup_size = 0.4
bmi_cup_size = 0.2 
height_cup_size = 0.2
```

### Discord-Integration
```ini
[Discord]
enable_discord = True  
webhook_url = https://discord.com/api/webhooks/...
post_schedule = daily
```

### Logging & Erweitert
```ini
[Logging]
log_level = INFO
log_file = stashapp_analytics.log

[Advanced]  
workers = 4
connection_timeout = 30
cache_ttl = 3600
```

Vollständige Konfigurationsoptionen findest du in der `configuration.ini.example` Datei.

## Dashboard

Das Dashboard bietet eine interaktive Oberfläche zur Anzeige aller Statistiken und Empfehlungen.

1. **Starten des Dashboards** 
   ```bash
   python main.py --dashboard
   ```

2. **Zugriff auf das Dashboard**  
   Öffne in deinem Browser: http://localhost:8080 (oder die in der Konfiguration festgelegte URL)

Das Dashboard enthält: 
- Übersicht mit wichtigen Kennzahlen
- Detaillierte Performer-Statistiken mit Diagrammen
- Szenen-Statistiken und O-Counter-Analysen  
- Empfehlungen für Performer und Szenen

## Automatisierung

Du kannst regelmäßige Analysen und Updates einrichten:

### Cron-Job (Linux/macOS)
```bash
# Tägliche Analyse und Discord-Updates um 3 Uhr morgens
0 3 * * * cd /pfad/zu/stashapp-analytics && /pfad/zu/python main.py --all > /pfad/zu/log.txt 2>&1
```

### Task Scheduler (Windows) 
Erstelle eine geplante Aufgabe, die regelmäßig `python main.py --all` ausführt.

## Dokumentation

Ausführliche Dokumentation findest du in den folgenden Dateien:
- [docs/SETUP.md](docs/SETUP.md): Detaillierte Installationsanleitung  
- [docs/USAGE.md](docs/USAGE.md): Ausführliche Bedienungsanleitung

## Mitwirken

Beiträge sind willkommen! Hier sind einige Möglichkeiten, wie du helfen kannst:
- Fehler melden
- Neue Funktionen vorschlagen
- Pull Requests einreichen

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz veröffentlicht - siehe die [LICENSE](LICENSE) Datei für Details.
