# output/dashboard_components/pages/overview_page.py
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime

# Import the data loader function
from output.dashboard_components.data_loader import get_summary_stats

def create_layout():
    """Creates the layout for the overview page."""
    summary = get_summary_stats() # Load summary data when layout is created

    layout = dbc.Container([
        dbc.Row(dbc.Col(html.H2("Dashboard Overview"), width=12), className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Total Performers"),
                dbc.CardBody(html.H4(summary.get("total_performers", "N/A"), className="card-title"))
            ]), md=3),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Total Scenes"),
                dbc.CardBody(html.H4(summary.get("total_scenes", "N/A"), className="card-title"))
            ]), md=3),
             dbc.Col(dbc.Card([
                dbc.CardHeader("Unique Tags"), # Example stat
                dbc.CardBody(html.H4(summary.get("total_tags", "N/A"), className="card-title"))
            ]), md=3),
             dbc.Col(dbc.Card([
                dbc.CardHeader("Last Update"),
                dbc.CardBody(html.H4(summary.get("last_updated", "N/A"), className="card-title"))
            ]), md=3),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                html.H4("Welcome!"),
                html.P("This dashboard provides analytics and recommendations for your StashApp library."),
                html.P("Use the tabs above to navigate through different sections:"),
                html.Ul([
                    html.Li("Statistics: View detailed charts and data distributions."),
                    html.Li("Performer Recommendations: Discover performers you might like."),
                    html.Li("Scene Recommendations: Find scenes based on your preferences.")
                ])
                # Add maybe a high-level chart here later
            ], md=12)
        ])
    ], fluid=True)
    return layout

# Assign the layout function to a variable named 'layout'
# Dash convention often looks for a variable named 'layout' in page modules
layout = create_layout()
