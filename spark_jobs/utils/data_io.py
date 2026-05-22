"""Data I/O utilities for Spark jobs."""

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from monitoring.logger import get_logger

logger = get_logger(__name__)


def read_json(spark: SparkSession, path: str) -> DataFrame:
    """Read JSON data into a DataFrame."""
    logger.info("reading_json", path=path)
    return spark.read.json(path)


def read_parquet(spark: SparkSession, path: str) -> DataFrame:
    """Read Parquet data into a DataFrame."""
    logger.info("reading_parquet", path=path)
    return spark.read.parquet(path)


def read_delta(spark: SparkSession, path: str) -> DataFrame:
    """Read Delta Lake table into a DataFrame."""
    logger.info("reading_delta", path=path)
    return spark.read.format("delta").load(path)


def write_parquet(
    df: DataFrame, path: str, mode: str = "overwrite", partition_by: list[str] | None = None
) -> None:
    """Write DataFrame to Parquet format."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    writer = df.write.mode(mode)
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    writer.parquet(path)
    logger.info("written_parquet", path=path, mode=mode, rows=df.count())


def write_delta(
    df: DataFrame,
    path: str,
    mode: str = "overwrite",
    partition_by: list[str] | None = None,
    merge_schema: bool = False,
) -> None:
    """Write DataFrame to Delta Lake format."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    writer = df.write.format("delta").mode(mode)
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    if merge_schema:
        writer = writer.option("mergeSchema", "true")
    writer.save(path)
    logger.info("written_delta", path=path, mode=mode, rows=df.count())
