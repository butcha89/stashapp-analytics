"""
Visualization Performer Module

Dieses Modul ist verantwortlich für die Erstellung von Visualisierungen und Diagrammen
für Performer-bezogene Daten. Es erstellt Visualisierungen zu Cup-Größen, BMI-Werten,
Altersverteilungen und Bewertungen der Performer.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Interner Import
from core.data_models import Performer
from analysis.visualization_core import VisualizationCore

# Logger konfigurieren
logger = logging.getLogger(__name__)

class PerformerVisualization:
    """
    Klasse zur Erstellung von Performer-bezogenen Visualisierungen.
    
    Diese Klasse erstellt verschiedene Diagramme und Visualisierungen
    für Performer-Daten wie Cup-Größen, BMI, Alter und Bewertungen.
    """
    
    def __init__(self, core: VisualizationCore):
        """
        Initialisiert das Performer-Visualisierungsmodul.
        
        Args:
            core: VisualizationCore-Instanz mit gemeinsamen Funktionen und Konfigurationen
        """
        self.core = core
        self.stats_module = core.stats_module
        self.api = core.api
        self.config = core.config
        logger.info("Performer-Visualisierungsmodul initialisiert")
    
    def create_cup_size_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen für Cup-Größen-Statistiken.
        
        Erzeugt folgende Visualisierungen:
        - Balkendiagramm der Cup-Größen-Verteilung
        - Kuchendiagramm der Cup-Größen-Verteilung
        - Interaktives Balkendiagramm der Cup-Größen-Verteilung
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Cup-Größen-Visualisierungen...")
        visualizations = []
        
        # Überprüfe, ob Cup-Größen-Statistiken verfügbar sind
        if not hasattr(self.stats_module, 'performer_stats') or not self.stats_module.performer_stats:
            logger.warning("Keine Performer-Statistiken verfügbar")
            return visualizations
            
        try:
            # Daten vorbereiten
            cup_distribution = self.stats_module.performer_stats.cup_distribution
            if not cup_distribution:
                logger.warning("Keine Cup-Größen-Verteilung verfügbar")
                return visualizations
                
            # Sortiere die Cup-Größen (alphanumerisch)
            sorted_cups = sorted(cup_distribution.keys(), key=lambda x: (len(x), x))
            counts = [cup_distribution[cup] for cup in sorted_cups]
            
            # Erstelle das Balkendiagramm
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            bars = ax.bar(sorted_cups, counts, color=self.core.palettes['categorical'])
            
            # Beschriftungen hinzufügen
            self.core.format_axes(ax, 
                                 title='Verteilung der Cup-Größen', 
                                 xlabel='Cup-Größe', 
                                 ylabel='Anzahl')
            
            # Zahlen über den Balken
            self.core.add_value_labels(ax, bars)
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "cup_size_distribution")
            if path:
                visualizations.append(path)
            
            # Erstelle ein Kuchendiagramm für die Cup-Größen
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            # Berechne Prozentsätze
            total = sum(counts)
            percentages = [count / total * 100 for count in counts]
            
            # Kuchendiagramm mit Prozentangaben
            patches, texts, autotexts = ax.pie(counts, labels=sorted_cups, autopct='%1.1f%%',
                                              colors=self.core.palettes['pastel'], startangle=90)
            
            # Formatierung
            for text in texts:
                text.set_fontsize(self.core.label_fontsize)
            for autotext in autotexts:
                autotext.set_fontsize(self.core.label_fontsize - 2)
                autotext.set_color('black')  # Ändern von 'white' zu 'black' für bessere Lesbarkeit
            
            ax.set_title('Prozentuale Verteilung der Cup-Größen', fontsize=self.core.title_fontsize)
            ax.axis('equal')  # Sorgt für ein kreisförmiges Diagramm
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "cup_size_pie_chart")
            if path:
                visualizations.append(path)
            
            # Erstelle interaktives Balkendiagramm für Cup-Größen, wenn interaktiv aktiviert
            if self.core.interactive_mode:
                try:
                    # Interaktives Plotly-Diagramm für Cup-Größen
                    df = pd.DataFrame({
                        'Cup-Größe': sorted_cups,
                        'Anzahl': counts,
                        'Prozent': percentages
                    })
                    
                    fig = px.bar(df, x='Cup-Größe', y='Anzahl', text='Anzahl',
                                color='Cup-Größe', color_discrete_sequence=px.colors.qualitative.Pastel)
                    
                    fig.update_layout(
                        title='Interaktive Darstellung der Cup-Größen-Verteilung',
                        xaxis_title='Cup-Größe',
                        yaxis_title='Anzahl',
                        height=600,
                        width=900
                    )
                    
                    path = self.core.save_plotly_figure(fig, "cup_size_interactive")
                    if path:
                        visualizations.append(path)
                    
                    # Erstelle interaktives Kuchendiagramm
                    fig = px.pie(df, values='Anzahl', names='Cup-Größe', 
                                title='Interaktive Darstellung der Cup-Größen-Verteilung')
                    
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(
                        height=600,
                        width=800
                    )
                    
                    path = self.core.save_plotly_figure(fig, "cup_size_pie_interactive")
                    if path:
                        visualizations.append(path)
                except Exception as e:
                    logger.warning(f"Fehler bei der Erstellung der interaktiven Cup-Größen-Diagramme: {str(e)}")
            
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Cup-Größen-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_bmi_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen für BMI-Statistiken.
        
        Erzeugt folgende Visualisierungen:
        - Balkendiagramm der BMI-Kategorien
        - Histogramm der BMI-Verteilung
        - Streudiagramm BMI vs. Cup-Größe
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle BMI-Visualisierungen...")
        visualizations = []
        
        # Überprüfe, ob genügend Performer mit BMI-Daten verfügbar sind
        performers_with_bmi = [p for p in self.stats_module.performers if p.bmi is not None]
        if len(performers_with_bmi) < 5:
            logger.warning(f"Zu wenige Performer mit BMI-Daten ({len(performers_with_bmi)}). Mindestens 5 benötigt.")
            return visualizations
        
        try:
            # BMI-Kategorien-Verteilung
            bmi_categories = self.stats_module.performer_stats.bmi_distribution
            if not bmi_categories:
                logger.warning("Keine BMI-Kategorien-Verteilung verfügbar")
                return visualizations
            
            # Sortiere die BMI-Kategorien
            category_order = ["Untergewicht", "Normalgewicht", "Übergewicht", "Adipositas"]
            sorted_categories = sorted(bmi_categories.keys(), key=lambda x: category_order.index(x) if x in category_order else 999)
            counts = [bmi_categories[cat] for cat in sorted_categories]
            
            # Erstelle das Balkendiagramm
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            # Wähle passende Farben für BMI-Kategorien
            custom_colors = []
            for cat in sorted_categories:
                if cat == "Untergewicht":
                    custom_colors.append("#FFC107")  # Gelb
                elif cat == "Normalgewicht":
                    custom_colors.append("#4CAF50")  # Grün
                elif cat == "Übergewicht":
                    custom_colors.append("#FF9800")  # Orange
                elif cat == "Adipositas":
                    custom_colors.append("#F44336")  # Rot
                else:
                    custom_colors.append("#2196F3")  # Blau (Fallback)
            
            bars = ax.bar(sorted_categories, counts, color=custom_colors)
            
            # Beschriftungen hinzufügen
            self.core.format_axes(ax, 
                                 title='Verteilung der BMI-Kategorien', 
                                 xlabel='BMI-Kategorie', 
                                 ylabel='Anzahl')
            
            # Zahlen über den Balken
            self.core.add_value_labels(ax, bars)
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "bmi_category_distribution")
            if path:
                visualizations.append(path)
            
            # BMI-Histogramm (kontinuierliche Verteilung)
            bmis = [p.bmi for p in self.stats_module.performers if p.bmi is not None]
            if bmis:
                # Entferne Ausreißer für ein besseres Histogramm
                filtered_bmis = self.core.filter_outliers(bmis, method='IQR', threshold=2.0)
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                # Histogramm mit KDE (Kerndichteschätzung)
                sns.histplot(filtered_bmis, kde=True, ax=ax, bins=20, color=self.core.palettes['categorical'][0])
                
                # Markiere BMI-Grenzen
                bmi_boundaries = [18.5, 25, 30]
                boundary_labels = ['Untergewicht', 'Normalgewicht', 'Übergewicht', 'Adipositas']
                boundary_colors = ['#FFC107', '#4CAF50', '#FF9800', '#F44336']
                
                for i, bmi in enumerate(bmi_boundaries):
                    ax.axvline(x=bmi, color=boundary_colors[i], linestyle='--', alpha=0.7)
                
                # Füge Bereichslabels hinzu
                y_pos = ax.get_ylim()[1] * 0.9
                x_positions = [18.5/2, (18.5+25)/2, (25+30)/2, (30+max(filtered_bmis))/2]
                
                for i, (x, label) in enumerate(zip(x_positions, boundary_labels)):
                    ax.text(x, y_pos, label, ha='center', va='center', 
                           color=boundary_colors[i], fontsize=self.core.label_fontsize - 2,
                           bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.3'))
                
                # Beschriftungen hinzufügen
                self.core.format_axes(ax, 
                                     title='BMI-Verteilung', 
                                     xlabel='BMI', 
                                     ylabel='Anzahl')
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "bmi_distribution_histogram")
                if path:
                    visualizations.append(path)
                
                # Korrelation zwischen BMI und Cup-Größe
                cup_sizes = [p.cup_numeric for p in self.stats_module.performers 
                           if p.cup_numeric > 0 and p.bmi is not None]
                bmis_with_cup = [p.bmi for p in self.stats_module.performers 
                               if p.cup_numeric > 0 and p.bmi is not None]
                
                # Prüfen, ob genügend Daten für eine sinnvolle Korrelation vorhanden sind
                if len(cup_sizes) >= 10 and len(bmis_with_cup) >= 10 and len(cup_sizes) == len(bmis_with_cup):
                    # Filter extreme Ausreißer
                    valid_data = [(bmi, cup) for bmi, cup in zip(bmis_with_cup, cup_sizes) 
                                 if bmi > 10 and bmi < 50]  # Realistischer BMI-Bereich
                    
                    if len(valid_data) >= 10:
                        filtered_bmis = [d[0] for d in valid_data]
                        filtered_cups = [d[1] for d in valid_data]
                        
                        fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                        
                        # Scatterplot mit Regression
                        sns.regplot(x=filtered_bmis, y=filtered_cups, scatter_kws={'alpha':0.5}, 
                                   line_kws={'color': 'red'}, ax=ax)
                        
                        # Beschriftungen hinzufügen
                        self.core.format_axes(ax, 
                                             title='Korrelation: BMI vs. Cup-Größe', 
                                             xlabel='BMI', 
                                             ylabel='Cup-Größe (numerisch)')
                        
                        # Y-Achse mit Cup-Buchstaben beschriften
                        y_ticks = range(1, 11)
                        ax.set_yticks(y_ticks)
                        ax.set_yticklabels([Performer.CUP_NUMERIC_TO_LETTER.get(i, "?") for i in y_ticks])
                        
                        # Diagramm speichern
                        path = self.core.save_figure(fig, "bmi_vs_cup_correlation")
                        if path:
                            visualizations.append(path)
                    
                    # Interaktives Plotly-Streudiagramm
                    if self.core.interactive_mode:
                        df = pd.DataFrame({
                            'BMI': bmis_with_cup,
                            'Cup-Größe (numerisch)': cup_sizes,
                            'Cup-Größe': [Performer.CUP_NUMERIC_TO_LETTER.get(i, "?") for i in cup_sizes]
                        })
                        
                        fig = px.scatter(df, x='BMI', y='Cup-Größe (numerisch)', color='Cup-Größe',
                                        trendline='ols', trendline_color_override='red',
                                        color_discrete_sequence=px.colors.qualitative.Pastel)
                        
                        fig.update_layout(
                            title='Interaktiver Scatterplot: BMI vs. Cup-Größe',
                            xaxis_title='BMI',
                            yaxis_title='Cup-Größe (numerisch)',
                            height=600,
                            width=900
                        )
                        
                        # Y-Achse mit Cup-Buchstaben beschriften
                        fig.update_yaxes(
                            tickvals=list(range(1, 11)),
                            ticktext=[Performer.CUP_NUMERIC_TO_LETTER.get(i, "?") for i in range(1, 11)]
                        )
                        
                        path = self.core.save_plotly_figure(fig, "bmi_vs_cup_interactive")
                        if path:
                            visualizations.append(path)
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der BMI-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_age_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen für Alters-Statistiken.
        
        Erzeugt folgende Visualisierungen:
        - Balkendiagramm der Altersgruppen
        - Histogramm der Altersverteilung
        - Streudiagramm Alter vs. Cup-Größe
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Alters-Visualisierungen...")
        visualizations = []
        
        # Überprüfe, ob Alters-Statistiken verfügbar sind
        if not hasattr(self.stats_module, 'age_groups') or not self.stats_module.age_groups:
            logger.warning("Keine Alters-Statistiken verfügbar")
            return visualizations
        
        try:
            # Altersgruppen-Verteilung
            age_distribution = self.stats_module.performer_stats.age_distribution
            if not age_distribution:
                return visualizations
            
            # Sortiere die Altersgruppen (nach erster Zahl im Bereich)
            def sort_key(age_range):
                return int(age_range.split('-')[0]) if '-' in age_range else 100
                
            sorted_age_groups = sorted(age_distribution.keys(), key=sort_key)
            counts = [age_distribution[group] for group in sorted_age_groups]
            
            # Erstelle das Balkendiagramm
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            bars = ax.bar(sorted_age_groups, counts, color=self.core.palettes['age'])
            
            # Beschriftungen hinzufügen
            self.core.format_axes(ax, 
                                 title='Verteilung der Altersgruppen', 
                                 xlabel='Altersgruppe', 
                                 ylabel='Anzahl')
            
            # Zahlen über den Balken
            self.core.add_value_labels(ax, bars)
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "age_group_distribution")
            if path:
                visualizations.append(path)
            
            # Alters-Histogramm (kontinuierliche Verteilung)
            ages = [p.age for p in self.stats_module.performers if p.age is not None]
            if ages:
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                # Histogramm mit KDE (Kerndichteschätzung)
                sns.histplot(ages, kde=True, ax=ax, bins=20, color=self.core.palettes['categorical'][1])
                
                # Beschriftungen hinzufügen
                self.core.format_axes(ax, 
                                     title='Altersverteilung', 
                                     xlabel='Alter', 
                                     ylabel='Anzahl')
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "age_distribution_histogram")
                if path:
                    visualizations.append(path)
                
                # Korrelation zwischen Alter und Cup-Größe
                cup_sizes = [p.cup_numeric for p in self.stats_module.performers 
                           if p.cup_numeric > 0 and p.age is not None]
                ages_with_cup = [p.age for p in self.stats_module.performers 
                               if p.cup_numeric > 0 and p.age is not None]
                
                if cup_sizes and ages_with_cup and len(cup_sizes) == len(ages_with_cup):
                    fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                    
                    # Scatterplot mit Regression
                    sns.regplot(x=ages_with_cup, y=cup_sizes, scatter_kws={'alpha':0.5}, ax=ax)
                    
                    # Beschriftungen hinzufügen
                    self.core.format_axes(ax, 
                                         title='Korrelation: Alter vs. Cup-Größe', 
                                         xlabel='Alter', 
                                         ylabel='Cup-Größe (numerisch)')
                    
                    # Y-Achse mit Cup-Buchstaben beschriften
                    y_ticks = range(1, 11)
                    ax.set_yticks(y_ticks)
                    ax.set_yticklabels([Performer.CUP_NUMERIC_TO_LETTER.get(i, "?") for i in y_ticks])
                    
                    # Diagramm speichern
                    path = self.core.save_figure(fig, "age_vs_cup_correlation")
                    if path:
                        visualizations.append(path)
                    
                    # Durchschnittliches Alter nach Cup-Größe
                    age_by_cup = {}
                    for p in self.stats_module.performers:
                        if p.cup_numeric > 0 and p.age is not None:
                            cup = p.cup_size
                            if cup not in age_by_cup:
                                age_by_cup[cup] = []
                            age_by_cup[cup].append(p.age)
                    
                    avg_age_by_cup = {cup: sum(ages) / len(ages) for cup, ages in age_by_cup.items() if ages}
                    
                    if avg_age_by_cup:
                        # Sortiere nach Cup-Größe
                        sorted_cups = sorted(avg_age_by_cup.keys(), key=lambda x: (len(x), x))
                        avg_ages = [avg_age_by_cup[cup] for cup in sorted_cups]
                        
                        fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                        
                        bars = ax.bar(sorted_cups, avg_ages, color=self.core.palettes['age'])
                        
                        # Beschriftungen
                        self.core.format_axes(ax, 
                                             title='Durchschnittsalter nach Cup-Größe', 
                                             xlabel='Cup-Größe', 
                                             ylabel='Durchschnittsalter')
                        
                        # Zahlen über den Balken
                        self.core.add_value_labels(ax, bars, fmt="{:.1f}")
                        
                        # Diagramm speichern
                        path = self.core.save_figure(fig, "avg_age_by_cup")
                        if path:
                            visualizations.append(path)
                        
                        # Interaktive Version mit Plotly
                        if self.core.interactive_mode:
                            df = pd.DataFrame({
                                'Cup-Größe': sorted_cups,
                                'Durchschnittsalter': avg_ages
                            })
                            
                            fig = px.bar(df, x='Cup-Größe', y='Durchschnittsalter',
                                        color='Cup-Größe', text_auto='.1f')
                            
                            fig.update_layout(
                                title='Interaktive Darstellung: Durchschnittsalter nach Cup-Größe',
                                xaxis_title='Cup-Größe',
                                yaxis_title='Durchschnittsalter',
                                height=600,
                                width=900
                            )
                            
                            path = self.core.save_plotly_figure(fig, "avg_age_by_cup_interactive")
                            if path:
                                visualizations.append(path)
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Alters-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_rating_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen für Rating-Statistiken der Performer.
        
        Erzeugt folgende Visualisierungen:
        - Verteilung der Performer-Bewertungen
        - Durchschnittsbewertung nach Cup-Größe
        - Streudiagramm Rating vs. Cup-Größe
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Rating-Visualisierungen...")
        visualizations = []
        
        try:
            # Rating-Verteilung (Sterne)
            rating_distribution = self.stats_module.performer_stats.rating_distribution
            if rating_distribution:
                # Sortiere nach Stern-Anzahl
                sorted_ratings = sorted(rating_distribution.keys())
                counts = [rating_distribution[rating] for rating in sorted_ratings]
                
                # Erstelle das Balkendiagramm
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                bars = ax.bar([f"{r}★" for r in sorted_ratings], counts, color=self.core.palettes['ratings'])
                
                # Beschriftungen hinzufügen
                self.core.format_axes(ax, 
                                     title='Verteilung der Performer-Bewertungen', 
                                     xlabel='Bewertung', 
                                     ylabel='Anzahl')
                
                # Zahlen über den Balken
                self.core.add_value_labels(ax, bars)
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "performer_rating_distribution")
                if path:
                    visualizations.append(path)
                
                # Durchschnittliche Bewertung nach Cup-Größe
                rating_by_cup = {}
                for p in self.stats_module.performers:
                    if p.cup_numeric > 0 and p.rating100 is not None:
                        cup = p.cup_size
                        if cup not in rating_by_cup:
                            rating_by_cup[cup] = []
                        rating_by_cup[cup].append(p.rating100)
                
                avg_rating_by_cup = {cup: sum(ratings) / len(ratings) for cup, ratings in rating_by_cup.items() if ratings}
                
                if avg_rating_by_cup:
                    # Sortiere nach Cup-Größe
                    sorted_cups = sorted(avg_rating_by_cup.keys(), key=lambda x: (len(x), x))
                    avg_ratings = [avg_rating_by_cup[cup] for cup in sorted_cups]
                    
                    fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                    
                    bars = ax.bar(sorted_cups, avg_ratings, color=self.core.palettes['categorical'])
                    
                    # Beschriftungen
                    self.core.format_axes(ax, 
                                         title='Durchschnittsbewertung nach Cup-Größe', 
                                         xlabel='Cup-Größe', 
                                         ylabel='Durchschnittsbewertung (0-100)')
                    
                    # Zahlen über den Balken
                    self.core.add_value_labels(ax, bars, fmt="{:.1f}")
                    
                    # Diagramm speichern
                    path = self.core.save_figure(fig, "avg_rating_by_cup")
                    if path:
                        visualizations.append(path)
                    
                    # Interaktive Version mit Plotly
                    if self.core.interactive_mode:
                        df = pd.DataFrame({
                            'Cup-Größe': sorted_cups,
                            'Durchschnittsbewertung': avg_ratings
                        })
                        
                        fig = px.bar(df, x='Cup-Größe', y='Durchschnittsbewertung',
                                    color='Cup-Größe', text_auto='.1f')
                        
                        fig.update_layout(
                            title='Interaktive Darstellung: Durchschnittsbewertung nach Cup-Größe',
                            xaxis_title='Cup-Größe',
                            yaxis_title='Durchschnittsbewertung (0-100)',
                            height=600,
                            width=900
                        )
                        
                        path = self.core.save_plotly_figure(fig, "avg_rating_by_cup_interactive")
                        if path:
                            visualizations.append(path)
                
                # Streudiagramm: Bewertung vs. Cup-Größe
                cup_sizes = [p.cup_numeric for p in self.stats_module.performers 
                           if p.cup_numeric > 0 and p.rating100 is not None]
                ratings = [p.rating100 for p in self.stats_module.performers 
                          if p.cup_numeric > 0 and p.rating100 is not None]
                
                if cup_sizes and ratings and len(cup_sizes) == len(ratings):
                    fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                    
                    # Scatterplot mit Regression
                    sns.regplot(x=cup_sizes, y=ratings, scatter_kws={'alpha':0.5}, ax=ax)
                    
                    # Beschriftungen hinzufügen
                    self.core.format_axes(ax, 
                                         title='Korrelation: Cup-Größe vs. Bewertung', 
                                         xlabel='Cup-Größe (numerisch)', 
                                         ylabel='Bewertung (0-100)')
                    
                    # X-Achse mit Cup-Buchstaben beschriften
                    x_ticks = range(1, 11)
                    ax.set_xticks(x_ticks)
                    ax.set_xticklabels([Performer.CUP_NUMERIC_TO_LETTER.get(i, "?") for i in x_ticks])
                    
                    # Diagramm speichern
                    path = self.core.save_figure(fig, "cup_vs_rating_correlation")
                    if path:
                        visualizations.append(path)
                
            # Heatmap: Bewertung nach Altersgruppe und Cup-Größe
            rating_by_age_cup = {}
            
            for p in self.stats_module.performers:
                if p.age is not None and p.cup_size and p.rating100 is not None:
                    # Altersgruppe bestimmen
                    age_group = "46+"
                    if p.age < 26:
                        age_group = "18-25"
                    elif p.age < 31:
                        age_group = "26-30"
                    elif p.age < 36:
                        age_group = "31-35"
                    elif p.age < 41:
                        age_group = "36-40"
                    elif p.age < 46:
                        age_group = "41-45"
                    
                    key = (age_group, p.cup_size)
                    if key not in rating_by_age_cup:
                        rating_by_age_cup[key] = []
                    rating_by_age_cup[key].append(p.rating100)
            
            if rating_by_age_cup:
                # Berechne Durchschnittswerte
                avg_ratings = {key: sum(ratings) / len(ratings) for key, ratings in rating_by_age_cup.items()}
                
                # Für die Heatmap brauchen wir Altersgruppen und Cup-Größen sortiert
                age_groups = sorted(set(key[0] for key in avg_ratings.keys()), 
                                   key=lambda x: int(x.split('-')[0]) if '-' in x else 100)
                cup_sizes = sorted(set(key[1] for key in avg_ratings.keys()), 
                                  key=lambda x: (len(x), x))
                
                # Erstelle die Matrix für die Heatmap
                heatmap_data = np.zeros((len(age_groups), len(cup_sizes)))
                
                for i, age in enumerate(age_groups):
                    for j, cup in enumerate(cup_sizes):
                        if (age, cup) in avg_ratings:
                            heatmap_data[i, j] = avg_ratings[(age, cup)]
                
                # Erstelle die Heatmap
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                sns.heatmap(heatmap_data, annot=True, fmt=".1f", linewidths=.5, cmap="YlOrRd",
                           xticklabels=cup_sizes, yticklabels=age_groups, ax=ax)
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Durchschnittsbewertung nach Altersgruppe und Cup-Größe', 
                                     xlabel='Cup-Größe', 
                                     ylabel='Altersgruppe')
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "rating_by_age_cup_heatmap")
                if path:
                    visualizations.append(path)
                
                # Interaktive Version mit Plotly
                if self.core.interactive_mode:
                    # Konvertiere in Dataframe-Format für Plotly
                    heatmap_df = []
                    for i, age in enumerate(age_groups):
                        for j, cup in enumerate(cup_sizes):
                            if (age, cup) in avg_ratings:
                                heatmap_df.append({
                                    'Altersgruppe': age,
                                    'Cup-Größe': cup,
                                    'Durchschnittsbewertung': avg_ratings[(age, cup)]
                                })
                    
                    df = pd.DataFrame(heatmap_df)
                    
                    fig = px.density_heatmap(df, x='Cup-Größe', y='Altersgruppe', z='Durchschnittsbewertung',
                                           color_continuous_scale='YlOrRd')
                    
                    fig.update_layout(
                        title='Interaktive Heatmap: Bewertung nach Altersgruppe und Cup-Größe',
                        xaxis_title='Cup-Größe',
                        yaxis_title='Altersgruppe',
                        height=600,
                        width=900
                    )
                    
                    path = self.core.save_plotly_figure(fig, "rating_by_age_cup_heatmap_interactive")
                    if path:
                        visualizations.append(path)
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Rating-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_custom_visualization(self, visualization_type: str, params: Dict[str, Any] = None) -> Optional[str]:
        """
        Erstellt eine benutzerdefinierte Performer-Visualisierung.
        
        Args:
            visualization_type: Art der zu erstellenden Visualisierung
            params: Parameter für die Visualisierung
            
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        if params is None:
            params = {}
            
        logger.info(f"Erstelle benutzerdefinierte Performer-Visualisierung: {visualization_type}")
        
        try:
            # Je nach Typ an spezialisierte Methode delegieren
            if visualization_type == 'performer_top_rated':
                return self._create_top_rated_visualization(params)
            elif visualization_type == 'performer_cup_size_comparison':
                return self._create_cup_size_comparison(params)
            elif visualization_type == 'performer_attributes_radar':
                return self._create_performer_attributes_radar(params)
            elif visualization_type == 'performer_favorites_analysis':
                return self._create_favorites_analysis(params)
            else:
                logger.warning(f"Unbekannter Visualisierungstyp: {visualization_type}")
                return None
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der benutzerdefinierten Visualisierung: {str(e)}")
            return None
    
    def _create_top_rated_visualization(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt eine Visualisierung der Top-bewerteten Performer.
        
        Args:
            params: Parameter für die Visualisierung
                - limit: Maximale Anzahl anzuzeigender Performer (Standard: 10)
                - min_rating: Minimale Bewertung (Standard: 0)
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        limit = params.get('limit', 10)
        min_rating = params.get('min_rating', 0)
        
        # Performer mit Bewertungen filtern und sortieren
        rated_performers = [(p, p.rating100) for p in self.stats_module.performers 
                          if p.rating100 is not None and p.rating100 >= min_rating]
        
        if not rated_performers:
            logger.warning("Keine bewerteten Performer gefunden")
            return None
            
        # Nach Bewertung absteigend sortieren und begrenzen
        top_performers = sorted(rated_performers, key=lambda x: x[1], reverse=True)[:limit]
        
        # Daten für das Diagramm extrahieren
        names = [p.name for p, _ in top_performers]
        ratings = [rating for _, rating in top_performers]
        
        # Für bessere Lesbarkeit lange Namen kürzen
        names = [name[:20] + '...' if len(name) > 20 else name for name in names]
        
        # Farben basierend auf Cup-Größe, falls verfügbar
        colors = []
        for p, _ in top_performers:
            if p.cup_numeric and p.cup_numeric > 0:
                cup_idx = min(p.cup_numeric - 1, len(self.core.palettes['cup_sizes']) - 1)
                colors.append(self.core.palettes['cup_sizes'][cup_idx])
            else:
                colors.append(self.core.palettes['categorical'][0])
        
        # Horizontales Balkendiagramm erstellen
        fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
        
        # Namen umkehren für bessere Anzeige (höchste Bewertung oben)
        names.reverse()
        ratings.reverse()
        colors.reverse()
        
        bars = ax.barh(names, ratings, color=colors)
        
        # Beschriftungen
        self.core.format_axes(ax, 
                             title=f'Top {limit} bewertete Performer', 
                             xlabel='Bewertung (0-100)', 
                             ylabel='')
        
        # Zahlen neben den Balken
        self.core.add_value_labels(ax, bars, fmt="{:.1f}", xpos='right')
        
        # Diagramm speichern
        filename = f"top_{limit}_rated_performers"
        path = self.core.save_figure(fig, filename)
        
        return path
    
    def _create_cup_size_comparison(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt ein Vergleichsdiagramm für bestimmte Cup-Größen.
        
        Args:
            params: Parameter für die Visualisierung
                - cup_sizes: Liste der zu vergleichenden Cup-Größen
                - attributes: Liste der zu vergleichenden Attribute
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        cup_sizes = params.get('cup_sizes', ['B', 'C', 'D', 'DD'])
        attributes = params.get('attributes', ['rating100', 'o_counter', 'age'])
        
        # Prüfen, ob genügend Daten vorhanden sind
        if not cup_sizes or not attributes:
            logger.warning("Keine Cup-Größen oder Attribute für den Vergleich angegeben")
            return None
        
        # Sammle Daten für jede Cup-Größe und jedes Attribut
        data = {}
        for cup in cup_sizes:
            data[cup] = {}
            for attr in attributes:
                data[cup][attr] = []
        
        for p in self.stats_module.performers:
            if p.cup_size in cup_sizes:
                for attr in attributes:
                    attr_value = getattr(p, attr, None)
                    if attr_value is not None:
                        data[p.cup_size][attr].append(attr_value)
        
        # Berechne Durchschnitte
        for cup in cup_sizes:
            for attr in attributes:
                values = data[cup][attr]
                if values:
                    data[cup][attr] = sum(values) / len(values)
                else:
                    data[cup][attr] = 0
        
        # Erstelle ein Gruppiertes Balkendiagramm
        x = np.arange(len(attributes))  # X-Positionen der Balkengruppen
        width = 0.8 / len(cup_sizes)  # Breite der Balken
        
        fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
        
        for i, cup in enumerate(cup_sizes):
            # Setze Positionen für diese Cup-Größe
            positions = x - 0.4 + (i + 0.5) * width
            
            # Hole Werte für dieses Attribut
            values = [data[cup][attr] for attr in attributes]
            
            # Zeichne Balken
            ax.bar(positions, values, width, label=f'Cup {cup}')
        
        # Achsenbeschriftungen
        self.core.format_axes(ax, 
                             title='Vergleich nach Cup-Größe', 
                             xlabel='Attribut', 
                             ylabel='Durchschnittswert')
        
        # Anpassen der X-Achse
        ax.set_xticks(x)
        ax.set_xticklabels(attributes)
        
        # Legende
        ax.legend()
        
        # Diagramm speichern
        cup_str = '_'.join(cup_sizes)
        filename = f"cup_size_comparison_{cup_str}"
        path = self.core.save_figure(fig, filename)
        
        return path
    
    def _create_performer_attributes_radar(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt ein Radar-Chart für einen bestimmten Performer mit verschiedenen Attributen.
        
        Args:
            params: Parameter für die Visualisierung
                - performer_id: ID des Performers
                - attributes: Liste der anzuzeigenden Attribute
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        performer_id = params.get('performer_id')
        
        if not performer_id:
            logger.warning("Keine Performer-ID angegeben")
            return None
        
        # Finde den Performer
        performer = None
        for p in self.stats_module.performers:
            if p.id == performer_id:
                performer = p
                break
        
        if not performer:
            logger.warning(f"Performer mit ID {performer_id} nicht gefunden")
            return None
        
        # Attribute, die für das Radar-Chart verwendet werden sollen
        attributes = params.get('attributes', [
            'cup_numeric', 'rating100', 'o_counter', 'age', 'height_cm', 
            'scene_count'
        ])
        
        # Normalisierungswerte für jedes Attribut
        max_values = {
            'cup_numeric': 10,
            'rating100': 100,
            'o_counter': max(p.o_counter for p in self.stats_module.performers) or 1,
            'age': 50,
            'height_cm': 200,
            'scene_count': max(p.scene_count for p in self.stats_module.performers) or 1
        }
        
        # Anzeigenamen für die Attribute
        attribute_labels = {
            'cup_numeric': 'Cup-Größe',
            'rating100': 'Bewertung',
            'o_counter': 'O-Counter',
            'age': 'Alter',
            'height_cm': 'Größe',
            'scene_count': 'Szenen'
        }
        
        # Sammle Daten für das Radar-Chart
        values = []
        labels = []
        
        for attr in attributes:
            attr_value = getattr(performer, attr, None)
            if attr_value is not None:
                # Normalisiere auf 0-1
                normalized_value = attr_value / max_values.get(attr, 1)
                values.append(normalized_value)
                labels.append(attribute_labels.get(attr, attr))
            else:
                values.append(0)
                labels.append(attribute_labels.get(attr, attr))
        
        # Radar-Chart erstellen
        fig = plt.figure(figsize=(self.core.figure_width, self.core.figure_height))
        ax = fig.add_subplot(111, polar=True)
        
        # Anzahl der Attribute
        N = len(attributes)
        
        # Winkel für jede Achse
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Schließe den Kreis
        
        # Werte für das Diagramm (wiederhole den ersten Wert am Ende)
        values += values[:1]
        
        # Zeichne das Radar-Chart
        ax.plot(angles, values, linewidth=1, linestyle='solid')
        ax.fill(angles, values, alpha=0.1)
        
        # Achsenbeschriftungen hinzufügen
        plt.xticks(angles[:-1], labels)
        
        # Ergebnisse im Diagramm anzeigen
        for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
            ax.annotate(
                f"{labels[i]}: {getattr(performer, attributes[i], 0)}", 
                xy=(angle, value + 0.1)
            )
        
        # Diagrammtitel
        plt.title(f"Attribute für {performer.name}", size=self.core.title_fontsize)
        
        # Diagramm speichern
        filename = f"performer_radar_{performer.id}"
        path = self.core.save_figure(fig, filename)
        
        return path
    
    def _create_favorites_analysis(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt eine Analysegrafik für favorisierte Performer.
        
        Args:
            params: Parameter für die Visualisierung
                - compare_attributes: Attribute zum Vergleichen von Favoriten mit Nicht-Favoriten
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        compare_attributes = params.get('compare_attributes', [
            'cup_numeric', 'rating100', 'o_counter', 'age'
        ])
        
        # Favoriten und Nicht-Favoriten trennen
        favorites = [p for p in self.stats_module.performers if p.favorite]
        non_favorites = [p for p in self.stats_module.performers if not p.favorite]
        
        if not favorites:
            logger.warning("Keine favorisierten Performer gefunden")
            return None
        
        # Attribute-Labels
        attribute_labels = {
            'cup_numeric': 'Cup-Größe',
            'rating100': 'Bewertung',
            'o_counter': 'O-Counter',
            'age': 'Alter',
            'height_cm': 'Größe (cm)',
            'scene_count': 'Szenen-Anzahl',
            'bmi': 'BMI'
        }
        
        # Durchschnittswerte für jedes Attribut berechnen
        favorite_avgs = {}
        non_favorite_avgs = {}
        
        for attr in compare_attributes:
            # Favoriten
            fav_values = [getattr(p, attr, None) for p in favorites if getattr(p, attr, None) is not None]
            if fav_values:
                favorite_avgs[attr] = sum(fav_values) / len(fav_values)
            else:
                favorite_avgs[attr] = 0
                
            # Nicht-Favoriten
            non_fav_values = [getattr(p, attr, None) for p in non_favorites if getattr(p, attr, None) is not None]
            if non_fav_values:
                non_favorite_avgs[attr] = sum(non_fav_values) / len(non_fav_values)
            else:
                non_favorite_avgs[attr] = 0
        
        # Erstelle ein Balkendiagramm für den Vergleich
        fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
        
        x = np.arange(len(compare_attributes))
        width = 0.35
        
        # Daten für das Diagramm
        fav_values = [favorite_avgs[attr] for attr in compare_attributes]
        non_fav_values = [non_favorite_avgs[attr] for attr in compare_attributes]
        
        # Zeichne Balken
        rects1 = ax.bar(x - width/2, fav_values, width, label='Favoriten')
        rects2 = ax.bar(x + width/2, non_fav_values, width, label='Nicht-Favoriten')
        
        # Beschriftungen
        self.core.format_axes(ax, 
                             title='Vergleich: Favoriten vs. Nicht-Favoriten', 
                             xlabel='Attribut', 
                             ylabel='Durchschnittswert')
        
        # Anpassen der X-Achse
        ax.set_xticks(x)
        ax.set_xticklabels([attribute_labels.get(attr, attr) for attr in compare_attributes])
        
        # Zahlen über den Balken
        self.core.add_value_labels(ax, rects1, fmt="{:.1f}")
        self.core.add_value_labels(ax, rects2, fmt="{:.1f}")
        
        # Legende
        ax.legend()
        
        # Diagramm speichern
        filename = "favorites_analysis"
        path = self.core.save_figure(fig, filename)
        
        return path
