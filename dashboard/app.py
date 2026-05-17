"""Main Streamlit dashboard application for IPL Analytics."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="IPL Analytics Lakehouse",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #333;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">IPL Real-Time Analytics Lakehouse</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-header">Production-Grade Data Engineering Platform</div>',
    unsafe_allow_html=True,
)

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Overview",
        "Live Match",
        "Team Analytics",
        "Player Analytics",
        "Venue Analytics",
        "Fantasy Insights",
    ],
)

if page == "Overview":
    from dashboard.pages.overview import render_overview

    render_overview()
elif page == "Live Match":
    from dashboard.pages.live_match import render_live_match

    render_live_match()
elif page == "Team Analytics":
    from dashboard.pages.team_analytics import render_team_analytics

    render_team_analytics()
elif page == "Player Analytics":
    from dashboard.pages.player_analytics import render_player_analytics

    render_player_analytics()
elif page == "Venue Analytics":
    from dashboard.pages.venue_analytics import render_venue_analytics

    render_venue_analytics()
elif page == "Fantasy Insights":
    from dashboard.pages.fantasy_insights import render_fantasy_insights

    render_fantasy_insights()

st.sidebar.markdown("---")
st.sidebar.markdown("### Platform Info")
st.sidebar.info(
    "**Architecture:** Medallion (Bronze/Silver/Gold)\n\n"
    "**Stack:** Spark | Kafka | Airflow | dbt\n\n"
    "**API:** FastAPI | Port 8000\n\n"
    "**Version:** 1.0.0"
)
