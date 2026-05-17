"""Spark session factory for IPL Data Platform."""

from pyspark.sql import SparkSession

from monitoring.logger import get_logger

logger = get_logger(__name__)


def create_spark_session(
    app_name: str = "IPL-Analytics",
    master: str = "local[*]",
    enable_delta: bool = True,
    extra_config: dict[str, str] | None = None,
) -> SparkSession:
    """Create a configured Spark session."""
    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
    )

    if enable_delta:
        builder = (
            builder.config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config(
                "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
            )
        )

    if extra_config:
        for key, value in extra_config.items():
            builder = builder.config(key, value)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    logger.info("spark_session_created", app_name=app_name, master=master)
    return spark
