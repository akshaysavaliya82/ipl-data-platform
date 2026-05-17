"""Silver layer: Clean and transform match data."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType

from monitoring.logger import get_logger
from spark_jobs.utils.data_io import write_parquet
from spark_jobs.utils.spark_session import create_spark_session

logger = get_logger(__name__)


class SilverMatchTransformer:
    """Transform Bronze match data into Silver layer."""

    def __init__(self, spark: SparkSession | None = None,
                 bronze_path: str = "data/bronze",
                 silver_path: str = "data/silver"):
        self.spark = spark or create_spark_session("IPL-Silver-Matches")
        self.bronze_path = bronze_path
        self.silver_path = silver_path

    def transform_matches(self) -> DataFrame:
        """Clean and transform match data."""
        logger.info("transforming_matches")
        df = self.spark.read.parquet(f"{self.bronze_path}/matches")

        cleaned = (
            df
            .dropDuplicates(["match_id"])
            .filter(F.col("match_id").isNotNull())
            .withColumn("date", F.to_date("date", "yyyy-MM-dd"))
            .withColumn("season", F.col("season").cast(IntegerType()))
            .withColumn("innings1_runs", F.col("innings1_runs").cast(IntegerType()))
            .withColumn("innings1_wickets", F.col("innings1_wickets").cast(IntegerType()))
            .withColumn("innings2_runs", F.col("innings2_runs").cast(IntegerType()))
            .withColumn("innings2_wickets", F.col("innings2_wickets").cast(IntegerType()))
            .withColumn("innings1_overs", F.col("innings1_overs").cast(DoubleType()))
            .withColumn("innings2_overs", F.col("innings2_overs").cast(DoubleType()))
            .withColumn("innings1_run_rate",
                        F.round(F.col("innings1_runs") / F.col("innings1_overs"), 2))
            .withColumn("innings2_run_rate",
                        F.round(F.col("innings2_runs") / F.col("innings2_overs"), 2))
            .withColumn("total_runs",
                        F.col("innings1_runs") + F.col("innings2_runs"))
            .withColumn("is_high_scoring",
                        F.when(F.col("total_runs") > 350, True).otherwise(False))
            .withColumn("margin_value",
                        F.regexp_extract("margin", r"(\d+)", 1).cast(IntegerType()))
            .withColumn("toss_winner_is_match_winner",
                        F.when(F.col("toss_winner") == F.col("winner"), True).otherwise(False))
            .withColumn("batting_first_won",
                        F.when(F.col("result_type") == "runs", True).otherwise(False))
            .drop("_ingestion_timestamp", "_source", "_ingestion_date", "_batch_id")
            .withColumn("_processed_timestamp", F.current_timestamp())
        )

        output_path = f"{self.silver_path}/matches"
        write_parquet(cleaned, output_path, partition_by=["season"])
        logger.info("matches_transformed", count=cleaned.count())
        return cleaned

    def transform_ball_events(self) -> DataFrame:
        """Clean and transform ball-by-ball data."""
        logger.info("transforming_ball_events")
        df = self.spark.read.parquet(f"{self.bronze_path}/ball_events")

        cleaned = (
            df
            .filter(F.col("match_id").isNotNull())
            .withColumn("runs_scored", F.col("runs_scored").cast(IntegerType()))
            .withColumn("innings", F.col("innings").cast(IntegerType()))
            .withColumn("over", F.col("over").cast(IntegerType()))
            .withColumn("ball", F.col("ball").cast(IntegerType()))
            .withColumn("is_dot_ball",
                        F.when(F.col("runs_scored") == 0, True).otherwise(False))
            .withColumn("is_boundary",
                        F.when(F.col("runs_scored").isin(4, 6), True).otherwise(False))
            .withColumn("is_four",
                        F.when(F.col("runs_scored") == 4, True).otherwise(False))
            .withColumn("is_six",
                        F.when(F.col("runs_scored") == 6, True).otherwise(False))
            .withColumn("over_ball",
                        F.concat(F.col("over"), F.lit("."), F.col("ball")))
            .withColumn("ball_number",
                        F.col("over") * 6 + F.col("ball") + 1)
            .drop("_ingestion_timestamp", "_source", "_ingestion_date", "_batch_id")
            .withColumn("_processed_timestamp", F.current_timestamp())
        )

        output_path = f"{self.silver_path}/ball_events"
        write_parquet(cleaned, output_path, partition_by=["season"])
        logger.info("ball_events_transformed", count=cleaned.count())
        return cleaned

    def run_all_transforms(self) -> dict[str, int]:
        """Run all Silver layer transformations."""
        logger.info("silver_transformation_started")
        results = {}
        results["matches"] = self.transform_matches().count()
        results["ball_events"] = self.transform_ball_events().count()
        logger.info("silver_transformation_completed", results=results)
        return results


if __name__ == "__main__":
    transformer = SilverMatchTransformer()
    transformer.run_all_transforms()
