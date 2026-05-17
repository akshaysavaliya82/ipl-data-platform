"""Player analytics API endpoints."""

from fastapi import APIRouter, Query

from api.models.schemas import PlayerListResponse
from api.services.analytics_service import get_players

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("/", response_model=PlayerListResponse)
async def list_players(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("total_runs", description="Sort field"),
    role: str | None = Query(None, description="Filter by role"),
) -> PlayerListResponse:
    """Get paginated list of player statistics."""
    result = get_players(page=page, per_page=per_page, sort_by=sort_by, role=role)
    return PlayerListResponse(**result)


@router.get("/top-batsmen")
async def top_batsmen(
    limit: int = Query(10, ge=1, le=50),
    season: int | None = Query(None),
) -> dict:
    """Get top batsmen by runs scored."""
    result = get_players(page=1, per_page=limit, sort_by="total_runs")
    return {
        "top_batsmen": result["players"][:limit],
        "criteria": "total_runs",
    }


@router.get("/top-bowlers")
async def top_bowlers(
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """Get top bowlers by wickets taken."""
    result = get_players(page=1, per_page=limit, sort_by="total_wickets", role="Bowler")
    return {
        "top_bowlers": result["players"][:limit],
        "criteria": "total_wickets",
    }


@router.get("/strike-rate-leaders")
async def strike_rate_leaders(
    limit: int = Query(10, ge=1, le=50),
    min_runs: int = Query(100, description="Minimum runs to qualify"),
) -> dict:
    """Get players with highest strike rates."""
    result = get_players(page=1, per_page=100, sort_by="strike_rate")
    filtered = [p for p in result["players"] if p.get("total_runs", 0) >= min_runs]
    return {
        "strike_rate_leaders": filtered[:limit],
        "criteria": "strike_rate",
        "min_runs_qualifier": min_runs,
    }
