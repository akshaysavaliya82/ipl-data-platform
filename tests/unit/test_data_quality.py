"""Tests for data quality validation framework."""

import json
import tempfile
from pathlib import Path

from data_quality.checks.validators import DataValidator, ValidationResult


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_passed_result(self) -> None:
        result = ValidationResult(check_name="test", passed=True)
        assert result.passed is True
        assert result.check_name == "test"
        assert len(result.failures) == 0

    def test_failed_result(self) -> None:
        result = ValidationResult(
            check_name="test", passed=False,
            failures=["error1", "error2"],
        )
        assert result.passed is False
        assert len(result.failures) == 2

    def test_to_dict(self) -> None:
        result = ValidationResult(
            check_name="test", passed=True,
            details={"key": "value"},
        )
        d = result.to_dict()
        assert d["check_name"] == "test"
        assert d["passed"] is True
        assert "timestamp" in d


class TestDataValidator:
    """Tests for DataValidator class."""

    def _create_sample_data(self, tmpdir: str) -> None:
        """Create sample data files for testing."""
        samples_dir = Path(tmpdir) / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)

        matches = [
            {
                "match_id": f"M{i}",
                "season": 2024,
                "date": "2024-04-01",
                "venue": "Wankhede",
                "city": "Mumbai",
                "team1": "MI",
                "team2": "CSK",
                "winner": "MI",
                "toss_winner": "MI",
                "toss_decision": "bat",
                "innings1_runs": 180,
                "innings2_runs": 170,
                "first_batting": "MI",
                "second_batting": "CSK",
            }
            for i in range(5)
        ]
        with open(samples_dir / "matches.json", "w") as f:
            json.dump(matches, f)

        players = [
            {
                "player_id": f"P{i}",
                "player_name": f"Player {i}",
                "nationality": "India",
                "batting_style": "Right",
                "bowling_style": "Right-arm fast",
                "role": "Batsman",
                "ipl_debut_year": 2020,
            }
            for i in range(5)
        ]
        with open(samples_dir / "players.json", "w") as f:
            json.dump(players, f)

        balls = [
            {
                "ball_id": f"B{i}",
                "match_id": "M0",
                "season": 2024,
                "innings": 1,
                "over": 0,
                "ball": i,
                "batsman": "Player 0",
                "non_striker": "Player 1",
                "bowler": "Player 2",
                "runs_scored": 4,
                "extras": 0,
                "extras_type": None,
                "is_wicket": False,
                "dismissal_type": None,
                "batting_team": "MI",
                "bowling_team": "CSK",
            }
            for i in range(6)
        ]
        with open(samples_dir / "ball_by_ball.json", "w") as f:
            json.dump(balls, f)

        with open(samples_dir / "teams.json", "w") as f:
            json.dump([{"team_name": "MI"}], f)
        with open(samples_dir / "venues.json", "w") as f:
            json.dump([{"venue_name": "Wankhede"}], f)

    def test_null_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_sample_data(tmpdir)
            validator = DataValidator(tmpdir)
            result = validator.check_nulls(tmpdir)
            assert result["passed"] is True

    def test_duplicate_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_sample_data(tmpdir)
            validator = DataValidator(tmpdir)
            result = validator.check_duplicates(tmpdir)
            assert result["passed"] is True

    def test_schema_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_sample_data(tmpdir)
            validator = DataValidator(tmpdir)
            result = validator.check_schema(tmpdir)
            assert result["passed"] is True

    def test_freshness_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_sample_data(tmpdir)
            validator = DataValidator(tmpdir)
            result = validator.check_freshness(tmpdir)
            assert result["passed"] is True

    def test_run_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_sample_data(tmpdir)
            validator = DataValidator(tmpdir)
            result = validator.run_all_checks(tmpdir)
            assert result["overall_passed"] is True
            assert result["total_checks"] == 4
