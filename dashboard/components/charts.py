"""Reusable chart components for the Streamlit dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_team_wins_chart(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart of team wins."""
    team_wins = df["winner"].value_counts().head(10).reset_index()
    team_wins.columns = ["Team", "Wins"]

    fig = px.bar(
        team_wins, x="Team", y="Wins",
        title="Top 10 Teams by Wins",
        color="Wins",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        template="plotly_dark",
        height=400,
    )
    return fig


def create_season_runs_chart(df: pd.DataFrame) -> go.Figure:
    """Create a line chart of runs per season."""
    season_stats = (
        df.groupby("season")
        .agg(
            total_runs=("innings1_runs", lambda x: (
                x.sum() + df.loc[x.index, "innings2_runs"].sum()
            )),
            matches=("match_id", "count"),
        )
        .reset_index()
    )
    season_stats["avg_runs"] = season_stats["total_runs"] / season_stats["matches"]

    fig = px.line(
        season_stats, x="season", y="avg_runs",
        title="Average Runs per Match by Season",
        markers=True,
    )
    fig.update_layout(template="plotly_dark", height=400)
    return fig


def create_venue_chart(df: pd.DataFrame) -> go.Figure:
    """Create a venue analysis chart."""
    venue_stats = (
        df.groupby("venue")
        .agg(
            matches=("match_id", "count"),
            avg_i1=("innings1_runs", "mean"),
        )
        .reset_index()
        .sort_values("matches", ascending=False)
        .head(10)
    )

    fig = px.bar(
        venue_stats, x="venue", y="matches",
        title="Top 10 Venues by Matches Hosted",
        color="avg_i1",
        color_continuous_scale="RdYlGn",
        labels={"avg_i1": "Avg 1st Innings"},
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        template="plotly_dark",
        height=400,
    )
    return fig


def create_toss_impact_chart(df: pd.DataFrame) -> go.Figure:
    """Create toss impact analysis chart."""
    df_copy = df.copy()
    df_copy["toss_winner_won"] = df_copy["toss_winner"] == df_copy["winner"]
    toss_stats = df_copy.groupby("toss_decision")["toss_winner_won"].mean().reset_index()
    toss_stats.columns = ["Toss Decision", "Win Rate"]
    toss_stats["Win Rate"] = toss_stats["Win Rate"] * 100

    fig = px.bar(
        toss_stats, x="Toss Decision", y="Win Rate",
        title="Toss Winner Match Win Rate by Decision",
        color="Toss Decision",
        text="Win Rate",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(template="plotly_dark", height=400, yaxis_range=[0, 100])
    return fig


def create_player_runs_chart(df: pd.DataFrame, player_col: str = "batsman") -> go.Figure:
    """Create top run scorers chart."""
    top_scorers = (
        df.groupby(player_col)["runs_scored"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )
    top_scorers.columns = ["Player", "Runs"]

    fig = px.bar(
        top_scorers, x="Player", y="Runs",
        title="Top 15 Run Scorers",
        color="Runs",
        color_continuous_scale="Oranges",
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        template="plotly_dark",
        height=400,
    )
    return fig


def create_phase_analysis_chart(df: pd.DataFrame) -> go.Figure:
    """Create match phase analysis chart."""
    phase_stats = (
        df.groupby("phase")
        .agg(
            total_runs=("runs_scored", "sum"),
            total_balls=("runs_scored", "count"),
            wickets=("is_wicket", "sum"),
        )
        .reset_index()
    )
    phase_stats["run_rate"] = phase_stats["total_runs"] / (phase_stats["total_balls"] / 6)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Run Rate", x=phase_stats["phase"], y=phase_stats["run_rate"],
        marker_color="rgba(255, 165, 0, 0.8)",
    ))
    fig.update_layout(
        title="Run Rate by Match Phase",
        template="plotly_dark",
        height=400,
    )
    return fig


def create_win_probability_gauge(probability: float, team_name: str) -> go.Figure:
    """Create a win probability gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=probability * 100,
        title={"text": f"{team_name} Win Probability"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 30], "color": "red"},
                {"range": [30, 50], "color": "orange"},
                {"range": [50, 70], "color": "yellow"},
                {"range": [70, 100], "color": "green"},
            ],
        },
    ))
    fig.update_layout(template="plotly_dark", height=300)
    return fig
