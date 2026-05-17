"""Overview dashboard page."""

import streamlit as st

from dashboard.components.charts import (
    create_season_runs_chart,
    create_team_wins_chart,
    create_toss_impact_chart,
)
from dashboard.components.kpis import render_match_kpis
from dashboard.utils.data_loader import get_matches_df


def render_overview() -> None:
    """Render the overview dashboard."""
    st.header("Platform Overview")

    matches_df = get_matches_df()

    if matches_df.empty:
        st.warning("No data available. Please run the ingestion pipeline first.")
        return

    render_match_kpis(matches_df)
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(create_team_wins_chart(matches_df), use_container_width=True)

    with col2:
        st.plotly_chart(create_season_runs_chart(matches_df), use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.plotly_chart(create_toss_impact_chart(matches_df), use_container_width=True)

    with col4:
        st.subheader("Recent Matches")
        recent = matches_df.sort_values("date", ascending=False).head(10)
        display_cols = ["date", "team1", "team2", "winner", "margin", "venue"]
        available_cols = [c for c in display_cols if c in recent.columns]
        st.dataframe(recent[available_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Season-wise Match Count")
    season_counts = matches_df["season"].value_counts().sort_index()
    st.bar_chart(season_counts)
