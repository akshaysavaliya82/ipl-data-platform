"""Kafka producer for ball-by-ball events."""

import json
import time
from typing import Any

from confluent_kafka import Producer

from ingestion.simulators.match_simulator import MatchSimulator
from kafka.config.topics import TOPICS
from monitoring.logger import get_logger
from monitoring.metrics import kafka_messages_produced

logger = get_logger(__name__)


class BallEventProducer:
    """Produces ball-by-ball events to Kafka topics."""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "ipl-ball-event-producer",
            "acks": "all",
            "retries": 3,
            "retry.backoff.ms": 1000,
            "linger.ms": 10,
            "batch.size": 16384,
            "compression.type": "snappy",
        }
        self.producer = Producer(self.config)
        self.ball_topic = TOPICS["ball_events"].name
        self.score_topic = TOPICS["score_updates"].name
        self.wicket_topic = TOPICS["wicket_events"].name
        self.match_state_topic = TOPICS["match_state"].name
        logger.info(
            "producer_initialized", topics=[self.ball_topic, self.score_topic, self.wicket_topic]
        )

    def _delivery_callback(self, err: Any, msg: Any) -> None:
        if err:
            logger.error("message_delivery_failed", error=str(err), topic=msg.topic())
        else:
            kafka_messages_produced.labels(topic=msg.topic()).inc()

    def produce_ball_event(self, event: dict[str, Any]) -> None:
        """Produce a single ball event to relevant topics."""
        key = event.get("match_id", "unknown")
        value = json.dumps(event).encode("utf-8")

        self.producer.produce(
            topic=self.ball_topic,
            key=key.encode("utf-8"),
            value=value,
            callback=self._delivery_callback,
        )

        score_update = {
            "match_id": event["match_id"],
            "timestamp": event["timestamp"],
            "innings": event["innings"],
            "over": event["over"],
            "ball": event["ball"],
            "total_runs": event["total_runs"],
            "total_wickets": event["total_wickets"],
            "run_rate": event["run_rate"],
            "batting_team": event["batting_team"],
            "bowling_team": event["bowling_team"],
        }
        self.producer.produce(
            topic=self.score_topic,
            key=key.encode("utf-8"),
            value=json.dumps(score_update).encode("utf-8"),
            callback=self._delivery_callback,
        )

        if event.get("is_wicket"):
            wicket_event = {
                "match_id": event["match_id"],
                "timestamp": event["timestamp"],
                "innings": event["innings"],
                "batsman": event["batsman"],
                "bowler": event["bowler"],
                "dismissal_type": event.get("dismissal_type", "unknown"),
                "total_wickets": event["total_wickets"],
            }
            self.producer.produce(
                topic=self.wicket_topic,
                key=key.encode("utf-8"),
                value=json.dumps(wicket_event).encode("utf-8"),
                callback=self._delivery_callback,
            )

        match_state = {
            "match_id": event["match_id"],
            "match_state": event.get("match_state", "in_progress"),
            "innings": event["innings"],
            "total_runs": event["total_runs"],
            "total_wickets": event["total_wickets"],
            "over": event["over"],
            "ball": event["ball"],
        }
        self.producer.produce(
            topic=self.match_state_topic,
            key=key.encode("utf-8"),
            value=json.dumps(match_state).encode("utf-8"),
            callback=self._delivery_callback,
        )

        self.producer.poll(0)

    def simulate_live_match(self, speed: float = 1.0, delay: float = 1.0) -> None:
        """Simulate a live match and produce events."""
        simulator = MatchSimulator(speed=speed)
        logger.info("live_match_simulation_started", match_id=simulator.match_id)

        events = simulator.simulate_match(delay=0)
        for event in events:
            self.produce_ball_event(event)
            time.sleep(delay / speed)

        self.producer.flush(timeout=30)
        logger.info(
            "live_match_simulation_completed", match_id=simulator.match_id, total_events=len(events)
        )

    def close(self) -> None:
        self.producer.flush(timeout=30)
        logger.info("producer_closed")


def run_producer(bootstrap_servers: str = "localhost:9092", speed: float = 2.0) -> None:
    """Run the ball event producer."""
    producer = BallEventProducer(bootstrap_servers)
    try:
        producer.simulate_live_match(speed=speed)
    finally:
        producer.close()


if __name__ == "__main__":
    run_producer()
