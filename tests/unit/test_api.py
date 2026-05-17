"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_health(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"

    def test_api_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"


class TestPlayerEndpoints:
    """Tests for player API endpoints."""

    def test_list_players(self, client: TestClient) -> None:
        response = client.get("/api/v1/players/")
        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert "total" in data

    def test_top_batsmen(self, client: TestClient) -> None:
        response = client.get("/api/v1/players/top-batsmen?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "top_batsmen" in data


class TestMatchEndpoints:
    """Tests for match API endpoints."""

    def test_list_matches(self, client: TestClient) -> None:
        response = client.get("/api/v1/matches/")
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data

    def test_recent_matches(self, client: TestClient) -> None:
        response = client.get("/api/v1/matches/recent?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "recent_matches" in data

    def test_seasons(self, client: TestClient) -> None:
        response = client.get("/api/v1/matches/seasons")
        assert response.status_code == 200
        data = response.json()
        assert "seasons" in data


class TestTeamEndpoints:
    """Tests for team API endpoints."""

    def test_list_teams(self, client: TestClient) -> None:
        response = client.get("/api/v1/teams/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_team_rankings(self, client: TestClient) -> None:
        response = client.get("/api/v1/teams/rankings")
        assert response.status_code == 200
        data = response.json()
        assert "rankings" in data


class TestVenueEndpoints:
    """Tests for venue API endpoints."""

    def test_list_venues(self, client: TestClient) -> None:
        response = client.get("/api/v1/venues/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_best_batting_venues(self, client: TestClient) -> None:
        response = client.get("/api/v1/venues/best-batting?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert "best_batting_venues" in data


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoints."""

    def test_win_probability(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/analytics/win-probability",
            json={
                "target": 180,
                "current_score": 100,
                "wickets_fallen": 3,
                "overs_completed": 12.0,
                "is_chasing": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "batting_team_win_probability" in data
        assert "bowling_team_win_probability" in data

    def test_fantasy_score(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/analytics/fantasy-score",
            json={
                "runs": 50,
                "balls_faced": 35,
                "fours": 5,
                "sixes": 2,
                "wickets": 1,
                "overs_bowled": 4.0,
                "runs_conceded": 28,
                "catches": 1,
                "run_outs": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_fantasy_points" in data

    def test_pressure_index(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/analytics/pressure-index",
            params={
                "runs_needed": 50,
                "balls_remaining": 30,
                "wickets_in_hand": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "pressure_index" in data
        assert "assessment" in data
