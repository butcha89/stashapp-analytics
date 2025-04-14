for scene in scenes_with_age:
                    # Bestimme Altersgruppe basierend auf durchschnittlichem Alter
                    age = scene.avg_age
                    age_group = "46+"  # Standardwert
                    
                    for group, (min_age, max_age) in age_groups.items():
                        if min_age <= age <= max_age:
                            age_group = group
                            break
                    
                    age_ratings[age_group].append(scene.rating100)
                
                # Berechne Durchschnittsbewertung pro Altersgruppe
                avg_age_ratings = {}
                for group, ratings in age_ratings.items():
                    if len(ratings) >= 3:  # Mindestens 3 Szenen pro Altersgruppe
                        avg_age_ratings[group] = sum(ratings) / len(ratings)
                
                if avg_age_ratings:
                    # Sortiere Altersgruppen
                    sorted_groups = sorted(avg_age_ratings.keys(), 
                                          key=lambda x: int(x.split('-')[0]) if '-' in x else 100)
                    avg_values = [avg_age_ratings[group] for group in sorted_groups]
                    
                    fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                    
                    bars = ax.bar(sorted_groups, avg_values, color=self.core.palettes['age'])
                    
                    # Beschriftungen
                    self.core.format_axes(ax, 
                                         title='Durchschnittsbewertung nach Altersgruppe der Performer', 
                                         xlabel='Altersgruppe', 
                                         ylabel='Durchschnittsbewertung (0-100)')
                    
                    # Zahlen über den Balken
                    self.core.add_value_labels(ax, bars, fmt="{:.1f}")
                    
                    # Diagramm speichern
                    path = self.core.save_figure(fig, "rating_by_performer_age")
                    if path:
                        visualizations.append(path)
            
            # Szenen pro Performer (Top-N)
            performer_scene_counts = {}
            for performer in self.stats_module.performers:
                if performer.scene_count > 0:
                    performer_scene_counts[performer.name] = performer.scene_count
            
            if performer_scene_counts:
                # Sortiere nach Anzahl (absteigend) und nimm Top 15
                sorted_performers = sorted(performer_scene_counts.items(), key=lambda x: x[1], reverse=True)[:15]
                names = [name for name, _ in sorted_performers]
                counts = [count for _, count in sorted_performers]
                
                # Kürze lange Namen für bessere Lesbarkeit
                names = [name[:20] + '...' if len(name) > 20 else name for name in names]
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                # Horizontales Balkendiagramm für bessere Lesbarkeit bei vielen Namen
                bars = ax.barh(names, counts, color=self.core.palettes['categorical'])
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Top-15 Performer nach Anzahl der Szenen', 
                                     xlabel='Anzahl Szenen', 
                                     ylabel='')
                
                # Zahlen neben den Balken
                self.core.add_value_labels(ax, bars, fmt="{:.0f}", xpos='right')
                
                # Invertiere y-Achse, damit höchste Anzahl oben steht
                ax.invert_yaxis()
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "top_performers_by_scene_count")
                if path:
                    visualizations.append(path)
                
                # Interaktives Diagramm mit Plotly
                if self.core.interactive_mode:
                    try:
                        df = pd.DataFrame({
                            'Performer': names,
                            'Anzahl Szenen': counts
                        })
                        
                        fig = px.bar(df, y='Performer', x='Anzahl Szenen', 
                                    color='Anzahl Szenen', text='Anzahl Szenen',
                                    orientation='h',
                                    color_continuous_scale='Viridis',
                                    height=700, width=900)
                        
                        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                        
                        fig.update_layout(
                            title='Interaktive Darstellung: Top Performer nach Anzahl der Szenen',
                            yaxis={'categoryorder':'total ascending'}  # Sortierung
                        )
                        
                        path = self.core.save_plotly_figure(fig, "top_performers_scene_count_interactive")
                        if path:
                            visualizations.append(path)
                    except Exception as e:
                        logger.warning(f"Fehler bei der Erstellung des interaktiven Performer-Szenen-Diagramms: {str(e)}")
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Performer-Szenen-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_scene_attribute_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen zu verschiedenen Szenen-Attributen.
        
        Erzeugt folgende Visualisierungen:
        - Verteilung der Szenen-Dauer
        - Verteilung der Szenen-Auflösung
        - Verteilung der Anzahl der Performer pro Szene
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Szenen-Attribut-Visualisierungen...")
        visualizations = []
        
        try:
            # Szenen mit gültigen Attributen filtern
            scenes_with_duration = [s for s in self.stats_module.scenes if s.duration > 0]
            
            if scenes_with_duration:
                # Umwandlung der Sekunden in Minuten für eine bessere Darstellung
                durations_min = [s.duration / 60 for s in scenes_with_duration]
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                # Histogramm der Dauer mit KDE
                sns.histplot(durations_min, kde=True, bins=20, ax=ax, color=self.core.palettes['categorical'][3])
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Verteilung der Szenen-Dauer', 
                                     xlabel='Dauer (Minuten)', 
                                     ylabel='Anzahl')
                
                # Vertikale Linien für häufige Dauern (15, 30, 45, 60 Minuten)
                for duration in [15, 30, 45, 60]:
                    ax.axvline(x=duration, color='red', linestyle='--', alpha=0.5)
                    ax.text(duration, ax.get_ylim()[1]*0.9, f"{duration} min", 
                           ha='center', va='top', color='red', fontsize=self.core.label_fontsize-2)
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "scene_duration_distribution")
                if path:
                    visualizations.append(path)
            
            # Verteilung der Performer pro Szene
            performer_counts = [len(s.performer_ids) for s in self.stats_module.scenes if s.performer_ids]
            
            if performer_counts:
                # Zähle die Häufigkeit jeder Anzahl
                count_distribution = {}
                for count in performer_counts:
                    if count not in count_distribution:
                        count_distribution[count] = 0
                    count_distribution[count] += 1
                
                # Sortiere nach Anzahl der Performer
                sorted_counts = sorted(count_distribution.keys())
                frequencies = [count_distribution[count] for count in sorted_counts]
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                bars = ax.bar(sorted_counts, frequencies, color=self.core.palettes['categorical'])
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Anzahl der Performer pro Szene', 
                                     xlabel='Anzahl Performer', 
                                     ylabel='Anzahl Szenen')
                
                # Zahlen über den Balken
                self.core.add_value_labels(ax, bars)
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "performers_per_scene")
                if path:
                    visualizations.append(path)
            
            # Verteilung der Szenen-Auflösungen
            resolution_counts = {}
            for scene in self.stats_module.scenes:
                if hasattr(scene, 'resolution') and scene.resolution[0] > 0 and scene.resolution[1] > 0:
                    # Kategorisiere nach häufigen Auflösungen
                    width, height = scene.resolution
                    
                    if width >= 3840:
                        resolution = "4K"
                    elif width >= 1920:
                        resolution = "1080p"
                    elif width >= 1280:
                        resolution = "720p"
                    elif width >= 640:
                        resolution = "SD"
                    else:
                        resolution = "Niedrig"
                    
                    if resolution not in resolution_counts:
                        resolution_counts[resolution] = 0
                    resolution_counts[resolution] += 1
            
            if resolution_counts:
                # Definiere eine sinnvolle Reihenfolge für die Auflösungen
                resolution_order = ["Niedrig", "SD", "720p", "1080p", "4K"]
                sorted_resolutions = sorted(resolution_counts.keys(), 
                                          key=lambda x: resolution_order.index(x) if x in resolution_order else 999)
                counts = [resolution_counts[res] for res in sorted_resolutions]
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                # Farbpalette, die höhere Auflösungen hervorhebt
                colors = self.core.palettes['sequential'][:len(sorted_resolutions)]
                bars = ax.bar(sorted_resolutions, counts, color=colors)
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Verteilung der Szenen-Auflösungen', 
                                     xlabel='Auflösung', 
                                     ylabel='Anzahl')
                
                # Zahlen über den Balken
                self.core.add_value_labels(ax, bars)
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "scene_resolution_distribution")
                if path:
                    visualizations.append(path)
                
                # Interaktives Kreisdiagramm mit Plotly
                if self.core.interactive_mode:
                    try:
                        df = pd.DataFrame({
                            'Auflösung': sorted_resolutions,
                            'Anzahl': counts
                        })
                        
                        fig = px.pie(df, values='Anzahl', names='Auflösung', 
                                    title='Verteilung der Szenen-Auflösungen')
                        
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        
                        path = self.core.save_plotly_figure(fig, "scene_resolution_pie_interactive")
                        if path:
                            visualizations.append(path)
                    except Exception as e:
                        logger.warning(f"Fehler bei der Erstellung des interaktiven Auflösungs-Diagramms: {str(e)}")
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Szenen-Attribut-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_custom_visualization(self, visualization_type: str, params: Dict[str, Any] = None) -> Optional[str]:
        """
        Erstellt eine benutzerdefinierte Szenen-Visualisierung.
        
        Args:
            visualization_type: Art der zu erstellenden Visualisierung
            params: Parameter für die Visualisierung
            
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        if params is None:
            params = {}
            
        logger.info(f"Erstelle benutzerdefinierte Szenen-Visualisierung: {visualization_type}")
        
        try:
            # Je nach Typ an spezialisierte Methode delegieren
            if visualization_type == 'scene_tag_analysis':
                return self._create_tag_analysis_visualization(params)
            elif visualization_type == 'scene_studio_comparison':
                return self._create_studio_comparison(params)
            elif visualization_type == 'scene_duration_vs_rating':
                return self._create_duration_vs_rating(params)
            elif visualization_type == 'scene_top_rated':
                return self._create_top_rated_scenes(params)
            else:
                logger.warning(f"Unbekannter Visualisierungstyp: {visualization_type}")
                return None
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der benutzerdefinierten Visualisierung: {str(e)}")
            return None
    
    def _create_tag_analysis_visualization(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt eine Visualisierung zur Analyse von Szenen-Tags.
        
        Args:
            params: Parameter für die Visualisierung
                - top_n: Anzahl der Top-Tags (Standard: 10)
                - include_rating: Ob Bewertungen angezeigt werden sollen (Standard: True)
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        top_n = params.get('top_n', 10)
        include_rating = params.get('include_rating', True)
        
        # Sammle Tag-Häufigkeiten
        tag_counts = {}
        tag_ratings = {}
        
        for scene in self.stats_module.scenes:
            for tag in scene.tags:
                if tag not in tag_counts:
                    tag_counts[tag] = 0
                    tag_ratings[tag] = []
                
                tag_counts[tag] += 1
                if scene.rating100 is not None:
                    tag_ratings[tag].append(scene.rating100)
        
        if not tag_counts:
            logger.warning("Keine Tags in Szenen gefunden")
            return None
        
        # Sortiere nach Häufigkeit und wähle Top-N
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        tags = [tag for tag, _ in sorted_tags]
        counts = [count for _, count in sorted_tags]
        
        # Berechne durchschnittliche Bewertungen pro Tag
        avg_ratings = {}
        if include_rating:
            for tag in tags:
                ratings = tag_ratings[tag]
                if ratings:
                    avg_ratings[tag] = sum(ratings) / len(ratings)
                else:
                    avg_ratings[tag] = 0
        
        # Erstelle das Diagramm
        fig, ax1 = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
        
        # Horizontales Balkendiagramm für Häufigkeiten
        bars = ax1.barh(tags, counts, color=self.core.palettes['categorical'][0], alpha=0.7)
        
        # Beschriftungen
        ax1.set_title(f'Top-{top_n} Tags in Szenen', fontsize=self.core.title_fontsize)
        ax1.set_xlabel('Anzahl', fontsize=self.core.label_fontsize)
        ax1.invert_yaxis()  # Höchster Wert oben
        
        # Zahlen neben den Balken
        self.core.add_value_labels(ax1, bars, fmt="{:.0f}", xpos='right')
        
        # Optional: Bewertungen auf sekundärer Y-Achse
        if include_rating and avg_ratings:
            ax2 = ax1.twiny()  # Zweite X-Achse oben
            
            # Sortiere Bewertungen entsprechend der Tag-Reihenfolge
            ratings = [avg_ratings[tag] for tag in tags]
            
            # Bewertungen als Punkte mit Linie
            ax2.plot(ratings, range(len(tags)), 'ro-', linewidth=2, markersize=8)
            
            ax2.set_xlabel('Durchschnittsbewertung', fontsize=self.core.label_fontsize)
            ax2.set_xlim(0, 100)  # Bewertungsskala 0-100
            
            # Legende
            ax1.plot([], [], 'ro-', label='Bewertung')
            ax1.plot([], [], color=self.core.palettes['categorical'][0], alpha=0.7, label='Anzahl')
            ax1.legend(loc='lower right')
        
        # Diagramm speichern
        filename = f"top_{top_n}_scene_tags"
        path = self.core.save_figure(fig, filename)
        
        return path
    
    def _create_studio_comparison(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt ein Vergleichsdiagramm für ausgewählte Studios.
        
        Args:
            params: Parameter für die Visualisierung
                - studios: Liste der zu vergleichenden Studios
                - metrics: Liste der zu vergleichenden Metriken (z.B. rating, o_counter, duration)
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        studios = params.get('studios', [])
        metrics = params.get('metrics', ['rating', 'o_counter', 'duration'])
        
        # Fall keine Studios angegeben wurden, verwende die häufigsten
        if not studios:
            studio_counts = {}
            for scene in self.stats_module.scenes:
                if scene.studio_name:
                    if scene.studio_name not in studio_counts:
                        studio_counts[scene.studio_name] = 0
                    studio_counts[scene.studio_name] += 1
            
            # Wähle Top-5 Studios
            sorted_studios = sorted(studio_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            studios = [studio for studio, _ in sorted_studios]
        
        if not studios:
            logger.warning("Keine Studios gefunden")
            return None
        
        # Sammle Metrik-Werte für jedes Studio
        studio_data = {}
        for studio in studios:
            studio_data[studio] = {metric: [] for metric in metrics}
        
        for scene in self.stats_module.scenes:
            if scene.studio_name in studios:
                for metric in metrics:
                    if metric == 'rating' and scene.rating100 is not None:
                        studio_data[scene.studio_name]['rating'].append(scene.rating100)
                    elif metric == 'o_counter':
                        studio_data[scene.studio_name]['o_counter'].append(scene.o_counter)
                    elif metric == 'duration' and scene.duration > 0:
                        # Konvertiere in Minuten
                        studio_data[scene.studio_name]['duration'].append(scene.duration / 60)
        
        # Berechne Durchschnittswerte
        avg_values = {}
        for studio, metrics_data in studio_data.items():
            avg_values[studio] = {}
            for metric, values in metrics_data.items():
                if values:
                    avg_values[studio][metric] = sum(values) / len(values)
                else:
                    avg_values[studio][metric] = 0
        
        # Prüfe, ob genügend Daten vorhanden sind
        if not any(any(values.values()) for values in avg_values.values()):
            logger.warning("Keine ausreichenden Daten für den Studio-Vergleich")
            return None
        
        # Erstelle ein gruppiertes Balkendiagramm für jede Metrik
        metric_labels = {
            'rating': 'Bewertung',
            'o_counter': 'O-Counter',
            'duration': 'Dauer (min)'
        }
        
        # Erstelle Subplots für jede Metrik
        fig, axes = plt.subplots(len(metrics), 1, figsize=(self.core.figure_width, self.core.figure_height * len(metrics) * 0.6))
        
        # Wenn nur eine Metrik, ist axes kein Array
        if len(metrics) == 1:
            axes = [axes]
        
        # Zeichne für jede Metrik ein separates Diagramm
        for i, metric in enumerate(metrics):
            values = [avg_values[studio][metric] for studio in studios]
            
            bars = axes[i].bar(studios, values, color=self.core.palettes['categorical'])
            
            # Beschriftungen
            axes[i].set_title(f'{metric_labels.get(metric, metric)} nach Studio', fontsize=self.core.label_fontsize + 2)
            axes[i].set_ylabel(metric_labels.get(metric, metric), fontsize=self.core.label_fontsize)
            
            # Zahlen über den Balken
            self.core.add_value_labels(axes[i], bars, fmt="{:.1f}")
            
            # X-Achsenbeschriftungen rotieren, wenn viele Studios
            if len(studios) > 3:
                plt.setp(axes[i].get_xticklabels(), rotation=45, ha='right')
        
        # Gesamttitel
        fig.suptitle('Studio-Vergleich', fontsize=self.core.title_fontsize)
        
        # Layout anpassen
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Diagramm speichern
        studio_str = '_'.join(studios[:3])
        if len(studios) > 3:
            studio_str += '_etc'
        
        filename = f"studio_comparison_{studio_str}"
        path = self.core.save_figure(fig, filename, tight_layout=False)
        
        return path
    
    def _create_duration_vs_rating(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt ein Streudiagramm zum Zusammenhang zwischen Szenen-Dauer und Bewertung.
        
        Args:
            params: Parameter für die Visualisierung
                - bin_size: Größe der Bins in Minuten für Gruppierung (Standard: 5)
                - max_duration: Maximale Dauer in Minuten für die Analyse (Standard: 120)
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        bin_size = params.get('bin_size', 5)
        max_duration = params.get('max_duration', 120)
        
        # Szenen mit gültiger Dauer und Bewertung
        valid_scenes = [s for s in self.stats_module.scenes 
                       if s.duration > 0 and s.rating100 is not None and (s.duration / 60) <= max_duration]
        
        if len(valid_scenes) < 10:
            logger.warning("Zu wenige Szenen mit gültiger Dauer und Bewertung")
            return None
        
        # Extrahiere Dauer (in Minuten) und Bewertung
        durations = [s.duration / 60 for s in valid_scenes]
        ratings = [s.rating100 for s in valid_scenes]
        
        # Erstelle Streudiagramm
        fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
        
        # Streudiagramm mit Transparenz für überlappende Punkte
        scatter = ax.scatter(durations, ratings, alpha=0.5, c=ratings, cmap='viridis')
        
        # Regressionslinien hinzufügen
        try:
            z = np.polyfit(durations, ratings, 1)
            p = np.poly1d(z)
            ax.plot(sorted(durations), p(sorted(durations)), 'r--', linewidth=2, 
                   label=f'Trend: y = {z[0]:.2f}x + {z[1]:.2f}')
        except Exception as e:
            logger.warning(f"Fehler bei der Berechnung der Regressionslinie: {str(e)}")
        
        # Gruppiere nach Dauer-Bins und berechne Durchschnittsbewertung
        if bin_size > 0:
            duration_bins = {}
            for duration, rating in zip(durations, ratings):
                bin_idx = int(duration / bin_size)
                bin_key = bin_idx * bin_size
                if bin_key not in duration_bins:
                    duration_bins[bin_key] = []
                duration_bins[bin_key].append(rating)
            
            # Berechne Durchschnittsbewertung pro Bin
            bin_avg = {}
            for bin_key, bin_ratings in duration_bins.items():
                bin_avg[bin_key] = sum(bin_ratings) / len(bin_ratings)
            
            # Sortiere Bins
            sorted_bins = sorted(bin_avg.items())
            bin_keys = [f"{key}-{key+bin_size}" for key, _ in sorted_bins]
            bin_values = [value for _, value in sorted_bins]
            
            # Zweites Panel für die gruppierten Daten
            ax2 = ax.twinx()
            line = ax2.plot([key + bin_size/2 for key, _ in sorted_bins], bin_values, 'go-', 
                           linewidth=2, markersize=8, label='Grupp. Durchschnitt')
            ax2.set_ylabel('Durchschnittsbewertung pro Bin', color='g')
            ax2.tick_params(axis='y', labelcolor='g')
            
            # Legende für beide Achsen
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines + lines2, labels + labels2, loc='best')
        else:
            ax.legend(loc='best')
        
        # Beschriftungen
        self.core.format_axes(ax, 
                             title='Zusammenhang zwischen Szenen-Dauer und Bewertung', 
                             xlabel='Dauer (Minuten)', 
                             ylabel='Bewertung (0-100)')
        
        # Farbbalken für die Bewertung
        cbar = plt.colorbar(scatter)
        cbar.set_label('Bewertung')
        
        # Diagramm speichern
        filename = f"duration_vs_rating_bin{bin_size}"
        path = self.core.save_figure(fig, filename)
        
        # Interaktive Version mit Plotly
        if self.core.interactive_mode:
            try:
                # Erstelle DataFrame für Plotly
                df = pd.DataFrame({
                    'Dauer (min)': durations,
                    'Bewertung': ratings
                })
                
                fig = px.scatter(df, x='Dauer (min)', y='Bewertung', 
                                trendline="ols", trendline_color_override="red",
                                color='Bewertung', color_continuous_scale='Viridis')
                
                fig.update_layout(
                    title='Interaktives Diagramm: Dauer vs. Bewertung',
                    height=600,
                    width=900
                )
                
                # Gruppierte Durchschnitte hinzufügen
                if bin_size > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=[key + bin_size/2 for key, _ in sorted_bins],
                            y=bin_values,
                            mode='lines+markers',
                            name='Gruppierter Durchschnitt',
                            line=dict(color='green', width=3),
                            marker=dict(size=10)
                        )
                    )
                
                path_interactive = self.core.save_plotly_figure(fig, f"duration_vs_rating_interactive")
                if path_interactive:
                    return path_interactive  # Interaktive Version bevorzugen, wenn verfügbar
            except Exception as e:
                logger.warning(f"Fehler bei der Erstellung des interaktiven Dauer-vs-Bewertung-Diagramms: {str(e)}")
        
        return path
    
    def _create_top_rated_scenes(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Erstellt eine Visualisierung der Top-bewerteten Szenen.
        
        Args:
            params: Parameter für die Visualisierung
                - limit: Maximale Anzahl anzuzeigender Szenen (Standard: 10)
                - min_rating: Minimale Bewertung (Standard: 0)
                
        Returns:
            Optional[str]: Pfad zur erstellten Visualisierung oder None bei Fehler
        """
        limit = params.get('limit', 10)
        min_rating = params.get('min_rating', 0)
        
        # Szenen mit Bewertungen filtern und sortieren
        rated_scenes = [(s, s.rating100) for s in self.stats_module.scenes 
                       if s.rating100 is not None and s.rating100 >= min_rating]
        
        if not rated_scenes:
            logger.warning("Keine bewerteten Szenen gefunden")"""
Visualization Scenes Module

Dieses Modul ist verantwortlich für die Erstellung von Visualisierungen und Diagrammen
für Szenen-bezogene Daten. Es erstellt Visualisierungen zu Bewertungen, zeitlichen
Trends, Studios und andere Szenen-spezifische Analysen.
"""

