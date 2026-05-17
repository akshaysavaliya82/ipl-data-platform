"""Bronze layer: Ingest raw data into the lakehouse."""

from datetime import UTC, datetime

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from monitoring.logger import get_logger
from spark_jobs.utils.data_io import write_parquet
from spark_jobs.utils.spark_session import create_spark_session

logger = get_logger(__name__)


class BronzeIngestion:
    """Ingest raw data into Bronze layer with metadata."""

    def __init__(
        self,
        spark: SparkSession | None = None,
        raw_path: str = "data/samples",
        bronze_path: str = "data/bronze",
    ):
        self.spark = spark or create_spark_session("IPL-Bronze-Ingestion")
        self.raw_path = raw_path
        self.bronze_path = bronze_path

    def _add_metadata(self, df: DataFrame, source: str) -> DataFrame:
        """Add ingestion metadata columns."""
        return (
            df.withColumn("_ingestion_timestamp", F.current_timestamp())
            .withColumn("_source", F.lit(source))
            .withColumn("_ingestion_date", F.current_date())
            .withColumn("_batch_id", F.lit(datetime.now(UTC).strftime("%Y%m%d_%H%M%S")))
        )

    def ingest_matches(self) -> DataFrame:
        """Ingest raw match data into Bronze layer."""
        source_path = f"{self.raw_path}/matches.json"
        logger.info("ingesting_matches", source=source_path)

        df = self.spark.read.json(source_path)
        df = self._add_metadata(df, "sample_matches")

        output_path = f"{self.bronze_path}/matches"
        write_parquet(df, output_path, partition_by=["season"])
        logger.info("matches_ingested", count=df.count())
        return df

    def ingest_ball_events(self) -> DataFrame:
        """Ingest raw ball-by-ball data into Bronze layer."""
        source_path = f"{self.raw_path}/ball_by_ball.json"
        logger.info("ingesting_ball_events", source=source_path)

        df = self.spark.read.json(source_path)
        df = self._add_metadata(df, "sample_ball_events")

        output_path = f"{self.bronze_path}/ball_events"
        write_parquet(df, output_path, partition_by=["season"])
        logger.info("ball_events_ingested", count=df.count())
        return df

    def ingest_players(self) -> DataFrame:
        """Ingest raw player data into Bronze layer."""
        source_path = f"{self.raw_path}/players.json"
        logger.info("ingesting_players", source=source_path)

        df = self.spark.read.json(source_path)
        df = self._add_metadata(df, "sample_players")

        output_path = f"{self.bronze_path}/players"
        write_parquet(df, output_path)
        logger.info("players_ingested", count=df.count())
        return df

    def ingest_teams(self) -> DataFrame:
        """Ingest raw team data into Bronze layer."""
        source_path = f"{self.raw_path}/teams.json"
        logger.info("ingesting_teams", source=source_path)

        df = self.spark.read.json(source_path)
        df = self._add_metadata(df, "sample_teams")

        output_path = f"{self.bronze_path}/teams"
        write_parquet(df, output_path)
        logger.info("teams_ingested", count=df.count())
        return df

    def ingest_venues(self) -> DataFrame:
        """Ingest raw venue data into Bronze layer."""
        source_path = f"{self.raw_path}/venues.json"
        logger.info("ingesting_venues", source=source_path)

        df = self.spark.read.json(source_path)
        df = self._add_metadata(df, "sample_venues")

        output_path = f"{self.bronze_path}/venues"
        write_parquet(df, output_path)
        logger.info("venues_ingested", count=df.count())
        return df

    def run_full_ingestion(self) -> dict[str, int]:
        """Run complete Bronze layer ingestion."""
        logger.info("bronze_ingestion_started")
        results = {}

        results["matches"] = self.ingest_matches().count()
        results["ball_events"] = self.ingest_ball_events().count()
        results["players"] = self.ingest_players().count()
        results["teams"] = self.ingest_teams().count()
        results["venues"] = self.ingest_venues().count()

        logger.info("bronze_ingestion_completed", results=results)
        return results


if __name__ == "__main__":
    ingestion = BronzeIngestion()
    ingestion.run_full_ingestion()
