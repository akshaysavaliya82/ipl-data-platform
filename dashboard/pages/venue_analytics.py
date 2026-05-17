"""Venue analytics dashboard page."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import create_venue_chart
from dashboard.utils.data_loader import get_matches_df


def render_venue_analytics() -> None:
    """Render venue analytics dashboard."""
    st.header("Venue Analytics")

    matches_df = get_matches_df()
    if matches_df.empty:
        st.warning("No data available.")
        return

    venues = sorted(matches_df["venue"].unique())
    selected_venue = st.selectbox("Select Venue", ["All Venues"] + list(venues))

    if selected_venue == "All Venues":
        _render_all_venues(matches_df)
    else:
        _render_venue_detail(matches_df, selected_venue)


def _render_all_venues(df) -> None:
    """Render overview for all venues."""
    st.plotly_chart(create_venue_chart(df), use_container_width=True)

    venue_stats = (
        df.groupby(["venue", "city"])
        .agg(
            matches=("match_id", "count"),
            avg_i1=("innings1_runs", "mean"),
            avg_i2=("innings2_runs", "mean"),
        )
        .reset_index()
    )
    venue_stats["avg_total"] = venue_stats["avg_i1"] + venue_stats["avg_i2"]
    venue_stats = venue_stats.sort_values("matches", ascending=False)

    for col in ["avg_i1", "avg_i2", "avg_total"]:
        venue_stats[col] = venue_stats[col].round(1)

    st.subheader("Venue Statistics")
    st.dataframe(venue_stats, use_container_width=True, hide_index=True)


def _render_venue_detail(df, venue: str) -> None:
    """Render detailed stats for a specific venue."""
    venue_df = df[df["venue"] == venue]
    city = venue_df["city"].iloc[0] if not venue_df.empty else "Unknown"

    st.subheader(f"{venue} - {city}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Matches", len(venue_df))
    col2.metric("Avg 1st Innings", f"{venue_df['innings1_runs'].mean():.0f}")
    col3.metric("Avg 2nd Innings", f"{venue_df['innings2_runs'].mean():.0f}")

    bat_first_wins = len(venue_df[venue_df["result_type"] == "runs"])
    chase_wins = len(venue_df) - bat_first_wins
    col4.metric("Bat 1st Win %", f"{bat_first_wins / max(len(venue_df), 1) * 100:.0f}%")

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=["Bat First Wins", "Chase Wins"],
            values=[bat_first_wins, chase_wins],
            hole=0.4,
            marker_colors=["#FF9800", "#2196F3"],
        )])
        fig.update_layout(title="Bat First vs Chase", template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        toss_stats = venue_df.copy()
        toss_stats["toss_won_match"] = toss_stats["toss_winner"] == toss_stats["winner"]
        toss_decision_stats = (
            toss_stats.groupby("toss_decision")["toss_won_match"]
            .mean()
            .reset_index()
        )
        toss_decision_stats.columns = ["Decision", "Win Rate"]
        toss_decision_stats["Win Rate"] = (toss_decision_stats["Win Rate"] * 100).round(1)

        fig = px.bar(toss_decision_stats, x="Decision", y="Win Rate",
                     title="Toss Decision Impact",
                     color="Decision", text="Win Rate")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(template="plotly_dark", height=350, yaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Score Distribution")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=venue_df["innings1_runs"], name="1st Innings",
                                marker_color="#FF9800", opacity=0.7))
    fig.add_trace(go.Histogram(x=venue_df["innings2_runs"], name="2nd Innings",
                                marker_color="#2196F3", opacity=0.7))
    fig.update_layout(title="Score Distribution", template="plotly_dark",
                      height=350, barmode="overlay")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Matches at Venue")
    recent = venue_df.sort_values("date", ascending=False).head(10)
    display_cols = [c for c in ["date", "team1", "team2", "winner", "margin", "player_of_match"]
                    if c in recent.columns]
    st.dataframe(recent[display_cols], use_container_width=True, hide_index=True)