import logging
import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Interner Import
from core.data_models import Scene
from analysis.visualization_core import VisualizationCore

# Logger konfigurieren
logger = logging.getLogger(__name__)

class SceneVisualization:
    """
    Klasse zur Erstellung von Szenen-bezogenen Visualisierungen.
    
    Diese Klasse erstellt verschiedene Diagramme und Visualisierungen
    für Szenen-Daten wie Bewertungen, zeitliche Verteilungen, Studios
    und andere Szenen-spezifische Analysen.
    """
    
    def __init__(self, core: VisualizationCore):
        """
        Initialisiert das Szenen-Visualisierungsmodul.
        
        Args:
            core: VisualizationCore-Instanz mit gemeinsamen Funktionen und Konfigurationen
        """
        self.core = core
        self.stats_module = core.stats_module
        self.api = core.api
        self.config = core.config
        logger.info("Szenen-Visualisierungsmodul initialisiert")
    
    def create_scene_rating_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen für Szenen-Bewertungen.
        
        Erzeugt folgende Visualisierungen:
        - Verteilung der Szenen-Bewertungen
        - Bewertung nach Studio
        - Bewertung nach Datum (Trend)
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Szenen-Bewertungs-Visualisierungen...")
        visualizations = []
        
        try:
            # Szenen mit gültigen Bewertungen filtern
            rated_scenes = [s for s in self.stats_module.scenes if s.rating100 is not None]
            
            if not rated_scenes:
                logger.warning("Keine bewerteten Szenen verfügbar")
                return visualizations
            
            # Bewertungsverteilung als Histogramm
            ratings = [s.rating100 for s in rated_scenes]
            
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            # Histogramm mit KDE
            sns.histplot(ratings, kde=True, bins=20, ax=ax, color=self.core.palettes['categorical'][2])
            
            # Beschriftungen
            self.core.format_axes(ax, 
                                 title='Verteilung der Szenen-Bewertungen', 
                                 xlabel='Bewertung (0-100)', 
                                 ylabel='Anzahl')
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "scene_rating_distribution")
            if path:
                visualizations.append(path)
            
            # Bewertung nach Studio
            studio_ratings = {}
            for s in rated_scenes:
                if s.studio_name:
                    if s.studio_name not in studio_ratings:
                        studio_ratings[s.studio_name] = []
                    studio_ratings[s.studio_name].append(s.rating100)
            
            # Berechne Durchschnittsbewertungen pro Studio
            avg_studio_ratings = {}
            for studio, ratings in studio_ratings.items():
                if len(ratings) >= 3:  # Mindestens 3 bewertete Szenen pro Studio
                    avg_studio_ratings[studio] = sum(ratings) / len(ratings)
            
            if avg_studio_ratings:
                # Sortiere nach Durchschnittsbewertung (absteigend)
                sorted_studios = sorted(avg_studio_ratings.items(), key=lambda x: x[1], reverse=True)
                top_studios = sorted_studios[:15]  # Top 15 Studios
                
                studios = [studio for studio, _ in top_studios]
                avg_ratings = [rating for _, rating in top_studios]
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                
                # Horizontales Balkendiagramm für bessere Lesbarkeit
                bars = ax.barh(studios, avg_ratings, color=self.core.palettes['categorical'])
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Top-15 Studios nach Durchschnittsbewertung', 
                                     xlabel='Durchschnittsbewertung (0-100)', 
                                     ylabel='Studio')
                
                # Zahlen neben den Balken
                self.core.add_value_labels(ax, bars, fmt="{:.1f}", xpos='right')
                
                # Invertiere y-Achse, damit höchste Bewertung oben steht
                ax.invert_yaxis()
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "studio_avg_ratings")
                if path:
                    visualizations.append(path)
                
                # Interaktives Diagramm mit Plotly
                if self.core.interactive_mode:
                    try:
                        # Erweitere die Daten um die Anzahl der Szenen pro Studio
                        studio_counts = {studio: len(ratings) for studio, ratings in studio_ratings.items() 
                                        if len(ratings) >= 3}
                        
                        df = pd.DataFrame({
                            'Studio': studios,
                            'Durchschnittsbewertung': avg_ratings,
                            'Anzahl Szenen': [studio_counts.get(studio, 0) for studio in studios]
                        })
                        
                        fig = px.bar(df, y='Studio', x='Durchschnittsbewertung', 
                                    color='Durchschnittsbewertung', text='Durchschnittsbewertung',
                                    hover_data=['Anzahl Szenen'],
                                    orientation='h',
                                    color_continuous_scale='Viridis',
                                    height=700, width=900)
                        
                        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                        
                        fig.update_layout(
                            title='Interaktive Darstellung: Top Studios nach Bewertung',
                            yaxis={'categoryorder':'total ascending'}  # Sortierung
                        )
                        
                        path = self.core.save_plotly_figure(fig, "studio_ratings_interactive")
                        if path:
                            visualizations.append(path)
                    except Exception as e:
                        logger.warning(f"Fehler bei der Erstellung des interaktiven Studio-Ratings-Diagramms: {str(e)}")
            
            # Bewertung nach Datum (Zeitreihe)
            scenes_with_date = [s for s in rated_scenes if s.date]
            
            if scenes_with_date:
                # Konvertiere Strings in Datumsformate
                scene_dates = []
                scene_ratings = []
                
                for scene in scenes_with_date:
                    try:
                        date = datetime.datetime.strptime(scene.date, "%Y-%m-%d")
                        scene_dates.append(date)
                        scene_ratings.append(scene.rating100)
                    except Exception:
                        continue
                
                if scene_dates and scene_ratings:
                    # Konvertiere zu Pandas DataFrame für einfachere Zeitreihenanalyse
                    df = pd.DataFrame({
                        'date': scene_dates,
                        'rating': scene_ratings
                    })
                    
                    # Gruppiere nach Monat und berechne Durchschnitt
                    df['month'] = df['date'].dt.to_period('M')
                    monthly_avg = df.groupby('month')['rating'].mean().reset_index()
                    monthly_avg['date'] = monthly_avg['month'].dt.to_timestamp()
                    
                    fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                    
                    # Scatterplot der einzelnen Bewertungen
                    ax.scatter(df['date'], df['rating'], alpha=0.3, label='Einzelbewertungen', color=self.core.palettes['categorical'][0])
                    
                    # Linie der monatlichen Durchschnitte
                    ax.plot(monthly_avg['date'], monthly_avg['rating'], 'r-', linewidth=2, label='Monatlicher Durchschnitt')
                    
                    # Trendlinie (lineare Regression)
                    try:
                        z = np.polyfit([(d - datetime.datetime(1970, 1, 1)).days for d in df['date']], df['rating'], 1)
                        p = np.poly1d(z)
                        ax.plot(df['date'], p([(d - datetime.datetime(1970, 1, 1)).days for d in df['date']]), 
                               'g--', linewidth=2, label=f'Trend (Steigung: {z[0]:.4f})')
                    except Exception as e:
                        logger.warning(f"Fehler bei der Berechnung der Trendlinie: {str(e)}")
                    
                    # Beschriftungen
                    self.core.format_axes(ax, 
                                         title='Bewertungstrend über Zeit', 
                                         xlabel='Datum', 
                                         ylabel='Bewertung (0-100)')
                    
                    # X-Achsen-Format anpassen
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                    plt.xticks(rotation=45)
                    
                    # Legende
                    ax.legend()
                    
                    # Diagramm speichern
                    path = self.core.save_figure(fig, "rating_time_trend")
                    if path:
                        visualizations.append(path)
                    
                    # Interaktive Plotly-Version
                    if self.core.interactive_mode:
                        try:
                            fig = px.scatter(df, x='date', y='rating', opacity=0.5,
                                            trendline="ols", trendline_color_override="red")
                            
                            # Monatliche Durchschnitte hinzufügen
                            fig.add_trace(
                                go.Scatter(x=monthly_avg['date'], y=monthly_avg['rating'],
                                          mode='lines+markers',
                                          name='Monatlicher Durchschnitt',
                                          line=dict(color='green', width=2))
                            )
                            
                            fig.update_layout(
                                title='Interaktiver Bewertungstrend über Zeit',
                                xaxis_title='Datum',
                                yaxis_title='Bewertung (0-100)',
                                height=600,
                                width=900,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                            )
                            
                            path = self.core.save_plotly_figure(fig, "rating_time_trend_interactive")
                            if path:
                                visualizations.append(path)
                        except Exception as e:
                            logger.warning(f"Fehler bei der Erstellung des interaktiven Zeittrend-Diagramms: {str(e)}")
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Szenen-Bewertungs-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_time_series_visualizations(self) -> List[str]:
        """
        Erstellt Zeitreihen-Visualisierungen für Szenen.
        
        Erzeugt folgende Visualisierungen:
        - Szenen pro Monat/Jahr
        - Saisonale Muster
        - Durchschnittlicher O-Counter über Zeit
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Zeitreihen-Visualisierungen...")
        visualizations = []
        
        try:
            # Szenen mit gültigem Datum filtern
            scenes_with_date = [s for s in self.stats_module.scenes if s.date]
            
            if not scenes_with_date:
                logger.warning("Keine Szenen mit Datumsangaben verfügbar")
                return visualizations
            
            # Konvertiere Strings in Datumsformate
            scene_dates = []
            scene_ratings = []
            scene_o_counters = []
            
            for scene in scenes_with_date:
                try:
                    date = datetime.datetime.strptime(scene.date, "%Y-%m-%d")
                    scene_dates.append(date)
                    
                    if scene.rating100 is not None:
                        scene_ratings.append(scene.rating100)
                    else:
                        scene_ratings.append(None)
                    
                    scene_o_counters.append(scene.o_counter)
                except Exception:
                    continue
            
            if not scene_dates:
                logger.warning("Keine gültigen Datumsformate gefunden")
                return visualizations
            
            # Konvertiere zu Pandas DataFrame für einfachere Zeitreihenanalyse
            df = pd.DataFrame({
                'date': scene_dates,
                'rating': scene_ratings,
                'o_counter': scene_o_counters
            })
            
            # Szenen pro Monat
            df['year_month'] = df['date'].dt.to_period('M')
            monthly_counts = df.groupby('year_month').size().reset_index(name='count')
            monthly_counts['date'] = monthly_counts['year_month'].dt.to_timestamp()
            
            # Anzahl der Szenen pro Monat
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            ax.plot(monthly_counts['date'], monthly_counts['count'], 'o-', 
                   linewidth=2, color=self.core.palettes['categorical'][0])
            
            # Gleitender Durchschnitt hinzufügen (6 Monate)
            rolling_avg = monthly_counts['count'].rolling(window=6, min_periods=1).mean()
            ax.plot(monthly_counts['date'], rolling_avg, 'r--', 
                   linewidth=2, label='6-Monats-Durchschnitt')
            
            # Beschriftungen
            self.core.format_axes(ax, 
                                 title='Anzahl der Szenen pro Monat', 
                                 xlabel='Datum', 
                                 ylabel='Anzahl')
            
            # X-Achsen-Format anpassen
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.xticks(rotation=45)
            
            # Legende
            ax.legend()
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "scenes_per_month")
            if path:
                visualizations.append(path)
            
            # Saisonale Muster (Szenen pro Monat des Jahres)
            df['month'] = df['date'].dt.month
            monthly_agg = df.groupby('month').agg({
                'date': 'count',
                'rating': lambda x: np.nanmean([val for val in x if val is not None]),
                'o_counter': 'mean'
            }).reset_index()
            
            monthly_agg.columns = ['month', 'count', 'avg_rating', 'avg_o_counter']
            
            # Sortiere nach Monat
            monthly_agg = monthly_agg.sort_values('month')
            
            # Monatsnamen für die x-Achse
            month_names = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            
            # Anzahl der Szenen pro Monat (saisonal)
            fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            bars = ax.bar(monthly_agg['month'], monthly_agg['count'], color=self.core.palettes['categorical'])
            
            # Beschriftungen
            self.core.format_axes(ax, 
                                 title='Saisonale Verteilung der Szenen', 
                                 xlabel='Monat', 
                                 ylabel='Anzahl')
            
            # X-Achse mit Monatsnamen
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels(month_names)
            
            # Zahlen über den Balken
            self.core.add_value_labels(ax, bars)
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "seasonal_scene_distribution")
            if path:
                visualizations.append(path)
            
            # Durchschnittlicher O-Counter und Rating pro Monat (saisonal)
            fig, ax1 = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
            
            # Erste Y-Achse: O-Counter
            color1 = self.core.palettes['categorical'][0]
            ax1.set_xlabel('Monat', fontsize=self.core.label_fontsize)
            ax1.set_ylabel('Durchschnittlicher O-Counter', color=color1, fontsize=self.core.label_fontsize)
            line1 = ax1.plot(monthly_agg['month'], monthly_agg['avg_o_counter'], 'o-', color=color1, linewidth=2, label='O-Counter')
            ax1.tick_params(axis='y', labelcolor=color1)
            
            # X-Achse mit Monatsnamen
            ax1.set_xticks(range(1, 13))
            ax1.set_xticklabels(month_names)
            
            # Zweite Y-Achse: Rating
            ax2 = ax1.twinx()
            color2 = self.core.palettes['categorical'][1]
            ax2.set_ylabel('Durchschnittliche Bewertung', color=color2, fontsize=self.core.label_fontsize)
            line2 = ax2.plot(monthly_agg['month'], monthly_agg['avg_rating'], 's-', color=color2, linewidth=2, label='Bewertung')
            ax2.tick_params(axis='y', labelcolor=color2)
            
            # Titel
            plt.title('Saisonale Trends: O-Counter und Bewertung', fontsize=self.core.title_fontsize)
            
            # Legende
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='best')
            
            # Diagramm speichern
            path = self.core.save_figure(fig, "seasonal_o_counter_rating")
            if path:
                visualizations.append(path)
            
            # Interaktives Plotly-Diagramm für saisonale Trends
            if self.core.interactive_mode:
                try:
                    fig = go.Figure()
                    
                    # Füge O-Counter-Linie hinzu
                    fig.add_trace(go.Scatter(
                        x=monthly_agg['month'],
                        y=monthly_agg['avg_o_counter'],
                        mode='lines+markers',
                        name='O-Counter',
                        line=dict(color='royalblue', width=2)
                    ))
                    
                    # Füge Rating-Linie auf zweiter Y-Achse hinzu
                    fig.add_trace(go.Scatter(
                        x=monthly_agg['month'],
                        y=monthly_agg['avg_rating'],
                        mode='lines+markers',
                        name='Bewertung',
                        line=dict(color='firebrick', width=2),
                        yaxis='y2'
                    ))
                    
                    # Layout mit doppelter Y-Achse
                    fig.update_layout(
                        title='Interaktive Darstellung: Saisonale Trends',
                        xaxis=dict(
                            title='Monat',
                            tickmode='array',
                            tickvals=list(range(1, 13)),
                            ticktext=month_names
                        ),
                        yaxis=dict(
                            title='Durchschnittlicher O-Counter',
                            titlefont=dict(color='royalblue'),
                            tickfont=dict(color='royalblue')
                        ),
                        yaxis2=dict(
                            title='Durchschnittliche Bewertung',
                            titlefont=dict(color='firebrick'),
                            tickfont=dict(color='firebrick'),
                            anchor='x',
                            overlaying='y',
                            side='right'
                        ),
                        height=600,
                        width=900
                    )
                    
                    path = self.core.save_plotly_figure(fig, "seasonal_trends_interactive")
                    if path:
                        visualizations.append(path)
                except Exception as e:
                    logger.warning(f"Fehler bei der Erstellung des interaktiven saisonalen Trend-Diagramms: {str(e)}")
            
            # Heat-Map der Szenen über Jahre und Monate
            # Prüfen, ob genügend Daten für sinnvolle Heatmap vorhanden sind
            unique_years = df['date'].dt.year.nunique()
            if unique_years >= 2:  # Mindestens 2 Jahre Daten
                df['year'] = df['date'].dt.year
                df['month'] = df['date'].dt.month
                
                # Aggregiere nach Jahr und Monat
                heatmap_data = df.groupby(['year', 'month']).size().reset_index(name='count')
                
                # Erstelle Pivot-Tabelle für Heatmap
                pivot_data = heatmap_data.pivot(index='year', columns='month', values='count').fillna(0)
                
                # Setze Spaltennamen auf Monatsnamen
                pivot_data.columns = [month_names[int(col)-1] for col in pivot_data.columns]
                
                fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height * 0.8))
                
                # Heatmap
                sns.heatmap(pivot_data, cmap=self.core.color_scheme, annot=True, fmt='.0f', linewidths=.5, ax=ax)
                
                # Beschriftungen
                self.core.format_axes(ax, 
                                     title='Anzahl der Szenen nach Jahr und Monat', 
                                     xlabel='Monat', 
                                     ylabel='Jahr')
                
                # Diagramm speichern
                path = self.core.save_figure(fig, "scenes_year_month_heatmap")
                if path:
                    visualizations.append(path)
                
                # Interaktive Heatmap mit Plotly
                if self.core.interactive_mode:
                    try:
                        # Daten für plotly aufbereiten
                        heatmap_plotly = []
                        for _, row in heatmap_data.iterrows():
                            heatmap_plotly.append({
                                'Jahr': row['year'],
                                'Monat': month_names[row['month']-1],
                                'Anzahl': row['count'],
                                'Monat_Nr': row['month']  # Für die Sortierung
                            })
                        
                        df_plotly = pd.DataFrame(heatmap_plotly)
                        
                        # Sortieren nach Monat
                        month_order = {month: i for i, month in enumerate(month_names)}
                        df_plotly['Monat_Order'] = df_plotly['Monat'].map(month_order)
                        df_plotly = df_plotly.sort_values(['Jahr', 'Monat_Order'])
                        
                        fig = px.density_heatmap(
                            df_plotly, 
                            x='Monat', 
                            y='Jahr', 
                            z='Anzahl',
                            category_orders={'Monat': month_names},
                            color_continuous_scale='Viridis',
                            text_auto=True
                        )
                        
                        fig.update_layout(
                            title='Interaktive Heatmap: Szenen nach Jahr und Monat',
                            height=600,
                            width=900
                        )
                        
                        path = self.core.save_plotly_figure(fig, "scenes_year_month_heatmap_interactive")
                        if path:
                            visualizations.append(path)
                    except Exception as e:
                        logger.warning(f"Fehler bei der Erstellung der interaktiven Heatmap: {str(e)}")
        
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Zeitreihen-Visualisierungen: {str(e)}")
        
        return visualizations
    
    def create_performer_scene_visualizations(self) -> List[str]:
        """
        Erstellt Visualisierungen zum Zusammenhang zwischen Performer-Eigenschaften und Szenen.
        
        Erzeugt folgende Visualisierungen:
        - Bewertung nach Cup-Größe der Performer
        - Bewertung nach Altersgruppe der Performer
        - Szenen pro Performer
        
        Returns:
            List[str]: Liste der Pfade zu den erstellten Visualisierungen
        """
        logger.info("Erstelle Performer-Szenen-Visualisierungen...")
        visualizations = []
        
        try:
            # Szenen mit erweiterten Performer-Attributen
            scenes_with_extended = [s for s in self.stats_module.scenes 
                                  if hasattr(s, 'avg_cup_size') and s.avg_cup_size is not None]
            
            if not scenes_with_extended:
                logger.warning("Keine Szenen mit erweiterten Performer-Attributen verfügbar")
                return visualizations
            
            # Bewertung nach durchschnittlicher Cup-Größe
            scenes_with_rating_cup = [s for s in scenes_with_extended 
                                     if s.rating100 is not None and s.avg_cup_size > 0]
            
            if scenes_with_rating_cup:
                # Gruppiere nach gerundeter Cup-Größe
                cup_ratings = {}
                for scene in scenes_with_rating_cup:
                    # Runde auf nächste ganze Zahl für die Gruppierung
                    rounded_cup = round(scene.avg_cup_size)
                    if rounded_cup not in cup_ratings:
                        cup_ratings[rounded_cup] = []
                    cup_ratings[rounded_cup].append(scene.rating100)
                
                # Berechne Durchschnittsbewertung pro Cup-Größe
                avg_ratings = {}
                for cup, ratings in cup_ratings.items():
                    if len(ratings) >= 3:  # Mindestens 3 Szenen pro Cup-Größe
                        avg_ratings[cup] = sum(ratings) / len(ratings)
                
                if avg_ratings:
                    # Sortiere nach Cup-Größe
                    sorted_cups = sorted(avg_ratings.keys())
                    cup_labels = [f"{Scene.CUP_NUMERIC_TO_LETTER.get(cup, '?')} ({cup})" for cup in sorted_cups]
                    avg_values = [avg_ratings[cup] for cup in sorted_cups]
                    
                    fig, ax = plt.subplots(figsize=(self.core.figure_width, self.core.figure_height))
                    
                    bars = ax.bar(cup_labels, avg_values, color=self.core.palettes['cup_sizes'])
                    
                    # Beschriftungen
                    self.core.format_axes(ax, 
                                         title='Durchschnittsbewertung nach Cup-Größe der Performer', 
                                         xlabel='Cup-Größe', 
                                         ylabel='Durchschnittsbewertung (0-100)')
                    
                    # Zahlen über den Balken
                    self.core.add_value_labels(ax, bars, fmt="{:.1f}")
                    
                    # Diagramm speichern
                    path = self.core.save_figure(fig, "rating_by_performer_cup")
                    if path:
                        visualizations.append(path)
            
            # Bewertung nach Altersgruppe
            scenes_with_age = [s for s in scenes_with_extended 
                              if s.rating100 is not None and hasattr(s, 'avg_age') and s.avg_age is not None]
            
            if scenes_with_age:
                # Definiere Altersgruppen
                age_groups = {
                    "18-25": (18, 25),
                    "26-30": (26, 30),
                    "31-35": (31, 35),
                    "36-40": (36, 40),
                    "41-45": (41, 45),
                    "46+": (46, 100)
                }
                
                # Gruppiere nach Altersgruppe
                age_ratings = {group: [] for group in age_groups}
                
                for
