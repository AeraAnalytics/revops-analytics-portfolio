from pathlib import Path
import sys
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import RAW_DIR, DUCKDB_PATH

def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / name)

def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for c in ["subtotal", "discount", "tax", "shipping_fee", "order_total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.drop_duplicates(subset=["order_id"])

def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["quantity", "unit_price", "line_total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["unit_cost", "list_price"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.drop_duplicates(subset=["product_id"])

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    return df.drop_duplicates(subset=["customer_id"])

def clean_shipments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["ship_date", "estimated_delivery", "delivered_date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["shipping_cost"] = pd.to_numeric(df["shipping_cost"], errors="coerce")
    return df

def clean_returns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["return_date"] = pd.to_datetime(df["return_date"], errors="coerce")
    df["refund_amount"] = pd.to_numeric(df["refund_amount"], errors="coerce")
    return df

def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df

def clean_opps(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["probability"] = pd.to_numeric(df["probability"], errors="coerce")
    return df

def main():
    orders = clean_orders(read_csv("orders.csv"))
    items = clean_order_items(read_csv("order_items.csv"))
    products = clean_products(read_csv("products.csv"))
    customers = clean_customers(read_csv("customers.csv"))
    shipments = clean_shipments(read_csv("shipments.csv"))
    returns = clean_returns(read_csv("returns.csv"))
    payments = clean_payments(read_csv("payments.csv"))
    opps = clean_opps(read_csv("sf_opportunities.csv"))
    accounts = read_csv("sf_accounts.csv")
    dates = read_csv("dim_dates.csv")
    geo = read_csv("dim_geo.csv")

    con = duckdb.connect(str(DUCKDB_PATH))

    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    con.execute("CREATE SCHEMA IF NOT EXISTS stg;")
    con.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

    con.register("orders_df", orders)
    con.register("items_df", items)
    con.register("products_df", products)
    con.register("customers_df", customers)
    con.register("shipments_df", shipments)
    con.register("returns_df", returns)
    con.register("payments_df", payments)
    con.register("opps_df", opps)
    con.register("accounts_df", accounts)
    con.register("dates_df", dates)
    con.register("geo_df", geo)

    con.execute("CREATE OR REPLACE TABLE stg.orders AS SELECT * FROM orders_df")
    con.execute("CREATE OR REPLACE TABLE stg.order_items AS SELECT * FROM items_df")
    con.execute("CREATE OR REPLACE TABLE stg.products AS SELECT * FROM products_df")
    con.execute("CREATE OR REPLACE TABLE stg.customers AS SELECT * FROM customers_df")
    con.execute("CREATE OR REPLACE TABLE stg.shipments AS SELECT * FROM shipments_df")
    con.execute("CREATE OR REPLACE TABLE stg.returns AS SELECT * FROM returns_df")
    con.execute("CREATE OR REPLACE TABLE stg.payments AS SELECT * FROM payments_df")
    con.execute("CREATE OR REPLACE TABLE stg.sf_opportunities AS SELECT * FROM opps_df")
    con.execute("CREATE OR REPLACE TABLE stg.sf_accounts AS SELECT * FROM accounts_df")
    con.execute("CREATE OR REPLACE TABLE analytics.dim_dates AS SELECT * FROM dates_df")
    con.execute("CREATE OR REPLACE TABLE analytics.dim_geo AS SELECT * FROM geo_df")

    con.execute("""
        CREATE OR REPLACE TABLE analytics.fact_orders AS
        SELECT
            order_id,
            customer_id,
            warehouse_id,
            order_date,
            channel,
            status,
            subtotal,
            discount,
            tax,
            shipping_fee,
            order_total
        FROM stg.orders
    """)

    con.execute("""
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
        FROM stg.order_items i
        LEFT JOIN stg.products p
            ON i.product_id = p.product_id
    """)

    con.execute("""
        CREATE OR REPLACE TABLE analytics.fact_pipeline AS
        SELECT
            opportunity_id,
            account_id,
            stage,
            amount,
            probability,
            close_date
        FROM stg.sf_opportunities
    """)

    print("DuckDB warehouse load complete.")
    print(con.execute("SELECT COUNT(*) AS orders FROM analytics.fact_orders").fetchdf())
    print(con.execute("SELECT COUNT(*) AS order_items FROM analytics.fact_order_items").fetchdf())
    print(con.execute("SELECT COUNT(*) AS opps FROM analytics.fact_pipeline").fetchdf())

    con.close()

if __name__ == "__main__":
    main()
