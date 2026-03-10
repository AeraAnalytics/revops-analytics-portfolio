# OmniEdge Professionals — Snowflake Warehouse (RAW / STG / ANALYTICS)

This layer loads OmniEdge synthetic business data into Snowflake using a Director-level medallion architecture:
- **RAW:** landed source extracts
- **STG:** typed + standardized tables
- **ANALYTICS:** star schema facts/dims for BI and executive reporting

## What’s included
- DDL scripts for schemas + tables
- COPY INTO templates for loading files
- Analytics star schema + KPI-ready views
- Data validation checks

## Run order
1) 00_admin (schemas, warehouse)
2) 01_raw (RAW tables)
3) 02_stg (typed STG tables)
4) 03_analytics (dims/facts)
5) 04_views (exec views)
6) 99_checks (validation queries)
