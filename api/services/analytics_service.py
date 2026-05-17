"""Analytics service for computing IPL statistics."""

import json
from pathlib import Path
from typing import Any

from monitoring.logger import get_logger

logger = get_logger(__name__)

_DATA_DIR = Path("data/samples")


def _load_json(filename: str) -> list[dict[str, Any]]:
    """Load JSON data file."""
    filepath = _DATA_DIR / filename
    if not filepath.exists():
        from ingestion.sources.sample_data import save_sample_data

        save_sample_data(str(_DATA_DIR))
    with open(filepath) as f:
        return json.load(f)


def get_players(
    page: int = 1, per_page: int = 20, sort_by: str = "total_runs", role: str | None = None
) -> dict[str, Any]:
    """Get player statistics with pagination."""
    players = _load_json("players.json")
    balls = _load_json("ball_by_ball.json")

    batting_stats: dict[str, dict[str, Any]] = {}
    for ball in balls:
        batsman = ball["batsman"]
        if batsman not in batting_stats:
            batting_stats[batsman] = {
                "runs": 0,
                "balls": 0,
                "fours": 0,
                "sixes": 0,
                "matches": set(),
                "dismissals": 0,
            }
        stats = batting_stats[batsman]
        stats["runs"] += ball.get("runs_scored", 0)
        stats["balls"] += 1
        stats["matches"].add(ball["match_id"])
        if ball.get("runs_scored") == 4:
            stats["fours"] += 1
        if ball.get("runs_scored") == 6:
            stats["sixes"] += 1
        if ball.get("is_wicket") and ball.get("batsman") == batsman:
            stats["dismissals"] += 1

    enriched = []
    for player in players:
        name = player["player_name"]
        bs = batting_stats.get(
            name,
            {
                "runs": 0,
                "balls": 0,
                "fours": 0,
                "sixes": 0,
                "matches": set(),
                "dismissals": 0,
            },
        )
        matches = len(bs["matches"]) if isinstance(bs["matches"], set) else 0
        enriched.append(
            {
                **player,
                "matches_played": matches,
                "total_runs": bs["runs"],
                "batting_average": round(bs["runs"] / max(bs["dismissals"], 1), 2),
                "strike_rate": round(bs["runs"] / max(bs["balls"], 1) * 100, 2),
                "highest_score": 0,
                "fours": bs["fours"],
                "sixes": bs["sixes"],
                "fifties": 0,
                "centuries": 0,
                "total_wickets": 0,
                "economy_rate": 0.0,
                "role": player.get("role", "Unknown"),
                "nationality": player.get("nationality", "Unknown"),
            }
        )

    if role:
        enriched = [p for p in enriched if p["role"].lower() == role.lower()]

    enriched.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
    total = len(enriched)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "players": enriched[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_matches(
    page: int = 1, per_page: int = 20, season: int | None = None, team: str | None = None
) -> dict[str, Any]:
    """Get match data with filtering."""
    matches = _load_json("matches.json")

    if season:
        matches = [m for m in matches if m.get("season") == season]
    if team:
        matches = [
            m
            for m in matches
            if team.lower() in m.get("team1", "").lower()
            or team.lower() in m.get("team2", "").lower()
        ]

    matches.sort(key=lambda x: x.get("date", ""), reverse=True)
    total = len(matches)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "matches": matches[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_team_stats(team_name: str | None = None) -> list[dict[str, Any]]:
    """Get team statistics."""
    matches = _load_json("matches.json")

    team_data: dict[str, dict[str, Any]] = {}
    for match in matches:
        for team_key in ["team1", "team2"]:
            team = match[team_key]
            if team_name and team_name.lower() not in team.lower():
                continue
            if team not in team_data:
                team_data[team] = {
                    "team_name": team,
                    "matches_played": 0,
                    "wins": 0,
                    "total_runs": 0,
                    "seasons": set(),
                }
            team_data[team]["matches_played"] += 1
            team_data[team]["seasons"].add(match.get("season", 0))
            if match.get("winner") == team:
                team_data[team]["wins"] += 1

    result = []
    for team, stats in team_data.items():
        result.append(
            {
                "team_name": team,
                "matches_played": stats["matches_played"],
                "wins": stats["wins"],
                "losses": stats["matches_played"] - stats["wins"],
                "win_percentage": round(stats["wins"] / max(stats["matches_played"], 1) * 100, 2),
                "avg_runs_scored": 0.0,
                "seasons_played": len(stats["seasons"]),
            }
        )

    result.sort(key=lambda x: x["win_percentage"], reverse=True)
    return result


def get_team_comparison(team1: str, team2: str) -> dict[str, Any]:
    """Compare two teams head-to-head."""
    matches = _load_json("matches.json")
    all_stats = get_team_stats()

    t1_stats = next((t for t in all_stats if team1.lower() in t["team_name"].lower()), None)
    t2_stats = next((t for t in all_stats if team2.lower() in t["team_name"].lower()), None)

    h2h_matches = [
        m
        for m in matches
        if (
            team1.lower() in m.get("team1", "").lower()
            or team1.lower() in m.get("team2", "").lower()
        )
        and (
            team2.lower() in m.get("team1", "").lower()
            or team2.lower() in m.get("team2", "").lower()
        )
    ]

    t1_wins = len([m for m in h2h_matches if t1_stats and t1_stats["team_name"] == m.get("winner")])
    t2_wins = len([m for m in h2h_matches if t2_stats and t2_stats["team_name"] == m.get("winner")])

    return {
        "team1": t1_stats
        or {
            "team_name": team1,
            "matches_played": 0,
            "wins": 0,
            "losses": 0,
            "win_percentage": 0,
            "seasons_played": 0,
        },
        "team2": t2_stats
        or {
            "team_name": team2,
            "matches_played": 0,
            "wins": 0,
            "losses": 0,
            "win_percentage": 0,
            "seasons_played": 0,
        },
        "head_to_head": {
            "total_matches": len(h2h_matches),
            "team1_wins": t1_wins,
            "team2_wins": t2_wins,
        },
    }


def get_venue_stats() -> list[dict[str, Any]]:
    """Get venue statistics."""
    matches = _load_json("matches.json")

    venue_data: dict[str, dict[str, Any]] = {}
    for match in matches:
        venue = match.get("venue", "Unknown")
        if venue not in venue_data:
            venue_data[venue] = {
                "venue_name": venue,
                "city": match.get("city", "Unknown"),
                "matches_hosted": 0,
                "i1_runs": [],
                "i2_runs": [],
                "bat_first_wins": 0,
            }
        venue_data[venue]["matches_hosted"] += 1
        venue_data[venue]["i1_runs"].append(match.get("innings1_runs", 0))
        venue_data[venue]["i2_runs"].append(match.get("innings2_runs", 0))
        if match.get("result_type") == "runs":
            venue_data[venue]["bat_first_wins"] += 1

    result = []
    for venue, stats in venue_data.items():
        total = stats["matches_hosted"]
        result.append(
            {
                "venue_name": venue,
                "city": stats["city"],
                "matches_hosted": total,
                "avg_first_innings": round(
                    sum(stats["i1_runs"]) / max(len(stats["i1_runs"]), 1), 1
                ),
                "avg_second_innings": round(
                    sum(stats["i2_runs"]) / max(len(stats["i2_runs"]), 1), 1
                ),
                "bat_first_win_pct": round(stats["bat_first_wins"] / max(total, 1) * 100, 2),
                "chase_win_pct": round((total - stats["bat_first_wins"]) / max(total, 1) * 100, 2),
                "avg_run_rate": 0.0,
            }
        )

    result.sort(key=lambda x: x["matches_hosted"], reverse=True)
    return result
