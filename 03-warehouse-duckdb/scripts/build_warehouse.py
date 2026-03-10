from pathlib import Path
import duckdb

REPO_ROOT = Path(__file__).resolve().parents[2]
DUCKDB_PATH = REPO_ROOT / "03-warehouse-duckdb" / "omniedge_revops.duckdb"

# Inputs: prefer SILVER parquet (clean/typed), fallback to GOLD, then CSV
GOLD_DIR = REPO_ROOT / "02-etl-pipeline-python" / "outputs" / "gold"
SILVER_DIR = REPO_ROOT / "02-etl-pipeline-python" / "outputs" / "silver"
DATA_OUT_DIR = REPO_ROOT / "data_out"  # fallback for dims as CSV if needed


def run_sql(con, sql: str):
    con.execute(sql)


def main():
    con = duckdb.connect(str(DUCKDB_PATH))
    con.execute("PRAGMA threads=4;")

    # 00_admin: schemas
    run_sql(
        con,
        """
        CREATE SCHEMA IF NOT EXISTS raw;
        CREATE SCHEMA IF NOT EXISTS stg;
        CREATE SCHEMA IF NOT EXISTS analytics;
        """,
    )

    # 01_raw: create raw tables from files (parquet preferred)
    def create_raw_from_parquet(table_name: str, parquet_path: Path):
        run_sql(
            con,
            f"""
            CREATE OR REPLACE TABLE raw.{table_name} AS
            SELECT * FROM read_parquet('{parquet_path.as_posix()}');
            """,
        )

    def create_raw_from_csv(table_name: str, csv_path: Path):
        run_sql(
            con,
            f"""
            CREATE OR REPLACE TABLE raw.{table_name} AS
            SELECT * FROM read_csv_auto('{csv_path.as_posix()}', header=true);
            """,
        )

    # Load core tables
    tables = [
        "orders",
        "order_items",
        "payments",
        "returns",
        "shipments",
        "shipment_events",
        "inventory_snapshots",
        "inventory_movements",
        "support_cases",
        "customers",
        "products",
        "warehouses",
        "sf_accounts",
        "sf_opportunities",
        "sf_contacts",
        "sf_leads",
        "sf_opportunity_line_items",
        "sf_activities",
        "dim_geo",
        "dim_dates",
    ]

    for t in tables:
        p_silver = SILVER_DIR / f"{t}.parquet"
        p_gold = GOLD_DIR / f"{t}.parquet"
        c_csv = DATA_OUT_DIR / f"{t}.csv"

        if p_silver.exists():
            create_raw_from_parquet(t, p_silver)
        elif p_gold.exists():
            create_raw_from_parquet(t, p_gold)
        elif c_csv.exists():
            create_raw_from_csv(t, c_csv)
        else:
            print(f"Skipping (not found): {t}")

    # 02_stg: typed STG tables (bulletproof string-safe casting)
        run_sql(con, """
        -- Orders
        CREATE OR REPLACE TABLE stg.stg_orders AS
        SELECT
          CAST(order_id AS VARCHAR) AS order_id,
          CAST(customer_id AS VARCHAR) AS customer_id,
          try_cast(NULLIF(CAST(order_date AS VARCHAR), '') AS DATE) AS order_date,
          CAST(channel AS VARCHAR) AS channel,
          CAST(status AS VARCHAR) AS status,
          CAST(warehouse_id AS VARCHAR) AS warehouse_id,

          try_cast(NULLIF(CAST(subtotal AS VARCHAR), '') AS DOUBLE) AS subtotal,
          try_cast(NULLIF(CAST(discount AS VARCHAR), '') AS DOUBLE) AS discount,
          try_cast(NULLIF(CAST(tax AS VARCHAR), '') AS DOUBLE) AS tax,
          try_cast(NULLIF(CAST(shipping_fee AS VARCHAR), '') AS DOUBLE) AS shipping_fee,
          try_cast(NULLIF(CAST(order_total AS VARCHAR), '') AS DOUBLE) AS order_total,

          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.orders;

        -- Order Items
        CREATE OR REPLACE TABLE stg.stg_order_items AS
        SELECT
          CAST(order_id AS VARCHAR) AS order_id,
          CAST(product_id AS VARCHAR) AS product_id,
          try_cast(NULLIF(CAST(quantity AS VARCHAR), '') AS BIGINT) AS quantity,
          try_cast(NULLIF(CAST(unit_price AS VARCHAR), '') AS DOUBLE) AS unit_price,
          try_cast(NULLIF(CAST(line_total AS VARCHAR), '') AS DOUBLE) AS line_total
        FROM raw.order_items;

        -- Products
        CREATE OR REPLACE TABLE stg.stg_products AS
        SELECT
          CAST(product_id AS VARCHAR) AS product_id,
          CAST(sku AS VARCHAR) AS sku,
          CAST(product_name AS VARCHAR) AS product_name,
          CAST(category AS VARCHAR) AS category,
          try_cast(NULLIF(CAST(unit_cost AS VARCHAR), '') AS DOUBLE) AS unit_cost,
          try_cast(NULLIF(CAST(list_price AS VARCHAR), '') AS DOUBLE) AS list_price,
          try_cast(NULLIF(CAST(is_active AS VARCHAR), '') AS BOOLEAN) AS is_active,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.products;

        -- Customers
        CREATE OR REPLACE TABLE stg.stg_customers AS
        SELECT
          CAST(customer_id AS VARCHAR) AS customer_id,
          CAST(email AS VARCHAR) AS email,
          CAST(first_name AS VARCHAR) AS first_name,
          CAST(last_name AS VARCHAR) AS last_name,
          CAST(geo_id AS VARCHAR) AS geo_id,
          CAST(segment AS VARCHAR) AS segment,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.customers;

        -- Warehouses
        CREATE OR REPLACE TABLE stg.stg_warehouses AS
        SELECT
          CAST(warehouse_id AS VARCHAR) AS warehouse_id,
          CAST(warehouse_name AS VARCHAR) AS warehouse_name,
          CAST(geo_id AS VARCHAR) AS geo_id,
          try_cast(NULLIF(CAST(capacity_units AS VARCHAR), '') AS BIGINT) AS capacity_units,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.warehouses;

        -- Shipments
        CREATE OR REPLACE TABLE stg.stg_shipments AS
        SELECT
          CAST(shipment_id AS VARCHAR) AS shipment_id,
          CAST(order_id AS VARCHAR) AS order_id,
          CAST(carrier AS VARCHAR) AS carrier,
          try_cast(NULLIF(CAST(ship_date AS VARCHAR), '') AS DATE) AS ship_date,
          try_cast(NULLIF(CAST(estimated_delivery AS VARCHAR), '') AS DATE) AS estimated_delivery,
          try_cast(NULLIF(CAST(delivered_date AS VARCHAR), '') AS DATE) AS delivered_date,
          try_cast(NULLIF(CAST(shipping_cost AS VARCHAR), '') AS DOUBLE) AS shipping_cost,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.shipments;

        -- Payments
        CREATE OR REPLACE TABLE stg.stg_payments AS
        SELECT
          CAST(payment_id AS VARCHAR) AS payment_id,
          CAST(order_id AS VARCHAR) AS order_id,
          try_cast(NULLIF(CAST(payment_date AS VARCHAR), '') AS DATE) AS payment_date,
          CAST(method AS VARCHAR) AS method,
          try_cast(NULLIF(CAST(amount AS VARCHAR), '') AS DOUBLE) AS amount,
          CAST(status AS VARCHAR) AS status
        FROM raw.payments;

        -- Returns
        CREATE OR REPLACE TABLE stg.stg_returns AS
        SELECT
          CAST(return_id AS VARCHAR) AS return_id,
          CAST(order_id AS VARCHAR) AS order_id,
          try_cast(NULLIF(CAST(return_date AS VARCHAR), '') AS DATE) AS return_date,
          CAST(reason AS VARCHAR) AS reason,
          try_cast(NULLIF(CAST(refund_amount AS VARCHAR), '') AS DOUBLE) AS refund_amount,
          CAST(status AS VARCHAR) AS status
        FROM raw.returns;

        -- Support Cases
        CREATE OR REPLACE TABLE stg.stg_support_cases AS
        SELECT
          CAST(case_id AS VARCHAR) AS case_id,
          CAST(customer_id AS VARCHAR) AS customer_id,
          CAST(case_type AS VARCHAR) AS case_type,
          CAST(priority AS VARCHAR) AS priority,
          CAST(status AS VARCHAR) AS status,
          try_cast(NULLIF(CAST(sla_hours AS VARCHAR), '') AS DOUBLE) AS sla_hours,
          try_cast(NULLIF(CAST(csat_score AS VARCHAR), '') AS DOUBLE) AS csat_score,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(first_response_at AS VARCHAR), '') AS TIMESTAMP) AS first_response_at,
          try_cast(NULLIF(CAST(resolved_at AS VARCHAR), '') AS TIMESTAMP) AS resolved_at
        FROM raw.support_cases;

        -- Salesforce Accounts
        CREATE OR REPLACE TABLE stg.stg_sf_accounts AS
        SELECT
          CAST(account_id AS VARCHAR) AS account_id,
          CAST(account_name AS VARCHAR) AS account_name,
          CAST(industry AS VARCHAR) AS industry,
          CAST(tier AS VARCHAR) AS tier,
          try_cast(NULLIF(CAST(employees AS VARCHAR), '') AS BIGINT) AS employees,
          CAST(geo_id AS VARCHAR) AS geo_id,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.sf_accounts;

        -- Salesforce Opportunities
        CREATE OR REPLACE TABLE stg.stg_sf_opportunities AS
        SELECT
          CAST(opportunity_id AS VARCHAR) AS opportunity_id,
          CAST(account_id AS VARCHAR) AS account_id,
          CAST(stage AS VARCHAR) AS stage,
          try_cast(NULLIF(CAST(amount AS VARCHAR), '') AS DOUBLE) AS amount,
          try_cast(NULLIF(CAST(probability AS VARCHAR), '') AS BIGINT) AS probability,
          try_cast(NULLIF(CAST(close_date AS VARCHAR), '') AS DATE) AS close_date,
          try_cast(NULLIF(CAST(created_at AS VARCHAR), '') AS TIMESTAMP) AS created_at,
          try_cast(NULLIF(CAST(updated_at AS VARCHAR), '') AS TIMESTAMP) AS updated_at
        FROM raw.sf_opportunities;
        """)

    # 03_analytics: star schema
    run_sql(
        con,
        """
        -- Dimensions
        CREATE OR REPLACE TABLE analytics.dim_date AS
        SELECT
          try_cast(NULLIF(CAST(date_key AS VARCHAR), '') AS BIGINT) AS date_key,
          try_cast(NULLIF(CAST(date AS VARCHAR), '') AS DATE) AS date,
          try_cast(NULLIF(CAST(year AS VARCHAR), '') AS BIGINT) AS year,
          try_cast(NULLIF(CAST(quarter AS VARCHAR), '') AS BIGINT) AS quarter,
          try_cast(NULLIF(CAST(month AS VARCHAR), '') AS BIGINT) AS month,
          CAST(month_name AS VARCHAR) AS month_name,
          try_cast(NULLIF(CAST(week AS VARCHAR), '') AS BIGINT) AS week,
          try_cast(NULLIF(CAST(day_of_week AS VARCHAR), '') AS BIGINT) AS day_of_week,
          try_cast(NULLIF(CAST(is_weekend AS VARCHAR), '') AS BOOLEAN) AS is_weekend
        FROM raw.dim_dates;
          
          
        CREATE OR REPLACE TABLE analytics.dim_geo AS
        SELECT
          geo_id::VARCHAR AS geo_id,
          country::VARCHAR AS country,
          state::VARCHAR AS state,
          city::VARCHAR AS city,
          postal_code::VARCHAR AS postal_code,
          region::VARCHAR AS region
        FROM raw.dim_geo;

        CREATE OR REPLACE TABLE analytics.dim_product AS
        SELECT
          product_id, sku, product_name, category, unit_cost, list_price, is_active
        FROM stg.stg_products;

        CREATE OR REPLACE TABLE analytics.dim_customer AS
        SELECT
          customer_id, email, first_name, last_name, geo_id, segment, created_at
        FROM stg.stg_customers;

        CREATE OR REPLACE TABLE analytics.dim_account AS
        SELECT
          account_id, account_name, industry, tier, employees, geo_id, created_at
        FROM stg.stg_sf_accounts;

        CREATE OR REPLACE TABLE analytics.dim_warehouse AS
        SELECT
          warehouse_id, warehouse_name, geo_id, capacity_units
        FROM stg.stg_warehouses;

        -- Facts
        CREATE OR REPLACE TABLE analytics.fact_orders AS
        SELECT
          o.order_id,
          o.customer_id,
          o.warehouse_id,
          try_cast(strftime(o.order_date, '%Y%m%d') AS BIGINT) AS date_key,
          o.channel,
          o.status,
          o.subtotal,
          o.discount,
          o.tax,
          o.shipping_fee,
          o.order_total
        FROM stg.stg_orders o;

        CREATE OR REPLACE TABLE analytics.fact_order_items AS
        SELECT
          i.order_id,
          i.product_id,
          i.quantity,
          i.unit_price,
          i.line_total,
          p.unit_cost,
          (i.quantity * p.unit_cost) AS extended_cost,
          (i.line_total - (i.quantity * p.unit_cost)) AS gross_margin
        FROM stg.stg_order_items i
        LEFT JOIN analytics.dim_product p
          ON i.product_id = p.product_id;

        CREATE OR REPLACE TABLE analytics.fact_payments AS
        SELECT
          payment_id,
          order_id,
          try_cast(strftime(payment_date, '%Y%m%d') AS BIGINT) AS date_key,
          method,
          amount,
          status
        FROM stg.stg_payments;

        CREATE OR REPLACE TABLE analytics.fact_returns AS
        SELECT
          return_id,
          order_id,
          try_cast(strftime(return_date, '%Y%m%d') AS BIGINT) AS date_key,
          reason,
          refund_amount,
          status
        FROM stg.stg_returns;

        CREATE OR REPLACE TABLE analytics.fact_shipments AS
        SELECT
          shipment_id,
          order_id,
          carrier,
          try_cast(strftime(ship_date, '%Y%m%d') AS BIGINT) AS ship_date_key,
          shipping_cost,
          CASE
            WHEN delivered_date IS NOT NULL AND delivered_date <= estimated_delivery THEN TRUE
            ELSE FALSE
          END AS is_on_time
        FROM stg.stg_shipments;

        CREATE OR REPLACE TABLE analytics.fact_pipeline AS
        SELECT
          opportunity_id,
          account_id,
          stage,
          amount,
          probability,
          try_cast(strftime(close_date, '%Y%m%d') AS BIGINT) AS close_date_key
        FROM stg.stg_sf_opportunities;
        """,
    )

    # 04_views: executive views for Tableau
    run_sql(
        con,
        """
        CREATE OR REPLACE VIEW analytics.v_exec_revenue_daily AS
        SELECT
          d.date,
          SUM(o.order_total) AS gross_revenue,
          SUM(o.discount) AS discounts,
          COUNT(DISTINCT o.order_id) AS orders,
          SUM(o.order_total) / NULLIF(COUNT(DISTINCT o.order_id),0) AS aov
        FROM analytics.fact_orders o
        JOIN analytics.dim_date d ON o.date_key = d.date_key
        WHERE o.status <> 'Cancelled'
        GROUP BY 1
        ORDER BY 1;

        CREATE OR REPLACE VIEW analytics.v_exec_margin_daily AS
        SELECT
          d.date,
          SUM(i.line_total) AS sales,
          SUM(i.extended_cost) AS cogs,
          SUM(i.gross_margin) AS gross_margin,
          SUM(i.gross_margin) / NULLIF(SUM(i.line_total),0) AS gross_margin_pct
        FROM analytics.fact_order_items i
        JOIN analytics.fact_orders o ON i.order_id = o.order_id
        JOIN analytics.dim_date d ON o.date_key = d.date_key
        WHERE o.status <> 'Cancelled'
        GROUP BY 1
        ORDER BY 1;

        CREATE OR REPLACE VIEW analytics.v_exec_pipeline AS
        SELECT
          stage,
          COUNT(*) AS opp_count,
          SUM(amount) AS pipeline_amount,
          AVG(probability) AS avg_probability
        FROM analytics.fact_pipeline
        GROUP BY 1
        ORDER BY pipeline_amount DESC;

        CREATE OR REPLACE VIEW analytics.v_exec_fulfillment AS
        SELECT
          carrier,
          COUNT(*) AS shipments,
          AVG(CASE WHEN is_on_time THEN 1 ELSE 0 END) AS on_time_rate
        FROM analytics.fact_shipments
        GROUP BY 1
        ORDER BY shipments DESC;
        """,
    )

    # 99_checks: validation prints
    print("\n=== VALIDATION ===")
    print(con.execute("SELECT COUNT(*) AS orders FROM analytics.fact_orders").fetchdf())
    print(con.execute("SELECT COUNT(*) AS items FROM analytics.fact_order_items").fetchdf())
    print(con.execute("SELECT * FROM analytics.v_exec_pipeline LIMIT 5").fetchdf())
    print("\nWarehouse built at:", DUCKDB_PATH)

    con.close()


if __name__ == "__main__":
    main()
