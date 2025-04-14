# StashApp Analytics - Setup-Anleitung

Diese Anleitung führt dich durch die Installation und Konfiguration des StashApp Analytics-Tools.

## Voraussetzungen

- Python 3.8 oder höher
- Zugang zu einer StashApp-Instanz mit API-Schlüssel
- Grundlegende Kenntnisse in der Verwendung der Kommandozeile

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/dein-benutzername/stashapp-analytics.git
cd stashapp-analytics
```

### 2. Virtuelle Umgebung erstellen (optional, aber empfohlen)

#### Unter Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### Unter macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

## Konfiguration

### 1. Konfigurationsdatei erstellen

Kopiere die Beispielkonfiguration und passe sie an deine Bedürfnisse an:

```bash
cp configuration.ini.example configuration.ini
```

### 2. Konfiguration anpassen

Öffne die Datei `configuration.ini` in einem Texteditor und passe die folgenden Einstellungen an:

1. **StashApp-Verbindung**:
   ```ini
   [StashApp]
   url = http://deine-stashapp-url:9999
   api_key = dein-api-key
   ssl_verify = False
   ```
   
   Den API-Schlüssel findest du in deiner StashApp-Installation unter:
   Settings → Security → Authentication → API Key

2. **Ausgabe-Verzeichnisse**:
   ```ini
   [Output]
   output_dir = ./output
   visualization_dir = ./output/graphs
   ```

3. **Discord-Integration (optional)**:
   ```ini
   [Discord]
   enable_discord = True
   webhook_url = https://discord.com/api/webhooks/deine-webhook-url
   ```
   
   Um einen Discord-Webhook zu erstellen:
   - Server-Einstellungen → Integrationen → Webhooks → Neuer Webhook
   - Namen und Zielkanal festlegen, dann URL kopieren und in der Konfiguration einfügen

4. **Weitere Einstellungen**:
   Alle anderen Einstellungen können zunächst auf den Standardwerten belassen und später nach Bedarf angepasst werden.

## Erste Schritte

### Grundlegende Statistiken erstellen

Um grundlegende Statistiken zu berechnen und zu visualisieren:

```bash
python main.py --stats --vis
```

### Dashboard starten

Um das interaktive Dashboard zu starten:

```bash
python main.py --dashboard
```

Das Dashboard ist dann unter http://localhost:8080 erreichbar (sofern in der Konfiguration nicht anders angegeben).

### Empfehlungen generieren

Um Performer- und Szenen-Empfehlungen zu generieren:

```bash
python main.py --rec-performers --rec-scenes
```

### Updates an Discord senden

Um Statistiken und Empfehlungen an Discord zu senden:

```bash
python main.py --discord
```

### Alle Funktionen ausführen

Um alle verfügbaren Funktionen auszuführen:

```bash
python main.py --all
```

## Geplante Ausführung

Du kannst das Tool auch automatisiert ausführen lassen, zum Beispiel mit einem Cron-Job oder einer geplanten Aufgabe in Windows.

### Beispiel Cron-Job (Linux/macOS)

Um das Tool täglich um 3 Uhr morgens auszuführen:

```bash
0 3 * * * cd /pfad/zu/stashapp-analytics && /pfad/zu/python main.py --all > /pfad/zu/stashapp-analytics/logs/cron.log 2>&1
```

### Geplante Aufgabe in Windows

1. Öffne die Aufgabenplanung
2. Erstelle eine neue Aufgabe
3. Setze als Aktion: Start eines Programms
4. Programm/Skript: `C:\Pfad\zu\Python\python.exe`
5. Argumente: `C:\Pfad\zu\stashapp-analytics\main.py --all`
6. Startordner: `C:\Pfad\zu\stashapp-analytics`

## Fehlerbehebung

### Verbindungsprobleme zur StashApp

- Überprüfe, ob die StashApp-URL und der API-Schlüssel korrekt sind
- Stelle sicher, dass StashApp läuft und von dem System aus erreichbar ist, auf dem das Analyse-Tool ausgeführt wird
- Bei SSL-Problemen setze `ssl_verify = False` in der Konfiguration

### Fehler bei der Installation der Abhängigkeiten

Falls Probleme bei der Installation der Abhängigkeiten auftreten, versuche folgendes:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Bei speziellen Problemen mit einzelnen Paketen, installiere diese separat:

```bash
pip install numpy pandas matplotlib
pip install dash flask
pip install requests discord-webhook
```

### Logdateien prüfen

Bei Problemen überprüfe die Logdatei, die standardmäßig unter `stashapp_analytics.log` gespeichert wird. Du kannst den Pfad und das Log-Level in der Konfigurationsdatei unter `[Logging]` anpassen.

## Weiterführende Konfiguration

Für erweiterte Einstellungen und benutzerdefinierte Anpassungen, konsultiere die vollständige Dokumentation in [USAGE.md](USAGE.md).
