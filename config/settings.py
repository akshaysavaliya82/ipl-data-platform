"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    db: str = "ipl_analytics"
    user: str = "ipl_admin"
    password: str = "ipl_secure_password_2024"

    model_config = {"env_prefix": "POSTGRES_"}

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class KafkaSettings(BaseSettings):
    bootstrap_servers: str = "localhost:9092"
    topic_ball_events: str = "ipl.ball.events"
    topic_match_updates: str = "ipl.match.updates"
    topic_player_events: str = "ipl.player.events"
    consumer_group: str = "ipl-analytics-group"

    model_config = {"env_prefix": "KAFKA_"}


class SparkSettings(BaseSettings):
    master: str = "local[*]"
    app_name: str = "IPLAnalyticsPlatform"
    driver_memory: str = "2g"
    executor_memory: str = "2g"

    model_config = {"env_prefix": "SPARK_"}


class DataPathSettings(BaseSettings):
    lake_path: str = "/opt/data/lake"
    warehouse_path: str = "/opt/data/warehouse"
    raw_data_path: str = "/opt/data/raw"
    bronze_path: str = "/opt/data/lake/bronze"
    silver_path: str = "/opt/data/lake/silver"
    gold_path: str = "/opt/data/lake/gold"

    model_config = {"env_prefix": "DATA_"}

    def ensure_paths(self) -> None:
        for attr in [
            "lake_path",
            "warehouse_path",
            "raw_data_path",
            "bronze_path",
            "silver_path",
            "gold_path",
        ]:
            Path(getattr(self, attr)).mkdir(parents=True, exist_ok=True)


class APISettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    model_config = {"env_prefix": "API_"}


class Settings(BaseSettings):
    """Root settings aggregating all sub-settings."""

    app_name: str = "IPL Real-Time Analytics Lakehouse Platform"
    environment: str = "development"
    log_level: str = "INFO"

    postgres: PostgresSettings = PostgresSettings()
    kafka: KafkaSettings = KafkaSettings()
    spark: SparkSettings = SparkSettings()
    data_paths: DataPathSettings = DataPathSettings()
    api: APISettings = APISettings()

    model_config = {"env_prefix": "APP_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
