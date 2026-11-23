# SIS-2: FDA Adverse Event Data Pipeline

## Project Overview

This project implements a data engineering pipeline for collecting, processing, validating, and analyzing adverse drug event reports using the OpenFDA API.

The pipeline uses Python, Apache Kafka, Pandera, Pandas, NumPy, SQLite, and Matplotlib.

## Technologies

- Python — main programming language
- OpenFDA API — source of adverse event reports
- Apache Kafka 4.1.0 — message streaming
- Docker Compose — Kafka environment
- Pandera — data validation
- Pandas and NumPy — data cleaning and transformation
- SQLite — data storage
- Matplotlib — data visualization

## Project Structure

```text
SIS-2/
├── docker-compose.yml
├── data/
│   ├── raw/
│   │   ├── openfda_raw_responses.json
│   │   └── raw_data.csv
│   ├── validated/
│   │   ├── valid_data.csv
│   │   └── invalid_data.csv
│   ├── processed/
│   │   ├── clean_data.csv
│   │   ├── groupby_summary.csv
│   │   ├── pivot_summary.csv
│   │   └── melt_summary.csv
│   └── database/
│       └── sis2.db
├── src/
│   ├── api_client.py
│   ├── producer.py
│   ├── consumer.py
│   ├── validator.py
│   ├── cleaner.py
│   ├── loader.py
│   └── analysis.py
├── reports/
│   ├── validation_report.txt
│   └── report.pdf
├── figures/
│   ├── reports_by_country.png
│   ├── reports_over_time.png
│   └── serious_vs_non_serious.png
└── README.md
```

## Pipeline Architecture

1. **Data Collection:** The API client retrieves adverse event reports from OpenFDA and saves raw JSON responses and flattened CSV data.
2. **Message Streaming:** Kafka Producer publishes records to the `fda-reports` topic. Kafka Consumer reads the messages.
3. **Data Validation:** Pandera and additional validation rules check required fields, data types, age, dates, and seriousness values.
4. **Data Cleaning:** Pandas and NumPy remove duplicate records, normalize text, convert patient age into years, and create derived columns.
5. **Data Transformation:** GroupBy, Pivot, and Melt operations generate summary datasets.
6. **Database Loading:** Clean records are loaded into SQLite using `INSERT OR IGNORE`.
7. **Data Analysis:** Matplotlib generates three visualizations.

## Installation

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install pandas numpy requests kafka-python pandera matplotlib
```

## Running the Pipeline

### 1. Start Kafka

```bash
docker compose up -d
```

### 2. Collect API Data

```bash
python src/api_client.py
```

### 3. Start Kafka Producer

```bash
python src/producer.py
```

### 4. Start Kafka Consumer

```bash
python src/consumer.py
```

### 5. Validate Data

```bash
python src/validator.py
```

### 6. Clean and Transform Data

```bash
python src/cleaner.py
```

### 7. Load Data into SQLite

```bash
python src/loader.py
```

### 8. Analyze Data

```bash
python src/analysis.py
```

## Validation Results

The validation process checked 203 records:

- Original records: 200
- Artificial test records: 3
- Original valid records: 195
- Original invalid records: 5
- Artificial invalid records detected: 3
- Total invalid records: 8

## Cleaning Results

- Records loaded: 195
- Duplicate records removed: 0
- Final cleaned records: 195

## Analysis Results

The analysis processed 195 cleaned records.

- Serious reports: 139 (71.28%)
- Non-serious reports: 56 (28.72%)

Three charts were generated:

- Reports by country
- Reports over time
- Serious versus non-serious reports

## Database

The project uses SQLite with the database file `data/database/sis2.db`.

The table is named `fda_reports`. The `safetyreportid` field is used as the primary key.

The loader uses `INSERT OR IGNORE` to prevent duplicate records when the pipeline is executed multiple times.

## Conclusion

The project demonstrates a complete data engineering workflow, including API data collection, Kafka streaming, data validation, data cleaning, transformation, database storage, and visualization.