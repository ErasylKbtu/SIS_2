
import json

from kafka import KafkaConsumer


BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "fda-reports"
EXPECTED_MESSAGES = 200
IDLE_TIMEOUT_SECONDS = 15


def main():
    consumer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id=None,
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
        consumer_timeout_ms=IDLE_TIMEOUT_SECONDS * 1000
    )

    consumer.subscribe([TOPIC])

    consumed = 0

    try:
        for message in consumer:
            record = message.value
            consumed += 1

            if consumed <= 3:
                print(
                    f"Received {consumed}: "
                    f"{record.get('safetyreportid')}"
                )

            if consumed >= EXPECTED_MESSAGES:
                break

    finally:
        consumer.close()

    print("\n========== CONSUMER RESULTS ==========")
    print(f"Expected: {EXPECTED_MESSAGES}")
    print(f"Consumed: {consumed}")
    print(f"Topic: {TOPIC}")
    print("======================================")

    if consumed != EXPECTED_MESSAGES:
        raise RuntimeError(
            f"Expected {EXPECTED_MESSAGES}, received {consumed}"
        )


if __name__ == "__main__":
    main()
