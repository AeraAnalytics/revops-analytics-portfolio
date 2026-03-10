from pathlib import Path
import sys
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import DUCKDB_PATH, PROCESSED_DIR

def main():
    con = duckdb.connect(str(DUCKDB_PATH))

    monthly_revenue = con.execute("""
        SELECT
            date_trunc('month', order_date) AS month,
            SUM(order_total) AS total_revenue,
            COUNT(DISTINCT order_id) AS total_orders,
            SUM(order_total) / COUNT(DISTINCT order_id) AS aov
        FROM analytics.fact_orders
        WHERE status <> 'Cancelled'
          AND order_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).fetchdf()

    monthly_margin = con.execute("""
        SELECT
            date_trunc('month', o.order_date) AS month,
            SUM(i.line_total) AS sales,
            SUM(i.extended_cost) AS cogs,
            SUM(i.gross_margin) AS gross_margin,
            SUM(i.gross_margin) / NULLIF(SUM(i.line_total), 0) AS gross_margin_pct
        FROM analytics.fact_order_items i
        JOIN analytics.fact_orders o
          ON i.order_id = o.order_id
        WHERE o.status <> 'Cancelled'
          AND o.order_date IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).fetchdf()

    pipeline_stage = con.execute("""
        SELECT
            stage,
            COUNT(*) AS opp_count,
            SUM(amount) AS pipeline_amount,
            AVG(probability) AS avg_probability
        FROM analytics.fact_pipeline
        GROUP BY 1
        ORDER BY pipeline_amount DESC
    """).fetchdf()

    monthly_revenue.to_csv(PROCESSED_DIR / "monthly_revenue.csv", index=False)
    monthly_margin.to_csv(PROCESSED_DIR / "monthly_margin.csv", index=False)
    pipeline_stage.to_csv(PROCESSED_DIR / "pipeline_stage.csv", index=False)

    print("KPI outputs created:")
    print("- monthly_revenue.csv")
    print("- monthly_margin.csv")
    print("- pipeline_stage.csv")
    print()
    print("Preview: monthly_revenue")
    print(monthly_revenue.head())
    print()
    print("Preview: monthly_margin")
    print(monthly_margin.head())
    print()
    print("Preview: pipeline_stage")
    print(pipeline_stage.head())

    con.close()

if __name__ == "__main__":
    main()

