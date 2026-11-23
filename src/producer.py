
import json
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer


PROJECT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_DIR / "data" / "raw" / "raw_data.csv"

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "fda-reports"


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    # Convert missing values to JSON null.
    df = df.astype(object).where(pd.notna(df), None)
    records = df.to_dict(orient="records")

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(
            value,
            ensure_ascii=False
        ).encode("utf-8"),
        acks="all",
        retries=3,
        max_request_size=2 * 1024 * 1024
    )

    futures = []

    try:
        for record in records:
            future = producer.send(TOPIC, value=record)
            futures.append(future)

        # Wait until all messages have been sent.
        producer.flush(timeout=60)

        published = 0

        for future in futures:
            future.get(timeout=30)
            published += 1

        print("========== PRODUCER RESULTS ==========")
        print(f"Records in CSV: {len(records)}")
        print(f"Published: {published}")
        print(f"Topic: {TOPIC}")
        print("======================================")

    finally:
        producer.close()


if __name__ == "__main__":
    main()
