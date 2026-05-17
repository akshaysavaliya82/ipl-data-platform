"""Tests for match simulator."""

from ingestion.simulators.match_simulator import MatchSimulator


class TestMatchSimulator:
    """Tests for MatchSimulator class."""

    def test_simulator_initialization(self) -> None:
        sim = MatchSimulator(speed=10)
        assert sim.innings == 1
        assert sim.over == 0
        assert sim.ball == 0
        assert sim.runs == 0
        assert sim.wickets == 0

    def test_generate_sample_events(self) -> None:
        sim = MatchSimulator(speed=10)
        events = sim.generate_sample_events(num_events=5)
        assert len(events) == 5
        for event in events:
            assert "event_id" in event
            assert "match_id" in event
            assert "innings" in event
            assert "over" in event
            assert "ball" in event
            assert "batsman" in event
            assert "bowler" in event
            assert "runs_scored" in event

    def test_event_fields_complete(self) -> None:
        sim = MatchSimulator(speed=10)
        events = sim.generate_sample_events(num_events=1)
        event = events[0]
        required_fields = [
            "event_id", "match_id", "timestamp", "innings",
            "over", "ball", "batsman", "bowler", "runs_scored",
            "is_wicket", "total_runs", "total_wickets", "run_rate",
        ]
        for field in required_fields:
            assert field in event, f"Missing field: {field}"

    def test_runs_scored_valid(self) -> None:
        sim = MatchSimulator(speed=10)
        events = sim.generate_sample_events(num_events=50)
        for event in events:
            assert event["runs_scored"] >= 0
            assert event["runs_scored"] <= 6

    def test_wickets_bounded(self) -> None:
        sim = MatchSimulator(speed=10)
        events = sim.generate_sample_events(num_events=100)
        for event in events:
            assert event["total_wickets"] >= 0
            assert event["total_wickets"] <= 10

    def test_match_summary(self) -> None:
        sim = MatchSimulator(speed=10)
        sim.generate_sample_events(num_events=10)
        summary = sim.generate_match_summary()
        assert "match_id" in summary
        assert "total_runs" in summary
        assert "total_wickets" in summary
