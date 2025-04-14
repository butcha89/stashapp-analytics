# output/dashboard_components/pages/performer_rec_page.py
import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

from output.dashboard_components.data_loader import get_performer_recommendations

def create_recommendation_table(recs_list, title):
    """Helper to create a Dash DataTable for recommendations."""
    if not recs_list:
        return html.P(f"No recommendations found for '{title}'.")

    df = pd.DataFrame(recs_list)
    # Optional: Add links if you have performer URLs
    # df['Link'] = df['id'].apply(lambda x: f"http://your-stash-url/performers/{x}") # Example link structure

    return dbc.Card([
        dbc.CardHeader(title),
        dbc.CardBody(
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Score', 'id': 'score', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    # {'name': 'Link', 'id': 'Link', 'type': 'text', 'presentation': 'markdown'} # If adding links
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                page_size=10, # Show 10 rows per page
                sort_action='native',
                filter_action='native',
            )
        )
    ])


def create_layout():
    """Creates the layout for the performer recommendations page."""
    recs_data = get_performer_recommendations()
    if recs_data is None:
        return dbc.Container([dbc.Alert("Could not load performer recommendations data.", color="danger")])

    # --- Create Tables for each category ---
    top_recs_table = create_recommendation_table(
        recs_data.get('top_recommendations', []),
        "Top Overall Performer Recommendations"
    )
    cup_recs_table = create_recommendation_table(
        recs_data.get('similar_cup_size', []),
        "Recommendations: Similar Cup Size"
    )
    tag_recs_table = create_recommendation_table(
        recs_data.get('similar_tags', []),
        "Recommendations: Similar Tags"
    )
    # Add tables for other categories as needed...
    prop_recs_table = create_recommendation_table(recs_data.get('similar_proportions', []), "Recommendations: Similar Proportions")
    age_recs_table = create_recommendation_table(recs_data.get('similar_age', []), "Recommendations: Similar Age")
    quality_recs_table = create_recommendation_table(recs_data.get('high_quality', []), "Recommendations: High Quality")
    novelty_recs_table = create_recommendation_table(recs_data.get('novelty', []), "Recommendations: Novelty")
    versatile_recs_table = create_recommendation_table(recs_data.get('versatile', []), "Recommendations: Versatile")
    fav_sim_recs_table = create_recommendation_table(recs_data.get('similar_to_favorites', []), "Recommendations: Similar to Favorites")
    zero_o_recs_table = create_recommendation_table(recs_data.get('zero_counter', []), "Recommendations: Low O-Counter")


    layout = dbc.Container([
        dbc.Row(dbc.Col(html.H2("Performer Recommendations"), width=12), className="mb-4"),
        dbc.Row(dbc.Col(top_recs_table, width=12), className="mb-4"), # Show top recs prominently
        dbc.Row([
            dbc.Col(cup_recs_table, md=6),
            dbc.Col(tag_recs_table, md=6),
        ], className="mb-4"),
         dbc.Row([
            dbc.Col(prop_recs_table, md=6),
            dbc.Col(age_recs_table, md=6),
        ], className="mb-4"),
         dbc.Row([
            dbc.Col(quality_recs_table, md=6),
            dbc.Col(novelty_recs_table, md=6),
        ], className="mb-4"),
         dbc.Row([
            dbc.Col(versatile_recs_table, md=6),
             dbc.Col(fav_sim_recs_table, md=6),
        ], className="mb-4"),
         dbc.Row([
             dbc.Col(zero_o_recs_table, md=6),
        ], className="mb-4"),
        # Add more rows for other recommendation categories
    ], fluid=True)
    return layout

layout = create_layout()
