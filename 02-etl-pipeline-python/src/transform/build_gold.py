import pandas as pd

def build_gold(s: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    g = {}

    # --- Dimensions (clean subset for BI) ---
    g["dim_geo"] = s["dim_geo"][["geo_id","country","state","city","postal_code","region"]].copy()
    g["dim_product"] = s["products"][["product_id","sku","product_name","category","unit_cost","list_price","is_active"]].copy()
    g["dim_customer"] = s["customers"][["customer_id","email","first_name","last_name","geo_id","segment","created_at"]].copy()
    g["dim_account"] = s["sf_accounts"][["account_id","account_name","industry","tier","employees","geo_id","created_at"]].copy()
    g["dim_warehouse"] = s["warehouses"][["warehouse_id","warehouse_name","geo_id","capacity_units"]].copy()

    # --- Fact: Order header (Revenue lens) ---
    orders = s["orders"].copy()
    orders["date_key"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y%m%d").astype(int)
    g["fact_orders"] = orders[[
        "order_id","customer_id","warehouse_id","date_key","channel","status",
        "subtotal","discount","tax","shipping_fee","order_total"
    ]].copy()

    # --- Fact: Order items (Margin lens) ---
    items = s["order_items"].copy()
    prod = s["products"][["product_id","unit_cost"]].copy()
    items = items.merge(prod, on="product_id", how="left")
    items["extended_cost"] = items["quantity"] * items["unit_cost"]
    items["gross_margin"] = items["line_total"] - items["extended_cost"]
    g["fact_order_items"] = items[[
        "order_id","product_id","quantity","unit_price","line_total","unit_cost","extended_cost","gross_margin"
    ]].copy()

    # --- Fact: Payments (Cash lens) ---
    pay = s["payments"].copy()
    pay["date_key"] = pd.to_datetime(pay["payment_date"]).dt.strftime("%Y%m%d").astype(int)
    g["fact_payments"] = pay[["payment_id","order_id","date_key","method","amount","status"]].copy()

    # --- Fact: Returns (Refund lens) ---
    ret = s["returns"].copy()
    if len(ret) > 0:
        ret["date_key"] = pd.to_datetime(ret["return_date"]).dt.strftime("%Y%m%d").astype(int)
        g["fact_returns"] = ret[["return_id","order_id","date_key","reason","refund_amount","status"]].copy()
    else:
        g["fact_returns"] = ret

    # --- Fact: Shipments (OTIF proxy) ---
    shp = s["shipments"].copy()
    shp["ship_date_key"] = pd.to_datetime(shp["ship_date"]).dt.strftime("%Y%m%d").astype(int)
    shp["delivered_date_dt"] = pd.to_datetime(shp["delivered_date"], errors="coerce")
    shp["estimated_delivery_dt"] = pd.to_datetime(shp["estimated_delivery"], errors="coerce")
    shp["is_on_time"] = (shp["delivered_date_dt"].notna()) & (shp["delivered_date_dt"] <= shp["estimated_delivery_dt"])
    g["fact_shipments"] = shp[[
        "shipment_id","order_id","carrier","ship_date_key","shipping_cost","is_on_time"
    ]].copy()

    # --- Fact: Support (SLA) ---
    cases = s["support_cases"].copy()
    cases["created_date_key"] = pd.to_datetime(cases["created_at"]).dt.strftime("%Y%m%d").astype(int)
    # SLA met: first response within sla_hours
    fr_hours = (pd.to_datetime(cases["first_response_at"]) - pd.to_datetime(cases["created_at"])).dt.total_seconds() / 3600
    cases["sla_met"] = fr_hours <= cases["sla_hours"]
    g["fact_support_cases"] = cases[[
        "case_id","customer_id","created_date_key","case_type","priority","status","sla_hours","sla_met","csat_score"
    ]].copy()

    # --- Fact: Pipeline (Salesforce opps) ---
    opp = s["sf_opportunities"].copy()
    opp["close_date_key"] = pd.to_datetime(opp["close_date"]).astype("datetime64[ns]").dt.strftime("%Y%m%d").astype(int)
    g["fact_pipeline"] = opp[[
        "opportunity_id","account_id","stage","amount","probability","close_date_key"
    ]].copy()

    return g