from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import PROCESSED_DIR, EXPORT_DIR

FILES = [
    "monthly_revenue.csv",
    "monthly_margin.csv",
    "pipeline_stage.csv",
]

def main():
    for file_name in FILES:
        src = PROCESSED_DIR / file_name
        dst = EXPORT_DIR / file_name

        if not src.exists():
            print(f"Missing processed file: {src}")
            continue

        df = pd.read_csv(src)
        df.to_csv(dst, index=False)
        print(f"Exported {file_name} -> {dst}")

    print("\nTableau export step complete.")
    print(f"Export folder: {EXPORT_DIR}")

if __name__ == "__main__":
    main()
