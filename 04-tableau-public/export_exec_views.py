from pathlib import Path
import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "03-warehouse-duckdb" / "omniedge_revops.duckdb"
OUT_DIR = Path(__file__).resolve().parent / "exports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXPORTS = {
    "exec_revenue_daily.csv": "SELECT * FROM analytics.v_exec_revenue_daily",
    "exec_margin_daily.csv": "SELECT * FROM analytics.v_exec_margin_daily",
    "exec_pipeline.csv": "SELECT * FROM analytics.v_exec_pipeline",
    "exec_fulfillment.csv": "SELECT * FROM analytics.v_exec_fulfillment",
}

def main():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    for filename, query in EXPORTS.items():
        df = con.execute(query).fetchdf()
        df.to_csv(OUT_DIR / filename, index=False)
        print(f"Exported: {filename} ({len(df)} rows)")
    con.close()
    print("Done. Files located at:", OUT_DIR)

if __name__ == "__main__":
    main()
