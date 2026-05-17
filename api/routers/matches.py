"""Match analytics API endpoints."""

from fastapi import APIRouter, Query

from api.models.schemas import MatchListResponse
from api.services.analytics_service import get_matches

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("/", response_model=MatchListResponse)
async def list_matches(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    season: int | None = Query(None, description="Filter by season"),
    team: str | None = Query(None, description="Filter by team"),
) -> MatchListResponse:
    """Get paginated list of matches with optional filters."""
    result = get_matches(page=page, per_page=per_page, season=season, team=team)
    return MatchListResponse(**result)


@router.get("/seasons")
async def get_seasons() -> dict:
    """Get available seasons and summary stats."""
    result = get_matches(page=1, per_page=1000)
    seasons: dict[int, dict] = {}
    for match in result["matches"]:
        season = match.get("season", 0)
        if season not in seasons:
            seasons[season] = {
                "season": season, "matches": 0, "total_runs": 0,
            }
        seasons[season]["matches"] += 1
        seasons[season]["total_runs"] += (
            match.get("innings1_runs", 0) + match.get("innings2_runs", 0)
        )

    season_list = sorted(seasons.values(), key=lambda x: x["season"], reverse=True)
    for s in season_list:
        s["avg_runs_per_match"] = round(s["total_runs"] / max(s["matches"], 1), 1)
    return {"seasons": season_list}


@router.get("/recent")
async def recent_matches(
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """Get most recent matches."""
    result = get_matches(page=1, per_page=limit)
    return {"recent_matches": result["matches"][:limit]}
