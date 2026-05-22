"""Team analytics dashboard page."""

import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.data_loader import get_matches_df


def render_team_analytics() -> None:
    """Render team analytics dashboard."""
    st.header("Team Analytics")

    matches_df = get_matches_df()
    if matches_df.empty:
        st.warning("No data available.")
        return

    all_teams = sorted(set(matches_df["team1"].tolist() + matches_df["team2"].tolist()))

    col1, col2 = st.columns(2)
    with col1:
        selected_team = st.selectbox("Select Team", all_teams, index=0)
    with col2:
        season_filter = st.multiselect(
            "Filter by Season",
            sorted(matches_df["season"].unique()),
            default=[],
        )

    if season_filter:
        matches_df = matches_df[matches_df["season"].isin(season_filter)]

    team_matches = matches_df[
        (matches_df["team1"] == selected_team) | (matches_df["team2"] == selected_team)
    ]

    wins = len(team_matches[team_matches["winner"] == selected_team])
    total = len(team_matches)
    losses = total - wins

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Matches Played", total)
    col2.metric("Wins", wins)
    col3.metric("Losses", losses)
    col4.metric("Win %", f"{wins / max(total, 1) * 100:.1f}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        season_wins = (
            team_matches[team_matches["winner"] == selected_team]
            .groupby("season")
            .size()
            .reset_index(name="wins")
        )
        season_total = team_matches.groupby("season").size().reset_index(name="total")
        season_stats = season_total.merge(season_wins, on="season", how="left").fillna(0)
        season_stats["win_pct"] = season_stats["wins"] / season_stats["total"] * 100

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=season_stats["season"],
                y=season_stats["wins"],
                name="Wins",
                marker_color="#4CAF50",
            )
        )
        fig.add_trace(
            go.Bar(
                x=season_stats["season"],
                y=season_stats["total"] - season_stats["wins"],
                name="Losses",
                marker_color="#F44336",
            )
        )
        fig.update_layout(
            title=f"{selected_team} - Season Performance",
            barmode="stack",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        toss_data = team_matches[team_matches["toss_winner"] == selected_team]
        toss_won_match = len(toss_data[toss_data["winner"] == selected_team])
        toss_total = len(toss_data)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Won After Toss Win", "Lost After Toss Win"],
                    values=[toss_won_match, toss_total - toss_won_match],
                    hole=0.4,
                    marker_colors=["#4CAF50", "#F44336"],
                )
            ]
        )
        fig.update_layout(
            title=f"{selected_team} - Toss Impact", template="plotly_dark", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Head-to-Head Comparison")

    other_team = st.selectbox("Compare with", [t for t in all_teams if t != selected_team], index=0)

    h2h = team_matches[
        (team_matches["team1"] == other_team) | (team_matches["team2"] == other_team)
    ]
    h2h_wins_selected = len(h2h[h2h["winner"] == selected_team])
    h2h_wins_other = len(h2h[h2h["winner"] == other_team])

    col1, col2, col3 = st.columns(3)
    col1.metric(f"{selected_team} Wins", h2h_wins_selected)
    col2.metric("Total H2H", len(h2h))
    col3.metric(f"{other_team} Wins", h2h_wins_other)

    st.subheader("Recent Matches")
    recent = team_matches.sort_values("date", ascending=False).head(10)
    display_cols = [
        c for c in ["date", "team1", "team2", "winner", "margin", "venue"] if c in recent.columns
    ]
    st.dataframe(recent[display_cols], use_container_width=True, hide_index=True)
