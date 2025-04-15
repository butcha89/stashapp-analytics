"""
Export Module

Dieses Modul exportiert Statistiken und Empfehlungen aus dem StashApp-Analysesystem
in verschiedene Ausgabeformate wie JSON, CSV und HTML.
"""

import os
import json
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
import datetime
import pandas as pd

# Interne Importe
from core.utils import ensure_dir
from analysis.statistics_module import StatisticsModule
from recommendations.recommendation_performer import PerformerRecommendationModule
from recommendations.recommendation_scenes import SceneRecommendationModule

# Logger konfigurieren
logger = logging.getLogger(__name__)

class ExportModule:
    """
    Klasse zum Exportieren von Statistiken und Empfehlungen in verschiedene Formate.
    """
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialisiert das Export-Modul.
        
        Args:
            output_dir: Verzeichnis für die Ausgabedateien
        """
        self.output_dir = output_dir
        self.exports_dir = os.path.join(output_dir, "exports")
        
        # Erstelle Ausgabeverzeichnisse, falls sie nicht existieren
        ensure_dir(self.exports_dir)
        
        logger.info(f"Export-Modul initialisiert. Ausgabeverzeichnis: {self.exports_dir}")
    
    def export_statistics_to_json(self, statistics: Dict[str, Any], filename: str = "statistics_export.json") -> str:
        """
        Exportiert Statistiken als JSON-Datei.
        
        Args:
            statistics: Dictionary mit den zu exportierenden Statistiken
            filename: Name der Ausgabedatei
            
        Returns:
            str: Pfad zur erstellten Datei
        """
        output_path = os.path.join(self.exports_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Statistiken erfolgreich als JSON exportiert: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Fehler beim Export der Statistiken als JSON: {str(e)}")
            return ""
    
    def export_statistics_to_csv(self, statistics: Dict[str, Any], base_filename: str = "statistics_export") -> List[str]:
        """
        Exportiert Statistiken als CSV-Dateien (mehrere Dateien für verschiedene Statistiktypen).
        
        Args:
            statistics: Dictionary mit den zu exportierenden Statistiken
            base_filename: Basis-Name für die Ausgabedateien
            
        Returns:
            List[str]: Liste der erstellten Dateipfade
        """
        created_files = []
        
        try:
            # Extrahiere relevante Statistiken für CSV-Export
            stats_to_export = {}
            
            # Performer-Statistiken
            if "performers" in statistics:
                perf_stats = statistics["performers"]
                
                # Cup-Größen-Verteilung
                if "cup_distribution" in perf_stats:
                    stats_to_export["cup_sizes"] = [
                        {"cup_size": cup, "count": count}
                        for cup, count in perf_stats["cup_distribution"].items()
                    ]
                
                # BMI-Verteilung
                if "bmi_distribution" in perf_stats:
                    stats_to_export["bmi_categories"] = [
                        {"bmi_category": cat, "count": count}
                        for cat, count in perf_stats["bmi_distribution"].items()
                    ]
                
                # Altersverteilung
                if "age_distribution" in perf_stats:
                    stats_to_export["age_groups"] = [
                        {"age_group": group, "count": count}
                        for group, count in perf_stats["age_distribution"].items()
                    ]
                
                # Rating-Verteilung
                if "rating_distribution" in perf_stats:
                    stats_to_export["rating_distribution"] = [
                        {"stars": stars, "count": count}
                        for stars, count in perf_stats["rating_distribution"].items()
                    ]
            
            # Szenen-Statistiken
            if "scenes" in statistics:
                scene_stats = statistics["scenes"]
                
                # Studio-Verteilung
                if "studio_distribution" in scene_stats:
                    stats_to_export["studios"] = [
                        {"studio": studio, "count": count}
                        for studio, count in scene_stats["studio_distribution"].items()
                    ]
                
                # Datumsverteilung
                if "date_distribution" in scene_stats:
                    stats_to_export["dates"] = [
                        {"year": year, "count": count}
                        for year, count in scene_stats["date_distribution"].items()
                    ]
            
            # Speichern der CSV-Dateien
            for stat_type, data in stats_to_export.items():
                if not data:
                    continue
                
                filename = f"{base_filename}_{stat_type}.csv"
                output_path = os.path.join(self.exports_dir, filename)
                
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                
                created_files.append(output_path)
                logger.info(f"Statistik '{stat_type}' als CSV exportiert: {output_path}")
            
            return created_files
        except Exception as e:
            logger.error(f"Fehler beim Export der Statistiken als CSV: {str(e)}")
            return created_files
    
    def export_performer_recommendations_to_json(self, recommendations: Dict[str, List[Dict[str, Any]]], 
                                               filename: str = "performer_recommendations_export.json") -> str:
        """
        Exportiert Performer-Empfehlungen als JSON-Datei.
        
        Args:
            recommendations: Dictionary mit den zu exportierenden Empfehlungen
            filename: Name der Ausgabedatei
            
        Returns:
            str: Pfad zur erstellten Datei
        """
        output_path = os.path.join(self.exports_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Performer-Empfehlungen erfolgreich als JSON exportiert: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Fehler beim Export der Performer-Empfehlungen als JSON: {str(e)}")
            return ""
    
    def export_scene_recommendations_to_json(self, recommendations: Dict[str, List[Dict[str, Any]]], 
                                          filename: str = "scene_recommendations_export.json") -> str:
        """
        Exportiert Szenen-Empfehlungen als JSON-Datei.
        
        Args:
            recommendations: Dictionary mit den zu exportierenden Empfehlungen
            filename: Name der Ausgabedatei
            
        Returns:
            str: Pfad zur erstellten Datei
        """
        output_path = os.path.join(self.exports_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(recommendations, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Szenen-Empfehlungen erfolgreich als JSON exportiert: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Fehler beim Export der Szenen-Empfehlungen als JSON: {str(e)}")
            return ""
    
    def export_statistics_to_excel(self, statistics: Dict[str, Any], filename: str = "statistics_export.xlsx") -> str:
        """
        Exportiert Statistiken als Excel-Datei mit mehreren Arbeitsblättern.
        
        Args:
            statistics: Dictionary mit den zu exportierenden Statistiken
            filename: Name der Ausgabedatei
            
        Returns:
            str: Pfad zur erstellten Datei
        """
        output_path = os.path.join(self.exports_dir, filename)
        
        try:
            # Erstelle Excel-Writer
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Blatt mit allgemeinen Statistiken
                if "general" in statistics:
                    general_stats = statistics["general"]
                    general_df = pd.DataFrame(list(general_stats.items()), columns=["Metrik", "Wert"])
                    general_df.to_excel(writer, sheet_name="Allgemein", index=False)
                
                # Blatt mit Performer-Statistiken
                if "performers" in statistics:
                    perf_stats = statistics["performers"]
                    
                    # Durchschnittswerte
                    avg_data = {k: v for k, v in perf_stats.items() if k.startswith("avg_")}
                    if avg_data:
                        avg_df = pd.DataFrame(list(avg_data.items()), columns=["Metrik", "Wert"])
                        avg_df.to_excel(writer, sheet_name="Performer_Durchschnitt", index=False)
                    
                    # Cup-Größen-Verteilung
                    if "cup_distribution" in perf_stats:
                        cup_df = pd.DataFrame(list(perf_stats["cup_distribution"].items()), 
                                             columns=["Cup-Größe", "Anzahl"])
                        cup_df.to_excel(writer, sheet_name="Cup_Größen", index=False)
                    
                    # BMI-Verteilung
                    if "bmi_distribution" in perf_stats:
                        bmi_df = pd.DataFrame(list(perf_stats["bmi_distribution"].items()), 
                                             columns=["BMI-Kategorie", "Anzahl"])
                        bmi_df.to_excel(writer, sheet_name="BMI_Kategorien", index=False)
                    
                    # Altersverteilung
                    if "age_distribution" in perf_stats:
                        age_df = pd.DataFrame(list(perf_stats["age_distribution"].items()), 
                                             columns=["Altersgruppe", "Anzahl"])
                        age_df.to_excel(writer, sheet_name="Altersgruppen", index=False)
                
                # Blatt mit Szenen-Statistiken
                if "scenes" in statistics:
                    scene_stats = statistics["scenes"]
                    
                    # Studio-Verteilung
                    if "studio_distribution" in scene_stats:
                        studio_df = pd.DataFrame(list(scene_stats["studio_distribution"].items()), 
                                                columns=["Studio", "Anzahl"])
                        studio_df = studio_df.sort_values("Anzahl", ascending=False)
                        studio_df.to_excel(writer, sheet_name="Studios", index=False)
                    
                    # Dauer-Verteilung
                    if "duration_distribution" in scene_stats:
                        duration_df = pd.DataFrame(list(scene_stats["duration_distribution"].items()), 
                                                  columns=["Dauer", "Anzahl"])
                        duration_df.to_excel(writer, sheet_name="Dauer", index=False)
                    
                    # Datumsverteilung
                    if "date_distribution" in scene_stats:
                        date_df = pd.DataFrame(list(scene_stats["date_distribution"].items()), 
                                              columns=["Jahr", "Anzahl"])
                        date_df = date_df.sort_values("Jahr")
                        date_df.to_excel(writer, sheet_name="Jahre", index=False)
            
            logger.info(f"Statistiken erfolgreich als Excel exportiert: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Fehler beim Export der Statistiken als Excel: {str(e)}")
            return ""
    
    def export_all(self, stats_module: StatisticsModule, 
                  performer_rec_module: Optional[PerformerRecommendationModule] = None,
                  scene_rec_module: Optional[SceneRecommendationModule] = None) -> Dict[str, List[str]]:
        """
        Exportiert alle verfügbaren Daten in verschiedene Formate.
        
        Args:
            stats_module: Statistikmodul mit berechneten Statistiken
            performer_rec_module: Performer-Empfehlungsmodul (oder None)
            scene_rec_module: Szenen-Empfehlungsmodul (oder None)
            
        Returns:
            Dict[str, List[str]]: Dictionary mit Pfaden zu den erstellten Dateien nach Kategorie
        """
        exported_files = {
            "json": [],
            "csv": [],
            "excel": []
        }
        
        try:
            # Statistiken exportieren
            if hasattr(stats_module, 'get_all_statistics'):
                statistics = stats_module.get_all_statistics()
            else:
                # Fallback, falls get_all_statistics nicht vorhanden ist
                statistics = {
                    "general": stats_module._get_general_stats() if hasattr(stats_module, '_get_general_stats') else {},
                    "performers": stats_module.performer_stats.to_dict() if hasattr(stats_module, 'performer_stats') and stats_module.performer_stats else {},
                    "scenes": stats_module.scene_stats.to_dict() if hasattr(stats_module, 'scene_stats') and stats_module.scene_stats else {}
                }
            
            # Timestamp für Dateinamen generieren
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Statistiken als JSON exportieren
            json_file = self.export_statistics_to_json(statistics, f"statistics_{timestamp}.json")
            if json_file:
                exported_files["json"].append(json_file)
            
            # Statistiken als CSV exportieren
            csv_files = self.export_statistics_to_csv(statistics, f"statistics_{timestamp}")
            exported_files["csv"].extend(csv_files)
            
            # Statistiken als Excel exportieren
            excel_file = self.export_statistics_to_excel(statistics, f"statistics_{timestamp}.xlsx")
            if excel_file:
                exported_files["excel"].append(excel_file)
            
            # Performer-Empfehlungen exportieren
            if performer_rec_module and hasattr(performer_rec_module, 'get_recommendations'):
                performer_recs = performer_rec_module.get_recommendations()
                json_file = self.export_performer_recommendations_to_json(
                    performer_recs, f"performer_recommendations_{timestamp}.json"
                )
                if json_file:
                    exported_files["json"].append(json_file)
            
            # Szenen-Empfehlungen exportieren
            if scene_rec_module and hasattr(scene_rec_module, 'get_recommendations'):
                scene_recs = scene_rec_module.get_recommendations()
                json_file = self.export_scene_recommendations_to_json(
                    scene_recs, f"scene_recommendations_{timestamp}.json"
                )
                if json_file:
                    exported_files["json"].append(json_file)
            
            logger.info(f"Export abgeschlossen. Exportierte Dateien: {sum(len(files) for files in exported_files.values())}")
            return exported_files
        except Exception as e:
            logger.error(f"Fehler beim Export aller Daten: {str(e)}")
            return exported_files
    
    def generate_simple_html_report(self, statistics: Dict[str, Any], filename: str = "statistics_report.html") -> str:
        """
        Generiert einen einfachen HTML-Bericht aus den Statistikdaten.
        
        Args:
            statistics: Dictionary mit den zu exportierenden Statistiken
            filename: Name der Ausgabedatei
            
        Returns:
            str: Pfad zur erstellten Datei
        """
        output_path = os.path.join(self.exports_dir, filename)
        
        try:
            # HTML-Template erstellen
            html_content = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StashApp Analytics Bericht</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
        h1, h2, h3 { color: #2c3e50; }
        .container { max-width: 1200px; margin: 0 auto; }
        .section { margin-bottom: 30px; background: #f9f9f9; padding: 20px; border-radius: 5px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; margin-top: 15px; }
        .stat-card { background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stat-title { font-weight: bold; margin-bottom: 5px; color: #3498db; }
        .stat-value { font-size: 18px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>StashApp Analytics Bericht</h1>
        <p>Generiert am: {}</p>
""".format(datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))
            
            # Allgemeine Statistiken
            if "general" in statistics:
                general_stats = statistics["general"]
                html_content += """
        <div class="section">
            <h2>Allgemeine Statistiken</h2>
            <div class="stats-grid">
"""
                for key, value in general_stats.items():
                    # Formatiere Werte
                    display_key = key.replace("_", " ").title()
                    display_value = value
                    if isinstance(value, float):
                        display_value = f"{value:.2f}"
                    
                    html_content += f"""
                <div class="stat-card">
                    <div class="stat-title">{display_key}</div>
                    <div class="stat-value">{display_value}</div>
                </div>
"""
                html_content += """
            </div>
        </div>
"""
            
            # Performer-Statistiken
            if "performers" in statistics:
                perf_stats = statistics["performers"]
                html_content += """
        <div class="section">
            <h2>Performer-Statistiken</h2>
"""
                # Durchschnittswerte
                avg_data = {k: v for k, v in perf_stats.items() if k.startswith("avg_")}
                if avg_data:
                    html_content += """
            <h3>Durchschnittswerte</h3>
            <div class="stats-grid">
"""
                    for key, value in avg_data.items():
                        display_key = key.replace("avg_", "").replace("_", " ").title()
                        display_value = value
                        if isinstance(value, float):
                            display_value = f"{value:.2f}"
                        
                        html_content += f"""
                <div class="stat-card">
                    <div class="stat-title">{display_key}</div>
                    <div class="stat-value">{display_value}</div>
                </div>
"""
                    html_content += """
            </div>
"""
                
                # Cup-Größen-Verteilung
                if "cup_distribution" in perf_stats and perf_stats["cup_distribution"]:
                    html_content += """
            <h3>Cup-Größen-Verteilung</h3>
            <table>
                <tr>
                    <th>Cup-Größe</th>
                    <th>Anzahl</th>
                </tr>
"""
                    for cup, count in sorted(perf_stats["cup_distribution"].items()):
                        html_content += f"""
                <tr>
                    <td>{cup}</td>
                    <td>{count}</td>
                </tr>
"""
                    html_content += """
            </table>
"""
                
                # BMI-Verteilung
                if "bmi_distribution" in perf_stats and perf_stats["bmi_distribution"]:
                    html_content += """
            <h3>BMI-Kategorien</h3>
            <table>
                <tr>
                    <th>Kategorie</th>
                    <th>Anzahl</th>
                </tr>
"""
                    # Ordne BMI-Kategorien
                    bmi_order = {"Untergewicht": 1, "Normalgewicht": 2, "Übergewicht": 3, "Adipositas": 4}
                    sorted_bmi = sorted(perf_stats["bmi_distribution"].items(), 
                                        key=lambda x: bmi_order.get(x[0], 999))
                    
                    for category, count in sorted_bmi:
                        html_content += f"""
                <tr>
                    <td>{category}</td>
                    <td>{count}</td>
                </tr>
"""
                    html_content += """
            </table>
"""
                
                html_content += """
        </div>
"""
            
            # Szenen-Statistiken
            if "scenes" in statistics:
                scene_stats = statistics["scenes"]
                html_content += """
        <div class="section">
            <h2>Szenen-Statistiken</h2>
"""
                # Top Studios
                if "studio_distribution" in scene_stats and scene_stats["studio_distribution"]:
                    html_content += """
            <h3>Top Studios</h3>
            <table>
                <tr>
                    <th>Studio</th>
                    <th>Anzahl</th>
                </tr>
"""
                    # Sortiere nach Anzahl
                    sorted_studios = sorted(scene_stats["studio_distribution"].items(), 
                                           key=lambda x: x[1], reverse=True)[:10]
                    
                    for studio, count in sorted_studios:
                        html_content += f"""
                <tr>
                    <td>{studio}</td>
                    <td>{count}</td>
                </tr>
"""
                    html_content += """
            </table>
"""
                
                # Zeitliche Verteilung
                if "date_distribution" in scene_stats and scene_stats["date_distribution"]:
                    html_content += """
            <h3>Szenen nach Jahr</h3>
            <table>
                <tr>
                    <th>Jahr</th>
                    <th>Anzahl</th>
                </tr>
"""
                    # Sortiere nach Jahr
                    sorted_years = sorted(scene_stats["date_distribution"].items())
                    
                    for year, count in sorted_years:
                        html_content += f"""
                <tr>
                    <td>{year}</td>
                    <td>{count}</td>
                </tr>
"""
                    html_content += """
            </table>
"""
                
                html_content += """
        </div>
"""
            
            # Footer und Abschluss des HTML-Dokuments
            html_content += """
        <div class="footer">
            <p>Erstellt mit StashApp Analytics</p>
        </div>
    </div>
</body>
</html>
"""
            
            # HTML-Datei speichern
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML-Bericht erfolgreich erstellt: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Fehler bei der Generierung des HTML-Berichts: {str(e)}")
            return ""
