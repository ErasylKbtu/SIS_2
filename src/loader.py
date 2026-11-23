
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "data" / "processed" / "clean_data.csv"
DB_PATH = BASE_DIR / "data" / "database" / "sis2.db"

TABLE_NAME = "fda_reports"


def load_data():
    df = pd.read_csv(CSV_PATH)

    connection = sqlite3.connect(DB_PATH)

    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            safetyreportid TEXT PRIMARY KEY
        )
    """)

    existing_columns = {
        row[1] for row in connection.execute(
            f"PRAGMA table_info({TABLE_NAME})"
        ).fetchall()
    }

    for column in df.columns:
        if column not in existing_columns:
            connection.execute(
                f'ALTER TABLE {TABLE_NAME} ADD COLUMN "{column}"'
            )

    columns = list(df.columns)
    column_names = ", ".join(f'"{col}"' for col in columns)
    placeholders = ", ".join("?" for _ in columns)

    insert_sql = f"""
        INSERT OR IGNORE INTO {TABLE_NAME}
        ({column_names})
        VALUES ({placeholders})
    """

    df = df.astype(object).where(pd.notna(df), None)

    before = connection.execute(
        f"SELECT COUNT(*) FROM {TABLE_NAME}"
    ).fetchone()[0]

    connection.executemany(
        insert_sql,
        df[columns].itertuples(index=False, name=None)
    )

    connection.commit()

    after = connection.execute(
        f"SELECT COUNT(*) FROM {TABLE_NAME}"
    ).fetchone()[0]

    inserted = after - before

    print("========== SQLITE LOADER ==========")
    print(f"CSV records: {len(df)}")
    print(f"Records before loading: {before}")
    print(f"New records inserted: {inserted}")
    print(f"Total records in database: {after}")
    print("===================================")

    connection.close()


if __name__ == "__main__":
    load_data()
