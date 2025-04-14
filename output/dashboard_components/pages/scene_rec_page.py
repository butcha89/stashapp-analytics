# output/dashboard_components/pages/scene_rec_page.py
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

# Import the data loader function
from output.dashboard_components.data_loader import get_scene_recommendations
# Import the table helper from the performer page (or create a shared one)
from output.dashboard_components.pages.performer_rec_page import create_recommendation_table

def create_layout():
    """Creates the layout for the scene recommendations page."""
    recs_data = get_scene_recommendations()
    if recs_data is None:
        return dbc.Container([dbc.Alert("Could not load scene recommendations data.", color="danger")])

    # --- Create Tables for each category ---
    top_recs_table = create_recommendation_table(
        recs_data.get('top_recommendations', []),
        "Top Overall Scene Recommendations"
    )
    tag_recs_table = create_recommendation_table(
        recs_data.get('tag_similarity', []),
        "Recommendations: Similar Tags"
    )
    perf_recs_table = create_recommendation_table(
        recs_data.get('favorite_performers', []),
        "Recommendations: Features Favorite Performers"
    )
    # Add tables for other scene categories...
    studio_recs_table = create_recommendation_table(recs_data.get('preferred_studios', []), "Recommendations: Preferred Studios")
    quality_recs_table = create_recommendation_table(recs_data.get('high_quality_unwatched', []), "Recommendations: High Quality (Unwatched)")
    novelty_recs_table = create_recommendation_table(recs_data.get('novelty_unwatched', []), "Recommendations: Novelty (Unwatched)")
    top_unwatched_table = create_recommendation_table(recs_data.get('top_unwatched_overall', []), "Recommendations: Top Rated (Unwatched)")


    layout = dbc.Container([
        dbc.Row(dbc.Col(html.H2("Scene Recommendations"), width=12), className="mb-4"),
         dbc.Row(dbc.Col(top_recs_table, width=12), className="mb-4"),
         dbc.Row([
             dbc.Col(tag_recs_table, md=6),
             dbc.Col(perf_recs_table, md=6),
         ], className="mb-4"),
         dbc.Row([
             dbc.Col(studio_recs_table, md=6),
             dbc.Col(quality_recs_table, md=6),
         ], className="mb-4"),
         dbc.Row([
            dbc.Col(novelty_recs_table, md=6),
             dbc.Col(top_unwatched_table, md=6),
         ], className="mb-4"),
        # Add more rows for other recommendation categories
    ], fluid=True)
    return layout

layout = create_layout()
