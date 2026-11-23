
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "raw_data.csv"
OUTPUT_DIR = BASE_DIR / "data" / "validated"
REPORT_DIR = BASE_DIR / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DATE_COLUMNS = [
    "receivedate",
    "receiptdate",
    "transmissiondate"
]

SERIOUSNESS_COLUMNS = [
    "seriousnessdeath",
    "seriousnesslifethreatening",
    "seriousnesshospitalization",
    "seriousnessdisabling",
    "seriousnesscongenitalanomali",
    "seriousnessother"
]

REQUIRED_COLUMNS = [
    "safetyreportid",
    "receivedate",
    "receiptdate",
    "transmissiondate",
    "country",
    "serious",
    "n_reactions",
    "n_drugs"
]

NUMERIC_COLUMNS = [
    "safetyreportid",
    "serious",
    *SERIOUSNESS_COLUMNS,
    "patient_sex",
    "patient_age",
    "patient_age_unit",
    "patient_weight",
    "n_reactions",
    "n_drugs"
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

    missing = set(REQUIRED_COLUMNS) - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(
            df[col].astype("string"),
            format="%Y%m%d",
            errors="coerce"
        )

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def create_test_records(df):
    """Create three invalid records without modifying the original CSV."""

    tests = []

    # Test 1: Invalid patient sex
    row1 = df.iloc[0].copy()
    row1["safetyreportid"] = 99900001
    row1["patient_sex"] = 9
    tests.append(row1)

    # Test 2: Negative patient age
    row2 = df.iloc[1].copy()
    row2["safetyreportid"] = 99900002
    row2["patient_age"] = -5
    row2["patient_age_unit"] = 801
    tests.append(row2)

    # Test 3: Invalid date sequence
    row3 = df.iloc[2].copy()
    row3["safetyreportid"] = 99900003
    row3["receivedate"] = pd.Timestamp("2025-06-01")
    row3["receiptdate"] = pd.Timestamp("2025-01-01")
    tests.append(row3)

    return pd.DataFrame(tests)


def create_schema():

    columns = {
        "safetyreportid": pa.Column(
            float,
            nullable=False,
            unique=True
        ),

        "receivedate": pa.Column(
            pa.DateTime,
            nullable=False
        ),

        "receiptdate": pa.Column(
            pa.DateTime,
            nullable=False
        ),

        "transmissiondate": pa.Column(
            pa.DateTime,
            nullable=False
        ),

        "country": pa.Column(
            str,
            nullable=False
        ),

        "serious": pa.Column(
            float,
            checks=Check.isin([1, 2]),
            nullable=False
        ),

        "patient_sex": pa.Column(
            float,
            checks=Check.isin([0, 1, 2]),
            nullable=True
        ),

        "patient_age": pa.Column(
            float,
            nullable=True
        ),

        "patient_age_unit": pa.Column(
            float,
            nullable=True
        ),

        "patient_weight": pa.Column(
            float,
            checks=Check.in_range(0.1, 500),
            nullable=True
        ),

        "n_reactions": pa.Column(
            int,
            checks=Check.ge(0),
            nullable=False
        ),

        "n_drugs": pa.Column(
            int,
            checks=Check.ge(0),
            nullable=False
        )
    }

    for col in SERIOUSNESS_COLUMNS:
        columns[col] = pa.Column(
            float,
            checks=Check.isin([1, 2]),
            nullable=True
        )

    return pa.DataFrameSchema(
        columns,
        checks=[
            Check(
                lambda d: d["receiptdate"] >= d["receivedate"],
                error="receiptdate must be >= receivedate"
            ),

            Check(
                lambda d: d["transmissiondate"] >= d["receiptdate"],
                error="transmissiondate must be >= receiptdate"
            ),

            Check(
                lambda d: (
                    (d["serious"] == 1)
                    == d[SERIOUSNESS_COLUMNS].eq(1).any(axis=1)
                ),
                error="Seriousness flags must match serious"
            )
        ],
        strict=False,
        coerce=True
    )


def validate_records(df):

    errors = pd.Series("", index=df.index, dtype="object")

    def add_error(mask, message):
        mask = mask.fillna(False)
        errors.loc[mask] += message + "; "

    # 1. Required fields
    for col in REQUIRED_COLUMNS:
        add_error(df[col].isna(), f"Missing {col}")

    # 2. Unique safetyreportid
    add_error(
        df["safetyreportid"].duplicated(keep=False),
        "Duplicate safetyreportid"
    )

    # 3. Valid serious values
    add_error(
        ~df["serious"].isin([1, 2]),
        "Invalid serious value"
    )

    # 4. Valid patient sex
    add_error(
        df["patient_sex"].notna()
        & ~df["patient_sex"].isin([0, 1, 2]),
        "Invalid patient_sex"
    )

    # 5. Valid seriousness flags
    for col in SERIOUSNESS_COLUMNS:
        add_error(
            df[col].notna() & ~df[col].isin([1, 2]),
            f"Invalid {col}"
        )

    # 6. Age validation with age units
    age = df["patient_age"]
    unit = df["patient_age_unit"]

    age_years = age * unit.map(AGE_UNITS)

    add_error(
        age.notna()
        & (
            unit.isna()
            | ~unit.isin(AGE_UNITS)
            | (age < 0)
            | (age_years > 120)
        ),
        "Invalid patient age or age unit"
    )

    # 7. Weight range
    add_error(
        df["patient_weight"].notna()
        & ~df["patient_weight"].between(0.1, 500),
        "Invalid patient weight"
    )

    # 8. Date format
    for col in DATE_COLUMNS:
        add_error(
            df[col].isna(),
            f"Invalid or missing {col}"
        )

    # 9. Date sequence
    add_error(
        df["receivedate"].notna()
        & df["receiptdate"].notna()
        & (df["receiptdate"] < df["receivedate"]),
        "receiptdate < receivedate"
    )

    add_error(
        df["receiptdate"].notna()
        & df["transmissiondate"].notna()
        & (df["transmissiondate"] < df["receiptdate"]),
        "transmissiondate < receiptdate"
    )

    # 10. Seriousness consistency
    has_serious_flag = df[SERIOUSNESS_COLUMNS].eq(1).any(axis=1)

    add_error(
        ((df["serious"] == 1) & ~has_serious_flag)
        | ((df["serious"] == 2) & has_serious_flag),
        "Inconsistent serious flags"
    )

    return errors


def main():

    print("\n========== DATA VALIDATION ==========\n")

    original = load_data()

    print(f"Original records: {len(original)}")

    # Keep original records separate from test records
    original["_source"] = "original"

    test_records = create_test_records(original)

    test_records["_source"] = "test"

    combined = pd.concat(
        [original, test_records],
        ignore_index=True
    )

    print(f"Test records added: {len(test_records)}")
    print(f"Total records: {len(combined)}")

    # Pandera validation
    print("\n========== PANDERA SCHEMA ==========\n")

    schema = create_schema()

    try:
        schema.validate(combined, lazy=True)
        print("Pandera schema validation passed.")

    except pa.errors.SchemaErrors as exc:
        print("Pandera detected validation errors.")
        print(f"Schema errors: {len(exc.failure_cases)}")

    # Detailed row-level validation
    row_errors = validate_records(combined)

    combined["_validation_errors"] = row_errors

    valid = combined[row_errors == ""].copy()
    invalid = combined[row_errors != ""].copy()

    # Separate original and artificial test results
    original_valid = valid[valid["_source"] == "original"]
    original_invalid = invalid[invalid["_source"] == "original"]

    test_invalid = invalid[invalid["_source"] == "test"]

    # Save results
    export_columns = [
        col for col in combined.columns
        if col != "_source"
    ]

    original_valid[export_columns].to_csv(
        OUTPUT_DIR / "valid_data.csv",
        index=False
    )

    invalid[export_columns].to_csv(
        OUTPUT_DIR / "invalid_data.csv",
        index=False
    )

    # Generate report
    report = [
        "========== VALIDATION REPORT ==========",
        f"Original records: {len(original)}",
        f"Artificial test records: {len(test_records)}",
        f"Total records checked: {len(combined)}",
        "",
        f"Original valid: {len(original_valid)}",
        f"Original invalid: {len(original_invalid)}",
        f"Artificial invalid detected: {len(test_invalid)}",
        f"Total invalid: {len(invalid)}",
        "",
        "========== INVALID RECORDS =========="
    ]

    for index, row in invalid.iterrows():
        report.append(
            f"ID: {row['safetyreportid']} | "
            f"Source: {row['_source']} | "
            f"Errors: {row['_validation_errors']}"
        )

    report.append("\n========== END OF REPORT ==========")

    report_text = "\n".join(report)

    with open(
        REPORT_DIR / "validation_report.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(report_text)

    print("\n" + report_text)

    print("\n========== FILES CREATED ==========")
    print(OUTPUT_DIR / "valid_data.csv")
    print(OUTPUT_DIR / "invalid_data.csv")
    print(REPORT_DIR / "validation_report.txt")


if __name__ == "__main__":
    main()
