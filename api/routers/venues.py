"""Venue analytics API endpoints."""

from fastapi import APIRouter, Query

from api.models.schemas import VenueStats
from api.services.analytics_service import get_venue_stats

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.get("/", response_model=list[VenueStats])
async def list_venues() -> list[VenueStats]:
    """Get all venue statistics."""
    stats = get_venue_stats()
    return [VenueStats(**s) for s in stats]


@router.get("/best-batting")
async def best_batting_venues(
    limit: int = Query(5, ge=1, le=20),
) -> dict:
    """Get venues with highest average scores."""
    stats = get_venue_stats()
    stats.sort(key=lambda x: x["avg_first_innings"], reverse=True)
    return {"best_batting_venues": stats[:limit]}


@router.get("/chase-friendly")
async def chase_friendly_venues(
    limit: int = Query(5, ge=1, le=20),
) -> dict:
    """Get venues with highest chase success rate."""
    stats = get_venue_stats()
    stats.sort(key=lambda x: x["chase_win_pct"], reverse=True)
    return {"chase_friendly_venues": stats[:limit]}
