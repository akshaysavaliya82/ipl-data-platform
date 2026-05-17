"""KPI components for the Streamlit dashboard."""

import pandas as pd
import streamlit as st


def render_match_kpis(df: pd.DataFrame) -> None:
    """Render match-level KPIs."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Matches", len(df))
    with col2:
        avg_runs = (df["innings1_runs"] + df["innings2_runs"]).mean()
        st.metric("Avg Runs/Match", f"{avg_runs:.0f}")
    with col3:
        seasons = df["season"].nunique()
        st.metric("Seasons", seasons)
    with col4:
        top_team = df["winner"].value_counts().index[0] if len(df) > 0 else "N/A"
        st.metric("Most Wins", top_team)


def render_player_kpis(balls_df: pd.DataFrame) -> None:
    """Render player-level KPIs."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_players = balls_df["batsman"].nunique()
        st.metric("Unique Players", total_players)
    with col2:
        total_runs = balls_df["runs_scored"].sum()
        st.metric("Total Runs", f"{total_runs:,}")
    with col3:
        total_sixes = balls_df[balls_df["runs_scored"] == 6].shape[0]
        st.metric("Total Sixes", f"{total_sixes:,}")
    with col4:
        total_fours = balls_df[balls_df["runs_scored"] == 4].shape[0]
        st.metric("Total Fours", f"{total_fours:,}")


def render_live_match_kpis(
    batting_team: str, score: int, wickets: int,
    overs: float, run_rate: float, target: int | None = None,
) -> None:
    """Render live match KPIs."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(batting_team, f"{score}/{wickets}")
    with col2:
        st.metric("Overs", f"{overs:.1f}")
    with col3:
        st.metric("Run Rate", f"{run_rate:.2f}")
    with col4:
        if target:
            needed = max(0, target - score)
            st.metric("Runs Needed", needed)
        else:
            st.metric("Projected", f"{int(run_rate * 20)}")
