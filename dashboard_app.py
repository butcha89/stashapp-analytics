# dashboard_app.py
import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import logging

# Configure basic logging for the dashboard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import page layouts AFTER defining app and potentially loading data
# It's crucial that page layouts can access the data loader functions.
try:
    from output.dashboard_components.pages import overview_page, statistics_page, performer_rec_page, scene_rec_page
    logger.info("Successfully imported page layout modules.")
except ImportError as e:
     logger.error(f"Failed to import page modules: {e}")
     # Define dummy layouts if import fails to prevent app crash on startup
     overview_page = type('obj', (object,), {'layout': html.Div(f"Error loading overview page: {e}")})()
     statistics_page = type('obj', (object,), {'layout': html.Div(f"Error loading statistics page: {e}")})()
     performer_rec_page = type('obj', (object,), {'layout': html.Div(f"Error loading performer recommendations page: {e}")})()
     scene_rec_page = type('obj', (object,), {'layout': html.Div(f"Error loading scene recommendations page: {e}")})()


# --- Initialize the Dash App ---
# Use Dash Bootstrap Components for styling
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True) # LUX is a nice theme, try others like BOOTSTRAP, CYBORG, DARKLY etc.
app.title = "StashApp Analytics Dashboard"

# --- Define App Layout ---
app.layout = dbc.Container([
    # Header
    dbc.Row(
        dbc.Col(html.H1("StashApp Analytics Dashboard", className="text-center text-primary, mb-4"), width=12)
    ),

    # Tabs for Navigation
    dbc.Tabs(
        [
            dbc.Tab(label="Overview", tab_id="tab-overview"),
            dbc.Tab(label="Statistics", tab_id="tab-stats"),
            dbc.Tab(label="Performer Recommendations", tab_id="tab-perf-rec"),
            dbc.Tab(label="Scene Recommendations", tab_id="tab-scene-rec"),
        ],
        id="tabs-main",
        active_tab="tab-overview", # Default active tab
        className="mb-3",
    ),

    # Content Area - This will be updated by the callback
    dbc.Container(id="tab-content", fluid=True)

], fluid=True)


# --- Define Callbacks ---
@app.callback(
    Output("tab-content", "children"), # The component to update
    Input("tabs-main", "active_tab")   # The component that triggers the update
)
def render_tab_content(active_tab):
    """Renders the content based on the active tab."""
    logger.info(f"Switching to tab: {active_tab}")
    if active_tab == "tab-overview":
        # Return the layout defined in overview_page.py
        # Call create_layout() if data needs to be fresh on each load,
        # otherwise just return the imported layout variable.
        return overview_page.create_layout() # Use function call for fresh data
    elif active_tab == "tab-stats":
        return statistics_page.create_layout()
    elif active_tab == "tab-perf-rec":
        return performer_rec_page.create_layout()
    elif active_tab == "tab-scene-rec":
        return scene_rec_page.create_layout()
    else:
        # Fallback if tab id is unknown
        return html.P("This shouldn't happen...")


# --- Run the App ---
if __name__ == '__main__':
    logger.info("Starting StashApp Analytics Dashboard...")
    # Set host='0.0.0.0' to make it accessible on your network
    # Use debug=True for development (auto-reloading, error messages in browser)
    # Use debug=False for production
    app.run_server(debug=True, host='0.0.0.0', port=8050) # Default port is 8050
