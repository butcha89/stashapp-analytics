# StashApp Analytics - Benutzeranleitung

Diese Anleitung erklärt die Verwendung des StashApp Analytics-Tools und beschreibt alle verfügbaren Funktionen und Optionen im Detail.

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Kommandozeilenoptionen](#kommandozeilenoptionen)  
3. [Statistikmodule](#statistikmodule)
4. [Performer-Empfehlungen](#performer-empfehlungen)
5. [Szenen-Empfehlungen](#szenen-empfehlungen)  
6. [Dashboard](#dashboard)
7. [Discord-Integration](#discord-integration)
8. [Metadaten-Aktualisierung](#metadaten-aktualisierung)
9. [Konfigurationsoptionen](#konfigurationsoptionen)
10. [Tipps und Tricks](#tipps-und-tricks)

## Überblick

StashApp Analytics bietet verschiedene Module zur Analyse, Empfehlung und Visualisierung deiner StashApp-Daten. Die Funktionalität ist in mehrere Komponenten aufgeteilt:

- **Statistik**: Analysiert Performer-Daten und erstellt detaillierte Statistiken
- **Visualisierung**: Erstellt Grafiken und Diagramme aus den Statistikdaten  
- **Empfehlungen**: Generiert Vorschläge für ähnliche Performer und interessante Szenen
- **Dashboard**: Bietet eine interaktive Weboberfläche zur Anzeige aller Informationen
- **Discord**: Sendet Updates und Empfehlungen an einen Discord-Kanal
- **Updater**: Aktualisiert Metadaten in StashApp basierend auf Berechnungen

## Kommandozeilenoptionen

Das Tool kann über die Kommandozeile mit verschiedenen Optionen gesteuert werden:

```bash
python main.py [Optionen]  
```

Verfügbare Optionen:

| Option | Beschreibung |
|--------|--------------|
| `-c, --config` | Pfad zur Konfigurationsdatei (Standard: configuration.ini) |
| `--stats` | Führe Statistikanalyse aus |
| `--vis` | Erstelle Visualisierungen |
| `--rec-performers` | Generiere Performer-Empfehlungen |  
| `--rec-scenes` | Generiere Szenen-Empfehlungen |
| `--dashboard` | Starte interaktives Dashboard |
| `--discord` | Sende Updates an Discord |
| `--update` | Aktualisiere Performer-Metadaten |
| `--all` | Führe alle oben genannten Aktionen aus |

**Beispiele:**

Nur Statistiken berechnen:
```bash
python main.py --stats
```

Statistiken berechnen und visualisieren:
```bash 
python main.py --stats --vis
```

Alles ausführen außer Metadaten-Updates:
```bash
python main.py --stats --vis --rec-performers --rec-scenes --dashboard --discord
```

Alternative Konfigurationsdatei verwenden:
```bash
python main.py --all -c meine_config.ini  
```

## Statistikmodule

Das Statistikmodul analysiert die Daten aus StashApp und generiert verschiedene Statistiken.

### Verfügbare Statistiken

#### Performer-Statistiken:
- Verteilung der Cup-Größen (Zählung, Prozentsatz, Diagramme)
- BMI-Verteilung und Kategorien  
- Altersverteilung
- Bewertungsverteilung
- O-Counter-Verteilung
- Durchschnittswerte für alle Maße 
- Korrelationen zwischen verschiedenen Attributen

#### Szenen-Statistiken: 
- Häufigste Tags in gut bewerteten Szenen
- Verteilung von Szenen nach Performer-Attributen
- Zeitliche Verteilung (wann wurden Szenen am häufigsten angesehen)

### Verwendung

Berechnung aller Statistiken:
```bash
python main.py --stats
```

Die Ergebnisse werden im konfigurierten Output-Verzeichnis als Text- und JSON-Dateien gespeichert.

## Performer-Empfehlungen

Das Performer-Empfehlungsmodul findet Performer, die aufgrund verschiedener Kriterien interessant sein könnten:

### Empfehlungskriterien  

- **Ähnliche Cup-Größe**: Performer mit ähnlichen Cup-Größen wie Favoriten
- **Ähnliche Körperproportionen**: Performer mit ähnlichen BMI/Cup-Größe und Größe/Cup-Größe Verhältnissen 
- **Tag-Ähnlichkeit**: Performer mit ähnlichen Tags wie Favoriten
- **Szenen-Typen**: Performer, die in ähnlichen Szenen-Kategorien auftreten
- **Altersspanne**: Performer im ähnlichen Altersbereich wie Favoriten  
- **Neuheit**: Kürzlich hinzugefügte Performer, die deinen Präferenzen entsprechen
- **Szenen-Qualität**: Performer mit hochbewerteten Szenen 
- **Vielseitigkeit**: Performer, die in verschiedenen Arten von Szenen auftreten
- **Performer mit niedrigem O-Counter**: Potentiell interessante Performer, die noch nicht oft angesehen wurden

### Einstellung der Gewichtungen

Die relative Wichtigkeit der verschiedenen Kriterien kann in der Konfigurationsdatei unter `[Recommendations]` angepasst werden:

```ini
[Recommendations]
weight_cup_size = 0.4
bmi_cup_size = 0.2
height_cup_size = 0.2 
weight_tag_similarity = 0.6
# ... weitere Einstellungen
```


### Verwendung

Generieren von Performer-Empfehlungen:
```bash
python main.py --rec-performers
```

Die Empfehlungen werden im Output-Verzeichnis gespeichert und können im Dashboard eingesehen oder per Discord geteilt werden.

## Szenen-Empfehlungen

Das Szenen-Empfehlungsmodul identifiziert Szenen, die aufgrund deiner Sehgewohnheiten interessant sein könnten:

### Empfehlungstypen

- **Ähnlich zu Favoriten**: Szenen, die Ähnlichkeiten mit deinen favorisierten Szenen aufweisen
- **O-Counter-basiert**: Szenen mit ähnlichen Tags wie deine meistgesehenen Szenen
- **Empfohlene Performer**: Szenen mit Performern aus den Performer-Empfehlungen
- **Unentdeckte Perlen**: Hochbewertete Szenen, die du noch nicht oft angesehen hast
- **Getrennte Listen**: Separate Empfehlungen für Szenen mit favorisierten und nicht-favorisierten Performern

### Verwendung

Generieren von Szenen-Empfehlungen:
```bash
python main.py --rec-scenes
```

## Dashboard

Das Dashboard-Modul bietet eine interaktive Weboberfläche zur Anzeige aller Statistiken und Empfehlungen.

### Funktionen

- **Performer-Statistiken**: Interaktive Diagramme und Tabellen
- **Szenen-Statistiken**: Analysen und Trends
- **Empfehlungen**: Performer- und Szenen-Empfehlungen mit Bildern und Details
- **Suchfunktion**: Suche nach Performern und Szenen
- **Filter**: Filterung nach verschiedenen Kriterien

### Verwendung

Starten des Dashboards:
```bash
python main.py --dashboard
```

Das Dashboard ist dann unter `http://localhost:8080` erreichbar (oder dem in der Konfiguration angegebenen Port).

### Dashboard-Layout

Das Dashboard ist in verschiedene Bereiche unterteilt:

1. **Übersicht**: Zusammenfassung der wichtigsten Statistiken
2. **Performer-Statistiken**: Detaillierte Performer-Analysen
3. **Szenen-Statistiken**: Detaillierte Szenen-Analysen
4. **Empfehlungen**: Personalisierte Empfehlungen
5. **Einstellungen**: Konfigurationsoptionen für das Dashboard

## Discord-Integration

Die Discord-Integration sendet Statistiken und Empfehlungen an einen konfigurierten Discord-Kanal.

### Funktionen

- **Regelmäßige Updates**: Automatische Benachrichtigungen nach Zeitplan
- **Statistik-Updates**: Zusammenfassung der aktuellen Statistiken
- **Performer-Empfehlungen**: Tägliche Empfehlungen mit Bildern
- **Szenen-Empfehlungen**: Tägliche Szenen-Vorschläge

### Konfiguration

Die Discord-Integration wird in der Konfigurationsdatei eingerichtet:

```ini
[Discord]
enable_discord = True
webhook_url = https://discord.com/api/webhooks/...
post_schedule = daily  # Optionen: hourly, daily, weekly
post_time = 09:00
max_recommendations_per_message = 3
```

### Verwendung

Manuelles Senden von Updates an Discord:
```bash
python main.py --discord
```

## Metadaten-Aktualisierung

Das Updater-Modul kann Metadaten in StashApp basierend auf den Berechnungen aktualisieren.

### Funktionen

- **BH-Größen-Tagging**: Hinzufügen standardisierter BH-Größen-Tags
- **BMI-Tagging**: Hinzufügen von BMI-Kategorie-Tags
- **Verhältnis-Tagging**: Hinzufügen von Tags für verschiedene Verhältnisse (Cup/BMI, Cup/Größe)

### Konfiguration

Die zu aktualisierenden Metadaten können in der Konfigurationsdatei festgelegt werden:

```ini
[Updater]
update_bra_sizes = True
update_bmi_categories = True
update_ratios = True
create_missing_tags = True
```

### Verwendung

Aktualisieren der Metadaten:
```bash
python main.py --update
```

⚠️ **Achtung**: Diese Funktion ändert Daten in deiner StashApp-Datenbank. Stelle sicher, dass du ein Backup hast, bevor du diese Funktion verwendest.

## Konfigurationsoptionen

Die vollständige Konfiguration wird in der `configuration.ini` vorgenommen. Hier sind die wichtigsten Abschnitte und Optionen:

### StashApp
```ini
[StashApp]
url = http://localhost:9999
api_key = dein_api_key
ssl_verify = False
```

### Output
```ini
[Output]
output_dir = ./output
visualization_dir = ./output/graphs
dashboard_port = 8080
```

### Recommendations
```ini
[Recommendations]
min_similarity_score = 0.75
max_recommendations = 10
include_zero_counter = True
weight_cup_size = 0.4
bmi_cup_size = 0.2
height_cup_size = 0.2
# ... weitere Einstellungen
```

### Visualization
```ini
[Visualization]
image_format = png
image_dpi = 300
color_scheme = viridis
figure_height = 6
figure_width = 10
```

### Discord
```ini
[Discord]
enable_discord = True
webhook_url = https://discord.com/api/webhooks/...
post_schedule = daily
post_time = 09:00
```

### Logging
```ini
[Logging]
log_level = INFO
log_file = stashapp_analytics.log
```

## Tipps und Tricks

### Optimale Ergebnisse

1. **Vollständige Daten**: Je vollständiger deine Performer-Daten in StashApp sind, desto besser werden die Statistiken und Empfehlungen.

2. **O-Counter verwenden**: Der O-Counter ist ein wichtiger Faktor für die Empfehlungen. Achte darauf, diesen regelmäßig zu aktualisieren.

3. **Tagging**: Ein konsistentes Tagging-System verbessert die Qualität der Empfehlungen erheblich.

4. **Bewertungen**: Nutze das Bewertungssystem in StashApp, um bessere Empfehlungen zu erhalten.

### Leistungsoptimierung

1. **Caching**: In der `[Advanced]`-Sektion kannst du Caching aktivieren, um wiederholte API-Anfragen zu reduzieren.

2. **Worker-Threads**: Passe die Anzahl der Worker an die Leistung deines Systems an.

3. **Zeitplanung**: Plane ressourcenintensive Operationen für Zeiten, zu denen dein System nicht stark belastet ist.

### Fehlerbehandlung

1. **Logdateien**: Überprüfe die Logdateien bei Problemen.

2. **Debug-Modus**: Aktiviere den Debug-Modus für detailliertere Ausgaben.

3. **API-Limitierungen**: Beachte mögliche Limitierungen der StashApp-API bei großen Datenmengen.

### Erweiterte Funktionen

1. **Custom Tags**: Du kannst in der Konfiguration eigene Tags definieren, die basierend auf berechneten Werten erstellt werden.

2. **Alternative Empfehlungsalgorithmen**: In der Konfiguration können verschiedene Algorithmen für Empfehlungen aktiviert werden.

3. **Exportfunktionen**: Die generierten Daten können in verschiedene Formate exportiert werden.

4. **Automatisierung**: Kombiniere das Tool mit Skripten zur vollständigen Automatisierung deines Workflows.
