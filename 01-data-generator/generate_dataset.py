# generate_dataset.py
"""
Director-level Synthetic RevOps + Commerce + Supply Chain dataset generator.

Outputs CSVs to ../data_out/ for use in:
- Python ETL pipelines
- Snowflake loading & medallion modeling
- Tableau executive dashboards
- Salesforce-style CRM analytics

Usage:
  python generate_dataset.py
"""
import os
import random
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data_out")
os.makedirs(OUT_DIR, exist_ok=True)

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))

def jitter_ts(d: date) -> datetime:
    return datetime(d.year, d.month, d.day) + timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )

def write(df: pd.DataFrame, name: str):
    path = os.path.join(OUT_DIR, name)
    df.to_csv(path, index=False)
    print(f"Wrote {path} ({len(df):,} rows)")

def main(
    n_accounts=1200,
    n_contacts=2200,
    n_leads=3000,
    n_opps=2400,
    n_products=600,
    n_customers=8000,
    n_orders=12000,
    start_date=date(2024, 1, 1),
    end_date=date(2026, 3, 1),
):
    # --- Reference: geo ---
    states = ["CO","CA","TX","FL","NY","IL","WA","GA","NC","AZ","VA","MA"]
    cities = ["Denver","Aurora","Miami","Tampa","Austin","Dallas","Seattle","Chicago","Atlanta","Charlotte","Phoenix","Boston","San Jose","San Diego","NYC"]
    geo = []
    for i in range(1, 800):
        st = random.choice(states)
        city = random.choice(cities)
        geo.append({
            "geo_id": f"GEO{i:04d}",
            "country": "US",
            "state": st,
            "city": city,
            "postal_code": fake.postcode(),
            "region": random.choice(["West","South","Midwest","Northeast"]),
        })
    dim_geo = pd.DataFrame(geo)
    write(dim_geo, "dim_geo.csv")

    # --- dim_dates ---
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dim_dates = pd.DataFrame({
        "date_key": dates.strftime("%Y%m%d").astype(int),
        "date": dates.date,
        "year": dates.year,
        "quarter": dates.quarter,
        "month": dates.month,
        "month_name": dates.strftime("%B"),
        "week": dates.isocalendar().week.astype(int),
        "day_of_week": dates.dayofweek + 1,
        "is_weekend": (dates.dayofweek >= 5),
    })
    write(dim_dates, "dim_dates.csv")

    # --- Products ---
    categories = ["Electronics","Home","Sports","Office","Apparel","Auto","Healthcare","Grocery"]
    products = []
    for i in range(1, n_products+1):
        cat = random.choice(categories)
        cost = round(random.uniform(5, 350), 2)
        price = round(cost * random.uniform(1.15, 1.85), 2)
        created_d = rand_date(start_date, end_date)
        products.append({
            "product_id": f"P{i:05d}",
            "sku": fake.bothify(text="??-#####").upper(),
            "product_name": f"{fake.word().title()} {fake.word().title()}",
            "category": cat,
            "unit_cost": cost,
            "list_price": price,
            "is_active": random.choice([True]*95 + [False]*5),
            "created_at": jitter_ts(created_d).isoformat(),
            "updated_at": jitter_ts(rand_date(created_d, end_date)).isoformat(),
        })
    df_products = pd.DataFrame(products)
    write(df_products, "products.csv")

    # --- Warehouses ---
    warehouses = []
    for i in range(1, 18):
        geo_id = dim_geo.sample(1).iloc[0]["geo_id"]
        created_d = rand_date(start_date, end_date)
        warehouses.append({
            "warehouse_id": f"W{i:03d}",
            "warehouse_name": f"DC-{i:02d}",
            "geo_id": geo_id,
            "capacity_units": random.randint(20000, 200000),
            "created_at": jitter_ts(created_d).isoformat(),
            "updated_at": jitter_ts(rand_date(created_d, end_date)).isoformat(),
        })
    df_wh = pd.DataFrame(warehouses)
    write(df_wh, "warehouses.csv")

    # --- Customers (B2C/B2B-buyers) ---
    customers = []
    for i in range(1, n_customers+1):
        geo_id = dim_geo.sample(1).iloc[0]["geo_id"]
        created = rand_date(start_date, end_date)
        customers.append({
            "customer_id": f"C{i:06d}",
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "geo_id": geo_id,
            "segment": random.choice(["Consumer","SMB","Mid-Market"]),
            "created_at": jitter_ts(created).isoformat(),
            "updated_at": jitter_ts(rand_date(created, end_date)).isoformat(),
            "is_deleted": random.choice([0]*995 + [1]*5),
        })
    df_customers = pd.DataFrame(customers)
    write(df_customers, "customers.csv")

    # --- Salesforce Accounts (B2B) ---
    industries = ["Logistics","Retail","Healthcare","Manufacturing","Energy","Government","FinTech","Telecom"]
    tiers = ["Tier 1","Tier 2","Tier 3"]
    accounts = []
    for i in range(1, n_accounts+1):
        geo_id = dim_geo.sample(1).iloc[0]["geo_id"]
        created = rand_date(start_date, end_date)
        accounts.append({
            "account_id": f"A{i:05d}",
            "account_name": fake.company(),
            "industry": random.choice(industries),
            "tier": random.choice(tiers),
            "employees": random.choice([random.randint(10,200), random.randint(200,2000), random.randint(2000,40000)]),
            "geo_id": geo_id,
            "created_at": jitter_ts(created).isoformat(),
            "updated_at": jitter_ts(rand_date(created, end_date)).isoformat(),
            "is_deleted": random.choice([0]*990 + [1]*10),
        })
    df_accounts = pd.DataFrame(accounts)
    write(df_accounts, "sf_accounts.csv")

    # --- Salesforce Contacts ---
    contacts = []
    for i in range(1, n_contacts+1):
        acct = df_accounts.sample(1).iloc[0]
        created = datetime.fromisoformat(acct["created_at"]).date()
        contacts.append({
            "contact_id": f"CT{i:06d}",
            "account_id": acct["account_id"],
            "email": fake.company_email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "title": random.choice(["Director","Manager","VP","Analyst","Coordinator","CFO","COO","SVP"]),
            "created_at": jitter_ts(rand_date(created, end_date)).isoformat(),
            "updated_at": jitter_ts(rand_date(created, end_date)).isoformat(),
        })
    df_contacts = pd.DataFrame(contacts)
    write(df_contacts, "sf_contacts.csv")

    # --- Salesforce Leads ---
    sources = ["Web","Referral","Event","Outbound","Partner","Inbound SDR"]
    statuses = ["New","Working","Nurture","Qualified","Disqualified"]
    leads = []
    for i in range(1, n_leads+1):
        geo_id = dim_geo.sample(1).iloc[0]["geo_id"]
        created = rand_date(start_date, end_date)
        st = random.choice(statuses)
        leads.append({
            "lead_id": f"L{i:06d}",
            "email": fake.email(),
            "company": fake.company(),
            "source": random.choice(sources),
            "status": st,
            "geo_id": geo_id,
            "created_at": jitter_ts(created).isoformat(),
            "updated_at": jitter_ts(rand_date(created, end_date)).isoformat(),
        })
    df_leads = pd.DataFrame(leads)
    write(df_leads, "sf_leads.csv")

    # --- Opportunities ---
    stages = ["Prospecting","Discovery","Solutioning","Negotiation","Closed Won","Closed Lost"]
    opps = []
    for i in range(1, n_opps+1):
        acct = df_accounts.sample(1).iloc[0]
        created = rand_date(start_date, end_date)
        stage = random.choices(stages, weights=[16,18,20,18,18,10], k=1)[0]
        base_amt = random.uniform(5000, 500000) * (1.2 if acct["tier"]=="Tier 1" else 1.0)
        close = rand_date(created, min(end_date, created + timedelta(days=random.randint(10, 160))))
        amt = round(base_amt if stage in ["Closed Won","Closed Lost"] else base_amt * random.uniform(0.6, 1.2), 2)
        opps.append({
            "opportunity_id": f"O{i:06d}",
            "account_id": acct["account_id"],
            "opportunity_name": f"{acct['account_name']} - {fake.bs().title()}",
            "stage": stage,
            "amount": amt,
            "probability": {"Prospecting":10,"Discovery":25,"Solutioning":45,"Negotiation":70,"Closed Won":100,"Closed Lost":0}[stage],
            "created_at": jitter_ts(created).isoformat(),
            "close_date": close.isoformat(),
            "updated_at": jitter_ts(rand_date(created, end_date)).isoformat(),
        })
    df_opps = pd.DataFrame(opps)
    write(df_opps, "sf_opportunities.csv")

    # --- Opportunity line items ---
    oli = []
    for _, opp in df_opps.iterrows():
        n_lines = random.randint(1, 6)
        picks = df_products.sample(n_lines)
        for _, p in picks.iterrows():
            qty = random.randint(1, 50)
            price = round(float(p["list_price"]) * random.uniform(0.85, 1.1), 2)
            oli.append({
                "opportunity_id": opp["opportunity_id"],
                "product_id": p["product_id"],
                "quantity": qty,
                "unit_price": price,
                "line_total": round(qty * price, 2),
            })
    df_oli = pd.DataFrame(oli)
    write(df_oli, "sf_opportunity_line_items.csv")

    # --- Activities ---
    act_types = ["Call","Email","Meeting","Task"]
    outcomes = ["Connected","Left VM","No Answer","Replied","Booked Meeting","Follow-up Needed"]
    activities = []
    for i in range(1, 25000):
        acct = df_accounts.sample(1).iloc[0]["account_id"]
        contact = df_contacts.sample(1).iloc[0]["contact_id"]
        d = rand_date(start_date, end_date)
        activities.append({
            "activity_id": f"ACT{i:06d}",
            "account_id": acct,
            "contact_id": contact,
            "activity_type": random.choice(act_types),
            "outcome": random.choice(outcomes),
            "activity_ts": jitter_ts(d).isoformat(),
            "owner_role": random.choice(["SDR","AE","CSM","AM"]),
        })
    write(pd.DataFrame(activities), "sf_activities.csv")

    # --- Orders / items / payments / returns / shipments ---
    carriers = ["UPS","FedEx","USPS","DHL","OnTrac","XPO"]
    channels = ["Web","Marketplace","Mobile","B2B Portal"]
    order_status = ["Placed","Packed","Shipped","Delivered","Cancelled"]
    pay_methods = ["Card","ACH","PayPal","Wire"]
    return_reasons = ["Damaged","Wrong Item","Late Delivery","Changed Mind","Defective"]

    orders = []
    items = []
    payments = []
    returns = []
    shipments = []
    ship_events = []

    for i in range(1, n_orders+1):
        cust = df_customers.sample(1).iloc[0]
        od = rand_date(start_date, end_date)
        status = random.choices(order_status, weights=[18,18,22,35,7], k=1)[0]
        channel = random.choice(channels)

        order_id = f"ORD{i:08d}"
        wh = df_wh.sample(1).iloc[0]
        carrier = random.choice(carriers)

        n_lines = random.randint(1, 7)
        picks = df_products.sample(n_lines)
        subtotal = 0.0

        for _, p in picks.iterrows():
            qty = random.randint(1, 6)
            unit_price = float(p["list_price"]) * random.uniform(0.85, 1.15)
            line_total = round(qty * unit_price, 2)
            subtotal += line_total
            items.append({
                "order_id": order_id,
                "product_id": p["product_id"],
                "quantity": qty,
                "unit_price": round(unit_price, 2),
                "line_total": line_total,
            })

        shipping_fee = round(random.uniform(0, 35), 2)
        discount = round(subtotal * random.choice([0,0,0.05,0.1,0.15]), 2)
        tax = round((subtotal - discount) * random.uniform(0.03, 0.09), 2)
        total = round(subtotal - discount + tax + shipping_fee, 2)

        orders.append({
            "order_id": order_id,
            "customer_id": cust["customer_id"],
            "order_date": od.isoformat(),
            "channel": channel,
            "status": status,
            "warehouse_id": wh["warehouse_id"],
            "subtotal": round(subtotal, 2),
            "discount": discount,
            "tax": tax,
            "shipping_fee": shipping_fee,
            "order_total": total,
            "created_at": jitter_ts(od).isoformat(),
            "updated_at": jitter_ts(rand_date(od, end_date)).isoformat(),
        })

        # payment
        if status != "Cancelled":
            payments.append({
                "payment_id": f"PAY{i:08d}",
                "order_id": order_id,
                "payment_date": (od + timedelta(days=random.randint(0, 2))).isoformat(),
                "method": random.choice(pay_methods),
                "amount": total,
                "status": random.choices(["Succeeded","Failed","Pending"], weights=[93,3,4], k=1)[0],
            })

        # shipment + events
        if status in ["Shipped","Delivered"]:
            ship_id = f"SHP{i:08d}"
            ship_date = od + timedelta(days=random.randint(1, 3))
            deliv_date = ship_date + timedelta(days=random.randint(1, 7))
            shipments.append({
                "shipment_id": ship_id,
                "order_id": order_id,
                "carrier": carrier,
                "ship_date": ship_date.isoformat(),
                "estimated_delivery": (ship_date + timedelta(days=random.randint(2, 6))).isoformat(),
                "delivered_date": deliv_date.isoformat() if status == "Delivered" else "",
                "shipping_cost": round(random.uniform(4, 40), 2),
                "created_at": jitter_ts(ship_date).isoformat(),
                "updated_at": jitter_ts(rand_date(ship_date, end_date)).isoformat(),
            })
            evs = ["Label Created","Picked Up","In Transit","Out For Delivery","Delivered"]
            for j, ev in enumerate(evs):
                ev_dt = datetime(ship_date.year, ship_date.month, ship_date.day) + timedelta(days=min(j, 5), hours=random.randint(0, 20))
                ship_events.append({
                    "shipment_id": ship_id,
                    "event_ts": ev_dt.isoformat(),
                    "event_type": ev,
                    "event_city": fake.city(),
                    "event_state": random.choice(states),
                })

        # returns (small rate)
        if status == "Delivered" and random.random() < 0.07:
            returns.append({
                "return_id": f"RET{i:08d}",
                "order_id": order_id,
                "return_date": (od + timedelta(days=random.randint(5, 25))).isoformat(),
                "reason": random.choice(return_reasons),
                "refund_amount": round(total * random.uniform(0.2, 1.0), 2),
                "status": random.choice(["Requested","Approved","Refunded","Denied"]),
            })

    write(pd.DataFrame(orders), "orders.csv")
    write(pd.DataFrame(items), "order_items.csv")
    write(pd.DataFrame(payments), "payments.csv")
    write(pd.DataFrame(returns), "returns.csv")
    write(pd.DataFrame(shipments), "shipments.csv")
    write(pd.DataFrame(ship_events), "shipment_events.csv")

    # --- Inventory snapshots + movements ---
    inv_snap = []
    # keep snapshots moderate for portfolio size
    for wh in df_wh["warehouse_id"].tolist():
        for _, p in df_products.sample(min(250, len(df_products))).iterrows():
            qty = random.randint(0, 800)
            inv_snap.append({
                "snapshot_date": rand_date(start_date, end_date).isoformat(),
                "warehouse_id": wh,
                "product_id": p["product_id"],
                "on_hand_qty": qty,
                "allocated_qty": random.randint(0, min(120, qty)) if qty > 0 else 0,
                "reorder_point": random.randint(10, 120),
            })
    write(pd.DataFrame(inv_snap), "inventory_snapshots.csv")

    # inventory movements (vectorized for speed)
    mov_types = np.array(["RECEIPT","SHIP","ADJUSTMENT","TRANSFER_IN","TRANSFER_OUT"])
    wh_ids = df_wh["warehouse_id"].to_numpy()
    prod_ids = df_products["product_id"].to_numpy()

    n_mov = 8000
    wh_pick = np.random.choice(wh_ids, size=n_mov, replace=True)
    prod_pick = np.random.choice(prod_ids, size=n_mov, replace=True)
    mt_pick = np.random.choice(mov_types, size=n_mov, replace=True)

    qty_mag = np.random.randint(1, 50, size=n_mov)
    sign = np.where(np.isin(mt_pick, ["RECEIPT","TRANSFER_IN","ADJUSTMENT"]), 1, -1)
    qty_delta = qty_mag * sign

    # random timestamps across date range
    start_ts = np.datetime64(start_date)
    end_ts = np.datetime64(end_date + timedelta(days=1))
    rand_days = np.random.randint(0, int((end_ts - start_ts).astype("timedelta64[D]")/np.timedelta64(1, "D")), size=n_mov)
    rand_secs = np.random.randint(0, 86400, size=n_mov)
    ts = (start_ts + rand_days.astype("timedelta64[D]")) + rand_secs.astype("timedelta64[s]")

    inv_mov = pd.DataFrame({
        "movement_id": [f"IM{i:08d}" for i in range(1, n_mov+1)],
        "movement_ts": ts.astype("datetime64[s]").astype(str),
        "warehouse_id": wh_pick,
        "product_id": prod_pick,
        "movement_type": mt_pick,
        "qty_delta": qty_delta,
        "reference_id": [fake.uuid4() for _ in range(n_mov)],
    })
    write(inv_mov, "inventory_movements.csv")

    # --- Support cases ---
    customer_ids = df_customers['customer_id'].tolist()
    case_types = ["Delivery Issue","Payment Issue","Return Request","Product Defect","Account/Login","General Question"]
    priorities = ["Low","Medium","High","Critical"]
    cases = []
    for i in range(1, 6000):
        cust_id = random.choice(customer_ids)
        created = rand_date(start_date, end_date)
        pr = random.choices(priorities, weights=[35,45,16,4], k=1)[0]
        sla_hrs = {"Low":72,"Medium":48,"High":24,"Critical":6}[pr]
        first_response = created + timedelta(days=random.randint(0, 3))
        resolved = created + timedelta(days=random.randint(0, 12))
        cases.append({
            "case_id": f"CASE{i:07d}",
            "customer_id": cust_id,
            "case_type": random.choice(case_types),
            "priority": pr,
            "status": random.choices(["New","Open","Pending","Resolved","Closed"], weights=[8,22,10,40,20], k=1)[0],
            "created_at": jitter_ts(created).isoformat(),
            "first_response_at": jitter_ts(first_response).isoformat(),
            "resolved_at": jitter_ts(resolved).isoformat(),
            "sla_hours": sla_hrs,
            "csat_score": random.choice([1,2,3,4,5,""]),
        })
    write(pd.DataFrame(cases), "support_cases.csv")

if __name__ == "__main__":
    main()
