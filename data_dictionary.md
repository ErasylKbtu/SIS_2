# Data Dictionary

## Overview

The dataset contains adverse drug event reports collected from the OpenFDA API.

The original dataset contains 200 records. After validation, 195 original records were considered valid and used for cleaning and analysis.

## Source Fields

| Field | Description |
|---|---|
| `safetyreportid` | Unique adverse event report identifier |
| `receivedate` | Date the report was received |
| `receiptdate` | Date the report was entered into the system |
| `transmissiondate` | Date the report was transmitted |
| `country` | Country associated with the report |
| `serious` | Seriousness classification |
| `seriousnessdeath` | Death-related seriousness indicator |
| `seriousnesslifethreatening` | Life-threatening indicator |
| `seriousnesshospitalization` | Hospitalization indicator |
| `seriousnessdisabling` | Disability indicator |
| `seriousnesscongenitalanomali` | Congenital anomaly indicator |
| `seriousnessother` | Other serious event indicator |
| `patient_sex` | Patient sex code |
| `patient_age` | Original patient age |
| `patient_age_unit` | Original age measurement unit |
| `patient_weight` | Patient weight |
| `n_reactions` | Number of reported reactions |
| `n_drugs` | Number of reported drugs |
| `primary_drug` | Primary suspected drug |

## Derived Fields

| Field | Description |
|---|---|
| `patient_age_years` | Patient age converted into years |
| `serious_status` | Text classification: Serious, Non-serious, or Unknown |
| `received_year` | Year extracted from `receivedate` |
| `received_month` | Month extracted from `receivedate` |

## Data Transformation Rules

### Age Conversion

The original age is converted into years using the following units:

| Unit Code | Unit | Conversion |
|---|---|---|
| 801 | Years | 1 |
| 802 | Months | 1/12 |
| 803 | Weeks | 1/52.1775 |
| 804 | Days | 1/365.25 |
| 805 | Hours | 1/8766 |
| 806 | Decades | 10 |

### Seriousness Classification

| Original Value | Classification |
|---|---|
| 1 | Serious |
| 2 | Non-serious |
| Other or missing | Unknown |

### Text Normalization

The `country` and `primary_drug` columns are stripped of surrounding whitespace and converted to uppercase.

## Validation Rules

The validation process checks:

- Unique and non-null report identifiers
- Required dates and country values
- Valid seriousness values
- Valid patient sex codes
- Valid patient age and age units
- Patient weight range
- Non-negative reaction and drug counts
- Valid seriousness indicators
- Correct chronological order of dates
- Consistency between seriousness classification and seriousness indicators

Additional row-level validation rules are implemented in `validator.py`.

## Output Files

| File | Description |
|---|---|
| `raw_data.csv` | Flattened original API data |
| `valid_data.csv` | Original records that passed validation |
| `invalid_data.csv` | Invalid original and artificial test records |
| `clean_data.csv` | Cleaned dataset |
| `groupby_summary.csv` | Country and seriousness counts |
| `pivot_summary.csv` | Pivoted country and seriousness summary |
| `melt_summary.csv` | Melted summary dataset |

## Database

SQLite database: `data/database/sis2.db`

Table: `fda_reports`

Primary key: `safetyreportid`