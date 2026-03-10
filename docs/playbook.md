# Step-by-step build plan (Director-level)

## Phase 1 — Dataset (today)
- Run the generator to produce CSVs in `/data_out`
- Validate row counts and basic integrity checks (orders link to customers, etc.)

## Phase 2 — ETL (tomorrow)
- Create `02-etl-pipeline-python/`:
  - Extract: read CSVs
  - Transform: standardize types, dedupe, enforce keys
  - Quality: null checks, uniqueness, referential integrity, business rules
  - Load: write cleaned tables (parquet/csv) + audit logs

## Phase 3 — Snowflake (day 2–3)
- Create schemas: RAW, STG, ANALYTICS
- Load RAW via COPY INTO
- Build STG views/tables with typing + dedupe
- Build ANALYTICS star schema:
  - dims: date, product, customer, account, geo, warehouse, carrier
  - facts: orders, order_items, payments, returns, shipments, inventory, pipeline

## Phase 4 — Tableau Executive Dashboards (day 3–4)
- KPI Overview (Revenue, GM%, AOV, refund rate, CSAT, OTIF)
- Revenue drivers (category, geo, segment)
- Pipeline (coverage, velocity, win rate, ACV)
- Fulfillment (carrier & warehouse performance)
- Support (SLA attainment, case drivers, CSAT trend)

## Phase 5 — Upwork packaging (same week)
- Add 3 portfolio items:
  1) ETL + Warehouse
  2) Executive Tableau Dashboards
  3) Salesforce Analytics model
- Each with: scope, architecture, KPIs delivered, screenshots, repo link
