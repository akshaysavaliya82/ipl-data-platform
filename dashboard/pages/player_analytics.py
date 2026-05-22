"""Player analytics dashboard page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components.charts import create_phase_analysis_chart, create_player_runs_chart
from dashboard.components.kpis import render_player_kpis
from dashboard.utils.data_loader import get_ball_by_ball_df, get_players_df


def render_player_analytics() -> None:
    """Render player analytics dashboard."""
    st.header("Player Analytics")

    balls_df = get_ball_by_ball_df()
    get_players_df()

    if balls_df.empty:
        st.warning("No data available.")
        return

    render_player_kpis(balls_df)
    st.markdown("---")

    col1, col2 = st.columns([1, 3])
    with col1:
        analysis_type = st.radio(
            "Analysis Type",
            ["Batting", "Bowling", "All-round"],
        )
        top_n = st.slider("Top N Players", 5, 25, 10)

    with col2:
        if analysis_type == "Batting":
            _render_batting_analysis(balls_df, top_n)
        elif analysis_type == "Bowling":
            _render_bowling_analysis(balls_df, top_n)
        else:
            _render_allround_analysis(balls_df, top_n)

    st.markdown("---")
    st.subheader("Phase-wise Analysis")
    st.plotly_chart(create_phase_analysis_chart(balls_df), use_container_width=True)

    st.markdown("---")
    st.subheader("Player Search")
    all_players = sorted(balls_df["batsman"].unique())
    selected_player = st.selectbox("Select Player", all_players)

    if selected_player:
        _render_player_detail(balls_df, selected_player)


def _render_batting_analysis(df: pd.DataFrame, top_n: int) -> None:
    """Render batting analysis."""
    st.subheader("Top Run Scorers")
    st.plotly_chart(create_player_runs_chart(df), use_container_width=True)

    batting_stats = (
        df.groupby("batsman")
        .agg(
            runs=("runs_scored", "sum"),
            balls=("runs_scored", "count"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            matches=("match_id", "nunique"),
        )
        .reset_index()
    )
    batting_stats["strike_rate"] = (batting_stats["runs"] / batting_stats["balls"] * 100).round(2)
    batting_stats["avg"] = (batting_stats["runs"] / batting_stats["matches"]).round(2)
    batting_stats = batting_stats.sort_values("runs", ascending=False).head(top_n)

    st.dataframe(batting_stats, use_container_width=True, hide_index=True)


def _render_bowling_analysis(df: pd.DataFrame, top_n: int) -> None:
    """Render bowling analysis."""
    st.subheader("Top Wicket Takers")

    bowling_stats = (
        df.groupby("bowler")
        .agg(
            balls=("runs_scored", "count"),
            runs_conceded=("runs_scored", "sum"),
            wickets=("is_wicket", "sum"),
            matches=("match_id", "nunique"),
        )
        .reset_index()
    )
    bowling_stats["economy"] = (
        bowling_stats["runs_conceded"] / (bowling_stats["balls"] / 6)
    ).round(2)
    bowling_stats["overs"] = (bowling_stats["balls"] / 6).round(1)
    bowling_stats = bowling_stats.sort_values("wickets", ascending=False).head(top_n)

    fig = px.bar(
        bowling_stats,
        x="bowler",
        y="wickets",
        title=f"Top {top_n} Wicket Takers",
        color="economy",
        color_continuous_scale="RdYlGn_r",
    )
    fig.update_layout(template="plotly_dark", height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(bowling_stats, use_container_width=True, hide_index=True)


def _render_allround_analysis(df: pd.DataFrame, top_n: int) -> None:
    """Render all-round analysis."""
    st.subheader("All-round Performance")

    batting = df.groupby("batsman").agg(runs=("runs_scored", "sum")).reset_index()
    batting.columns = ["player", "runs"]

    bowling = df.groupby("bowler").agg(wickets=("is_wicket", "sum")).reset_index()
    bowling.columns = ["player", "wickets"]

    allround = batting.merge(bowling, on="player", how="inner")
    allround = allround[(allround["runs"] > 50) & (allround["wickets"] > 2)]
    allround = allround.sort_values("runs", ascending=False).head(top_n)

    fig = px.scatter(
        allround,
        x="runs",
        y="wickets",
        text="player",
        title="All-round Performance (Runs vs Wickets)",
        size="runs",
        color="wickets",
        color_continuous_scale="Viridis",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)


def _render_player_detail(df: pd.DataFrame, player: str) -> None:
    """Render detailed stats for a specific player."""
    player_batting = df[df["batsman"] == player]
    player_bowling = df[df["bowler"] == player]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Batting Runs", int(player_batting["runs_scored"].sum()))
    col2.metric("Balls Faced", len(player_batting))
    col3.metric("Bowling Wickets", int(player_bowling["is_wicket"].sum()))
    col4.metric("Matches", player_batting["match_id"].nunique())

    if not player_batting.empty:
        sr = player_batting["runs_scored"].sum() / max(len(player_batting), 1) * 100
        st.metric("Strike Rate", f"{sr:.2f}")

    season_runs = player_batting.groupby("season")["runs_scored"].sum().reset_index()
    if not season_runs.empty:
        fig = px.bar(season_runs, x="season", y="runs_scored", title=f"{player} - Runs by Season")
        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)
