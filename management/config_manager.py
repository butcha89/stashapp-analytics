"""
Configuration Manager Modul

Dieses Modul verwaltet die Konfiguration aus der configuration.ini Datei.
Es stellt Methoden zum Lesen, Validieren und Bereitstellen von Konfigurationswerten bereit.
"""

import os
import sys
import configparser
import logging
from typing import Any, Dict, Optional, Union, List, Tuple

class ConfigManager:
    """
    Klasse für die Verwaltung der Konfigurationsdatei.
    Bietet Methoden zum Lesen, Validieren und Abfragen von Konfigurationswerten.
    """
    
    def __init__(self, config_file: str = 'configuration.ini'):
        """
        Initialisiert den ConfigManager und lädt die Konfigurationsdatei.
        
        Args:
            config_file: Pfad zur Konfigurationsdatei (Standard: configuration.ini)
            
        Raises:
            FileNotFoundError: Wenn die Konfigurationsdatei nicht gefunden wird.
            configparser.Error: Bei Fehlern beim Parsen der Konfigurationsdatei.
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser(interpolation=configparser.BasicInterpolation())
        
        if not os.path.exists(config_file):
            example_file = f"{config_file}.example"
            if os.path.exists(example_file):
                error_msg = (
                    f"Konfigurationsdatei '{config_file}' nicht gefunden.\n"
                    f"Bitte kopieren Sie die Beispielkonfigurationsdatei '{example_file}' "
                    f"zu '{config_file}' und passen Sie die Werte an."
                )
            else:
                error_msg = f"Konfigurationsdatei '{config_file}' nicht gefunden."
            
            raise FileNotFoundError(error_msg)
        
        try:
            self.config.read(config_file)
            self._validate_required_settings()
        except configparser.Error as e:
            raise configparser.Error(f"Fehler beim Lesen der Konfigurationsdatei '{config_file}': {str(e)}")
    
    def _validate_required_settings(self):
        """
        Überprüft, ob alle erforderlichen Einstellungen in der Konfigurationsdatei vorhanden sind.
        
        Raises:
            ValueError: Wenn erforderliche Einstellungen fehlen.
        """
        required_settings = [
            ('StashApp', 'url'),
            ('StashApp', 'api_key'),
        ]
        
        missing_settings = []
        
        for section, option in required_settings:
            if not self.has_option(section, option):
                missing_settings.append(f"{section}.{option}")
        
        if missing_settings:
            raise ValueError(
                f"Fehlende erforderliche Einstellungen in '{self.config_file}': "
                f"{', '.join(missing_settings)}"
            )
    
    def get(self, section: str, option: str, fallback: Any = None) -> str:
        """
        Ruft einen Wert aus der Konfiguration ab.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die Option im Abschnitt
            fallback: Standardwert, falls die Option nicht existiert
            
        Returns:
            str: Der Wert aus der Konfiguration oder der Fallback-Wert
        """
        if self.has_option(section, option):
            return self.config.get(section, option)
        return fallback
    
    def getint(self, section: str, option: str, fallback: int = None) -> int:
        """
        Ruft einen Integer-Wert aus der Konfiguration ab.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die Option im Abschnitt
            fallback: Standardwert, falls die Option nicht existiert
            
        Returns:
            int: Der Integer-Wert aus der Konfiguration oder der Fallback-Wert
        """
        if self.has_option(section, option):
            return self.config.getint(section, option)
        return fallback
    
    def getfloat(self, section: str, option: str, fallback: float = None) -> float:
        """
        Ruft einen Float-Wert aus der Konfiguration ab.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die Option im Abschnitt
            fallback: Standardwert, falls die Option nicht existiert
            
        Returns:
            float: Der Float-Wert aus der Konfiguration oder der Fallback-Wert
        """
        if self.has_option(section, option):
            return self.config.getfloat(section, option)
        return fallback
    
    def getboolean(self, section: str, option: str, fallback: bool = None) -> bool:
        """
        Ruft einen Boolean-Wert aus der Konfiguration ab.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die Option im Abschnitt
            fallback: Standardwert, falls die Option nicht existiert
            
        Returns:
            bool: Der Boolean-Wert aus der Konfiguration oder der Fallback-Wert
        """
        if self.has_option(section, option):
            return self.config.getboolean(section, option)
        return fallback
    
    def getlist(self, section: str, option: str, fallback: List = None, delimiter: str = ',') -> List[str]:
        """
        Ruft eine Liste aus der Konfiguration ab.
        Die Liste wird als durch Komma getrennte Werte gespeichert.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die Option im Abschnitt
            fallback: Standardwert, falls die Option nicht existiert
            delimiter: Trennzeichen für die Liste (Standard: Komma)
            
        Returns:
            List[str]: Liste von Werten aus der Konfiguration oder der Fallback-Wert
        """
        if self.has_option(section, option):
            value = self.get(section, option)
            if value:
                return [item.strip() for item in value.split(delimiter)]
            return []
        return fallback if fallback is not None else []
    
    def has_section(self, section: str) -> bool:
        """
        Überprüft, ob ein Abschnitt in der Konfiguration existiert.
        
        Args:
            section: Der zu überprüfende Abschnitt
            
        Returns:
            bool: True, wenn der Abschnitt existiert, sonst False
        """
        return self.config.has_section(section)
    
    def has_option(self, section: str, option: str) -> bool:
        """
        Überprüft, ob eine Option in einem Abschnitt der Konfiguration existiert.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die zu überprüfende Option
            
        Returns:
            bool: True, wenn die Option existiert, sonst False
        """
        return self.config.has_section(section) and self.config.has_option(section, option)
    
    def set(self, section: str, option: str, value: Any) -> None:
        """
        Setzt einen Wert in der Konfiguration.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            option: Die Option im Abschnitt
            value: Der zu setzende Wert
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, option, str(value))
    
    def save(self, config_file: str = None) -> None:
        """
        Speichert die Konfiguration in einer Datei.
        
        Args:
            config_file: Pfad zur Zieldatei (Standard: Datei, aus der geladen wurde)
            
        Raises:
            IOError: Bei Fehlern beim Schreiben der Datei.
        """
        if not config_file:
            config_file = self.config_file
        
        try:
            with open(config_file, 'w') as file:
                self.config.write(file)
        except IOError as e:
            raise IOError(f"Fehler beim Speichern der Konfiguration in '{config_file}': {str(e)}")
    
    def get_all_sections(self) -> List[str]:
        """
        Gibt alle Abschnitte der Konfiguration zurück.
        
        Returns:
            List[str]: Liste aller Abschnitte
        """
        return self.config.sections()
    
    def get_section_options(self, section: str) -> List[str]:
        """
        Gibt alle Optionen eines Abschnitts zurück.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            
        Returns:
            List[str]: Liste aller Optionen im Abschnitt oder leere Liste, wenn der Abschnitt nicht existiert
        """
        if self.has_section(section):
            return list(self.config[section].keys())
        return []
    
    def get_section_dict(self, section: str) -> Dict[str, str]:
        """
        Gibt alle Optionen und Werte eines Abschnitts als Dictionary zurück.
        
        Args:
            section: Der Abschnitt in der Konfigurationsdatei
            
        Returns:
            Dict[str, str]: Dictionary mit Optionen und Werten oder leeres Dictionary, wenn der Abschnitt nicht existiert
        """
        if self.has_section(section):
            return dict(self.config[section])
        return {}
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validiert die gesamte Konfiguration auf Richtigkeit und Konsistenz.
        
        Returns:
            Tuple[bool, List[str]]: (Ist gültig, Liste von Fehlermeldungen)
        """
        is_valid = True
        errors = []
        
        # Validiere StashApp-Einstellungen
        if not self.get('StashApp', 'url', '').strip():
            is_valid = False
            errors.append("StashApp.url darf nicht leer sein.")
        
        if not self.get('StashApp', 'api_key', '').strip():
            is_valid = False
            errors.append("StashApp.api_key darf nicht leer sein.")
        
        # Validiere Ausgabeverzeichnisse
        output_dir = self.get('Output', 'output_dir', '')
        if output_dir and not os.path.isabs(output_dir):
            # Relativer Pfad, überprüfe auf ungültige Zeichen
            invalid_chars = '<>:"|?*'
            if any(char in output_dir for char in invalid_chars):
                is_valid = False
                errors.append(f"Output.output_dir enthält ungültige Zeichen: {invalid_chars}")
        
        # Validiere Zahlenwerte
        numeric_settings = [
            ('Recommendations', 'min_similarity_score', 0.0, 1.0),
            ('Recommendations', 'max_recommendations', 1, 100),
            ('Recommendations', 'weight_cup_size', 0.0, 1.0),
            ('Recommendations', 'bmi_cup_size', 0.0, 1.0),
            ('Recommendations', 'height_cup_size', 0.0, 1.0),
            ('Statistics', 'min_data_points', 1, 100),
            ('Statistics', 'confidence_interval', 0.0, 1.0),
            ('Visualization', 'image_dpi', 72, 1200),
            ('Discord', 'max_recommendations_per_message', 1, 20),
            ('BoobPedia', 'request_timeout', 1, 60),
            ('BoobPedia', 'request_delay', 0, 10),
        ]
        
        for section, option, min_val, max_val in numeric_settings:
            if self.has_option(section, option):
                try:
                    val = self.getfloat(section, option)
                    if val < min_val or val > max_val:
                        is_valid = False
                        errors.append(f"{section}.{option} muss zwischen {min_val} und {max_val} liegen.")
                except ValueError:
                    is_valid = False
                    errors.append(f"{section}.{option} muss eine Zahl sein.")
        
        # Validiere Webhook-URL
        if self.getboolean('Discord', 'enable_discord', False):
            webhook_url = self.get('Discord', 'webhook_url', '')
            if not webhook_url.startswith('https://discord.com/api/webhooks/'):
                is_valid = False
                errors.append("Discord.webhook_url muss eine gültige Discord-Webhook-URL sein.")
        
        return is_valid, errors

# Globale Hilfsfunktion zum einfachen Laden der Konfiguration
def load_config(config_file: str = 'configuration.ini') -> ConfigManager:
    """
    Lädt die Konfiguration aus einer Datei.
    
    Args:
        config_file: Pfad zur Konfigurationsdatei
        
    Returns:
        ConfigManager: Eine Instanz des ConfigManagers mit geladener Konfiguration
        
    Raises:
        FileNotFoundError: Wenn die Konfigurationsdatei nicht gefunden wird.
        configparser.Error: Bei Fehlern beim Parsen der Konfigurationsdatei.
    """
    return ConfigManager(config_file)
