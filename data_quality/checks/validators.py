"""Data quality validation framework for IPL Data Platform."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from monitoring.logger import get_logger

logger = get_logger(__name__)


class ValidationResult:
    """Result of a data quality check."""

    def __init__(self, check_name: str, passed: bool,
                 details: dict[str, Any] | None = None,
                 failures: list[str] | None = None):
        self.check_name = check_name
        self.passed = passed
        self.details = details or {}
        self.failures = failures or []
        self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "details": self.details,
            "failures": self.failures,
            "timestamp": self.timestamp,
        }


class DataValidator:
    """Comprehensive data quality validator."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.results: list[ValidationResult] = []

    def _load_json_safe(self, path: Path) -> list[dict[str, Any]] | None:
        """Safely load a JSON file."""
        if not path.exists():
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("json_load_error", path=str(path), error=str(e))
            return None

    def check_nulls(self, data_path: str = "data") -> dict[str, Any]:
        """Check for null/missing values in critical fields."""
        checks = {
            "matches": {
                "file": "samples/matches.json",
                "required_fields": ["match_id", "season", "team1", "team2",
                                     "winner", "venue", "date"],
            },
            "players": {
                "file": "samples/players.json",
                "required_fields": ["player_id", "player_name", "nationality", "role"],
            },
            "ball_events": {
                "file": "samples/ball_by_ball.json",
                "required_fields": ["match_id", "innings", "over", "ball",
                                     "batsman", "bowler", "runs_scored"],
            },
        }

        failures = []
        details = {}

        for dataset_name, config in checks.items():
            filepath = Path(data_path) / config["file"]
            data = self._load_json_safe(filepath)

            if data is None:
                failures.append(f"{dataset_name}: file not found or invalid")
                continue

            null_counts: dict[str, int] = {}
            for field in config["required_fields"]:
                nulls = sum(1 for record in data
                           if record.get(field) is None or record.get(field) == "")
                if nulls > 0:
                    null_counts[field] = nulls
                    failures.append(
                        f"{dataset_name}.{field}: {nulls} null values "
                        f"({nulls / len(data) * 100:.1f}%)"
                    )

            details[dataset_name] = {
                "total_records": len(data),
                "null_counts": null_counts,
                "fields_checked": config["required_fields"],
            }

        result = ValidationResult(
            check_name="null_check",
            passed=len(failures) == 0,
            details=details,
            failures=failures,
        )
        self.results.append(result)
        logger.info("null_check_completed", passed=result.passed,
                     failure_count=len(failures))
        return result.to_dict()

    def check_duplicates(self, data_path: str = "data") -> dict[str, Any]:
        """Check for duplicate records."""
        checks = {
            "matches": {
                "file": "samples/matches.json",
                "key_field": "match_id",
            },
            "players": {
                "file": "samples/players.json",
                "key_field": "player_id",
            },
        }

        failures = []
        details = {}

        for dataset_name, config in checks.items():
            filepath = Path(data_path) / config["file"]
            data = self._load_json_safe(filepath)

            if data is None:
                failures.append(f"{dataset_name}: file not found")
                continue

            key_field = config["key_field"]
            ids = [record.get(key_field) for record in data]
            unique_ids = set(ids)
            duplicates = len(ids) - len(unique_ids)

            if duplicates > 0:
                failures.append(
                    f"{dataset_name}: {duplicates} duplicate {key_field} values"
                )

            details[dataset_name] = {
                "total_records": len(data),
                "unique_keys": len(unique_ids),
                "duplicates": duplicates,
            }

        result = ValidationResult(
            check_name="duplicate_check",
            passed=len(failures) == 0,
            details=details,
            failures=failures,
        )
        self.results.append(result)
        logger.info("duplicate_check_completed", passed=result.passed)
        return result.to_dict()

    def check_schema(self, data_path: str = "data") -> dict[str, Any]:
        """Validate data schemas."""
        schemas = {
            "matches": {
                "file": "samples/matches.json",
                "expected_fields": [
                    "match_id", "season", "date", "venue", "city",
                    "team1", "team2", "winner", "toss_winner",
                    "toss_decision", "innings1_runs", "innings2_runs",
                ],
                "field_types": {
                    "season": (int, float),
                    "innings1_runs": (int, float),
                    "innings2_runs": (int, float),
                },
            },
            "players": {
                "file": "samples/players.json",
                "expected_fields": [
                    "player_id", "player_name", "nationality",
                    "batting_style", "bowling_style", "role",
                ],
                "field_types": {},
            },
        }

        failures = []
        details = {}

        for dataset_name, config in schemas.items():
            filepath = Path(data_path) / config["file"]
            data = self._load_json_safe(filepath)

            if data is None:
                failures.append(f"{dataset_name}: file not found")
                continue

            missing_fields = set()
            type_errors = []

            for i, record in enumerate(data[:100]):
                for field in config["expected_fields"]:
                    if field not in record:
                        missing_fields.add(field)

                for field, expected_types in config["field_types"].items():
                    if field in record and record[field] is not None:
                        if not isinstance(record[field], expected_types):
                            type_errors.append(
                                f"Record {i}: {field} expected "
                                f"{expected_types}, got {type(record[field])}"
                            )

            if missing_fields:
                failures.append(
                    f"{dataset_name}: missing fields: {missing_fields}"
                )
            if type_errors:
                failures.extend(type_errors[:5])

            details[dataset_name] = {
                "total_records": len(data),
                "missing_fields": list(missing_fields),
                "type_errors": len(type_errors),
                "records_checked": min(100, len(data)),
            }

        result = ValidationResult(
            check_name="schema_check",
            passed=len(failures) == 0,
            details=details,
            failures=failures,
        )
        self.results.append(result)
        logger.info("schema_check_completed", passed=result.passed)
        return result.to_dict()

    def check_freshness(self, data_path: str = "data",
                        max_age_hours: int = 48) -> dict[str, Any]:
        """Check data freshness based on file modification times."""
        files_to_check = [
            "samples/matches.json",
            "samples/players.json",
            "samples/ball_by_ball.json",
            "samples/teams.json",
            "samples/venues.json",
        ]

        failures = []
        details = {}
        now = datetime.now(UTC)

        for file_path in files_to_check:
            full_path = Path(data_path) / file_path
            if not full_path.exists():
                failures.append(f"{file_path}: file does not exist")
                details[file_path] = {"exists": False}
                continue

            mod_time = datetime.fromtimestamp(
                full_path.stat().st_mtime, tz=UTC
            )
            age_hours = (now - mod_time).total_seconds() / 3600

            details[file_path] = {
                "exists": True,
                "last_modified": mod_time.isoformat(),
                "age_hours": round(age_hours, 2),
                "is_fresh": age_hours <= max_age_hours,
            }

            if age_hours > max_age_hours:
                failures.append(
                    f"{file_path}: data is {age_hours:.1f}h old "
                    f"(max: {max_age_hours}h)"
                )

        result = ValidationResult(
            check_name="freshness_check",
            passed=len(failures) == 0,
            details=details,
            failures=failures,
        )
        self.results.append(result)
        logger.info("freshness_check_completed", passed=result.passed)
        return result.to_dict()

    def validate_bronze_layer(self, bronze_path: str = "data/bronze") -> dict[str, Any]:
        """Validate Bronze layer data quality."""
        path = Path(bronze_path)
        failures = []
        details = {}

        expected_datasets = ["matches", "ball_events", "players", "teams", "venues"]

        for dataset in expected_datasets:
            dataset_path = path / dataset
            if not dataset_path.exists():
                failures.append(f"Bronze {dataset}: directory not found")
                details[dataset] = {"exists": False}
            else:
                parquet_files = list(dataset_path.rglob("*.parquet"))
                details[dataset] = {
                    "exists": True,
                    "parquet_files": len(parquet_files),
                }
                if len(parquet_files) == 0:
                    failures.append(f"Bronze {dataset}: no parquet files found")

        result = ValidationResult(
            check_name="bronze_validation",
            passed=len(failures) == 0,
            details=details,
            failures=failures,
        )
        self.results.append(result)
        return result.to_dict()

    def run_all_checks(self, data_path: str = "data") -> dict[str, Any]:
        """Run all data quality checks."""
        logger.info("running_all_dq_checks")
        results = {
            "null_checks": self.check_nulls(data_path),
            "duplicate_checks": self.check_duplicates(data_path),
            "schema_checks": self.check_schema(data_path),
            "freshness_checks": self.check_freshness(data_path),
        }

        all_passed = all(r["passed"] for r in results.values())
        total_failures = sum(len(r["failures"]) for r in results.values())

        summary = {
            "overall_passed": all_passed,
            "total_checks": len(results),
            "total_failures": total_failures,
            "timestamp": datetime.now(UTC).isoformat(),
            "results": results,
        }

        report_path = Path(data_path) / "quality_reports"
        report_path.mkdir(parents=True, exist_ok=True)
        report_file = report_path / f"dq_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("all_dq_checks_completed", passed=all_passed,
                     total_failures=total_failures, report=str(report_file))
        return summary


if __name__ == "__main__":
    validator = DataValidator()
    summary = validator.run_all_checks()
    print(json.dumps(summary, indent=2))
