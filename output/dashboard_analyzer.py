"""
Dashboard Analyzer Module

Dieses Modul enthält Funktionen zur Analyse von Nutzerverhaltens- und 
Sehgewohnheitsdaten in der StashApp-Datenbank. Es wird vom
Dashboard-System genutzt, um Vorhersagen und Einblicke zu generieren.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter

# Logger konfigurieren
logger = logging.getLogger(__name__)

class UserBehaviorAnalyzer:
    """
    Klasse zur Analyse des Nutzungsverhaltens und der Sehgewohnheiten.
    
    Diese Klasse analysiert Nutzerdaten und Sehhistorien, um Muster
    zu erkennen und Nutzer in Gruppen einzuteilen.
    """
    
    def __init__(self, user_data: pd.DataFrame, viewing_history: pd.DataFrame):
        """
        Initialisiert den Analyzer mit Nutzerdaten und Sehhistorie.
        
        Args:
            user_data: DataFrame mit Nutzerdaten
            viewing_history: DataFrame mit Nutzungshistorie
        """
        self.user_data = user_data
        self.viewing_history = viewing_history
        self.usage_patterns = None
        self.user_segments = None
        
        logger.info("UserBehaviorAnalyzer initialisiert")
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analysiert Nutzungsmuster in der Sehhistorie.
        
        Returns:
            Dict[str, Any]: Dictionary mit erkannten Mustern
        """
        if self.usage_patterns is not None:
            return self.usage_patterns
        
        # Prüfe, ob ausreichend Daten vorhanden sind
        if self.viewing_history.empty:
            logger.warning("Keine Sehhistorie für die Analyse verfügbar")
            return {}
        
        logger.info("Analysiere Nutzungsmuster...")
        
        try:
            # Stelle sicher, dass das Datum im richtigen Format vorliegt
            self.viewing_history['timestamp'] = pd.to_datetime(self.viewing_history['timestamp'])
            
            # --- Zeitliche Muster ---
            # Füge Zeitkomponenten hinzu
            self.viewing_history['hour'] = self.viewing_history['timestamp'].dt.hour
            self.viewing_history['day_of_week'] = self.viewing_history['timestamp'].dt.dayofweek
            self.viewing_history['month'] = self.viewing_history['timestamp'].dt.month
            
            # Zähle pro Stunde
            hourly_distribution = self.viewing_history.groupby('hour').size().to_dict()
            
            # Zähle pro Wochentag
            weekday_distribution = self.viewing_history.groupby('day_of_week').size().to_dict()
            # Konvertiere numerische Wochentage in Namen
            weekday_names = {
                0: 'Montag', 1: 'Dienstag', 2: 'Mittwoch', 3: 'Donnerstag', 
                4: 'Freitag', 5: 'Samstag', 6: 'Sonntag'
            }
            weekday_distribution_named = {
                weekday_names[day]: count 
                for day, count in weekday_distribution.items()
            }
            
            # --- Content-bezogene Muster ---
            # Meistgesehene Content-Arten (falls verfügbar)
            content_type_distribution = {}
            if 'content_id' in self.viewing_history.columns and 'content_type' in self.viewing_history.columns:
                content_type_distribution = self.viewing_history.groupby('content_type').size().to_dict()
            
            # --- Meistgesehene Elemente ---
            top_content = []
            if 'content_id' in self.viewing_history.columns:
                # Zähle die Häufigkeit jeder Content-ID
                content_counts = self.viewing_history['content_id'].value_counts().head(10)
                top_content = [
                    {"content_id": content_id, "count": count}
                    for content_id, count in content_counts.items()
                ]
            
            # --- Berechnete Statistiken ---
            session_stats = self._calculate_session_statistics()
            
            # --- Wachstumstrends ---
            growth_trends = self._calculate_growth_trends()
            
            # Ergebnisse speichern
            self.usage_patterns = {
                "hourly_distribution": hourly_distribution,
                "weekday_distribution": weekday_distribution_named,
                "content_type_distribution": content_type_distribution,
                "top_content": top_content,
                "session_stats": session_stats,
                "growth_trends": growth_trends
            }
            
            logger.info("Nutzungsmusteranalyse abgeschlossen")
            return self.usage_patterns
            
        except Exception as e:
            logger.error(f"Fehler bei der Analyse der Nutzungsmuster: {str(e)}", exc_info=True)
            return {}
    
    def _calculate_session_statistics(self) -> Dict[str, Any]:
        """
        Berechnet Statistiken für Nutzungssitzungen.
        
        Returns:
            Dict[str, Any]: Sitzungsstatistiken
        """
        try:
            # Sortiere nach Nutzer und Zeitstempel
            sorted_history = self.viewing_history.sort_values(['user_id', 'timestamp'])
            
            # Definiere Schwellenwert für neue Sitzung (z.B. 30 Minuten)
            session_threshold = pd.Timedelta(minutes=30)
            
            # Identifiziere Sitzungen
            sorted_history['prev_timestamp'] = sorted_history.groupby('user_id')['timestamp'].shift(1)
            sorted_history['time_diff'] = sorted_history['timestamp'] - sorted_history['prev_timestamp']
            sorted_history['new_session'] = (sorted_history['time_diff'] > session_threshold) | (sorted_history['prev_timestamp'].isna())
            sorted_history['session_id'] = sorted_history['new_session'].cumsum()
            
            # Berechne Sitzungsdauern
            session_durations = sorted_history.groupby(['user_id', 'session_id']).agg({
                'timestamp': ['min', 'max']
            })
            
            session_durations['duration'] = session_durations[('timestamp', 'max')] - session_durations[('timestamp', 'min')]
            session_durations['duration_minutes'] = session_durations['duration'].dt.total_seconds() / 60
            
            # Statistiken berechnen
            avg_session_duration = session_durations['duration_minutes'].mean()
            median_session_duration = session_durations['duration_minutes'].median()
            max_session_duration = session_durations['duration_minutes'].max()
            
            # Anzahl der Inhalte pro Sitzung
            content_per_session = sorted_history.groupby(['user_id', 'session_id']).size()
            avg_content_per_session = content_per_session.mean()
            
            return {
                "avg_session_duration_minutes": round(float(avg_session_duration), 2) if not pd.isna(avg_session_duration) else None,
                "median_session_duration_minutes": round(float(median_session_duration), 2) if not pd.isna(median_session_duration) else None,
                "max_session_duration_minutes": round(float(max_session_duration), 2) if not pd.isna(max_session_duration) else None,
                "avg_content_per_session": round(float(avg_content_per_session), 2) if not pd.isna(avg_content_per_session) else None,
                "total_sessions": len(session_durations)
            }
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung der Sitzungsstatistiken: {str(e)}")
            return {}
    
    def _calculate_growth_trends(self) -> Dict[str, Any]:
        """
        Berechnet Wachstumstrends basierend auf der Sehhistorie.
        
        Returns:
            Dict[str, Any]: Wachstumstrends
        """
        try:
            # Stelle sicher, dass timestamp im Datetime-Format vorliegt
            self.viewing_history['timestamp'] = pd.to_datetime(self.viewing_history['timestamp'])
            
            # Erstelle wöchentliche Aggregate
            self.viewing_history['week'] = self.viewing_history['timestamp'].dt.isocalendar().week
            self.viewing_history['year'] = self.viewing_history['timestamp'].dt.isocalendar().year
            weekly_counts = self.viewing_history.groupby(['year', 'week']).size().reset_index(name='count')
            
            # Konvertiere zu DataFrame mit ordentlichem Index für Zeitreihenanalyse
            weekly_counts['date'] = weekly_counts.apply(
                lambda row: datetime.strptime(f"{row['year']}-{row['week']}-1", "%G-%V-%u"), 
                axis=1
            )
            weekly_counts.set_index('date', inplace=True)
            weekly_counts.sort_index(inplace=True)
            
            # Berechne gleitenden Durchschnitt
            if len(weekly_counts) >= 4:
                weekly_counts['rolling_avg'] = weekly_counts['count'].rolling(window=4).mean()
            
            # Berechne Wachstumsrate
            if len(weekly_counts) > 1:
                # Prozentuale Änderung von Woche zu Woche
                weekly_counts['growth_pct'] = weekly_counts['count'].pct_change() * 100
                
                # Durchschnittliches Wachstum über die letzten 4 Wochen (falls genug Daten)
                recent_growth = weekly_counts['growth_pct'].tail(4).mean() if len(weekly_counts) >= 4 else weekly_counts['growth_pct'].mean()
                
                # Gesamtwachstum (erstes verglichen mit letztem)
                first_count = weekly_counts['count'].iloc[0]
                last_count = weekly_counts['count'].iloc[-1]
                total_growth = ((last_count - first_count) / first_count * 100) if first_count > 0 else 0
                
                growth_data = {
                    "recent_weekly_growth_pct": round(float(recent_growth), 2) if not pd.isna(recent_growth) else None,
                    "total_growth_pct": round(float(total_growth), 2) if not pd.isna(total_growth) else None,
                    "weeks_analyzed": len(weekly_counts)
                }
            else:
                # Nicht genug Daten für Wachstumsanalyse
                growth_data = {
                    "recent_weekly_growth_pct": None,
                    "total_growth_pct": None,
                    "weeks_analyzed": len(weekly_counts)
                }
            
            return growth_data
            
        except Exception as e:
            logger.error(f"Fehler bei der Berechnung der Wachstumstrends: {str(e)}")
            return {}
    
    def segment_users(self, segment_count: int = 3) -> Dict[str, Any]:
        """
        Segmentiert Nutzer basierend auf ihrem Verhalten in verschiedene Gruppen.
        
        Args:
            segment_count: Anzahl der zu bildenden Segmente
            
        Returns:
            Dict[str, Any]: Nutzersegmente und deren Eigenschaften
        """
        if self.user_segments is not None:
            return self.user_segments
        
        if self.viewing_history.empty or 'user_id' not in self.viewing_history.columns:
            logger.warning("Keine ausreichenden Daten für die Nutzersegmentierung verfügbar")
            return {}
        
        logger.info(f"Segmentiere Nutzer in {segment_count} Gruppen...")
        
        try:
            # Aggregiere Nutzungsdaten pro Nutzer
            user_features = self.viewing_history.groupby('user_id').agg({
                'timestamp': ['count', 'min', 'max']  # Anzahl der Views, erste und letzte View
            }).reset_index()
            
            # Spalten umbenennen für klarere Struktur
            user_features.columns = ['user_id', 'view_count', 'first_view', 'last_view']
            
            # Zusätzliche Features berechnen
            user_features['days_active'] = (user_features['last_view'] - user_features['first_view']).dt.days + 1
            user_features['views_per_day'] = user_features['view_count'] / user_features['days_active'].clip(lower=1)
            
            # Wenn vorhanden, füge weitere Features hinzu (z.B. bevorzugte Content-Typen)
            if 'content_type' in self.viewing_history.columns:
                # Finde den am häufigsten angesehenen Content-Typ pro Nutzer
                user_preferred_types = self.viewing_history.groupby(['user_id', 'content_type']).size().reset_index(name='type_count')
                user_preferred_types = user_preferred_types.sort_values(['user_id', 'type_count'], ascending=[True, False])
                user_preferred_types = user_preferred_types.drop_duplicates('user_id')
                
                # Füge als Feature hinzu
                user_features = user_features.merge(
                    user_preferred_types[['user_id', 'content_type']], 
                    on='user_id', 
                    how='left'
                )
                
                # Konvertiere zu numerischem Feature (für clustering)
                user_features['content_type_numeric'] = pd.factorize(user_features['content_type'])[0]
            
            # Vorbereitung für Clustering: Auswahl der numerischen Features
            clustering_features = ['view_count', 'days_active', 'views_per_day']
            if 'content_type_numeric' in user_features.columns:
                clustering_features.append('content_type_numeric')
            
            X = user_features[clustering_features].copy()
            
            # Behandle NaN-Werte
            X.fillna(X.mean(), inplace=True)
            
            # Feature-Skalierung für besseres Clustering
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Clustering durchführen
            if len(X) >= segment_count:
                kmeans = KMeans(n_clusters=segment_count, random_state=42, n_init=10)
                user_features['segment'] = kmeans.fit_predict(X_scaled)
                
                # Segmentbeschreibungen erstellen
                segment_profiles = {}
                for segment_id in range(segment_count):
                    segment_data = user_features[user_features['segment'] == segment_id]
                    
                    profile = {
                        "count": len(segment_data),
                        "percentage": round(len(segment_data) / len(user_features) * 100, 2),
                        "avg_views": round(float(segment_data['view_count'].mean()), 2),
                        "avg_days_active": round(float(segment_data['days_active'].mean()), 2),
                        "avg_views_per_day": round(float(segment_data['views_per_day'].mean()), 2)
                    }
                    
                    # Bevorzugte Content-Typen, falls verfügbar
                    if 'content_type' in segment_data.columns:
                        top_types = segment_data['content_type'].value_counts().head(3).to_dict()
                        profile["top_content_types"] = top_types
                    
                    # Interpretiere das Segment
                    segment_label = self._interpret_segment(profile)
                    profile["label"] = segment_label
                    
                    segment_profiles[f"segment_{segment_id}"] = profile
                
                self.user_segments = {
                    "segment_count": segment_count,
                    "user_count": len(user_features),
                    "segments": segment_profiles
                }
                
                return self.user_segments
            else:
                logger.warning(f"Zu wenige Nutzer ({len(X)}) für {segment_count} Segmente")
                return {
                    "segment_count": 1,
                    "user_count": len(user_features),
                    "segments": {
                        "segment_0": {
                            "count": len(user_features),
                            "percentage": 100.0,
                            "avg_views": round(float(user_features['view_count'].mean()), 2),
                            "avg_days_active": round(float(user_features['days_active'].mean()), 2),
                            "avg_views_per_day": round(float(user_features['views_per_day'].mean()), 2),
                            "label": "Alle Nutzer"
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Fehler bei der Nutzersegmentierung: {str(e)}", exc_info=True)
            return {}
    
    def _interpret_segment(self, profile: Dict[str, Any]) -> str:
        """
        Interpretiert ein Nutzersegment und gibt ihm einen beschreibenden Namen.
        
        Args:
            profile: Profil-Dictionary mit Segmenteigenschaften
            
        Returns:
            str: Beschreibender Name für das Segment
        """
        avg_views = profile.get("avg_views", 0)
        avg_views_per_day = profile.get("avg_views_per_day", 0)
        avg_days_active = profile.get("avg_days_active", 0)
        
        # Bestimme die Aktivität
        if avg_views_per_day >= 3:
            activity_level = "Hochaktive"
        elif avg_views_per_day >= 1:
            activity_level = "Regelmäßige"
        elif avg_views_per_day >= 0.2:
            activity_level = "Gelegentliche"
        else:
            activity_level = "Seltene"
        
        # Bestimme die Treue
        if avg_days_active >= 60:
            loyalty = "Treue"
        elif avg_days_active >= 30:
            loyalty = "Wiederkehrende"
        elif avg_days_active >= 7:
            loyalty = "Neue"
        else:
            loyalty = "Einmalige"
        
        return f"{activity_level} {loyalty} Nutzer"
