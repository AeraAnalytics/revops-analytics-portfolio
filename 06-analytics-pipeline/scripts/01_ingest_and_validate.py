from pathlib import Path
import sys
import shutil
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from config.settings import SOURCE_DIR, RAW_DIR, LOG_DIR, SOURCE_FILES

def main():
    validation_rows = []

    for filename in SOURCE_FILES:
        src = SOURCE_DIR / filename
        dst = RAW_DIR / filename

        if not src.exists():
            validation_rows.append({
                "file_name": filename,
                "status": "MISSING",
                "row_count": None,
                "column_count": None,
                "duplicate_rows": None,
                "notes": "Source file not found"
            })
            continue

        shutil.copy2(src, dst)
        df = pd.read_csv(dst)

        validation_rows.append({
            "file_name": filename,
            "status": "LOADED",
            "row_count": len(df),
            "column_count": len(df.columns),
            "duplicate_rows": int(df.duplicated().sum()),
            "notes": "Loaded successfully"
        })

    results = pd.DataFrame(validation_rows)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = LOG_DIR / f"validation_report_{ts}.csv"
    results.to_csv(out_path, index=False)

    print("Validation complete.")
    print(results)
    print(f"Saved report to: {out_path}")

if __name__ == "__main__":
    main()
