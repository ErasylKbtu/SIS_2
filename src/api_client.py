
import json
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests


BASE_URL = "https://api.fda.gov/drug/event.json"

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"

TARGET_RECORDS = 200
PAGE_SIZE = 5
RECORDS_PER_WEEK = 10

START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 12, 31)


def make_date_windows(start_date, end_date):
    """Create consecutive weekly date windows."""
    windows = []
    current = start_date

    while current <= end_date:
        window_end = min(current + timedelta(days=6), end_date)
        windows.append((current, window_end))
        current = window_end + timedelta(days=1)

    return windows


def request_api(search_query, limit, skip):
    """Send an API request with basic retry handling."""
    params = {
        "search": search_query,
        "limit": limit,
        "skip": skip
    }

    for attempt in range(3):
        try:
            response = requests.get(
                BASE_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 404:
                return None

            if response.status_code == 429 or response.status_code >= 500:
                time.sleep(2 * (attempt + 1))
                continue

            response.raise_for_status()
            return response.json()

        except requests.RequestException as error:
            if attempt == 2:
                print(f"Request failed: {error}")
                return None

            time.sleep(2 * (attempt + 1))

        except ValueError as error:
            print(f"Invalid JSON response: {error}")
            return None

    return None


def get_number(value):
    """Convert a value to a number when possible."""
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def flatten_report(report):
    """Convert one FDA report into a flat table row."""
    patient = report.get("patient", {})

    drugs = patient.get("drug", [])
    reactions = patient.get("reaction", [])

    if not isinstance(drugs, list):
        drugs = []

    if not isinstance(reactions, list):
        reactions = []

    primary_drug = next(
        (
            drug for drug in drugs
            if str(drug.get("drugcharacterization")) == "1"
        ),
        drugs[0] if drugs else {}
    )

    return {
        "safetyreportid": report.get("safetyreportid"),
        "receivedate": report.get("receivedate"),
        "receiptdate": report.get("receiptdate"),
        "transmissiondate": report.get("transmissiondate"),
        "country": report.get("occurcountry"),
        "serious": report.get("serious"),

        "seriousnessdeath": report.get("seriousnessdeath"),
        "seriousnesslifethreatening": report.get(
            "seriousnesslifethreatening"
        ),
        "seriousnesshospitalization": report.get(
            "seriousnesshospitalization"
        ),
        "seriousnessdisabling": report.get("seriousnessdisabling"),
        "seriousnesscongenitalanomali": report.get(
            "seriousnesscongenitalanomali"
        ),
        "seriousnessother": report.get("seriousnessother"),

        "patient_sex": patient.get("patientsex"),
        "patient_age": get_number(patient.get("patientonsetage")),
        "patient_age_unit": patient.get("patientonsetageunit"),
        "patient_weight": get_number(patient.get("patientweight")),

        "n_reactions": len(reactions),
        "n_drugs": len(drugs),

        "primary_drug": primary_drug.get("medicinalproduct")
    }


def collect_data():
    """Collect reports from multiple weekly date windows."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_responses = []
    reports_by_id = {}

    windows = make_date_windows(START_DATE, END_DATE)

    for window_start, window_end in windows:
        if len(reports_by_id) >= TARGET_RECORDS:
            break

        start_str = window_start.strftime("%Y%m%d")
        end_str = window_end.strftime("%Y%m%d")

        search_query = f"receivedate:[{start_str} TO {end_str}]"

        print(f"\nRequesting: {start_str} - {end_str}")

        window_count = 0
        skip = 0

        while window_count < RECORDS_PER_WEEK:
            data = request_api(
                search_query,
                PAGE_SIZE,
                skip
            )

            if data is None:
                break

            all_responses.append({
                "window_start": start_str,
                "window_end": end_str,
                "skip": skip,
                "response": data
            })

            results = data.get("results", [])

            if not results:
                break

            for report in results:
                report_id = report.get("safetyreportid")

                if not report_id:
                    continue

                if report_id not in reports_by_id:
                    reports_by_id[report_id] = report
                    window_count += 1

                    if len(reports_by_id) >= TARGET_RECORDS:
                        break

            skip += PAGE_SIZE

            if len(results) < PAGE_SIZE:
                break

            if window_count >= RECORDS_PER_WEEK:
                break

            time.sleep(0.25)

        print(
            f"Unique records collected: {len(reports_by_id)}"
        )

    if len(reports_by_id) < TARGET_RECORDS:
        raise RuntimeError(
            f"Only {len(reports_by_id)} unique records collected. "
            f"At least {TARGET_RECORDS} are required."
        )

    # Save complete API responses.
    json_path = RAW_DIR / "openfda_raw_responses.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            all_responses,
            file,
            ensure_ascii=False,
            indent=2
        )

    # Convert reports into a flat table.
    rows = [
        flatten_report(report)
        for report in reports_by_id.values()
    ]

    dataframe = pd.DataFrame(rows)

    csv_path = RAW_DIR / "raw_data.csv"
    dataframe.to_csv(
        csv_path,
        index=False,
        encoding="utf-8-sig"
    )

    dates = pd.to_datetime(
        dataframe["receivedate"],
        format="%Y%m%d",
        errors="coerce"
    )

    print("\n========== COLLECTION RESULTS ==========")
    print(f"Unique records: {len(dataframe)}")
    print(f"Different receivedate values: {dates.nunique()}")
    print(f"Earliest receivedate: {dates.min()}")
    print(f"Latest receivedate: {dates.max()}")
    print(f"Full JSON: {json_path}")
    print(f"CSV: {csv_path}")
    print("========================================")


if __name__ == "__main__":
    collect_data()
