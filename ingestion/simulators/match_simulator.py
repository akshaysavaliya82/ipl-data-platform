"""Synthetic live match simulator for IPL ball-by-ball events."""

import random
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from monitoring.logger import get_logger

logger = get_logger(__name__)

IPL_TEAMS = [
    "Mumbai Indians",
    "Chennai Super Kings",
    "Royal Challengers Bangalore",
    "Kolkata Knight Riders",
    "Delhi Capitals",
    "Rajasthan Royals",
    "Sunrisers Hyderabad",
    "Punjab Kings",
    "Gujarat Titans",
    "Lucknow Super Giants",
]

IPL_VENUES = [
    {"name": "Wankhede Stadium", "city": "Mumbai", "capacity": 33108},
    {"name": "M. A. Chidambaram Stadium", "city": "Chennai", "capacity": 50000},
    {"name": "M. Chinnaswamy Stadium", "city": "Bangalore", "capacity": 40000},
    {"name": "Eden Gardens", "city": "Kolkata", "capacity": 68000},
    {"name": "Arun Jaitley Stadium", "city": "Delhi", "capacity": 41820},
    {"name": "Sawai Mansingh Stadium", "city": "Jaipur", "capacity": 30000},
    {"name": "Rajiv Gandhi Intl Stadium", "city": "Hyderabad", "capacity": 55000},
    {"name": "IS Bindra Stadium", "city": "Mohali", "capacity": 26950},
    {"name": "Narendra Modi Stadium", "city": "Ahmedabad", "capacity": 132000},
    {"name": "BRSABV Ekana Stadium", "city": "Lucknow", "capacity": 50000},
]


def _player(name: str, role: str, bat: str, bowl: str) -> dict[str, Any]:
    return {"name": name, "role": role, "batting_style": bat, "bowling_style": bowl}


PLAYER_POOL: dict[str, list[dict[str, Any]]] = {
    "Mumbai Indians": [
        _player("Rohit Sharma", "batsman", "right", "right-arm offbreak"),
        _player("Ishan Kishan", "wicketkeeper", "left", "none"),
        _player("Suryakumar Yadav", "batsman", "right", "right-arm offbreak"),
        _player("Tilak Varma", "batsman", "left", "right-arm offbreak"),
        _player("Hardik Pandya", "allrounder", "right", "right-arm medium-fast"),
        _player("Tim David", "batsman", "right", "right-arm offbreak"),
        _player("Nehal Wadhera", "batsman", "right", "none"),
        _player("Jasprit Bumrah", "bowler", "right", "right-arm fast"),
        _player("Piyush Chawla", "bowler", "right", "right-arm legbreak"),
        _player("Gerald Coetzee", "bowler", "right", "right-arm fast"),
        _player("Akash Madhwal", "bowler", "right", "right-arm medium-fast"),
    ],
    "Chennai Super Kings": [
        _player("Ruturaj Gaikwad", "batsman", "right", "right-arm offbreak"),
        _player("Devon Conway", "batsman", "left", "none"),
        _player("Ajinkya Rahane", "batsman", "right", "none"),
        _player("Shivam Dube", "allrounder", "left", "right-arm medium"),
        _player("Ravindra Jadeja", "allrounder", "left", "left-arm orthodox"),
        _player("MS Dhoni", "wicketkeeper", "right", "right-arm medium"),
        _player("Moeen Ali", "allrounder", "left", "right-arm offbreak"),
        _player("Deepak Chahar", "bowler", "right", "right-arm medium-fast"),
        _player("Tushar Deshpande", "bowler", "right", "right-arm fast"),
        _player("Matheesha Pathirana", "bowler", "right", "right-arm fast"),
        _player("Maheesh Theekshana", "bowler", "right", "right-arm offbreak"),
    ],
}

OUTCOMES = [0, 0, 1, 1, 1, 1, 2, 2, 2, 4, 4, 4, 4, 6, 6, "W", "wide", "noball"]
OUTCOME_WEIGHTS = [10, 10, 15, 15, 15, 15, 12, 12, 12, 20, 20, 20, 20, 8, 8, 3, 4, 2]
DISMISSAL_TYPES = ["bowled", "caught", "lbw", "run out", "stumped", "caught and bowled"]


