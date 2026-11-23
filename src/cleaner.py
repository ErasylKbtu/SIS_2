
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "validated" / "valid_data.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATE_COLUMNS = [
    "receivedate",
    "receiptdate",
    "transmissiondate"
]

AGE_UNITS = {
    801: 1,
    802: 1 / 12,
    803: 1 / 52.1775,
    804: 1 / 365.25,
    805: 1 / 8766,
    806: 10
}


def load_data():
    df = pd.read_csv(INPUT_FILE)

    df = df.drop(
        columns=["_validation_errors", "_source"],
        errors="ignore"
    )

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(
            df[col],
            errors="coerce"
        )

    return df


def clean_data(df):

    initial_count = len(df)

    # 1. Remove duplicates
    duplicates = df.duplicated(
        subset=["safetyreportid"]
    ).sum()

    df = df.drop_duplicates(
        subset=["safetyreportid"],
        keep="first"
    ).copy()

    # 2. Convert numeric columns
    numeric_columns = [
        "safetyreportid",
        "serious",
        "patient_sex",
        "patient_age",
        "patient_age_unit",
        "patient_weight",
        "n_reactions",
        "n_drugs"
    ]

    seriousness_columns = [
        "seriousnessdeath",
        "seriousnesslifethreatening",
        "seriousnesshospitalization",
        "seriousnessdisabling",
        "seriousnesscongenitalanomali",
        "seriousnessother"
    ]

    numeric_columns += seriousness_columns

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # 3. Normalize text
    df["country"] = (
        df["country"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    df["primary_drug"] = (
        df["primary_drug"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # 4. Convert age into years
    age_multiplier = df["patient_age_unit"].map(AGE_UNITS)

    df["patient_age_years"] = (
        df["patient_age"] * age_multiplier
    )

    # 5. Create serious status using NumPy
    df["serious_status"] = np.select(
        [
            df["serious"].eq(1),
            df["serious"].eq(2)
        ],
        [
            "Serious",
            "Non-serious"
        ],
        default="Unknown"
    )

    # 6. Extract date information
    df["received_year"] = df["receivedate"].dt.year
    df["received_month"] = df["receivedate"].dt.month

    # 7. Check remaining missing values
    missing_values = df.isnull().sum()

    return df, initial_count, duplicates, missing_values


def perform_groupby(df):

    print("\n========== GROUPBY ANALYSIS ==========")

    grouped = (
        df.groupby(
            ["country", "serious_status"],
            dropna=False
        )
        .size()
        .reset_index(name="report_count")
    )

    print(grouped.head(10).to_string(index=False))

    grouped.to_csv(
        OUTPUT_DIR / "groupby_summary.csv",
        index=False
    )

    return grouped


def perform_pivot(grouped):

    print("\n========== PIVOT TABLE ==========")

    pivot_table = grouped.pivot(
        index="country",
        columns="serious_status",
        values="report_count"
    ).fillna(0)

    pivot_table = pivot_table.astype(int)

    pivot_table.to_csv(
        OUTPUT_DIR / "pivot_summary.csv"
    )

    print(pivot_table.head(10).to_string())

    return pivot_table


def perform_melt(pivot_table):

    print("\n========== MELT TABLE ==========")

    melted = (
        pivot_table
        .reset_index()
        .melt(
            id_vars="country",
            var_name="serious_status",
            value_name="report_count"
        )
    )

    melted = melted[melted["report_count"] > 0]

    melted.to_csv(
        OUTPUT_DIR / "melt_summary.csv",
        index=False
    )

    print(melted.head(10).to_string(index=False))

    return melted


def main():

    print("\n========== DATA CLEANING ==========\n")

    df = load_data()

    print(f"Records loaded: {len(df)}")

    df, initial_count, duplicates, missing = clean_data(df)

    # Save cleaned dataset
    output_file = OUTPUT_DIR / "clean_data.csv"

    df.to_csv(
        output_file,
        index=False
    )

    print("\n========== CLEANING RESULTS ==========")

    print(f"Initial records: {initial_count}")
    print(f"Duplicates removed: {duplicates}")
    print(f"Final records: {len(df)}")

    print("\n========== MISSING VALUES ==========")

    print(missing[missing > 0].to_string())

    # GroupBy
    grouped = perform_groupby(df)

    # Pivot
    pivot_table = perform_pivot(grouped)

    # Melt
    melted = perform_melt(pivot_table)

    print("\n========== FILES CREATED ==========")

    print("clean_data.csv")
    print("groupby_summary.csv")
    print("pivot_summary.csv")
    print("melt_summary.csv")

    print("\nDATA CLEANING COMPLETED!")


if __name__ == "__main__":
    main()
