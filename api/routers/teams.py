"""Team analytics API endpoints."""

from fastapi import APIRouter, Query

from api.models.schemas import TeamComparisonResponse, TeamStats
from api.services.analytics_service import get_team_comparison, get_team_stats

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", response_model=list[TeamStats])
async def list_teams() -> list[TeamStats]:
    """Get all team statistics."""
    stats = get_team_stats()
    return [TeamStats(**s) for s in stats]


@router.get("/compare")
async def compare_teams(
    team1: str = Query(..., description="First team name"),
    team2: str = Query(..., description="Second team name"),
) -> TeamComparisonResponse:
    """Compare two teams head-to-head."""
    result = get_team_comparison(team1, team2)
    return TeamComparisonResponse(**result)


@router.get("/rankings")
async def team_rankings(
    season: int | None = Query(None),
) -> dict:
    """Get team rankings by win percentage."""
    stats = get_team_stats()
    return {
        "rankings": [
            {"rank": i + 1, **team}
            for i, team in enumerate(stats)
        ],
        "season": season or "all-time",
    }
