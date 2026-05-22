"""Tests for analytics service."""

from api.services.analytics_service import (
    get_matches,
    get_players,
    get_team_stats,
    get_venue_stats,
)


class TestGetPlayers:
    """Tests for get_players function."""

    def test_returns_players(self) -> None:
        result = get_players(page=1, per_page=10)
        assert "players" in result
        assert "total" in result
        assert len(result["players"]) <= 10

    def test_pagination(self) -> None:
        page1 = get_players(page=1, per_page=5)
        page2 = get_players(page=2, per_page=5)
        assert page1["page"] == 1
        assert page2["page"] == 2

    def test_sorting(self) -> None:
        result = get_players(page=1, per_page=10, sort_by="total_runs")
        players = result["players"]
        if len(players) >= 2:
            assert players[0]["total_runs"] >= players[1]["total_runs"]


class TestGetMatches:
    """Tests for get_matches function."""

    def test_returns_matches(self) -> None:
        result = get_matches(page=1, per_page=10)
        assert "matches" in result
        assert "total" in result

    def test_pagination(self) -> None:
        result = get_matches(page=1, per_page=5)
        assert result["page"] == 1
        assert result["per_page"] == 5


class TestGetTeamStats:
    """Tests for get_team_stats function."""

    def test_returns_team_stats(self) -> None:
        result = get_team_stats()
        assert len(result) > 0
        for team in result:
            assert "team_name" in team
            assert "matches_played" in team
            assert "wins" in team
            assert "win_percentage" in team

    def test_win_percentage_valid(self) -> None:
        result = get_team_stats()
        for team in result:
            assert 0 <= team["win_percentage"] <= 100


class TestGetVenueStats:
    """Tests for get_venue_stats function."""

    def test_returns_venue_stats(self) -> None:
        result = get_venue_stats()
        assert len(result) > 0
        for venue in result:
            assert "venue_name" in venue
            assert "matches_hosted" in venue
