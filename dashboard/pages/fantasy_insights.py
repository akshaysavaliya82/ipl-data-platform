"""Fantasy cricket insights dashboard page."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.data_loader import get_ball_by_ball_df, get_matches_df


def render_fantasy_insights() -> None:
    """Render fantasy cricket insights dashboard."""
    st.header("Fantasy Cricket Insights")

    balls_df = get_ball_by_ball_df()
    get_matches_df()

    if balls_df.empty:
        st.warning("No data available.")
        return

    tab1, tab2, tab3 = st.tabs(
        [
            "Fantasy Score Calculator",
            "Dream Team Builder",
            "Impact Players",
        ]
    )

    with tab1:
        _render_fantasy_calculator()

    with tab2:
        _render_dream_team(balls_df)

    with tab3:
        _render_impact_players(balls_df)


def _render_fantasy_calculator() -> None:
    """Render fantasy score calculator."""
    st.subheader("Fantasy Score Calculator")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Batting Performance**")
        runs = st.number_input("Runs Scored", 0, 300, 45)
        balls = st.number_input("Balls Faced", 0, 200, 30)
        fours = st.number_input("Fours", 0, 30, 4)
        sixes = st.number_input("Sixes", 0, 20, 2)

    with col2:
        st.markdown("**Bowling Performance**")
        wickets = st.number_input("Wickets Taken", 0, 10, 1)
        overs = st.number_input("Overs Bowled", 0.0, 20.0, 4.0, step=0.1)
        runs_conceded = st.number_input("Runs Conceded", 0, 200, 28)
        catches = st.number_input("Catches", 0, 10, 1)

    if st.button("Calculate Fantasy Score", type="primary"):
        from spark_jobs.gold.win_probability import calculate_fantasy_score

        result = calculate_fantasy_score(
            runs=runs,
            balls_faced=balls,
            fours=fours,
            sixes=sixes,
            wickets=wickets,
            overs_bowled=overs,
            runs_conceded=runs_conceded,
            catches=catches,
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Points", result["total_fantasy_points"])
        col2.metric("Batting", result["batting_points"])
        col3.metric("Bowling", result["bowling_points"])
        col4.metric("Fielding", result["fielding_points"])

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Batting", "Bowling", "Fielding"],
                    values=[
                        max(0, result["batting_points"]),
                        max(0, result["bowling_points"]),
                        max(0, result["fielding_points"]),
                    ],
                    hole=0.4,
                    marker_colors=["#1E88E5", "#43A047", "#FB8C00"],
                )
            ]
        )
        fig.update_layout(title="Points Breakdown", template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)


def _render_dream_team(df: pd.DataFrame) -> None:
    """Render dream team builder."""
    st.subheader("Auto Dream Team")

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
    batting_stats["impact_score"] = (
        batting_stats["runs"] * 1.0 + batting_stats["fours"] * 1.0 + batting_stats["sixes"] * 2.0
    ) / batting_stats["matches"]

    bowling_stats = (
        df.groupby("bowler")
        .agg(
            wickets=("is_wicket", "sum"),
            runs_conceded=("runs_scored", "sum"),
            balls=("runs_scored", "count"),
            matches=("match_id", "nunique"),
        )
        .reset_index()
    )
    bowling_stats["economy"] = (
        bowling_stats["runs_conceded"] / (bowling_stats["balls"] / 6)
    ).round(2)
    bowling_stats["bowling_impact"] = (bowling_stats["wickets"] * 25) / bowling_stats["matches"]

    top_batsmen = batting_stats.sort_values("impact_score", ascending=False).head(6)
    top_bowlers = bowling_stats.sort_values("bowling_impact", ascending=False).head(5)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 6 Batsmen**")
        display = top_batsmen[["batsman", "runs", "strike_rate", "impact_score"]].copy()
        display.columns = ["Player", "Runs", "SR", "Impact"]
        display["Impact"] = display["Impact"].round(1)
        st.dataframe(display, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Top 5 Bowlers**")
        display = top_bowlers[["bowler", "wickets", "economy", "bowling_impact"]].copy()
        display.columns = ["Player", "Wickets", "Economy", "Impact"]
        display["Impact"] = display["Impact"].round(1)
        st.dataframe(display, use_container_width=True, hide_index=True)


def _render_impact_players(df: pd.DataFrame) -> None:
    """Render impact player analysis."""
    st.subheader("Impact Players")

    phase = st.selectbox("Match Phase", ["All", "powerplay", "middle", "death"])

    filtered = df if phase == "All" else df[df["phase"] == phase]

    impact = (
        filtered.groupby("batsman")
        .agg(
            runs=("runs_scored", "sum"),
            balls=("runs_scored", "count"),
            boundaries=("is_boundary", "sum"),
        )
        .reset_index()
    )
    impact["strike_rate"] = (impact["runs"] / impact["balls"] * 100).round(2)
    impact["boundary_pct"] = (impact["boundaries"] / impact["balls"] * 100).round(2)
    impact = impact[impact["balls"] >= 20].sort_values("strike_rate", ascending=False).head(15)

    fig = px.scatter(
        impact,
        x="strike_rate",
        y="boundary_pct",
        size="runs",
        text="batsman",
        color="runs",
        title=f"Impact Players - {phase.title()} Phase",
        color_continuous_scale="Viridis",
        labels={"strike_rate": "Strike Rate", "boundary_pct": "Boundary %"},
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)
