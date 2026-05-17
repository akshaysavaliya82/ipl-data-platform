"""Spark Structured Streaming consumer for IPL Kafka events."""

from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from monitoring.logger import get_logger

logger = get_logger(__name__)

BALL_EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), True),
        StructField("match_id", StringType(), True),
        StructField("timestamp", StringType(), True),
        StructField("innings", IntegerType(), True),
        StructField("over", IntegerType(), True),
        StructField("ball", IntegerType(), True),
        StructField("batting_team", StringType(), True),
        StructField("bowling_team", StringType(), True),
        StructField("batsman", StringType(), True),
        StructField("bowler", StringType(), True),
        StructField("runs_scored", IntegerType(), True),
        StructField("is_wicket", BooleanType(), True),
        StructField("dismissal_type", StringType(), True),
        StructField("is_boundary", BooleanType(), True),
        StructField("total_runs", IntegerType(), True),
        StructField("total_wickets", IntegerType(), True),
        StructField("run_rate", DoubleType(), True),
        StructField("is_powerplay", BooleanType(), True),
        StructField("is_death_overs", BooleanType(), True),
        StructField("phase", StringType(), True),
        StructField("venue", StringType(), True),
        StructField("city", StringType(), True),
        StructField("match_state", StringType(), True),
    ]
)


class SparkStreamingConsumer:
    """Consumes Kafka events using Spark Structured Streaming."""

    def __init__(
        self,
        spark: SparkSession | None = None,
        kafka_servers: str = "localhost:9092",
        checkpoint_dir: str = "/opt/data/checkpoints",
        output_dir: str = "/opt/data/lake",
    ):
        self.spark = spark or self._create_spark_session()
        self.kafka_servers = kafka_servers
        self.checkpoint_dir = checkpoint_dir
        self.output_dir = output_dir

    @staticmethod
    def _create_spark_session() -> SparkSession:
        return (
            SparkSession.builder.appName("IPL-Streaming-Consumer")
            .config(
                "spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,io.delta:delta-spark_2.12:3.1.0",
            )
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config(
                "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
            )
            .config("spark.sql.streaming.checkpointLocation", "/opt/data/checkpoints")
            .getOrCreate()
        )

    def _read_kafka_stream(self, topic: str) -> DataFrame:
        """Read a Kafka topic as a streaming DataFrame."""
        return (
            self.spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_servers)
            .option("subscribe", topic)
            .option("startingOffsets", "latest")
            .option("failOnDataLoss", "false")
            .load()
        )

    def process_ball_events(self) -> Any:
        """Process ball-by-ball events stream."""
        raw_stream = self._read_kafka_stream("ipl.ball.events")

        parsed_stream = raw_stream.select(
            F.from_json(F.col("value").cast("string"), BALL_EVENT_SCHEMA).alias("data"),
            F.col("timestamp").alias("kafka_timestamp"),
        ).select("data.*", "kafka_timestamp")

        windowed_stats = (
            parsed_stream.withWatermark("kafka_timestamp", "30 seconds")
            .groupBy(
                F.window("kafka_timestamp", "1 minute", "30 seconds"),
                "match_id",
                "innings",
                "batting_team",
            )
            .agg(
                F.sum("runs_scored").alias("runs_in_window"),
                F.count("*").alias("balls_in_window"),
                F.sum(F.when(F.col("is_wicket"), 1).otherwise(0)).alias("wickets_in_window"),
                F.sum(F.when(F.col("runs_scored") == 4, 1).otherwise(0)).alias("fours"),
                F.sum(F.when(F.col("runs_scored") == 6, 1).otherwise(0)).alias("sixes"),
                F.max("total_runs").alias("current_total"),
                F.max("total_wickets").alias("current_wickets"),
                F.max("run_rate").alias("current_run_rate"),
            )
        )

        bronze_query = (
            parsed_stream.writeStream.format("delta")
            .outputMode("append")
            .option("checkpointLocation", f"{self.checkpoint_dir}/bronze_ball_events")
            .option("path", f"{self.output_dir}/bronze/ball_events")
            .trigger(processingTime="10 seconds")
            .start()
        )

        stats_query = (
            windowed_stats.writeStream.format("delta")
            .outputMode("update")
            .option("checkpointLocation", f"{self.checkpoint_dir}/live_match_stats")
            .option("path", f"{self.output_dir}/gold/live_match_stats")
            .trigger(processingTime="15 seconds")
            .start()
        )

        logger.info("streaming_queries_started", queries=["bronze_ball_events", "live_match_stats"])
        return bronze_query, stats_query

    def process_score_updates(self) -> Any:
        """Process score update events for real-time scoreboard."""
        raw_stream = self._read_kafka_stream("ipl.score.updates")

        score_schema = StructType(
            [
                StructField("match_id", StringType(), True),
                StructField("timestamp", StringType(), True),
                StructField("innings", IntegerType(), True),
                StructField("over", IntegerType(), True),
                StructField("ball", IntegerType(), True),
                StructField("total_runs", IntegerType(), True),
                StructField("total_wickets", IntegerType(), True),
                StructField("run_rate", DoubleType(), True),
                StructField("batting_team", StringType(), True),
                StructField("bowling_team", StringType(), True),
            ]
        )

        parsed = raw_stream.select(
            F.from_json(F.col("value").cast("string"), score_schema).alias("data"),
            F.col("timestamp").alias("kafka_timestamp"),
        ).select("data.*", "kafka_timestamp")

        query = (
            parsed.writeStream.format("delta")
            .outputMode("append")
            .option("checkpointLocation", f"{self.checkpoint_dir}/score_updates")
            .option("path", f"{self.output_dir}/silver/score_updates")
            .trigger(processingTime="5 seconds")
            .start()
        )

        logger.info("score_updates_stream_started")
        return query

    def start_all_streams(self) -> None:
        """Start all streaming queries and await termination."""
        bronze_q, stats_q = self.process_ball_events()
        self.process_score_updates()

        logger.info("all_streams_started")
        self.spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    consumer = SparkStreamingConsumer()
    consumer.start_all_streams()
