from pathlib import Path
import shutil
import pandas as pd

def write_bronze_copies(input_dir: Path, bronze_dir: Path):
    bronze_dir.mkdir(parents=True, exist_ok=True)
    for f in input_dir.glob("*.csv"):
        shutil.copy2(f, bronze_dir / f.name)

def write_parquet_tables(tables: dict[str, pd.DataFrame], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(out_dir / f"{name}.parquet", index=False)