"""Live match dashboard page with real-time simulation."""

import time

import plotly.graph_objects as go
import streamlit as st

from dashboard.components.charts import create_win_probability_gauge
from dashboard.components.kpis import render_live_match_kpis


def render_live_match() -> None:
    """Render the live match dashboard."""
    st.header("Live Match Dashboard")

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Simulation Controls")
        speed = st.slider("Simulation Speed", 1, 10, 5)
        start_sim = st.button("Start Live Simulation", type="primary")

    if start_sim or st.session_state.get("sim_running", False):
        st.session_state["sim_running"] = True
        _run_simulation(speed)
    else:
        st.info("Click 'Start Live Simulation' to begin a live match simulation.")
        _show_demo_state()


def _show_demo_state() -> None:
    """Show a demo match state."""
    render_live_match_kpis(
        batting_team="Mumbai Indians",
        score=156,
        wickets=4,
        overs=16.3,
        run_rate=9.45,
        target=185,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            create_win_probability_gauge(0.62, "Mumbai Indians"),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            create_win_probability_gauge(0.38, "Chennai Super Kings"),
            use_container_width=True,
        )

    st.markdown("---")

    st.subheader("Ball-by-Ball Commentary")
    commentary = [
        {
            "Over": "16.3",
            "Batsman": "Suryakumar Yadav",
            "Bowler": "Pathirana",
            "Result": "4 runs",
            "Score": "156/4",
        },
        {
            "Over": "16.2",
            "Batsman": "Suryakumar Yadav",
            "Bowler": "Pathirana",
            "Result": "1 run",
            "Score": "152/4",
        },
        {
            "Over": "16.1",
            "Batsman": "Hardik Pandya",
            "Bowler": "Pathirana",
            "Result": "6 runs!",
            "Score": "151/4",
        },
        {
            "Over": "15.6",
            "Batsman": "Hardik Pandya",
            "Bowler": "Jadeja",
            "Result": "2 runs",
            "Score": "145/4",
        },
        {
            "Over": "15.5",
            "Batsman": "Hardik Pandya",
            "Bowler": "Jadeja",
            "Result": "DOT",
            "Score": "143/4",
        },
    ]
    st.table(commentary)

    st.subheader("Run Rate Progression")
    overs = list(range(1, 17))
    run_rates = [6.0, 6.5, 7.2, 7.8, 8.1, 8.5, 8.2, 8.8, 9.0, 8.7, 9.1, 9.3, 9.5, 9.2, 9.4, 9.45]
    required = [9.25] * 16

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=overs, y=run_rates, mode="lines+markers", name="Current RR", line={"color": "#1E88E5"}
        )
    )
    fig.add_trace(
        go.Scatter(
            x=overs,
            y=required,
            mode="lines",
            name="Required RR",
            line={"color": "red", "dash": "dash"},
        )
    )
    fig.update_layout(
        title="Run Rate Progression",
        template="plotly_dark",
        height=350,
        xaxis_title="Overs",
        yaxis_title="Run Rate",
    )
    st.plotly_chart(fig, use_container_width=True)


def _run_simulation(speed: int) -> None:
    """Run a live match simulation with updates."""
    from ingestion.simulators.match_simulator import MatchSimulator
    from spark_jobs.gold.win_probability import calculate_win_probability

    if "simulator" not in st.session_state:
        st.session_state["simulator"] = MatchSimulator(speed=speed)
        st.session_state["events"] = []

    sim = st.session_state["simulator"]
    events = st.session_state["events"]

    kpi_placeholder = st.empty()
    chart_placeholder = st.empty()
    commentary_placeholder = st.empty()

    if sim.over < 20 and sim.wickets < 10:
        event = sim._simulate_ball()
        events.append(event)
        st.session_state["events"] = events

        with kpi_placeholder.container():
            render_live_match_kpis(
                batting_team=event["batting_team"],
                score=event["total_runs"],
                wickets=event["total_wickets"],
                overs=event["over"] + event["ball"] / 10,
                run_rate=event["run_rate"],
                target=event.get("target"),
            )

        with chart_placeholder.container():
            if event.get("target"):
                prob = calculate_win_probability(
                    target=event["target"],
                    current_score=event["total_runs"],
                    wickets_fallen=event["total_wickets"],
                    overs_completed=event["over"] + event["ball"] / 6,
                )
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(
                        create_win_probability_gauge(
                            prob["batting_team_win_probability"],
                            event["batting_team"],
                        ),
                        use_container_width=True,
                    )
                with col2:
                    st.plotly_chart(
                        create_win_probability_gauge(
                            prob["bowling_team_win_probability"],
                            event["bowling_team"],
                        ),
                        use_container_width=True,
                    )

        with commentary_placeholder.container():
            st.subheader("Recent Deliveries")
            recent = events[-10:][::-1]
            for ev in recent:
                result = f"{ev['runs_scored']} runs"
                if ev.get("is_wicket"):
                    result = f"WICKET! ({ev.get('dismissal_type', 'unknown')})"
                st.text(f"{ev['over']}.{ev['ball']} | {ev['batsman']} vs {ev['bowler']} | {result}")

        if event["match_state"] != "completed":
            time.sleep(max(0.1, 1.0 / speed))
            st.rerun()
    else:
        st.success("Match completed!")
        if st.button("New Match"):
            del st.session_state["simulator"]
            del st.session_state["events"]
            st.session_state["sim_running"] = False
            st.rerun()
