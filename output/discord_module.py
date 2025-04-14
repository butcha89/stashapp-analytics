"""
Discord Module

Dieses Modul ist verantwortlich für die Kommunikation mit Discord
über Webhooks. Es sendet Statistiken, Empfehlungen und Updates an
konfigurierte Discord-Kanäle.
"""

import os
import json
import time
import datetime
import logging
import requests
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple, Union
import random

from core.stash_api import StashAPI
from core.data_models import Performer, Scene
from analysis.statistics_module import StatisticsModule
from recommendations.recommendation_performer import PerformerRecommendationModule
from recommendations.recommendation_scenes import SceneRecommendationModule
from management.config_manager import ConfigManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class DiscordModule:
    """
    Klasse zur Kommunikation mit Discord über Webhooks.
    Sendet Statistiken, Empfehlungen und Updates an Discord-Kanäle.
    """
    
    def __init__(self, api: StashAPI, 
                 stats_module: StatisticsModule, 
                 performer_rec_module: Optional[PerformerRecommendationModule] = None, 
                 scene_rec_module: Optional[SceneRecommendationModule] = None, 
                 config: ConfigManager = None):
        """
        Initialisiert das Discord-Modul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz mit berechneten Statistiken
            performer_rec_module: Optional, PerformerRecommendationModule-Instanz mit Empfehlungen
            scene_rec_module: Optional, SceneRecommendationModule-Instanz mit Empfehlungen
            config: ConfigManager-Instanz mit der Konfiguration
        """
        self.api = api
        self.stats_module = stats_module
        self.performer_rec_module = performer_rec_module
        self.scene_rec_module = scene_rec_module
        self.config = config
        
        # Lade Konfigurationsoptionen
        self.webhook_url = self.config.get('Discord', 'webhook_url', fallback='')
        self.post_statistics = self.config.getboolean('Discord', 'post_statistics', fallback=True)
        self.post_recommendations = self.config.getboolean('Discord', 'post_recommendations', fallback=True)
        self.max_recommendations = self.config.getint('Discord', 'max_recommendations_per_message', fallback=3)
        self.max_stats = self.config.getint('Discord', 'max_stats_per_message', fallback=5)
        self.use_embeds = self.config.getboolean('Discord', 'use_embeds', fallback=True)
        self.include_images = self.config.getboolean('Discord', 'include_images', fallback=True)
        self.rate_limit_delay = self.config.getfloat('Discord', 'rate_limit_delay', fallback=1.0)
        
        # Boobpedia-Integration für Bilder
        self.enable_boobpedia = self.config.getboolean('BoobPedia', 'enable_image_lookup', fallback=False)
        self.boobpedia_max_images = self.config.getint('BoobPedia', 'max_images', fallback=1)
        
        # Prüfe, ob Discord-Integration aktiviert ist
        if not self.webhook_url:
            logger.warning("Keine Discord Webhook-URL konfiguriert. Discord-Funktionen sind deaktiviert.")
        else:
            logger.info(f"Discord-Modul initialisiert mit Webhook: {self.webhook_url[:20]}...")
    
    def send_all_updates(self) -> bool:
        """
        Sendet alle konfigurierten Updates an Discord.
        
        Returns:
            bool: True, wenn alle Updates erfolgreich gesendet wurden, sonst False
        """
        if not self.webhook_url:
            logger.error("Keine Discord Webhook-URL konfiguriert. Kann keine Updates senden.")
            return False
        
        success = True
        
        # Sendet eine Willkommensnachricht mit dem Titel und Zeitstempel
        self.send_welcome_message()
        time.sleep(self.rate_limit_delay)
        
        # Sendet Statistiken, wenn konfiguriert
        if self.post_statistics:
            logger.info("Sende Statistiken an Discord...")
            if not self.send_statistics():
                logger.error("Fehler beim Senden der Statistiken an Discord")
                success = False
            time.sleep(self.rate_limit_delay)
        
        # Sendet Performer-Empfehlungen, wenn konfiguriert und verfügbar
        if self.post_recommendations and self.performer_rec_module:
            logger.info("Sende Performer-Empfehlungen an Discord...")
            if not self.send_performer_recommendations():
                logger.error("Fehler beim Senden der Performer-Empfehlungen an Discord")
                success = False
            time.sleep(self.rate_limit_delay)
        
        # Sendet Szenen-Empfehlungen, wenn konfiguriert und verfügbar
        if self.post_recommendations and self.scene_rec_module:
            logger.info("Sende Szenen-Empfehlungen an Discord...")
            if not self.send_scene_recommendations():
                logger.error("Fehler beim Senden der Szenen-Empfehlungen an Discord")
                success = False
            time.sleep(self.rate_limit_delay)
        
        return success
    
    def send_welcome_message(self) -> bool:
        """
        Sendet eine Willkommensnachricht an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        message = {
            "content": f"# StashApp Analytics Update\n\n**Zeitpunkt:** {current_time}"
        }
        
        return self._send_discord_message(message)
    
    def send_statistics(self) -> bool:
        """
        Sendet Statistiken an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        stats = self.stats_module.get_summary_stats()
        
        if not stats:
            logger.warning("Keine Statistiken verfügbar zum Senden an Discord")
            return False
        
        # Erstelle Embed für die Statistiken
        if self.use_embeds:
            embed = {
                "title": "Performer-Statistiken",
                "description": "Zusammenfassung der wichtigsten Statistiken",
                "color": 3447003,  # Blau
                "fields": []
            }
            
            # Füge Felder für die wichtigsten Statistiken hinzu
            if "total_count" in stats:
                embed["fields"].append({
                    "name": "Anzahl Performer",
                    "value": f"{stats['total_count']}",
                    "inline": True
                })
            
            if "avg_cup_size" in stats:
                avg_cup = stats.get("avg_cup_size", 0)
                avg_cup_letter = ""
                if avg_cup:
                    avg_cup_letter = f" ({Performer.CUP_NUMERIC_TO_LETTER.get(round(avg_cup), '?')})"
                
                embed["fields"].append({
                    "name": "Durchschnittliche Cup-Größe",
                    "value": f"{avg_cup:.2f}{avg_cup_letter}",
                    "inline": True
                })
            
            if "avg_bmi" in stats:
                embed["fields"].append({
                    "name": "Durchschnittlicher BMI",
                    "value": f"{stats.get('avg_bmi', 0):.1f}",
                    "inline": True
                })
            
            if "avg_rating" in stats:
                embed["fields"].append({
                    "name": "Durchschnittliches Rating",
                    "value": f"{stats.get('avg_rating', 0)/20:.1f}/5 ⭐",
                    "inline": True
                })
            
            if "avg_o_counter" in stats:
                embed["fields"].append({
                    "name": "Durchschnittlicher O-Counter",
                    "value": f"{stats.get('avg_o_counter', 0):.1f}",
                    "inline": True
                })
            
            # Cup-Größen-Verteilung
            if "cup_distribution" in stats:
                cup_dist = stats["cup_distribution"]
                sorted_cups = sorted(cup_dist.keys(), key=lambda x: Performer.CUP_NUMERIC.get(x, 0))
                cup_text = "\n".join([f"{cup}: {cup_dist[cup]}" for cup in sorted_cups[:self.max_stats]])
                
                if len(sorted_cups) > self.max_stats:
                    cup_text += f"\n... und {len(sorted_cups) - self.max_stats} weitere"
                
                embed["fields"].append({
                    "name": "Cup-Größen-Verteilung",
                    "value": cup_text,
                    "inline": False
                })
            
            # BMI-Kategorien
            if "bmi_distribution" in stats:
                bmi_dist = stats["bmi_distribution"]
                sorted_categories = ["Untergewicht", "Normalgewicht", "Übergewicht", "Adipositas"]
                bmi_text = "\n".join([f"{cat}: {bmi_dist.get(cat, 0)}" for cat in sorted_categories if cat in bmi_dist])
                
                embed["fields"].append({
                    "name": "BMI-Kategorien",
                    "value": bmi_text,
                    "inline": False
                })
            
            # Top O-Counter
            if hasattr(self.stats_module, "get_top_o_counter_performers"):
                top_performers = self.stats_module.get_top_o_counter_performers(limit=self.max_stats)
                if top_performers:
                    top_text = "\n".join([f"{p.name}: {p.o_counter}" for p in top_performers])
                    
                    embed["fields"].append({
                        "name": "Top O-Counter Performer",
                        "value": top_text,
                        "inline": False
                    })
            
            message = {
                "content": "## Statistik-Zusammenfassung",
                "embeds": [embed]
            }
        else:
            # Alternativ: Text-basierte Nachricht
            content = "## Statistik-Zusammenfassung\n\n"
            
            content += f"**Anzahl Performer:** {stats.get('total_count', 0)}\n"
            
            avg_cup = stats.get("avg_cup_size", 0)
            avg_cup_letter = ""
            if avg_cup:
                avg_cup_letter = f" ({Performer.CUP_NUMERIC_TO_LETTER.get(round(avg_cup), '?')})"
            content += f"**Durchschnittliche Cup-Größe:** {avg_cup:.2f}{avg_cup_letter}\n"
            
            content += f"**Durchschnittlicher BMI:** {stats.get('avg_bmi', 0):.1f}\n"
            content += f"**Durchschnittliches Rating:** {stats.get('avg_rating', 0)/20:.1f}/5 ⭐\n"
            content += f"**Durchschnittlicher O-Counter:** {stats.get('avg_o_counter', 0):.1f}\n\n"
            
            # Cup-Größen-Verteilung
            if "cup_distribution" in stats:
                content += "**Cup-Größen-Verteilung:**\n"
                cup_dist = stats["cup_distribution"]
                sorted_cups = sorted(cup_dist.keys(), key=lambda x: Performer.CUP_NUMERIC.get(x, 0))
                
                for cup in sorted_cups[:self.max_stats]:
                    content += f"- {cup}: {cup_dist[cup]}\n"
                
                if len(sorted_cups) > self.max_stats:
                    content += f"- ... und {len(sorted_cups) - self.max_stats} weitere\n"
                
                content += "\n"
            
            # BMI-Kategorien
            if "bmi_distribution" in stats:
                content += "**BMI-Kategorien:**\n"
                bmi_dist = stats["bmi_distribution"]
                sorted_categories = ["Untergewicht", "Normalgewicht", "Übergewicht", "Adipositas"]
                
                for cat in sorted_categories:
                    if cat in bmi_dist:
                        content += f"- {cat}: {bmi_dist[cat]}\n"
                
                content += "\n"
            
            # Top O-Counter
            if hasattr(self.stats_module, "get_top_o_counter_performers"):
                top_performers = self.stats_module.get_top_o_counter_performers(limit=self.max_stats)
                if top_performers:
                    content += "**Top O-Counter Performer:**\n"
                    for p in top_performers:
                        content += f"- {p.name}: {p.o_counter}\n"
                    
                    content += "\n"
            
            message = {"content": content}
        
        return self._send_discord_message(message)
    
    def send_performer_recommendations(self) -> bool:
        """
        Sendet Performer-Empfehlungen an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if not self.performer_rec_module:
            logger.warning("Keine Performer-Empfehlungen verfügbar zum Senden an Discord")
            return False
        
        # Hole Empfehlungen
        recommendations = self.performer_rec_module.get_top_recommendations(self.max_recommendations)
        
        if not recommendations:
            logger.warning("Keine Empfehlungen gefunden zum Senden an Discord")
            return False
        
        # Erstelle Embed für die Empfehlungen
        if self.use_embeds:
            embeds = []
            
            for performer, score in recommendations:
                # Basisdaten für das Embed
                embed = {
                    "title": performer.name,
                    "description": f"**Ähnlichkeitswert:** {score:.2f}",
                    "color": 15105570,  # Orange
                    "fields": []
                }
                
                # Zusätzliche Infos als Felder
                if performer.cup_size:
                    embed["fields"].append({
                        "name": "Cup-Größe",
                        "value": performer.cup_size,
                        "inline": True
                    })
                
                if performer.german_bra_size:
                    embed["fields"].append({
                        "name": "BH-Größe",
                        "value": performer.german_bra_size,
                        "inline": True
                    })
                
                if performer.bmi:
                    embed["fields"].append({
                        "name": "BMI",
                        "value": f"{performer.bmi:.1f} ({performer.bmi_category})",
                        "inline": True
                    })
                
                if performer.rating100 is not None:
                    embed["fields"].append({
                        "name": "Rating",
                        "value": f"{performer.rating100/20:.1f}/5 ⭐",
                        "inline": True
                    })
                
                if performer.scene_count > 0:
                    embed["fields"].append({
                        "name": "Szenen",
                        "value": str(performer.scene_count),
                        "inline": True
                    })
                
                if performer.o_counter > 0:
                    embed["fields"].append({
                        "name": "O-Counter",
                        "value": str(performer.o_counter),
                        "inline": True
                    })
                
                # Füge Bild hinzu, wenn verfügbar und konfiguriert
                if self.include_images:
                    # Versuche StashApp-Bild zu verwenden
                    image_url = self._get_performer_image_url(performer)
                    
                    # Oder verwende Boobpedia, falls konfiguriert
                    if not image_url and self.enable_boobpedia:
                        image_url = self._get_boobpedia_image(performer.name)
                    
                    if image_url:
                        embed["thumbnail"] = {"url": image_url}
                
                embeds.append(embed)
            
            # Sende die Nachricht mit den Embeds
            message = {
                "content": "## Performer-Empfehlungen",
                "embeds": embeds
            }
        else:
            # Alternativ: Text-basierte Nachricht
            content = "## Performer-Empfehlungen\n\n"
            
            for performer, score in recommendations:
                content += f"### {performer.name} (Score: {score:.2f})\n\n"
                
                if performer.cup_size:
                    content += f"**Cup-Größe:** {performer.cup_size}\n"
                
                if performer.german_bra_size:
                    content += f"**BH-Größe:** {performer.german_bra_size}\n"
                
                if performer.bmi:
                    content += f"**BMI:** {performer.bmi:.1f} ({performer.bmi_category})\n"
                
                if performer.rating100 is not None:
                    content += f"**Rating:** {performer.rating100/20:.1f}/5 ⭐\n"
                
                if performer.scene_count > 0:
                    content += f"**Szenen:** {performer.scene_count}\n"
                
                if performer.o_counter > 0:
                    content += f"**O-Counter:** {performer.o_counter}\n"
                
                content += "\n"
            
            message = {"content": content}
        
        return self._send_discord_message(message)
    
    def send_scene_recommendations(self) -> bool:
        """
        Sendet Szenen-Empfehlungen an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if not self.scene_rec_module:
            logger.warning("Keine Szenen-Empfehlungen verfügbar zum Senden an Discord")
            return False
        
        # Hole Empfehlungen
        recommendations = self.scene_rec_module.get_top_recommendations(self.max_recommendations)
        
        if not recommendations:
            logger.warning("Keine Szenen-Empfehlungen gefunden zum Senden an Discord")
            return False
        
        # Erstelle Embed für die Empfehlungen
        if self.use_embeds:
            embeds = []
            
            for scene, score in recommendations:
                # Basisdaten für das Embed
                embed = {
                    "title": scene.title or "Unbenannte Szene",
                    "description": f"**Ähnlichkeitswert:** {score:.2f}",
                    "color": 3066993,  # Grün
                    "fields": []
                }
                
                # Performer als erstes Feld
                if scene.performer_names:
                    performers_text = ", ".join(scene.performer_names[:5])
                    if len(scene.performer_names) > 5:
                        performers_text += f" und {len(scene.performer_names) - 5} weitere"
                    
                    embed["fields"].append({
                        "name": "Performer",
                        "value": performers_text,
                        "inline": False
                    })
                
                # Studio
                if scene.studio_name:
                    embed["fields"].append({
                        "name": "Studio",
                        "value": scene.studio_name,
                        "inline": True
                    })
                
                # Tags
                if scene.tags:
                    tags_text = ", ".join(scene.tags[:5])
                    if len(scene.tags) > 5:
                        tags_text += f" und {len(scene.tags) - 5} weitere"
                    
                    embed["fields"].append({
                        "name": "Tags",
                        "value": tags_text,
                        "inline": True
                    })
                
                # Rating
                if scene.rating100 is not None:
                    embed["fields"].append({
                        "name": "Rating",
                        "value": f"{scene.rating100/20:.1f}/5 ⭐",
                        "inline": True
                    })
                
                # O-Counter
                if scene.o_counter > 0:
                    embed["fields"].append({
                        "name": "O-Counter",
                        "value": str(scene.o_counter),
                        "inline": True
                    })
                
                # Dauer
                if scene.duration > 0:
                    minutes = int(scene.duration / 60)
                    seconds = int(scene.duration % 60)
                    embed["fields"].append({
                        "name": "Dauer",
                        "value": f"{minutes}:{seconds:02d}",
                        "inline": True
                    })
                
                # Datum
                if scene.date:
                    embed["fields"].append({
                        "name": "Datum",
                        "value": scene.date,
                        "inline": True
                    })
                
                # Füge Bild hinzu, wenn verfügbar und konfiguriert
                if self.include_images:
                    image_url = self._get_scene_image_url(scene)
                    if image_url:
                        embed["thumbnail"] = {"url": image_url}
                
                embeds.append(embed)
            
            # Sende die Nachricht mit den Embeds
            message = {
                "content": "## Szenen-Empfehlungen",
                "embeds": embeds
            }
        else:
            # Alternativ: Text-basierte Nachricht
            content = "## Szenen-Empfehlungen\n\n"
            
            for scene, score in recommendations:
                content += f"### {scene.title or 'Unbenannte Szene'} (Score: {score:.2f})\n\n"
                
                # Performer
                if scene.performer_names:
                    performers_text = ", ".join(scene.performer_names[:5])
                    if len(scene.performer_names) > 5:
                        performers_text += f" und {len(scene.performer_names) - 5} weitere"
                    content += f"**Performer:** {performers_text}\n"
                
                # Studio
                if scene.studio_name:
                    content += f"**Studio:** {scene.studio_name}\n"
                
                # Tags
                if scene.tags:
                    tags_text = ", ".join(scene.tags[:5])
                    if len(scene.tags) > 5:
                        tags_text += f" und {len(scene.tags) - 5} weitere"
                    content += f"**Tags:** {tags_text}\n"
                
                # Rating
                if scene.rating100 is not None:
                    content += f"**Rating:** {scene.rating100/20:.1f}/5 ⭐\n"
                
                # O-Counter
                if scene.o_counter > 0:
                    content += f"**O-Counter:** {scene.o_counter}\n"
                
                # Dauer
                if scene.duration > 0:
                    minutes = int(scene.duration / 60)
                    seconds = int(scene.duration % 60)
                    content += f"**Dauer:** {minutes}:{seconds:02d}\n"
                
                # Datum
                if scene.date:
                    content += f"**Datum:** {scene.date}\n"
                
                content += "\n"
            
            message = {"content": content}
        
        return self._send_discord_message(message)
    
    def _send_discord_message(self, message: Dict[str, Any]) -> bool:
        """
        Sendet eine Nachricht an Discord über den konfigurierten Webhook.
        
        Args:
            message: Die zu sendende Nachricht als Dictionary
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if not self.webhook_url:
            logger.error("Keine Discord Webhook-URL konfiguriert")
            return False
        
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook_url,
                data=json.dumps(message),
                headers=headers
            )
            
            if response.status_code == 204:
                logger.info("Nachricht erfolgreich an Discord gesendet")
                return True
            elif response.status_code == 429:
                # Rate-Limiting - warte und versuche es erneut
                retry_after = float(response.headers.get("Retry-After", 1))
                logger.warning(f"Discord Rate-Limit erreicht. Warte {retry_after} Sekunden")
                time.sleep(retry_after)
                return self._send_discord_message(message)
            else:
                logger.error(f"Fehler beim Senden an Discord: Status {response.status_code}, {response.text}")
                return False
        except Exception as e:
            logger.error(f"Fehler beim Senden an Discord: {str(e)}")
            return False
    
    def _get_performer_image_url(self, performer: Performer) -> Optional[str]:
        """
        Ruft die Bild-URL eines Performers ab.
        
        Args:
            performer: Der Performer
            
        Returns:
            Optional[str]: Die Bild-URL oder None, wenn nicht verfügbar
        """
        # In den raw_data sollte das Bild als Base64 enthalten sein
        if performer.raw_data and "image_path" in performer.raw_data:
            image_path = performer.raw_data["image_path"]
            if image_path:
                # Konstruiere die URL zum Bild
                return f"{self.api.url}/performer/{performer.id}/image"
        
        return None
    
    def _get_scene_image_url(self, scene: Scene) -> Optional[str]:
        """
        Ruft die Screenshot-URL einer Szene ab.
        
        Args:
            scene: Die Szene
            
        Returns:
            Optional[str]: Die Screenshot-URL oder None, wenn nicht verfügbar
        """
        # In den raw_data sollten die Pfade enthalten sein
        if scene.raw_data and "paths" in scene.raw_data:
            paths = scene.raw_data["paths"]
            if paths and "screenshot" in paths:
                screenshot_path = paths["screenshot"]
                if screenshot_path:
                    # Konstruiere die URL zum Screenshot
                    return f"{self.api.url}/scene/{scene.id}/screenshot"
        
        return None
    
    def _get_boobpedia_image(self, performer_name: str) -> Optional[str]:
        """
        Versucht, ein Bild von Boobpedia zu erhalten.
        
        Args:
            performer_name: Der Name des Performers
            
        Returns:
            Optional[str]: Die Bild-URL oder None, wenn nicht verfügbar
        """
        if not self.enable_boobpedia:
            return None
        
        try:
            # Formatiere den Namen für die URL
            formatted_name = performer_name.replace(" ", "_")
            
            # Erstelle die URL zur Boobpedia-Seite
            url = f"https://www.boobpedia.com/boobs/{formatted_name}"
            
            # Versuche, die Seite abzurufen
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"Boobpedia-Seite für {performer_name} nicht gefunden: {response.status_code}")
                return None
            
            # Einfache Regex, um Bild-URLs zu finden
            image_urls = re.findall(r'<img[^>]+src="([^"]+/[^/]+\.(jpg|jpeg|png))"[^>]*>', response.text)
            
            # Filtere die gefundenen URLs
            valid_urls = []
            for url, ext in image_urls:
                if "/thumb/" in url:
                    # Bei Thumbnails verwende die Vollversion
                    url = re.sub(r'/thumb/([^/]+/[^/]+)/[^/]+\.(jpg|jpeg|png)$', r'/\1', url)
                
                if "face" not in url.lower() and "icon" not in url.lower() and "logo" not in url.lower():
                    valid_urls.append(url)
            
            # Wähle eine zufällige URL (falls mehrere gefunden wurden)
            if valid_urls:
                selected_url = random.choice(valid_urls[:self.boobpedia_max_images])
                
                # Stelle sicher, dass die URL absolut ist
                if not selected_url.startswith("http"):
                    selected_url = f"https://www.boobpedia.com{selected_url if selected_url.startswith('/') else '/' + selected_url}"
                
                logger.info(f"Boobpedia-Bild für {performer_name} gefunden: {selected_url}")
                return selected_url
                
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen des Boobpedia-Bildes für {performer_name}: {str(e)}")
        
        return None
