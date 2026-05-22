"""Tests for sample data generation."""

import json
import tempfile
from pathlib import Path

from ingestion.sources.sample_data import (
    generate_ball_by_ball_dataset,
    generate_matches_dataset,
    generate_players_dataset,
    save_sample_data,
)


class TestSampleDataGeneration:
    """Tests for sample data generators."""

    def test_generate_players(self) -> None:
        players = generate_players_dataset()
        assert len(players) >= 40
        for player in players:
            assert "player_id" in player
            assert "player_name" in player
            assert "nationality" in player
            assert "role" in player

    def test_generate_matches(self) -> None:
        matches = generate_matches_dataset()
        assert len(matches) >= 100
        for match in matches:
            assert "match_id" in match
            assert "season" in match
            assert "team1" in match
            assert "team2" in match
            assert "winner" in match

    def test_generate_ball_by_ball(self) -> None:
        matches = generate_matches_dataset()
        balls = generate_ball_by_ball_dataset(matches[:5])
        assert len(balls) > 0
        for ball in balls:
            assert "match_id" in ball
            assert "innings" in ball
            assert "batsman" in ball
            assert "bowler" in ball

    def test_save_sample_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            files = save_sample_data(tmpdir)
            assert len(files) > 0
            for filepath in files:
                path = Path(filepath)
                assert path.exists()
                with open(path) as f:
                    data = json.load(f)
                    assert len(data) > 0


class TestPlayerData:
    """Detailed tests for player data."""

    def test_player_fields(self) -> None:
        players = generate_players_dataset()
        player = players[0]
        expected_fields = [
            "player_id",
            "player_name",
            "nationality",
            "batting_style",
            "bowling_style",
            "role",
            "ipl_debut_year",
        ]
        for field in expected_fields:
            assert field in player

    def test_unique_player_ids(self) -> None:
        players = generate_players_dataset()
        ids = [p["player_id"] for p in players]
        assert len(ids) == len(set(ids))
