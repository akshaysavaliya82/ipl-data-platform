"""Kafka topic configuration for IPL Data Platform."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicConfig:
    name: str
    partitions: int = 3
    replication_factor: int = 1
    retention_ms: int = 86400000  # 24 hours
    cleanup_policy: str = "delete"


TOPICS = {
    "ball_events": TopicConfig(
        name="ipl.ball.events",
        partitions=6,
        retention_ms=172800000,  # 48 hours
    ),
    "match_updates": TopicConfig(
        name="ipl.match.updates",
        partitions=3,
    ),
    "player_events": TopicConfig(
        name="ipl.player.events",
        partitions=3,
    ),
    "score_updates": TopicConfig(
        name="ipl.score.updates",
        partitions=3,
    ),
    "wicket_events": TopicConfig(
        name="ipl.wicket.events",
        partitions=3,
    ),
    "match_state": TopicConfig(
        name="ipl.match.state",
        partitions=3,
        cleanup_policy="compact",
    ),
}


def get_all_topic_names() -> list[str]:
    return [t.name for t in TOPICS.values()]
