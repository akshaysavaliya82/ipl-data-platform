"""Win probability model using historical IPL data."""

import math

from monitoring.logger import get_logger

logger = get_logger(__name__)


def calculate_win_probability(
    target: int,
    current_score: int,
    wickets_fallen: int,
    overs_completed: float,
    is_chasing: bool = True,
) -> dict[str, float]:
    """Calculate win probability using a heuristic model.

    Based on historical IPL averages and run-rate projections.
    """
    if not is_chasing:
        projected_total = _project_first_innings_total(
            current_score, wickets_fallen, overs_completed,
        )
        batting_win_prob = min(0.95, max(0.05,
            0.5 + (projected_total - 165) * 0.008 - wickets_fallen * 0.03
        ))
        return {
            "batting_team_win_probability": round(batting_win_prob, 4),
            "bowling_team_win_probability": round(1 - batting_win_prob, 4),
            "projected_total": round(projected_total),
        }

    runs_needed = target - current_score
    balls_remaining = max(1, int((20 - overs_completed) * 6))
    wickets_in_hand = 10 - wickets_fallen

    required_rate = (runs_needed / balls_remaining) * 6
    current_rate = (current_score / max(1, overs_completed * 6)) * 6

    rate_factor = current_rate / max(0.1, required_rate)
    wicket_factor = wickets_in_hand / 10.0
    resource_factor = (balls_remaining / 120) * wicket_factor

    base_prob = 1 / (1 + math.exp(-2 * (rate_factor - 1)))
    adjusted_prob = base_prob * 0.6 + resource_factor * 0.3 + wicket_factor * 0.1

    if wickets_fallen >= 8:
        adjusted_prob *= 0.4
    elif wickets_fallen >= 6:
        adjusted_prob *= 0.7

    if runs_needed <= 0:
        adjusted_prob = 1.0
    elif balls_remaining <= 0 and runs_needed > 0:
        adjusted_prob = 0.0

    adjusted_prob = min(0.99, max(0.01, adjusted_prob))

    return {
        "batting_team_win_probability": round(adjusted_prob, 4),
        "bowling_team_win_probability": round(1 - adjusted_prob, 4),
        "required_rate": round(required_rate, 2),
        "current_rate": round(current_rate, 2),
        "runs_needed": runs_needed,
        "balls_remaining": balls_remaining,
        "wickets_in_hand": wickets_in_hand,
    }


def _project_first_innings_total(
    current_score: int, wickets: int, overs: float
) -> float:
    """Project first innings total based on current score and resources."""
    if overs <= 0:
        return 165.0

    current_rate = current_score / overs
    overs_remaining = 20 - overs

    acceleration = 1.0
    if overs < 6:
        acceleration = 1.3
    elif overs < 15:
        acceleration = 1.15
    else:
        acceleration = 1.05

    wicket_penalty = max(0.5, 1 - wickets * 0.08)
    projected_remaining = current_rate * overs_remaining * acceleration * wicket_penalty

    return current_score + projected_remaining


def calculate_fantasy_score(
    runs: int, balls_faced: int, fours: int, sixes: int,
    wickets: int, overs_bowled: float, runs_conceded: int,
    catches: int = 0, run_outs: int = 0,
) -> dict[str, float]:
    """Calculate fantasy cricket score for a player."""
    batting_points = (
        runs * 1.0
        + fours * 1.0
        + sixes * 2.0
        + (25 if runs >= 50 else 0)
        + (50 if runs >= 100 else 0)
        + (-2 if runs == 0 and balls_faced > 0 else 0)
    )

    if balls_faced > 0:
        strike_rate = (runs / balls_faced) * 100
        if strike_rate >= 170:
            batting_points += 6
        elif strike_rate >= 150:
            batting_points += 4
        elif strike_rate >= 130:
            batting_points += 2
        elif strike_rate < 60 and balls_faced >= 10:
            batting_points -= 6
        elif strike_rate < 70 and balls_faced >= 10:
            batting_points -= 4

    bowling_points = (
        wickets * 25.0
        + (25 if wickets >= 3 else 0)
        + (50 if wickets >= 5 else 0)
    )

    if overs_bowled >= 2:
        economy = runs_conceded / overs_bowled
        if economy <= 5:
            bowling_points += 6
        elif economy <= 6:
            bowling_points += 4
        elif economy <= 7:
            bowling_points += 2
        elif economy >= 12:
            bowling_points -= 6
        elif economy >= 11:
            bowling_points -= 4

    fielding_points = catches * 8.0 + run_outs * 12.0

    total = batting_points + bowling_points + fielding_points

    return {
        "total_fantasy_points": round(total, 1),
        "batting_points": round(batting_points, 1),
        "bowling_points": round(bowling_points, 1),
        "fielding_points": round(fielding_points, 1),
    }
