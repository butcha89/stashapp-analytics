"""
Visualization Export Module

Dieses Modul bietet Funktionen zum Exportieren von Visualisierungen und Daten in verschiedene Formate
(z.B. PNG, PDF, SVG, CSV). Es unterstützt Einzel- und Batch-Exporte aus dem Visualisierungskern.
"""

import os
import logging
from typing import Optional, List
import plotly.graph_objects as go
import pandas as pd

logger = logging.getLogger(__name__)

class VisualizationExporter:
    """
    Modul für den Export von Visualisierungen und Daten.
    """

    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)
        logger.info(f"Exportverzeichnis vorbereitet: {self.export_dir}")

    def export_plotly_figure(
        self,
        figure: go.Figure,
        filename: str,
        formats: List[str] = ["html", "png"]
    ) -> List[str]:
        """
        Exportiert eine Plotly-Figur in die gewünschten Formate.

        Args:
            figure: Plotly-Figur
            filename: Basisdateiname ohne Erweiterung
            formats: Liste der Formate: html, png, pdf, svg, etc.

        Returns:
            Liste der Pfade zu den gespeicherten Dateien
        """
        saved_files = []
        filepath_base = os.path.join(self.export_dir, filename)

        for fmt in formats:
            path = f"{filepath_base}.{fmt.lower()}"
            try:
                if fmt.lower() == "html":
                    figure.write_html(path)
                elif fmt.lower() == "png":
                    figure.write_image(path, format="png", scale=2)
                elif fmt.lower() == "pdf":
                    figure.write_image(path, format="pdf")
                elif fmt.lower() == "svg":
                    figure.write_image(path, format="svg")
                else:
                    logger.warning(f"Nicht unterstütztes Format: {fmt}")
                    continue
                saved_files.append(path)
                logger.info(f"Export erfolgreich: {path}")
            except Exception as e:
                logger.error(f"Fehler beim Export in {fmt}: {e}")

        return saved_files

    def export_dataframe(
        self,
        df: pd.DataFrame,
        filename: str,
        formats: List[str] = ["csv"]
    ) -> List[str]:
        """
        Exportiert einen DataFrame in verschiedene Formate.

        Args:
            df: Der zu exportierende DataFrame
            filename: Basisname ohne Erweiterung
            formats: z.B. ["csv", "xlsx"]

        Returns:
            Liste der gespeicherten Dateipfade
        """
        saved_files = []
        filepath_base = os.path.join(self.export_dir, filename)

        for fmt in formats:
            path = f"{filepath_base}.{fmt.lower()}"
            try:
                if fmt.lower() == "csv":
                    df.to_csv(path, index=False)
                elif fmt.lower() == "xlsx":
                    df.to_excel(path, index=False)
                else:
                    logger.warning(f"Nicht unterstütztes Format: {fmt}")
                    continue
                saved_files.append(path)
                logger.info(f"DataFrame exportiert: {path}")
            except Exception as e:
                logger.error(f"Fehler beim Export von DataFrame in {fmt}: {e}")

        return saved_files
