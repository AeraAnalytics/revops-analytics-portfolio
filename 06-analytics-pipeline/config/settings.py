from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BASE_DIR.parents[0]

SOURCE_DIR = REPO_ROOT / "data_out"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
EXPORT_DIR = BASE_DIR / "data" / "exports"
LOG_DIR = BASE_DIR / "logs"

DUCKDB_PATH = REPO_ROOT / "03-warehouse-duckdb" / "omniedge_revops.duckdb"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_FILES = [
    "orders.csv",
    "order_items.csv",
    "payments.csv",
    "returns.csv",
    "shipments.csv",
    "customers.csv",
    "products.csv",
    "sf_accounts.csv",
    "sf_opportunities.csv",
    "support_cases.csv",
    "dim_dates.csv",
    "dim_geo.csv",
]
