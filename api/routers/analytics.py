"""Advanced analytics API endpoints."""

from fastapi import APIRouter

from api.models.schemas import (
    FantasyScoreRequest,
    FantasyScoreResponse,
    WinProbabilityRequest,
    WinProbabilityResponse,
)
from spark_jobs.gold.win_probability import (
    calculate_fantasy_score,
    calculate_win_probability,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/win-probability", response_model=WinProbabilityResponse)
async def get_win_probability(
    request: WinProbabilityRequest,
) -> WinProbabilityResponse:
    """Calculate win probability based on current match state."""
    result = calculate_win_probability(
        target=request.target,
        current_score=request.current_score,
        wickets_fallen=request.wickets_fallen,
        overs_completed=request.overs_completed,
        is_chasing=request.is_chasing,
    )
    return WinProbabilityResponse(**result)


@router.post("/fantasy-score", response_model=FantasyScoreResponse)
async def get_fantasy_score(
    request: FantasyScoreRequest,
) -> FantasyScoreResponse:
    """Calculate fantasy cricket score for a player."""
    result = calculate_fantasy_score(
        runs=request.runs,
        balls_faced=request.balls_faced,
        fours=request.fours,
        sixes=request.sixes,
        wickets=request.wickets,
        overs_bowled=request.overs_bowled,
        runs_conceded=request.runs_conceded,
        catches=request.catches,
        run_outs=request.run_outs,
    )
    return FantasyScoreResponse(**result)


@router.get("/pressure-index")
async def pressure_index(
    runs_needed: int = 50,
    balls_remaining: int = 30,
    wickets_in_hand: int = 5,
) -> dict:
    """Calculate pressure index for current match situation."""
    required_rate = (runs_needed / balls_remaining) * 6 if balls_remaining > 0 else 999
    wicket_pressure = (10 - wickets_in_hand) / 10.0
    rate_pressure = min(required_rate / 12.0, 1.0)
    ball_pressure = 1 - (balls_remaining / 120.0)

    pressure_index = (rate_pressure * 0.4 + wicket_pressure * 0.35 + ball_pressure * 0.25) * 100

    return {
        "pressure_index": round(pressure_index, 1),
        "required_rate": round(required_rate, 2),
        "wicket_pressure": round(wicket_pressure * 100, 1),
        "rate_pressure": round(rate_pressure * 100, 1),
        "assessment": (
            "extreme" if pressure_index > 80
            else "high" if pressure_index > 60
            else "moderate" if pressure_index > 40
            else "low"
        ),
    }
