import pandas as pd

def _result(check, severity, passed, detail):
    return {"check": check, "severity": severity, "passed": bool(passed), "detail": str(detail)}

def run_quality_checks(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    results = []

    orders = silver["orders"]
    customers = silver["customers"]
    order_items = silver["order_items"]
    products = silver["products"]

    # CRITICAL: primary key uniqueness
    results.append(_result("orders.order_id unique", "CRITICAL",
                          orders["order_id"].is_unique,
                          f"dupes={orders.duplicated('order_id').sum()}"))

    # CRITICAL: referential integrity
    missing_customers = ~orders["customer_id"].isin(customers["customer_id"])
    results.append(_result("orders.customer_id exists in customers", "CRITICAL",
                          missing_customers.sum() == 0,
                          f"missing={missing_customers.sum()}"))

    missing_orders_in_items = ~order_items["order_id"].isin(orders["order_id"])
    results.append(_result("order_items.order_id exists in orders", "CRITICAL",
                          missing_orders_in_items.sum() == 0,
                          f"missing={missing_orders_in_items.sum()}"))

    missing_products_in_items = ~order_items["product_id"].isin(products["product_id"])
    results.append(_result("order_items.product_id exists in products", "CRITICAL",
                          missing_products_in_items.sum() == 0,
                          f"missing={missing_products_in_items.sum()}"))

    # HIGH: numeric sanity
    results.append(_result("orders.order_total non-negative", "HIGH",
                          (orders["order_total"] >= 0).all(),
                          f"negatives={(orders['order_total'] < 0).sum()}"))

    # HIGH: order_date present
    results.append(_result("orders.order_date not null", "HIGH",
                          orders["order_date"].notna().all(),
                          f"nulls={orders['order_date'].isna().sum()}"))

    # MEDIUM: shipments link to orders (only if table exists)
    if "shipments" in silver:
        shp = silver["shipments"]
        missing_shp_orders = ~shp["order_id"].isin(orders["order_id"])
        results.append(_result("shipments.order_id exists in orders", "MEDIUM",
                              missing_shp_orders.sum() == 0,
                              f"missing={missing_shp_orders.sum()}"))

    return pd.DataFrame(results)

def write_quality_report(df: pd.DataFrame, path):
    df.to_csv(path, index=False)