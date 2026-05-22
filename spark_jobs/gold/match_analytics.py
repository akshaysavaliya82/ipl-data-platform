"""Gold layer: Analytics-ready aggregated tables."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from monitoring.logger import get_logger
from spark_jobs.utils.data_io import write_parquet
from spark_jobs.utils.spark_session import create_spark_session

logger = get_logger(__name__)


class GoldMatchAnalytics:
    """Generate Gold layer analytics tables."""

    def __init__(
        self,
        spark: SparkSession | None = None,
        silver_path: str = "data/silver",
        gold_path: str = "data/gold",
    ):
        self.spark = spark or create_spark_session("IPL-Gold-Analytics")
        self.silver_path = silver_path
        self.gold_path = gold_path

    def generate_player_performance(self) -> DataFrame:
        """Generate fact_player_performance table."""
        logger.info("generating_player_performance")
        balls = self.spark.read.parquet(f"{self.silver_path}/ball_events")

        batting_stats = (
            balls.groupBy("season", "match_id", "batsman")
            .agg(
                F.sum("runs_scored").alias("runs"),
                F.count("*").alias("balls_faced"),
                F.sum(F.when(F.col("is_four"), 1).otherwise(0)).alias("fours"),
                F.sum(F.when(F.col("is_six"), 1).otherwise(0)).alias("sixes"),
                F.sum(F.when(F.col("is_dot_ball"), 1).otherwise(0)).alias("dot_balls"),
                F.first("batting_team").alias("team"),
            )
            .withColumn("strike_rate", F.round(F.col("runs") / F.col("balls_faced") * 100, 2))
            .withColumn(
                "boundary_percentage",
                F.round((F.col("fours") + F.col("sixes")) / F.col("balls_faced") * 100, 2),
            )
            .withColumnRenamed("batsman", "player_name")
        )

        bowling_stats = (
            balls.groupBy("season", "match_id", "bowler")
            .agg(
                F.sum("runs_scored").alias("runs_conceded"),
                F.count("*").alias("balls_bowled"),
                F.sum(F.when(F.col("is_wicket"), 1).otherwise(0)).alias("wickets"),
                F.sum(F.when(F.col("is_dot_ball"), 1).otherwise(0)).alias("dot_balls_bowled"),
                F.first("bowling_team").alias("bowling_team"),
            )
            .withColumn(
                "economy_rate", F.round(F.col("runs_conceded") / (F.col("balls_bowled") / 6), 2)
            )
            .withColumn("overs_bowled", F.round(F.col("balls_bowled") / 6, 1))
            .withColumnRenamed("bowler", "player_name")
        )

        output_path = f"{self.gold_path}/fact_player_performance"
        write_parquet(batting_stats, f"{output_path}/batting", partition_by=["season"])
        write_parquet(bowling_stats, f"{output_path}/bowling", partition_by=["season"])

        logger.info(
            "player_performance_generated",
            batting_rows=batting_stats.count(),
            bowling_rows=bowling_stats.count(),
        )
        return batting_stats

    def generate_match_summary(self) -> DataFrame:
        """Generate fact_match_summary table."""
        logger.info("generating_match_summary")
        matches = self.spark.read.parquet(f"{self.silver_path}/matches")

        summary = (
            matches.withColumn(
                "run_rate_diff", F.col("innings1_run_rate") - F.col("innings2_run_rate")
            )
            .withColumn(
                "match_competitiveness",
                F.when(F.col("margin_value") <= 10, "close")
                .when(F.col("margin_value") <= 30, "moderate")
                .otherwise("dominant"),
            )
            .withColumn(
                "is_last_ball_finish",
                F.when(
                    (F.col("result_type") == "wickets") & (F.col("innings2_overs") >= 19.4), True
                ).otherwise(False),
            )
        )

        output_path = f"{self.gold_path}/fact_match_summary"
        write_parquet(summary, output_path, partition_by=["season"])
        logger.info("match_summary_generated", count=summary.count())
        return summary

    def generate_team_statistics(self) -> DataFrame:
        """Generate team aggregate statistics."""
        logger.info("generating_team_statistics")
        matches = self.spark.read.parquet(f"{self.silver_path}/matches")

        team_stats_t1 = (
            matches.groupBy("season", "team1")
            .agg(
                F.count("*").alias("matches_played"),
                F.sum(F.when(F.col("winner") == F.col("team1"), 1).otherwise(0)).alias("wins"),
                F.avg("innings1_runs").alias("avg_runs_scored"),
                F.avg("innings1_run_rate").alias("avg_run_rate"),
            )
            .withColumnRenamed("team1", "team")
        )

        team_stats_t2 = (
            matches.groupBy("season", "team2")
            .agg(
                F.count("*").alias("matches_played"),
                F.sum(F.when(F.col("winner") == F.col("team2"), 1).otherwise(0)).alias("wins"),
                F.avg("innings2_runs").alias("avg_runs_scored"),
                F.avg("innings2_run_rate").alias("avg_run_rate"),
            )
            .withColumnRenamed("team2", "team")
        )

        team_stats = (
            team_stats_t1.unionByName(team_stats_t2)
            .groupBy("season", "team")
            .agg(
                F.sum("matches_played").alias("matches_played"),
                F.sum("wins").alias("wins"),
                F.avg("avg_runs_scored").alias("avg_runs_scored"),
                F.avg("avg_run_rate").alias("avg_run_rate"),
            )
            .withColumn("win_percentage", F.round(F.col("wins") / F.col("matches_played") * 100, 2))
            .withColumn("losses", F.col("matches_played") - F.col("wins"))
            .orderBy("season", F.desc("win_percentage"))
        )

        output_path = f"{self.gold_path}/team_statistics"
        write_parquet(team_stats, output_path, partition_by=["season"])
        logger.info("team_statistics_generated", count=team_stats.count())
        return team_stats

    def generate_venue_analytics(self) -> DataFrame:
        """Generate venue analytics."""
        logger.info("generating_venue_analytics")
        matches = self.spark.read.parquet(f"{self.silver_path}/matches")

        venue_stats = (
            matches.groupBy("venue", "city")
            .agg(
                F.count("*").alias("matches_hosted"),
                F.avg("total_runs").alias("avg_total_runs"),
                F.avg("innings1_runs").alias("avg_first_innings"),
                F.avg("innings2_runs").alias("avg_second_innings"),
                F.sum(F.when(F.col("batting_first_won"), 1).otherwise(0)).alias("bat_first_wins"),
                F.sum(F.when(~F.col("batting_first_won"), 1).otherwise(0)).alias("chase_wins"),
                F.avg("innings1_run_rate").alias("avg_run_rate"),
            )
            .withColumn(
                "bat_first_win_pct",
                F.round(F.col("bat_first_wins") / F.col("matches_hosted") * 100, 2),
            )
            .withColumn(
                "chase_win_pct", F.round(F.col("chase_wins") / F.col("matches_hosted") * 100, 2)
            )
            .orderBy(F.desc("matches_hosted"))
        )

        output_path = f"{self.gold_path}/venue_analytics"
        write_parquet(venue_stats, output_path)
        logger.info("venue_analytics_generated", count=venue_stats.count())
        return venue_stats

    def generate_toss_analysis(self) -> DataFrame:
        """Generate toss impact analysis."""
        logger.info("generating_toss_analysis")
        matches = self.spark.read.parquet(f"{self.silver_path}/matches")

        toss_stats = (
            matches.groupBy("venue", "toss_decision")
            .agg(
                F.count("*").alias("total_matches"),
                F.sum(F.when(F.col("toss_winner_is_match_winner"), 1).otherwise(0)).alias(
                    "toss_winner_won"
                ),
            )
            .withColumn(
                "toss_advantage_pct",
                F.round(F.col("toss_winner_won") / F.col("total_matches") * 100, 2),
            )
            .orderBy(F.desc("toss_advantage_pct"))
        )

        output_path = f"{self.gold_path}/toss_analysis"
        write_parquet(toss_stats, output_path)
        logger.info("toss_analysis_generated", count=toss_stats.count())
        return toss_stats

    def generate_powerplay_analysis(self) -> DataFrame:
        """Generate powerplay and death overs analysis."""
        logger.info("generating_powerplay_analysis")
        balls = self.spark.read.parquet(f"{self.silver_path}/ball_events")

        phase_stats = (
            balls.groupBy("season", "batting_team", "phase")
            .agg(
                F.sum("runs_scored").alias("total_runs"),
                F.count("*").alias("total_balls"),
                F.sum(F.when(F.col("is_wicket"), 1).otherwise(0)).alias("wickets"),
                F.sum(F.when(F.col("is_boundary"), 1).otherwise(0)).alias("boundaries"),
                F.sum(F.when(F.col("is_dot_ball"), 1).otherwise(0)).alias("dot_balls"),
            )
            .withColumn("run_rate", F.round(F.col("total_runs") / (F.col("total_balls") / 6), 2))
            .withColumn(
                "boundary_pct", F.round(F.col("boundaries") / F.col("total_balls") * 100, 2)
            )
            .withColumn("dot_ball_pct", F.round(F.col("dot_balls") / F.col("total_balls") * 100, 2))
            .orderBy("season", "batting_team", "phase")
        )

        output_path = f"{self.gold_path}/powerplay_analysis"
        write_parquet(phase_stats, output_path, partition_by=["season"])
        logger.info("powerplay_analysis_generated", count=phase_stats.count())
        return phase_stats

    def run_all_analytics(self) -> dict[str, int]:
        """Run all Gold layer analytics jobs."""
        logger.info("gold_analytics_started")
        results = {}
        results["player_performance"] = self.generate_player_performance().count()
        results["match_summary"] = self.generate_match_summary().count()
        results["team_statistics"] = self.generate_team_statistics().count()
        results["venue_analytics"] = self.generate_venue_analytics().count()
        results["toss_analysis"] = self.generate_toss_analysis().count()
        results["powerplay_analysis"] = self.generate_powerplay_analysis().count()
        logger.info("gold_analytics_completed", results=results)
        return results


if __name__ == "__main__":
    analytics = GoldMatchAnalytics()
    analytics.run_all_analytics()
