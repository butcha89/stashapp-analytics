# output/dashboard_components/data_loader.py
import json
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# --- Configuration ---
# Adjust these paths based on where your analysis/recommendation scripts save their output
STATS_DIR = './output' # Directory where statistics JSON is saved
REC_DIR = './output'   # Directory where recommendations JSON are saved

PERFORMER_STATS_FILE = os.path.join(STATS_DIR, 'performer_statistics.json') # Example filename
SCENE_STATS_FILE = os.path.join(STATS_DIR, 'scene_statistics.json')         # Example filename
PERFORMER_REC_FILE = os.path.join(REC_DIR, 'performer_recommendations.json')
SCENE_REC_FILE = os.path.join(REC_DIR, 'scene_recommendations.json')
# Add other stats file paths if needed (e.g., cup size distribution)


def load_json_data(filepath):
    """Loads data from a JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Data file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded data from: {filepath}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading file {filepath}: {e}")
        return None

def get_performer_recommendations():
    """Loads performer recommendations."""
    return load_json_data(PERFORMER_REC_FILE)

def get_scene_recommendations():
    """Loads scene recommendations."""
    return load_json_data(SCENE_REC_FILE)

def get_performer_statistics():
    """Loads performer statistics."""
    # Example: Assuming stats file has various keys like 'summary', 'distributions'
    return load_json_data(PERFORMER_STATS_FILE)

def get_scene_statistics():
    """Loads scene statistics."""
    return load_json_data(SCENE_STATS_FILE)

def get_summary_stats():
    """Extracts or computes basic summary statistics."""
    perf_stats = get_performer_statistics()
    scene_stats = get_scene_statistics()
    summary = {
        "total_performers": perf_stats.get("summary", {}).get("total_performers", "N/A") if perf_stats else "N/A",
        "total_scenes": scene_stats.get("summary", {}).get("total_scenes", "N/A") if scene_stats else "N/A",
        "total_tags": perf_stats.get("summary", {}).get("total_unique_tags", "N/A") if perf_stats else "N/A", # Example key
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Or get from stats files if available
    }
    # Add more summary stats as needed
    return summary

# Add more functions as needed to load specific parts of your data,
# potentially converting them to pandas DataFrames for easier plotting/tabulation.
# Example:
# def get_cup_size_distribution_df():
#     stats = get_performer_statistics()
#     if stats and 'distributions' in stats and 'cup_size' in stats['distributions']:
#         # Assuming data is like {'A': 10, 'B': 20, ...}
#         dist_data = stats['distributions']['cup_size']
#         df = pd.DataFrame(list(dist_data.items()), columns=['Cup Size', 'Count'])
#         # You might want to sort or process further
#         return df
#     return pd.DataFrame(columns=['Cup Size', 'Count'])
