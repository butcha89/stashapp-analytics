"""
Stash API Modul

Dieses Modul stellt Funktionen zur Kommunikation mit der StashApp GraphQL API bereit.
Es bietet Methoden zum Abrufen und Aktualisieren von Daten aus und in StashApp.
"""

import json
import requests
from typing import Dict, List, Any, Optional, Union
import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)

class StashAPI:
    """Klasse für die Kommunikation mit der Stash API"""
    
    def __init__(self, url: str, api_key: str, ssl_verify: bool = True):
        """
        Initialisiert die StashAPI Verbindung
        
        Args:
            url: Die URL des Stash-Servers (z.B. http://localhost:9999)
            api_key: Der API-Schlüssel für die Authentifizierung
            ssl_verify: SSL-Zertifikate überprüfen (True) oder ignorieren (False)
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.ssl_verify = ssl_verify
        self.graphql_endpoint = f"{self.url}/graphql"
        
        # Test-Verbindung herstellen
        self.test_connection()
    
    def test_connection(self) -> bool:
        """
        Testet die Verbindung zur Stash-API
        
        Returns:
            bool: True, wenn Verbindung erfolgreich, sonst False
        """
        query = """
        query {
            systemStatus {
                databaseSchema
                version
            }
        }
        """
        
        response = self.graphql_request(query)
        if response and "systemStatus" in response:
            logger.info(f"Erfolgreich mit Stash verbunden. Version: {response['systemStatus']['version']}")
            return True
        else:
            logger.error("Verbindung zu Stash fehlgeschlagen")
            return False
    
def graphql_request(query, variables=None):
    headers = {
        "Content-Type": "application/json",
        "ApiKey": CONFIG["api_key"]
    }
    
    try:
        response = requests.post(
            f"{CONFIG['stash_url']}/graphql",
            headers=headers,
            data=json.dumps({
                "query": query,
                "variables": variables
            })
        )
        
        if response.status_code == 200:
            result = response.json()
            if "errors" in result and result["errors"]:
                print(f"GraphQL Fehler: {result['errors']}")
                return None
            return result["data"]
        else:
            print(f"Fehler: Status Code {response.status_code}")
            return None
    except Exception as e:
        print(f"Fehler bei der Anfrage: {str(e)}")
        return None
    
def get_all_performers():
    query = """
    query {
        allPerformers {
            id
            name
            birthdate
            gender
            country
            height_cm
            weight
            measurements
            scene_count
            rating100
            favorite
            tags {
                name
            }
            o_counter
        }
    }
    """
    
    data = graphql_request(query)
    if not data or not data["allPerformers"]:
        return []
    
    performers = data["allPerformers"]
    return [process_performer(p) for p in performers]
    
    def get_all_scenes(self, filter_favorites: bool = False) -> List[Dict]:
        """
        Ruft alle Szenen von der Stash-API ab
        
        Args:
            filter_favorites: Wenn True, werden nur Szenen mit Favoriten zurückgegeben
            
        Returns:
            List[Dict]: Liste der Szenen oder leere Liste bei Fehler
        """
        query = """
        query getAllScenes($filter: SceneFilterType) {
            allScenes(filter: $filter) {
                id
                title
                details
                url
                date
                rating100
                o_counter
                organized
                interactive
                interactive_speed
                file {
                    size
                    duration
                    video_codec
                    audio_codec
                    width
                    height
                    framerate
                    bitrate
                }
                paths {
                    screenshot
                    preview
                    stream
                    webp
                    vtt
                }
                scene_markers {
                    id
                    title
                    seconds
                    tags {
                        id
                        name
                    }
                }
                galleries {
                    id
                    title
                }
                studio {
                    id
                    name
                }
                movies {
                    movie {
                        id
                        name
                    }
                    scene_index
                }
                tags {
                    id
                    name
                }
                performers {
                    id
                    name
                    favorite
                }
                stash_ids {
                    endpoint
                    stash_id
                }
                created_at
                updated_at
            }
        }
        """
        
        variables = {}
        if filter_favorites:
            variables["filter"] = {"performers": {"modifier": "INCLUDES", "value": "favorited"}}
        
        data = self.graphql_request(query, variables)
        if data and "allScenes" in data:
            scenes = data["allScenes"]
            logger.info(f"{len(scenes)} Szenen abgerufen")
            return scenes
        
        logger.warning("Keine Szenen abgerufen")
        return []
    
    def get_all_tags(self) -> List[Dict]:
        """
        Ruft alle Tags von der Stash-API ab
        
        Returns:
            List[Dict]: Liste der Tags oder leere Liste bei Fehler
        """
        query = """
        query {
            allTags {
                id
                name
                description
                aliases
                image_path
                scene_count
                performer_count
                parent_count
                child_count
                created_at
                updated_at
            }
        }
        """
        
        data = self.graphql_request(query)
        if data and "allTags" in data:
            tags = data["allTags"]
            logger.info(f"{len(tags)} Tags abgerufen")
            return tags
        
        logger.warning("Keine Tags abgerufen")
        return []
    
    def update_performer(self, performer_id: str, update_data: Dict) -> bool:
        """
        Aktualisiert die Metadaten eines Performers
        
        Args:
            performer_id: Die ID des zu aktualisierenden Performers
            update_data: Die zu aktualisierenden Daten
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        query = """
        mutation updatePerformer($input: PerformerUpdateInput!) {
            performerUpdate(input: $input) {
                id
            }
        }
        """
        
        # ID hinzufügen
        update_data["id"] = performer_id
        
        # GraphQL-Mutation ausführen
        result = self.graphql_request(query, {"input": update_data})
        
        if result and "performerUpdate" in result:
            logger.info(f"Performer {performer_id} erfolgreich aktualisiert")
            return True
        else:
            logger.error(f"Fehler beim Aktualisieren des Performers {performer_id}")
            return False
    
    def update_o_counter(self, scene_id: str, o_counter: int) -> bool:
        """
        Aktualisiert den O-Counter einer Szene
        
        Args:
            scene_id: Die ID der zu aktualisierenden Szene
            o_counter: Der neue O-Counter-Wert
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        query = """
        mutation SceneUpdateOCounter($id: ID!, $o_counter: Int!) {
            sceneUpdateOCounter(id: $id, o_counter: $o_counter)
        }
        """
        
        variables = {
            "id": scene_id,
            "o_counter": o_counter
        }
        
        result = self.graphql_request(query, variables)
        
        if result and "sceneUpdateOCounter" in result:
            logger.info(f"O-Counter für Szene {scene_id} erfolgreich auf {o_counter} aktualisiert")
            return True
        else:
            logger.error(f"Fehler beim Aktualisieren des O-Counters für Szene {scene_id}")
            return False
    
    def create_tag(self, name: str, description: str = "") -> Optional[str]:
        """
        Erstellt einen neuen Tag
        
        Args:
            name: Der Name des Tags
            description: Die Beschreibung des Tags (optional)
            
        Returns:
            Optional[str]: Die ID des erstellten Tags oder None bei Fehler
        """
        query = """
        mutation TagCreate($input: TagCreateInput!) {
            tagCreate(input: $input) {
                id
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "description": description
            }
        }
        
        result = self.graphql_request(query, variables)
        
        if result and "tagCreate" in result and "id" in result["tagCreate"]:
            tag_id = result["tagCreate"]["id"]
            logger.info(f"Tag '{name}' erfolgreich erstellt mit ID {tag_id}")
            return tag_id
        else:
            logger.error(f"Fehler beim Erstellen des Tags '{name}'")
            return None
    
    def add_tag_to_performer(self, performer_id: str, tag_id: str) -> bool:
        """
        Fügt einem Performer einen Tag hinzu
        
        Args:
            performer_id: Die ID des Performers
            tag_id: Die ID des Tags
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        query = """
        mutation PerformerAddTag($performer_id: ID!, $tag_id: ID!) {
            performerAddTag(performer_id: $performer_id, tag_id: $tag_id)
        }
        """
        
        variables = {
            "performer_id": performer_id,
            "tag_id": tag_id
        }
        
        result = self.graphql_request(query, variables)
        
        if result and "performerAddTag" in result:
            logger.info(f"Tag {tag_id} erfolgreich zum Performer {performer_id} hinzugefügt")
            return True
        else:
            logger.error(f"Fehler beim Hinzufügen des Tags {tag_id} zum Performer {performer_id}")
            return False
    
    def get_scenes_by_performer(self, performer_id: str) -> List[Dict]:
        """
        Ruft alle Szenen eines bestimmten Performers ab
        
        Args:
            performer_id: Die ID des Performers
            
        Returns:
            List[Dict]: Liste der Szenen oder leere Liste bei Fehler
        """
        query = """
        query FindScenes($filter: SceneFilterType) {
            findScenes(filter: $filter) {
                id
                title
                date
                rating100
                o_counter
                tags {
                    id
                    name
                }
                performers {
                    id
                    name
                }
                studio {
                    id
                    name
                }
            }
        }
        """
        
        variables = {
            "filter": {
                "performers": {
                    "value": performer_id,
                    "modifier": "INCLUDES"
                }
            }
        }
        
        data = self.graphql_request(query, variables)
        if data and "findScenes" in data:
            scenes = data["findScenes"]
            logger.info(f"{len(scenes)} Szenen für Performer {performer_id} abgerufen")
            return scenes
        
        logger.warning(f"Keine Szenen für Performer {performer_id} gefunden")
        return []
    
    def get_tag_id_by_name(self, tag_name: str) -> Optional[str]:
        """
        Sucht die ID eines Tags anhand seines Namens
        
        Args:
            tag_name: Der Name des Tags
            
        Returns:
            Optional[str]: Die ID des Tags oder None, wenn nicht gefunden
        """
        query = """
        query FindTags($filter: TagFilterType) {
            findTags(filter: $filter) {
                id
                name
            }
        }
        """
        
        variables = {
            "filter": {
                "name": {
                    "value": tag_name,
                    "modifier": "EQUALS"
                }
            }
        }
        
        data = self.graphql_request(query, variables)
        if data and "findTags" in data and data["findTags"]:
            return data["findTags"][0]["id"]
        
        logger.warning(f"Tag '{tag_name}' nicht gefunden")
        return None
    
    def get_performer_by_id(self, performer_id: str) -> Optional[Dict]:
        """
        Ruft einen einzelnen Performer anhand seiner ID ab
        
        Args:
            performer_id: Die ID des Performers
            
        Returns:
            Optional[Dict]: Die Performer-Daten oder None bei Fehler
        """
        query = """
        query FindPerformer($id: ID!) {
            findPerformer(id: $id) {
                id
                name
                gender
                url
                twitter
                instagram
                birthdate
                ethnicity
                country
                eye_color
                height_cm
                weight
                measurements
                fake_tits
                career_length
                tattoos
                piercings
                aliases
                favorite
                rating100
                details
                death_date
                hair_color
                image_path
                scene_count
                stash_ids {
                    endpoint
                    stash_id
                }
                tags {
                    id
                    name
                }
                o_counter
                created_at
                updated_at
            }
        }
        """
        
        variables = {
            "id": performer_id
        }
        
        data = self.graphql_request(query, variables)
        if data and "findPerformer" in data:
            logger.info(f"Performer {performer_id} abgerufen")
            return data["findPerformer"]
        
        logger.warning(f"Performer {performer_id} nicht gefunden")
        return None
    
    def get_scene_by_id(self, scene_id: str) -> Optional[Dict]:
        """
        Ruft eine einzelne Szene anhand ihrer ID ab
        
        Args:
            scene_id: Die ID der Szene
            
        Returns:
            Optional[Dict]: Die Szenen-Daten oder None bei Fehler
        """
        query = """
        query FindScene($id: ID!) {
            findScene(id: $id) {
                id
                title
                details
                url
                date
                rating100
                o_counter
                organized
                interactive
                file {
                    size
                    duration
                    video_codec
                    audio_codec
                    width
                    height
                    framerate
                    bitrate
                }
                performers {
                    id
                    name
                    favorite
                }
                tags {
                    id
                    name
                }
                studio {
                    id
                    name
                }
                created_at
                updated_at
            }
        }
        """
        
        variables = {
            "id": scene_id
        }
        
        data = self.graphql_request(query, variables)
        if data and "findScene" in data:
            logger.info(f"Szene {scene_id} abgerufen")
            return data["findScene"]
        
        logger.warning(f"Szene {scene_id} nicht gefunden")
        return None
