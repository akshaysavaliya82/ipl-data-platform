"""Sample IPL dataset generator for historical analytics."""

import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from monitoring.logger import get_logger

logger = get_logger(__name__)

SEASONS = list(range(2008, 2025))

TEAMS_BY_ERA: dict[str, list[int]] = {
    "Mumbai Indians": list(range(2008, 2025)),
    "Chennai Super Kings": [*list(range(2008, 2016)), *list(range(2018, 2025))],
    "Royal Challengers Bangalore": list(range(2008, 2025)),
    "Kolkata Knight Riders": list(range(2008, 2025)),
    "Delhi Capitals": list(range(2008, 2025)),
    "Rajasthan Royals": [*list(range(2008, 2016)), *list(range(2018, 2025))],
    "Sunrisers Hyderabad": list(range(2013, 2025)),
    "Punjab Kings": list(range(2008, 2025)),
    "Gujarat Titans": list(range(2022, 2025)),
    "Lucknow Super Giants": list(range(2022, 2025)),
    "Deccan Chargers": list(range(2008, 2013)),
    "Pune Warriors": list(range(2011, 2014)),
    "Kochi Tuskers Kerala": [2011],
    "Rising Pune Supergiant": [2016, 2017],
    "Gujarat Lions": [2016, 2017],
}

VENUES = [
    {"name": "Wankhede Stadium", "city": "Mumbai"},
    {"name": "M. A. Chidambaram Stadium", "city": "Chennai"},
    {"name": "M. Chinnaswamy Stadium", "city": "Bangalore"},
    {"name": "Eden Gardens", "city": "Kolkata"},
    {"name": "Arun Jaitley Stadium", "city": "Delhi"},
    {"name": "Sawai Mansingh Stadium", "city": "Jaipur"},
    {"name": "Rajiv Gandhi Intl Stadium", "city": "Hyderabad"},
    {"name": "IS Bindra Stadium", "city": "Mohali"},
    {"name": "Narendra Modi Stadium", "city": "Ahmedabad"},
    {"name": "BRSABV Ekana Stadium", "city": "Lucknow"},
    {"name": "DY Patil Stadium", "city": "Mumbai"},
    {"name": "Brabourne Stadium", "city": "Mumbai"},
]

PLAYER_NAMES = [
    "Virat Kohli",
    "Rohit Sharma",
    "MS Dhoni",
    "AB de Villiers",
    "David Warner",
    "Suresh Raina",
    "Chris Gayle",
    "Shikhar Dhawan",
    "KL Rahul",
    "Rishabh Pant",
    "Faf du Plessis",
    "Jos Buttler",
    "Quinton de Kock",
    "Sanju Samson",
    "Shreyas Iyer",
    "Ruturaj Gaikwad",
    "Suryakumar Yadav",
    "Hardik Pandya",
    "Ravindra Jadeja",
    "Andre Russell",
    "Kieron Pollard",
    "Glenn Maxwell",
    "Jasprit Bumrah",
    "Yuzvendra Chahal",
    "Rashid Khan",
    "Kagiso Rabada",
    "Trent Boult",
    "Pat Cummins",
    "Mohammed Shami",
    "Bhuvneshwar Kumar",
    "Amit Mishra",
    "Dwayne Bravo",
    "Lasith Malinga",
    "Sunil Narine",
    "Ravichandran Ashwin",
    "Axar Patel",
    "Washington Sundar",
    "Kuldeep Yadav",
    "Ishan Kishan",
    "Prithvi Shaw",
    "Devdutt Padikkal",
    "Shubman Gill",
    "Tilak Varma",
    "Rinku Singh",
    "Yashasvi Jaiswal",
    "Matheesha Pathirana",
]


