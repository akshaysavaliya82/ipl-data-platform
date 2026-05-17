"""Tests for win probability and fantasy score calculations."""

from spark_jobs.gold.win_probability import (
    calculate_fantasy_score,
    calculate_win_probability,
)


class TestWinProbability:
    """Tests for win probability calculations."""

    def test_basic_probability(self) -> None:
        result = calculate_win_probability(
            target=180, current_score=100,
            wickets_fallen=3, overs_completed=12.0,
        )
        assert "batting_team_win_probability" in result
        assert "bowling_team_win_probability" in result
        assert 0 <= result["batting_team_win_probability"] <= 1
        assert 0 <= result["bowling_team_win_probability"] <= 1

    def test_probabilities_sum_to_one(self) -> None:
        result = calculate_win_probability(
            target=180, current_score=100,
            wickets_fallen=3, overs_completed=12.0,
        )
        total = (
            result["batting_team_win_probability"]
            + result["bowling_team_win_probability"]
        )
        assert abs(total - 1.0) < 0.01

    def test_easy_chase(self) -> None:
        result = calculate_win_probability(
            target=150, current_score=145,
            wickets_fallen=1, overs_completed=18.0,
        )
        assert result["batting_team_win_probability"] > 0.5

    def test_difficult_chase(self) -> None:
        result = calculate_win_probability(
            target=200, current_score=50,
            wickets_fallen=7, overs_completed=15.0,
        )
        assert result["batting_team_win_probability"] < 0.5

    def test_response_fields(self) -> None:
        result = calculate_win_probability(
            target=180, current_score=90,
            wickets_fallen=4, overs_completed=10.0,
        )
        expected_fields = [
            "batting_team_win_probability",
            "bowling_team_win_probability",
            "required_rate",
            "current_rate",
            "runs_needed",
            "balls_remaining",
        ]
        for field in expected_fields:
            assert field in result


class TestFantasyScore:
    """Tests for fantasy score calculations."""

    def test_basic_fantasy_score(self) -> None:
        result = calculate_fantasy_score(
            runs=50, balls_faced=35, fours=5, sixes=2,
            wickets=1, overs_bowled=4.0, runs_conceded=28,
        )
        assert "total_fantasy_points" in result
        assert "batting_points" in result
        assert "bowling_points" in result
        assert "fielding_points" in result

    def test_zero_performance(self) -> None:
        result = calculate_fantasy_score()
        assert result["total_fantasy_points"] >= 0

    def test_high_batting_score(self) -> None:
        result = calculate_fantasy_score(
            runs=100, balls_faced=60, fours=10, sixes=5,
        )
        assert result["batting_points"] > 0
        assert result["total_fantasy_points"] > 100

    def test_bowling_performance(self) -> None:
        result = calculate_fantasy_score(
            wickets=3, overs_bowled=4.0, runs_conceded=20,
        )
        assert result["bowling_points"] > 0

    def test_fielding_points(self) -> None:
        result = calculate_fantasy_score(catches=2, run_outs=1)
        assert result["fielding_points"] > 0
