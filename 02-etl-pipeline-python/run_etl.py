import os
from pathlib import Path
import pandas as pd
from rich import print

from src.extract.read_sources import read_all_sources
from src.transform.clean_silver import build_silver
from src.transform.build_gold import build_gold
from src.quality.checks import run_quality_checks, write_quality_report
from src.load.writer import write_parquet_tables, write_bronze_copies

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = REPO_ROOT / "data_out"

OUT_DIR = Path(__file__).resolve().parent / "outputs"
BRONZE_DIR = OUT_DIR / "bronze"
SILVER_DIR = OUT_DIR / "silver"
GOLD_DIR = OUT_DIR / "gold"

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("[bold cyan]OmniEdge Professionals ETL starting...[/bold cyan]")
    print(f"Input dir: {INPUT_DIR}")

    # 1) Extract
    raw = read_all_sources(INPUT_DIR)

    # 2) Bronze (copy raw files for auditability)
    write_bronze_copies(INPUT_DIR, BRONZE_DIR)

    # 3) Silver (clean/typed/deduped)
    silver = build_silver(raw)

    # 4) Data Quality (Silver-level gates)
    dq_results = run_quality_checks(silver)
    write_quality_report(dq_results, REPORTS_DIR / "data_quality_report.csv")

    # Fail-fast rule (Director-level): any CRITICAL failure stops pipeline
    critical_fails = dq_results[(dq_results["severity"] == "CRITICAL") & (dq_results["passed"] == False)]
    if len(critical_fails) > 0:
        print("[bold red]CRITICAL quality checks failed. Fix before proceeding.[/bold red]")
        print(critical_fails[["check", "detail"]].to_string(index=False))
        raise SystemExit(1)

    # 5) Gold (exec-ready facts/dims)
    gold = build_gold(silver)

    # 6) Write outputs
    write_parquet_tables(silver, SILVER_DIR)
    write_parquet_tables(gold, GOLD_DIR)

    print("[bold green]ETL complete.[/bold green]")
    print(f"Silver: {SILVER_DIR}")
    print(f"Gold:   {GOLD_DIR}")
    print(f"Report: {REPORTS_DIR / 'data_quality_report.csv'}")

if __name__ == "__main__":
    main()
