"""Cricsheet data parser for historical IPL match data."""

from pathlib import Path
from typing import Any

import yaml

from monitoring.logger import get_logger

logger = get_logger(__name__)


class CricsheetParser:
    """Parse Cricsheet YAML/JSON format match data into platform schema."""

    def __init__(self, data_dir: str = "data/raw/cricsheet"):
        self.data_dir = Path(data_dir)

    def parse_yaml_match(self, file_path: str) -> dict[str, Any] | None:
        """Parse a single Cricsheet YAML match file."""
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            if not data or "info" not in data:
                logger.warning("invalid_cricsheet_file", path=file_path)
                return None

            info = data["info"]
            innings_data = data.get("innings", [])

            match = {
                "source": "cricsheet",
                "source_file": str(file_path),
                "teams": info.get("teams", []),
                "gender": info.get("gender", "male"),
                "match_type": info.get("match_type", "T20"),
                "season": info.get("season", ""),
                "date": str(info.get("dates", [""])[0]),
                "venue": info.get("venue", ""),
                "city": info.get("city", ""),
                "toss": info.get("toss", {}),
                "outcome": info.get("outcome", {}),
                "player_of_match": info.get("player_of_match", []),
                "umpires": info.get("umpires", []),
            }

            match["ball_events"] = self._parse_innings(innings_data)
            return match

        except Exception as e:
            logger.error("cricsheet_parse_error", path=file_path, error=str(e))
            return None

    def _parse_innings(self, innings_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse innings data into ball-by-ball events."""
        events = []
        for innings_idx, innings in enumerate(innings_data, 1):
            for innings_name, innings_detail in innings.items():
                deliveries = innings_detail.get("deliveries", [])
                for delivery in deliveries:
                    for over_ball, ball_data in delivery.items():
                        event = {
                            "innings": innings_idx,
                            "over_ball": str(over_ball),
                            "batsman": ball_data.get("batsman", ""),
                            "bowler": ball_data.get("bowler", ""),
                            "non_striker": ball_data.get("non_striker", ""),
                            "runs_batsman": ball_data.get("runs", {}).get("batsman", 0),
                            "runs_extras": ball_data.get("runs", {}).get("extras", 0),
                            "runs_total": ball_data.get("runs", {}).get("total", 0),
                        }

                        extras = ball_data.get("extras", {})
                        if extras:
                            event["extras_type"] = list(extras.keys())[0]
                            event["extras_value"] = list(extras.values())[0]

                        wickets = ball_data.get("wickets", [])
                        if wickets:
                            w = wickets[0]
                            event["is_wicket"] = True
                            event["dismissal_type"] = w.get("kind", "")
                            event["dismissed_player"] = w.get("player_out", "")
                        else:
                            event["is_wicket"] = False

                        events.append(event)
        return events

    def parse_directory(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Parse all match files in the data directory."""
        matches = []
        files = sorted(self.data_dir.glob("*.yaml")) + sorted(self.data_dir.glob("*.json"))

        for i, file_path in enumerate(files):
            if limit and i >= limit:
                break
            match = self.parse_yaml_match(str(file_path))
            if match:
                matches.append(match)

        logger.info("cricsheet_parse_complete", total_parsed=len(matches))
        return matches

    def to_flat_records(self, match: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten match data into individual ball records for ingestion."""
        records = []
        teams = match.get("teams", ["", ""])
        for event in match.get("ball_events", []):
            record = {
                "venue": match["venue"],
                "city": match["city"],
                "date": match["date"],
                "season": match["season"],
                "team1": teams[0] if len(teams) > 0 else "",
                "team2": teams[1] if len(teams) > 1 else "",
                **event,
            }
            records.append(record)
        return records
