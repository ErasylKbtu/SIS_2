
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "clean_data.csv"
FIGURES_DIR = BASE_DIR / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def find_column(df, candidates):
    """Find a column ignoring uppercase/lowercase differences."""
    columns = {col.lower().strip(): col for col in df.columns}

    for candidate in candidates:
        if candidate.lower() in columns:
            return columns[candidate.lower()]

    return None


def parse_dates(series):
    """Parse both YYYYMMDD and standard date formats."""
    values = series.astype("string").str.strip()

    result = pd.to_datetime(
        values,
        format="%Y%m%d",
        errors="coerce"
    )

    missing = result.isna()

    if missing.any():
        result.loc[missing] = pd.to_datetime(
            values.loc[missing],
            errors="coerce"
        )

    return result


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    if df.empty:
        raise ValueError("Dataset is empty.")

    df.columns = df.columns.str.strip()

    print("=" * 45)
    print("DATA ANALYSIS")
    print("=" * 45)

    print(f"Records loaded: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("\nAvailable columns:")
    print(df.columns.tolist())

    return df


def analyze_by_country(df):
    country_col = find_column(
        df,
        ["country", "primarysourcecountry", "country_code"]
    )

    if country_col is None:
        raise ValueError("Country column not found.")

    country_data = df.copy()

    country_data[country_col] = (
        country_data[country_col]
        .fillna("Unknown")
        .astype(str)
    )

    country_counts = (
        country_data[country_col]
        .value_counts()
        .head(10)
        .sort_values()
    )

    plt.figure(figsize=(10, 6))

    country_counts.plot(
        kind="barh",
        edgecolor="black"
    )

    plt.title("Top 10 Countries by FDA Reports")
    plt.xlabel("Number of Reports")
    plt.ylabel("Country")
    plt.tight_layout()

    output = FIGURES_DIR / "reports_by_country.png"
    plt.savefig(output, dpi=300)
    plt.close()

    print(f"\nCountry chart saved: {output}")


def analyze_over_time(df):
    date_col = find_column(
        df,
        ["receivedate", "receiptdate", "transmissiondate"]
    )

    if date_col is None:
        raise ValueError("Date column not found.")

    dates = parse_dates(df[date_col])

    valid_dates = dates.dropna()

    if valid_dates.empty:
        raise ValueError("No valid dates found.")

    monthly_counts = (
        valid_dates.dt.to_period("M")
        .value_counts()
        .sort_index()
    )

    monthly_counts.index = monthly_counts.index.astype(str)

    plt.figure(figsize=(12, 6))

    monthly_counts.plot(
        kind="line",
        marker="o",
        linewidth=2
    )

    plt.title("FDA Reports Over Time")
    plt.xlabel("Month")
    plt.ylabel("Number of Reports")
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output = FIGURES_DIR / "reports_over_time.png"
    plt.savefig(output, dpi=300)
    plt.close()

    print(f"Time chart saved: {output}")


def analyze_seriousness(df):
    serious_col = find_column(
        df,
        ["serious"]
    )

    if serious_col is None:
        raise ValueError("Serious column not found.")

    values = df[serious_col].astype("string").str.strip().str.lower()

    mapping = {
        "1": "Serious",
        "2": "Non-Serious",
        "true": "Serious",
        "false": "Non-Serious",
        "yes": "Serious",
        "no": "Non-Serious"
    }

    categories = values.map(mapping).dropna()

    if categories.empty:
        raise ValueError(
            "No valid Serious/Non-Serious values found."
        )

    counts = categories.value_counts()

    plt.figure(figsize=(8, 8))

    plt.pie(
        counts,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=90,
        explode=[0.04] * len(counts)
    )

    plt.title("Serious vs Non-Serious FDA Reports")
    plt.tight_layout()

    output = FIGURES_DIR / "serious_vs_non_serious.png"
    plt.savefig(output, dpi=300)
    plt.close()

    print(f"Seriousness chart saved: {output}")

    print("\nSeriousness statistics:")
    print(counts.to_string())


def main():
    df = load_data()

    analyze_by_country(df)
    analyze_over_time(df)
    analyze_seriousness(df)

    print("\n" + "=" * 45)
    print("ANALYSIS COMPLETED")
    print("=" * 45)

    print(f"Total records analyzed: {len(df)}")
    print(f"Charts saved in: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
