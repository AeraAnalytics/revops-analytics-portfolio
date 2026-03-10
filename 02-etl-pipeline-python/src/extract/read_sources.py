from pathlib import Path
import pandas as pd

EXPECTED_FILES = [
    "dim_geo.csv",
    "dim_dates.csv",
    "products.csv",
    "warehouses.csv",
    "customers.csv",
    "orders.csv",
    "order_items.csv",
    "payments.csv",
    "returns.csv",
    "shipments.csv",
    "shipment_events.csv",
    "inventory_snapshots.csv",
    "inventory_movements.csv",
    "support_cases.csv",
    "sf_accounts.csv",
    "sf_contacts.csv",
    "sf_leads.csv",
    "sf_opportunities.csv",
    "sf_opportunity_line_items.csv",
    "sf_activities.csv",
]

def read_all_sources(input_dir: Path) -> dict[str, pd.DataFrame]:
    data = {}
    for fn in EXPECTED_FILES:
        path = input_dir / fn
        if not path.exists():
            raise FileNotFoundError(f"Missing required input file: {path}")
        data[fn.replace(".csv", "")] = pd.read_csv(path)
    return data