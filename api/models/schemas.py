"""Pydantic schemas for API request/response models."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    service: str = "IPL Analytics API"


class PlayerStats(BaseModel):
    player_id: str
    player_name: str
    nationality: str
    role: str
    matches_played: int = 0
    total_runs: int = 0
    batting_average: float = 0.0
    strike_rate: float = 0.0
    highest_score: int = 0
    fours: int = 0
    sixes: int = 0
    fifties: int = 0
    centuries: int = 0
    total_wickets: int = 0
    economy_rate: float = 0.0


class PlayerListResponse(BaseModel):
    players: list[PlayerStats]
    total: int
    page: int = 1
    per_page: int = 20


class MatchSummary(BaseModel):
    match_id: str
    season: int
    date: str
    venue: str
    city: str
    team1: str
    team2: str
    winner: str
    margin: str
    player_of_match: str
    innings1_runs: int
    innings1_wickets: int
    innings2_runs: int
    innings2_wickets: int
    toss_winner: str
    toss_decision: str


class MatchListResponse(BaseModel):
    matches: list[MatchSummary]
    total: int
    page: int = 1
    per_page: int = 20


class TeamStats(BaseModel):
    team_name: str
    matches_played: int
    wins: int
    losses: int
    win_percentage: float
    avg_runs_scored: float = 0.0
    seasons_played: int = 0


class TeamComparisonResponse(BaseModel):
    team1: TeamStats
    team2: TeamStats
    head_to_head: dict[str, Any] = {}


class VenueStats(BaseModel):
    venue_name: str
    city: str
    matches_hosted: int
    avg_first_innings: float
    avg_second_innings: float
    bat_first_win_pct: float
    chase_win_pct: float
    avg_run_rate: float = 0.0


class WinProbabilityRequest(BaseModel):
    target: int = Field(..., gt=0, description="Target score")
    current_score: int = Field(..., ge=0, description="Current score")
    wickets_fallen: int = Field(..., ge=0, le=10, description="Wickets fallen")
    overs_completed: float = Field(..., ge=0, le=20, description="Overs completed")
    is_chasing: bool = True


class WinProbabilityResponse(BaseModel):
    batting_team_win_probability: float
    bowling_team_win_probability: float
    required_rate: float = 0.0
    current_rate: float = 0.0
    runs_needed: int = 0
    balls_remaining: int = 0


class FantasyScoreRequest(BaseModel):
    runs: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    wickets: int = 0
    overs_bowled: float = 0.0
    runs_conceded: int = 0
    catches: int = 0
    run_outs: int = 0


class FantasyScoreResponse(BaseModel):
    total_fantasy_points: float
    batting_points: float
    bowling_points: float
    fielding_points: float


class SeasonSummary(BaseModel):
    season: int
    total_matches: int
    total_runs: int
    avg_runs_per_match: float
    total_sixes: int
    total_fours: int
    highest_team_score: int
    lowest_team_score: int
