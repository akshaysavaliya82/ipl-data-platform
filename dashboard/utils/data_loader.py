"""Data loading utilities for the Streamlit dashboard."""

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

API_BASE_URL = "http://localhost:8000/api/v1"
DATA_DIR = Path("data/samples")


def load_from_api(endpoint: str, params: dict | None = None) -> dict[str, Any] | list:
    """Load data from the FastAPI backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return load_from_file(endpoint)


def load_from_file(data_type: str) -> Any:
    """Load data directly from JSON files as fallback."""
    file_map = {
        "players": "players.json",
        "matches": "matches.json",
        "teams": "teams.json",
        "venues": "venues.json",
        "ball_by_ball": "ball_by_ball.json",
    }

    clean_type = data_type.split("/")[0]
    filename = file_map.get(clean_type)
    if not filename:
        return []

    filepath = DATA_DIR / filename
    if not filepath.exists():
        from ingestion.sources.sample_data import save_sample_data

        save_sample_data(str(DATA_DIR))

    with open(filepath) as f:
        return json.load(f)


def get_matches_df() -> pd.DataFrame:
    """Get matches data as DataFrame."""
    data = load_from_file("matches")
    return pd.DataFrame(data)


def get_players_df() -> pd.DataFrame:
    """Get players data as DataFrame."""
    data = load_from_file("players")
    return pd.DataFrame(data)


def get_ball_by_ball_df() -> pd.DataFrame:
    """Get ball-by-ball data as DataFrame."""
    data = load_from_file("ball_by_ball")
    return pd.DataFrame(data)


def get_teams_df() -> pd.DataFrame:
    """Get teams data as DataFrame."""
    data = load_from_file("teams")
    return pd.DataFrame(data)


def get_venues_df() -> pd.DataFrame:
    """Get venues data as DataFrame."""
    data = load_from_file("venues")
    return pd.DataFrame(data)