def _generate_playing_xi(team: str) -> list[dict[str, Any]]:
    """Generate a playing XI for a team."""
    if team in PLAYER_POOL:
        return PLAYER_POOL[team][:11]
    return [
        {
            "name": f"Player {i + 1}",
            "role": "batsman" if i < 6 else "bowler",
            "batting_style": "right",
            "bowling_style": "right-arm medium",
        }
        for i in range(11)
    ]


class MatchSimulator:
    """Simulates a live IPL match producing ball-by-ball events."""

    def __init__(self, match_id: str | None = None, speed: float = 1.0):
        self.match_id = match_id or str(uuid.uuid4())
        self.speed = speed
        teams = random.sample(IPL_TEAMS, 2)
        self.team_batting = teams[0]
        self.team_bowling = teams[1]
        self.venue = random.choice(IPL_VENUES)
        self.toss_winner = random.choice(teams)
        self.toss_decision = random.choice(["bat", "field"])
        self.innings = 1
        self.over = 0
        self.ball = 0
        self.total_runs = 0
        self.wickets = 0
        self.extras = 0
        self.target: int | None = None
        self.match_state = "not_started"
        self.batting_xi = _generate_playing_xi(self.team_batting)
        self.bowling_xi = _generate_playing_xi(self.team_bowling)
        self.current_batsman_idx = 0
        self.non_striker_idx = 1
        self.events: list[dict[str, Any]] = []
        logger.info(
            "match_initialized",
            match_id=self.match_id,
            teams=f"{self.team_batting} vs {self.team_bowling}",
        )

    def _get_current_batsman(self) -> dict[str, Any]:
        return self.batting_xi[min(self.current_batsman_idx, len(self.batting_xi) - 1)]

    def _get_current_bowler(self) -> dict[str, Any]:
        bowlers = [p for p in self.bowling_xi if p["role"] in ("bowler", "allrounder")]
        bowler_idx = self.over % len(bowlers) if bowlers else 0
        if not bowlers:
            bowlers = self.bowling_xi[-4:]
        return bowlers[bowler_idx % len(bowlers)]

    def _simulate_ball(self) -> dict[str, Any]:
        """Simulate a single ball delivery."""
        outcome = random.choices(OUTCOMES, weights=OUTCOME_WEIGHTS, k=1)[0]
        batsman = self._get_current_batsman()
        bowler = self._get_current_bowler()

        event = {
            "event_id": str(uuid.uuid4()),
            "match_id": self.match_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "innings": self.innings,
            "over": self.over,
            "ball": self.ball,
            "batting_team": self.team_batting,
            "bowling_team": self.team_bowling,
            "batsman": batsman["name"],
            "bowler": bowler["name"],
            "venue": self.venue["name"],
            "city": self.venue["city"],
        }

        is_legal = True
        if outcome == "wide":
            event["runs_scored"] = 1
            event["extras_type"] = "wide"
            event["is_wicket"] = False
            event["is_legal"] = False
            self.total_runs += 1
            self.extras += 1
            is_legal = False
        elif outcome == "noball":
            runs = random.choice([0, 1, 2, 4, 6])
            event["runs_scored"] = runs + 1
            event["extras_type"] = "noball"
            event["is_wicket"] = False
            event["is_legal"] = False
            self.total_runs += runs + 1
            self.extras += 1
            is_legal = False
        elif outcome == "W":
            event["runs_scored"] = 0
            event["is_wicket"] = True
            event["dismissal_type"] = random.choice(DISMISSAL_TYPES)
            event["is_legal"] = True
            self.wickets += 1
            self.current_batsman_idx = min(self.current_batsman_idx + 1, len(self.batting_xi) - 1)
        else:
            runs = int(outcome)
            event["runs_scored"] = runs
            event["is_wicket"] = False
            event["is_legal"] = True
            self.total_runs += runs
            if runs % 2 == 1:
                self.current_batsman_idx, self.non_striker_idx = (
                    self.non_striker_idx,
                    self.current_batsman_idx,
                )

        event["total_runs"] = self.total_runs
        event["total_wickets"] = self.wickets
        event["run_rate"] = round(self.total_runs / max((self.over * 6 + self.ball) / 6, 0.1), 2)
        event["is_powerplay"] = self.over < 6
        event["is_death_overs"] = self.over >= 16
        event["phase"] = "powerplay" if self.over < 6 else "middle" if self.over < 16 else "death"

        if self.target is not None:
            event["target"] = self.target
            event["runs_needed"] = max(0, self.target - self.total_runs)
            balls_remaining = max(0, (20 * 6) - (self.over * 6 + self.ball))
            event["balls_remaining"] = balls_remaining
            event["required_rate"] = round(event["runs_needed"] / max(balls_remaining / 6, 0.1), 2)

        if is_legal:
            self.ball += 1
            if self.ball >= 6:
                self.over += 1
                self.ball = 0
                self.current_batsman_idx, self.non_striker_idx = (
                    self.non_striker_idx,
                    self.current_batsman_idx,
                )

        event["match_state"] = self._get_match_state()
        self.events.append(event)
        return event

    def _get_match_state(self) -> str:
        if self.innings == 1:
            if self.wickets >= 10 or self.over >= 20:
                return "innings_break"
            return "in_progress"
        else:
            if self.target and self.total_runs >= self.target:
                return "completed"
            if self.wickets >= 10 or self.over >= 20:
                return "completed"
            return "in_progress"

    def simulate_match(self, delay: float = 0.5) -> list[dict[str, Any]]:
        """Simulate a full match and return all events."""
        self.match_state = "in_progress"
        all_events: list[dict[str, Any]] = []

        logger.info("innings_started", match_id=self.match_id, innings=1, batting=self.team_batting)
        while self.over < 20 and self.wickets < 10:
            event = self._simulate_ball()
            all_events.append(event)
            if event["match_state"] == "innings_break":
                break
            time.sleep(delay / self.speed)

        first_innings_total = self.total_runs
        self.target = first_innings_total + 1
        self.innings = 2
        self.over = 0
        self.ball = 0
        self.total_runs = 0
        self.wickets = 0
        self.extras = 0
        self.current_batsman_idx = 0
        self.non_striker_idx = 1

        self.team_batting, self.team_bowling = self.team_bowling, self.team_batting
        self.batting_xi, self.bowling_xi = self.bowling_xi, self.batting_xi

        logger.info(
            "innings_started",
            match_id=self.match_id,
            innings=2,
            batting=self.team_batting,
            target=self.target,
        )
        while self.over < 20 and self.wickets < 10:
            event = self._simulate_ball()
            all_events.append(event)
            if event["match_state"] == "completed":
                break
            time.sleep(delay / self.speed)

        self.match_state = "completed"
        logger.info("match_completed", match_id=self.match_id, total_events=len(all_events))
        return all_events

    def generate_match_summary(self) -> dict[str, Any]:
        """Generate match summary from simulated events."""
        innings_1_events = [e for e in self.events if e["innings"] == 1]
        innings_2_events = [e for e in self.events if e["innings"] == 2]

        i1_runs = innings_1_events[-1]["total_runs"] if innings_1_events else 0
        i1_wickets = innings_1_events[-1]["total_wickets"] if innings_1_events else 0
        i2_runs = innings_2_events[-1]["total_runs"] if innings_2_events else 0
        i2_wickets = innings_2_events[-1]["total_wickets"] if innings_2_events else 0

        if self.target and i2_runs >= self.target:
            winner = self.team_batting
            margin = f"{10 - i2_wickets} wickets"
        else:
            winner = self.team_bowling
            margin = f"{(self.target or 0) - 1 - i2_runs} runs"

        return {
            "match_id": self.match_id,
            "venue": self.venue["name"],
            "city": self.venue["city"],
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "toss_winner": self.toss_winner,
            "toss_decision": self.toss_decision,
            "innings_1_team": innings_1_events[0]["batting_team"] if innings_1_events else "",
            "innings_1_runs": i1_runs,
            "innings_1_wickets": i1_wickets,
            "innings_2_team": innings_2_events[0]["batting_team"] if innings_2_events else "",
            "innings_2_runs": i2_runs,
            "innings_2_wickets": i2_wickets,
            "winner": winner,
            "margin": margin,
            "total_balls": len([e for e in self.events if e.get("is_legal", True)]),
            "total_fours": len(
                [e for e in self.events if e.get("runs_scored") == 4 and not e.get("extras_type")]
            ),
            "total_sixes": len(
                [e for e in self.events if e.get("runs_scored") == 6 and not e.get("extras_type")]
            ),
        }


def generate_sample_events(num_events: int = 100) -> list[dict[str, Any]]:
    """Generate sample ball-by-ball events without delay."""
    simulator = MatchSimulator(speed=100)
    events: list[dict[str, Any]] = []
    while len(events) < num_events and simulator.over < 20 and simulator.wickets < 10:
        event = simulator._simulate_ball()
        events.append(event)
    return events