def generate_players_dataset() -> list[dict[str, Any]]:
    """Generate player dimension data."""
    players = []
    for i, name in enumerate(PLAYER_NAMES):
        player = {
            "player_id": f"P{i + 1:04d}",
            "player_name": name,
            "nationality": random.choice(
                [
                    "India",
                    "Australia",
                    "South Africa",
                    "England",
                    "New Zealand",
                    "West Indies",
                    "Sri Lanka",
                    "Afghanistan",
                    "Bangladesh",
                ]
            ),
            "date_of_birth": (
                datetime(1985, 1, 1, tzinfo=UTC) + timedelta(days=random.randint(0, 5000))
            ).strftime("%Y-%m-%d"),
            "batting_style": random.choice(["Right-hand bat", "Left-hand bat"]),
            "bowling_style": random.choice(
                [
                    "Right-arm fast",
                    "Right-arm medium",
                    "Left-arm fast",
                    "Left-arm orthodox",
                    "Right-arm leg-break",
                    "Right-arm offbreak",
                    "Slow left-arm orthodox",
                    "None",
                ]
            ),
            "role": random.choice(["Batsman", "Bowler", "All-rounder", "Wicketkeeper"]),
            "ipl_debut_year": random.choice(SEASONS[:10]),
        }
        players.append(player)
    return players


def generate_matches_dataset(num_matches: int = 200) -> list[dict[str, Any]]:
    """Generate historical match data."""
    matches = []
    for i in range(num_matches):
        season = random.choice(SEASONS)
        teams_in_season = [t for t, years in TEAMS_BY_ERA.items() if season in years]
        if len(teams_in_season) < 2:
            continue
        team1, team2 = random.sample(teams_in_season, 2)
        venue = random.choice(VENUES)
        toss_winner = random.choice([team1, team2])
        toss_decision = random.choice(["bat", "field"])

        first_batting = (
            toss_winner if toss_decision == "bat" else (team2 if toss_winner == team1 else team1)
        )
        second_batting = team2 if first_batting == team1 else team1

        i1_runs = random.randint(100, 230)
        i1_wickets = random.randint(2, 10)
        i2_target = i1_runs + 1

        chase_success = random.random() > 0.45
        if chase_success:
            i2_runs = i2_target
            i2_wickets = random.randint(1, 8)
            winner = second_batting
            margin = f"{10 - i2_wickets} wickets"
            result_type = "wickets"
        else:
            i2_runs = random.randint(max(80, i1_runs - 60), i1_runs - 1)
            i2_wickets = random.choice([10, random.randint(5, 10)])
            winner = first_batting
            margin = f"{i1_runs - i2_runs} runs"
            result_type = "runs"

        match_date = datetime(season, random.randint(3, 5), random.randint(1, 28), tzinfo=UTC)
        match = {
            "match_id": f"M{i + 1:05d}",
            "season": season,
            "match_number": i + 1,
            "date": match_date.strftime("%Y-%m-%d"),
            "venue": venue["name"],
            "city": venue["city"],
            "team1": team1,
            "team2": team2,
            "toss_winner": toss_winner,
            "toss_decision": toss_decision,
            "first_batting": first_batting,
            "second_batting": second_batting,
            "innings1_runs": i1_runs,
            "innings1_wickets": i1_wickets,
            "innings1_overs": 20.0 if i1_wickets < 10 else round(random.uniform(15, 20), 1),
            "innings2_runs": i2_runs,
            "innings2_wickets": i2_wickets,
            "innings2_overs": round(random.uniform(15, 20), 1),
            "winner": winner,
            "result_type": result_type,
            "margin": margin,
            "player_of_match": random.choice(PLAYER_NAMES),
            "umpire1": random.choice(
                ["Nitin Menon", "KN Ananthapadmanabhan", "Anil Chaudhary", "Chris Gaffaney"]
            ),
            "umpire2": random.choice(
                ["Virender Sharma", "Jayaraman Madanagopal", "Michael Gough", "Rod Tucker"]
            ),
        }
        matches.append(match)
    return matches


