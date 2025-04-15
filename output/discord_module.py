"""
Discord Module

Dieses Modul sendet Zusammenfassungen der Statistiken und Empfehlungen an einen 
konfigurierten Discord-Webhook. Es verwendet Templates, um die Nachrichten zu 
formatieren und ermöglicht das Senden von Diagrammen als Bilder.
"""

import os
import logging
import json
import yaml
from typing import Dict, Optional
from discord_webhook import DiscordWebhook, DiscordEmbed
from core.stash_api import StashAPI 
from analysis.statistics_module import StatisticsModule
from recommendations.recommendation_performer import PerformerRecommendationModule
from recommendations.recommendation_scenes import SceneRecommendationModule
from management.config_manager import ConfigManager

# Logger konfigurieren
logger = logging.getLogger(__name__)

class DiscordModule:
    """
    Klasse zur Verwaltung der Discord-Integration und des Sendens von Updates.
    """
    
    def __init__(self, api: StashAPI, stats_module: StatisticsModule,
                 performer_rec_module: PerformerRecommendationModule,
                 scene_rec_module: SceneRecommendationModule, 
                 config: ConfigManager):
        """
        Initialisiert das Discord-Modul.
        
        Args:
            api: StashAPI-Instanz für die Kommunikation mit StashApp
            stats_module: StatisticsModule-Instanz
            performer_rec_module: PerformerRecommendationModule-Instanz
            scene_rec_module: SceneRecommendationModule-Instanz
            config: ConfigManager-Instanz
        """
        self.api = api
        self.stats_module = stats_module
        self.performer_rec_module = performer_rec_module
        self.scene_rec_module = scene_rec_module
        self.config = config
        
        # Lade Discord-Konfiguration
        self.enable_discord = config.getboolean('Discord', 'enable_discord', fallback=False)
        self.webhook_url = config.get('Discord', 'webhook_url')
        self.template_file = config.get('Discord', 'template_file', fallback='templates/discord_templates.yaml')
        self.max_recommendations = config.getint('Discord', 'max_recommendations_per_message', fallback=3)
        self.max_stats = config.getint('Discord', 'max_stats_per_message', fallback=5)
        
        # Lade Templates
        self.templates = self._load_templates()
        
        logger.info("Discord-Modul initialisiert")
    
    def _load_templates(self) -> Dict[str, str]:
        """
        Lädt die Message-Templates aus der Konfigurationsdatei.
        
        Returns:
            Dict[str, str]: Dictionary mit Template-Namen und Inhalten
        """
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Template-Datei nicht gefunden: {self.template_file}")
            return {}
        except Exception as e:
            logger.error(f"Fehler beim Laden der Templates: {str(e)}")
            return {}
    
    def _format_message(self, template_name: str, data: dict) -> str:
        """
        Formatiert eine Nachricht anhand des angegebenen Templates.
        
        Args:
            template_name: Name des zu verwendenden Templates
            data: Daten zur Ersetzung der Platzhalter im Template
            
        Returns:
            str: Formatierte Nachricht
        """
        template = self.templates.get(template_name)
        if not template:
            logger.warning(f"Template nicht gefunden: {template_name}")
            return ""
        
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Fehlender Platzhalter im Template '{template_name}': {str(e)}")
            return template
    
    def _send_discord_message(self, content: Optional[str] = None, embeds: Optional[list] = None, 
                              files: Optional[list] = None) -> bool:
        """
        Sendet eine Nachricht an den konfigurierten Discord-Webhook.
        
        Args:
            content: Nachrichteninhalt (optional)
            embeds: Liste von Embed-Objekten (optional)
            files: Liste von Dateipfaden zum Hochladen (optional)
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if not self.enable_discord or not self.webhook_url:
            logger.debug("Discord-Integration ist deaktiviert oder Webhook-URL fehlt")
            return False
        
        try:
            webhook = DiscordWebhook(url=self.webhook_url, content=content, embeds=embeds)
            if files:
                for file in files:
                    with open(file, "rb") as f:
                        webhook.add_file(file=f.read(), filename=os.path.basename(file))
            response = webhook.execute()
            
            # Prüfe Antwort-Status
            if response.status_code == 200:
                logger.info("Discord-Nachricht erfolgreich gesendet")
                return True
            else:
                logger.error(f"Fehler beim Senden der Discord-Nachricht - Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Fehler beim Senden der Discord-Nachricht: {str(e)}")
            return False
    
    def send_statistics_summary(self) -> bool:
        """
        Sendet eine Zusammenfassung der Statistiken an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info("Sende Statistik-Zusammenfassung an Discord...")
        
        if not self.stats_module:
            logger.warning("Statistikmodul nicht verfügbar, überspringe Zusammenfassung.")
            return False
        
        # Hole Statistikdaten
        stats = self.stats_module.get_all_statistics()
        general_stats = stats.get('general', {})
        performer_stats = stats.get('performers', {})
        scene_stats = stats.get('scenes', {})
        
        # Erstelle Datenkontext für Templates
        data = {
            'total_performers': general_stats.get('total_performers', 0),
            'total_scenes': general_stats.get('total_scenes', 0),
            'total_tags': general_stats.get('total_tags', 0),
            'avg_rating': general_stats.get('avg_rating', 0),
            'avg_o_counter': general_stats.get('avg_o_counter', 0),
            'rating_dist': self._format_distribution(performer_stats.get('rating_distribution', {}), self.max_stats),
            'most_common_tags': ', '.join([f"{tag} ({count})" for tag, count in performer_stats.get('top_tags', {}).items()][:self.max_stats]),
            'top_studios': ', '.join([f"{studio} ({count})" for studio, count in scene_stats.get('top_studios', {}).items()][:self.max_stats]),
        }
        
        # Generiere Nachrichteninhalt aus Template
        content = self._format_message('stats_summary', data)
        
        # Sende Nachricht
        return self._send_discord_message(content=content)
    
    def send_performer_recommendations(self) -> bool:
        """
        Sendet Performer-Empfehlungen an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info("Sende Performer-Empfehlungen an Discord...")
        
        if not self.performer_rec_module or not self.performer_rec_module.top_recommendations:
            logger.warning("Keine Performer-Empfehlungen verfügbar, überspringe.")
            return False
        
        # Hole Top-Empfehlungen
        recommendations = self.performer_rec_module.top_recommendations[:self.max_recommendations]
        
        # Erstelle Embed für jede Empfehlung
        embeds = []
        for performer, score in recommendations:
            embed = DiscordEmbed(title=f"{performer.name} (ID: {performer.id})", color='03b2f8')
            embed.add_embed_field(name='Ähnlichkeitswert', value=f"{score:.2f}")
            embed.add_embed_field(name='Cup-Größe', value=performer.cup_size or '-')
            embed.add_embed_field(name='Bewertung', value=f"{performer.rating100/10:.1f}" if performer.rating100 else '-')
            embeds.append(embed)
        
        # Sende Nachricht mit Embeds
        return self._send_discord_message(content="Hier sind deine Top Performer-Empfehlungen:", embeds=embeds)
    
    def send_scene_recommendations(self) -> bool:
        """
        Sendet Szenen-Empfehlungen an Discord.
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info("Sende Szenen-Empfehlungen an Discord...")
        
        if not self.scene_rec_module or not self.scene_rec_module.top_recommendations:
            logger.warning("Keine Szenen-Empfehlungen verfügbar, überspringe.")
            return False
        
        # Hole Top-Empfehlungen
        recommendations = self.scene_rec_module.top_recommendations[:self.max_recommendations]
        
        # Erstelle Embed für jede Empfehlung
        embeds = []
        for scene, score in recommendations:
            embed = DiscordEmbed(title=f"{scene.title} (ID: {scene.id})", color='03b2f8')
            embed.add_embed_field(name='Ähnlichkeitswert', value=f"{score:.2f}")
            embed.add_embed_field(name='Bewertung', value=f"{scene.rating100/10:.1f}" if scene.rating100 else '-')
            embed.add_embed_field(name='Studio', value=scene.studio_name or '-')
            embeds.append(embed)
        
        # Sende Nachricht mit Embeds
        return self._send_discord_message(content="Hier sind deine Top Szenen-Empfehlungen:", embeds=embeds)
    
    def send_visualization(self, filepath: str, title: str, description: str) -> bool:
        """
        Sendet eine Visualisierung als Bild an Discord.
        
        Args:
            filepath: Pfad zur Bilddatei
            title: Titel der Nachricht
            description: Beschreibung der Nachricht
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            files = [filepath]
            embed = DiscordEmbed(title=title, description=description)
            return self._send_discord_message(embeds=[embed], files=files)
        except Exception as e:
            logger.error(f"Fehler beim Senden der Visualisierung '{filepath}': {str(e)}")
            return False
    
    def send_all_updates(self) -> None:
        """
        Sendet alle verfügbaren Updates (Statistiken, Empfehlungen, Visualisierungen) an Discord.
        """
        logger.info("Sende alle Updates an Discord...")
        
        # Statistik-Zusammenfassung
        self.send_statistics_summary()
        
        # Performer-Empfehlungen
        self.send_performer_recommendations()
        
        # Szenen-Empfehlungen
        self.send_scene_recommendations()
        
        # TODO: Visualisierungen senden (Beispiel)
        # vis_file = "./output/graphs/cup_size_distribution.png"
        # self.send_visualization(vis_file, "Cup-Größen-Verteilung", "Verteilung der Cup-Größen aller Performer")
        
        logger.info("Alle Discord-Updates gesendet.")
