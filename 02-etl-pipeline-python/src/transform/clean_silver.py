import pandas as pd

def _to_datetime(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def build_silver(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    s = {}

    # Dimensions
    s["dim_geo"] = raw["dim_geo"].drop_duplicates(subset=["geo_id"]).copy()
    s["dim_dates"] = raw["dim_dates"].drop_duplicates(subset=["date_key"]).copy()

    # Products
    prod = raw["products"].copy()
    prod = _to_datetime(prod, ["created_at", "updated_at"])
    prod["unit_cost"] = pd.to_numeric(prod["unit_cost"], errors="coerce")
    prod["list_price"] = pd.to_numeric(prod["list_price"], errors="coerce")
    s["products"] = prod.drop_duplicates(subset=["product_id"])

    # Warehouses
    wh = raw["warehouses"].copy()
    wh = _to_datetime(wh, ["created_at", "updated_at"])
    s["warehouses"] = wh.drop_duplicates(subset=["warehouse_id"])

    # Customers
    cust = raw["customers"].copy()
    cust = _to_datetime(cust, ["created_at", "updated_at"])
    s["customers"] = cust.drop_duplicates(subset=["customer_id"])

    # Orders
    orders = raw["orders"].copy()
    orders = _to_datetime(orders, ["created_at", "updated_at"])
    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce").dt.date
    for c in ["subtotal","discount","tax","shipping_fee","order_total"]:
        orders[c] = pd.to_numeric(orders[c], errors="coerce")
    s["orders"] = orders.drop_duplicates(subset=["order_id"])

    # Order items
    oi = raw["order_items"].copy()
    for c in ["quantity","unit_price","line_total"]:
        oi[c] = pd.to_numeric(oi[c], errors="coerce")
    s["order_items"] = oi.drop_duplicates(subset=["order_id","product_id","unit_price","quantity"])

    # Payments
    pay = raw["payments"].copy()
    pay["payment_date"] = pd.to_datetime(pay["payment_date"], errors="coerce").dt.date
    pay["amount"] = pd.to_numeric(pay["amount"], errors="coerce")
    s["payments"] = pay.drop_duplicates(subset=["payment_id"])

    # Returns
    ret = raw["returns"].copy()
    if len(ret) > 0:
        ret["return_date"] = pd.to_datetime(ret["return_date"], errors="coerce").dt.date
        ret["refund_amount"] = pd.to_numeric(ret["refund_amount"], errors="coerce")
        s["returns"] = ret.drop_duplicates(subset=["return_id"])
    else:
        s["returns"] = ret

    # Shipments + events
    shp = raw["shipments"].copy()
    for c in ["ship_date","estimated_delivery","delivered_date","created_at","updated_at"]:
        if c in shp.columns:
            shp[c] = pd.to_datetime(shp[c], errors="coerce")
    shp["shipping_cost"] = pd.to_numeric(shp["shipping_cost"], errors="coerce")
    s["shipments"] = shp.drop_duplicates(subset=["shipment_id"])

    se = raw["shipment_events"].copy()
    se["event_ts"] = pd.to_datetime(se["event_ts"], errors="coerce")
    s["shipment_events"] = se.drop_duplicates(subset=["shipment_id","event_ts","event_type"])

    # Inventory
    invs = raw["inventory_snapshots"].copy()
    invs["snapshot_date"] = pd.to_datetime(invs["snapshot_date"], errors="coerce").dt.date
    for c in ["on_hand_qty","allocated_qty","reorder_point"]:
        invs[c] = pd.to_numeric(invs[c], errors="coerce")
    s["inventory_snapshots"] = invs.drop_duplicates(subset=["snapshot_date","warehouse_id","product_id"])

    invm = raw["inventory_movements"].copy()
    invm["movement_ts"] = pd.to_datetime(invm["movement_ts"], errors="coerce")
    invm["qty_delta"] = pd.to_numeric(invm["qty_delta"], errors="coerce")
    s["inventory_movements"] = invm.drop_duplicates(subset=["movement_id"])

    # Support cases
    cases = raw["support_cases"].copy()
    cases = _to_datetime(cases, ["created_at","first_response_at","resolved_at"])
    cases["sla_hours"] = pd.to_numeric(cases["sla_hours"], errors="coerce")
    s["support_cases"] = cases.drop_duplicates(subset=["case_id"])

    # Salesforce objects
    acct = raw["sf_accounts"].copy()
    acct = _to_datetime(acct, ["created_at","updated_at"])
    s["sf_accounts"] = acct.drop_duplicates(subset=["account_id"])

    con = raw["sf_contacts"].copy()
    con = _to_datetime(con, ["created_at","updated_at"])
    s["sf_contacts"] = con.drop_duplicates(subset=["contact_id"])

    leads = raw["sf_leads"].copy()
    leads = _to_datetime(leads, ["created_at","updated_at"])
    s["sf_leads"] = leads.drop_duplicates(subset=["lead_id"])

    opp = raw["sf_opportunities"].copy()
    opp = _to_datetime(opp, ["created_at","updated_at"])
    opp["close_date"] = pd.to_datetime(opp["close_date"], errors="coerce").dt.date
    opp["amount"] = pd.to_numeric(opp["amount"], errors="coerce")
    opp["probability"] = pd.to_numeric(opp["probability"], errors="coerce")
    s["sf_opportunities"] = opp.drop_duplicates(subset=["opportunity_id"])

    oli = raw["sf_opportunity_line_items"].copy()
    for c in ["quantity","unit_price","line_total"]:
        oli[c] = pd.to_numeric(oli[c], errors="coerce")
    s["sf_opportunity_line_items"] = oli.drop_duplicates(subset=["opportunity_id","product_id","unit_price","quantity"])

    act = raw["sf_activities"].copy()
    act["activity_ts"] = pd.to_datetime(act["activity_ts"], errors="coerce")
    s["sf_activities"] = act.drop_duplicates(subset=["activity_id"])

    return s