def generate_ball_by_ball_dataset(
    matches: list[dict[str, Any]], balls_per_match: int = 240
) -> list[dict[str, Any]]:
    """Generate ball-by-ball data for given matches."""
    all_balls = []
    for match in matches[:50]:  # Limit for sample data
        players = random.sample(PLAYER_NAMES, 22)
        batting_order = players[:11]
        bowling_options = players[11:]

        for innings in [1, 2]:
            batting_team = match["first_batting"] if innings == 1 else match["second_batting"]
            bowling_team = match["second_batting"] if innings == 1 else match["first_batting"]
            batsman_idx = 0
            non_striker_idx = 1
            total_runs = 0
            wickets = 0
            target = match["innings1_runs"] + 1 if innings == 2 else None

            for over in range(20):
                bowler = bowling_options[over % len(bowling_options)]
                for ball in range(6):
                    if wickets >= 10:
                        break
                    if innings == 2 and target and total_runs >= target:
                        break

                    runs = random.choices([0, 1, 2, 3, 4, 6], weights=[25, 30, 15, 5, 18, 7], k=1)[
                        0
                    ]
                    is_wicket = random.random() < 0.04
                    is_boundary = runs in (4, 6) and not is_wicket

                    if is_wicket:
                        runs = 0

                    total_runs += runs

                    ball_event = {
                        "ball_id": str(uuid.uuid4()),
                        "match_id": match["match_id"],
                        "season": match["season"],
                        "innings": innings,
                        "over": over,
                        "ball": ball,
                        "batting_team": batting_team,
                        "bowling_team": bowling_team,
                        "batsman": batting_order[min(batsman_idx, 10)],
                        "non_striker": batting_order[min(non_striker_idx, 10)],
                        "bowler": bowler,
                        "runs_scored": runs,
                        "extras": 0,
                        "extras_type": "none",
                        "is_wicket": is_wicket,
                        "dismissal_type": (
                            random.choice(["bowled", "caught", "lbw", "run out", "stumped"])
                            if is_wicket
                            else "none"
                        ),
                        "is_boundary": is_boundary,
                        "is_six": runs == 6 and is_boundary,
                        "is_four": runs == 4 and is_boundary,
                        "total_runs": total_runs,
                        "total_wickets": wickets + (1 if is_wicket else 0),
                        "phase": "powerplay" if over < 6 else "middle" if over < 16 else "death",
                    }
                    all_balls.append(ball_event)

                    if is_wicket:
                        wickets += 1
                        batsman_idx = min(batsman_idx + 1, 10)
                    elif runs % 2 == 1:
                        batsman_idx, non_striker_idx = non_striker_idx, batsman_idx

                if wickets >= 10:
                    break
                if innings == 2 and target and total_runs >= target:
                    break

    return all_balls


def save_sample_data(output_dir: str = "data/samples") -> dict[str, str]:
    """Generate and save all sample datasets."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    players = generate_players_dataset()
    matches = generate_matches_dataset(200)
    balls = generate_ball_by_ball_dataset(matches)

    files = {}

    players_file = output_path / "players.json"
    with open(players_file, "w") as f:
        json.dump(players, f, indent=2)
    files["players"] = str(players_file)

    matches_file = output_path / "matches.json"
    with open(matches_file, "w") as f:
        json.dump(matches, f, indent=2)
    files["matches"] = str(matches_file)

    balls_file = output_path / "ball_by_ball.json"
    with open(balls_file, "w") as f:
        json.dump(balls, f, indent=2)
    files["ball_by_ball"] = str(balls_file)

    teams = list({m["team1"] for m in matches} | {m["team2"] for m in matches})
    teams_data = [
        {
            "team_id": f"T{i + 1:03d}",
            "team_name": team,
            "home_venue": random.choice(VENUES)["name"],
            "home_city": random.choice(VENUES)["city"],
            "titles_won": random.randint(0, 5),
            "first_season": min(y for y in TEAMS_BY_ERA.get(team, [2008])),
        }
        for i, team in enumerate(sorted(teams))
    ]
    teams_file = output_path / "teams.json"
    with open(teams_file, "w") as f:
        json.dump(teams_data, f, indent=2)
    files["teams"] = str(teams_file)

    venues_data = [
        {
            **v,
            "venue_id": f"V{i + 1:03d}",
            "country": "India",
            "capacity": random.randint(25000, 130000),
        }
        for i, v in enumerate(VENUES)
    ]
    venues_file = output_path / "venues.json"
    with open(venues_file, "w") as f:
        json.dump(venues_data, f, indent=2)
    files["venues"] = str(venues_file)

    logger.info(
        "sample_data_saved",
        files=list(files.keys()),
        player_count=len(players),
        match_count=len(matches),
        ball_count=len(balls),
    )
    return files


if __name__ == "__main__":
    save_sample_data()
