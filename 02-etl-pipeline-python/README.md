# OmniEdge Professionals — ETL Pipeline (Bronze / Silver / Gold)

This pipeline converts raw CSV extracts into analytics-ready datasets using a Director-level approach:
- **Bronze:** landed raw data (as-is)
- **Silver:** typed, deduped, standardized tables + data quality checks
- **Gold:** executive-ready facts/dimensions for BI and warehouse loading

## Inputs
`../data_out/*.csv`

## Outputs
- `outputs/bronze/` (copies)
- `outputs/silver/` (cleaned parquet)
- `outputs/gold/` (analytics parquet)
- `reports/data_quality_report.csv`

## Run
```bash
python run_etl.py
