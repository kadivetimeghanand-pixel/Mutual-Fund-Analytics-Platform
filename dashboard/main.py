"""
dashboard/main.py — Day 1 Pipeline Entry Point.

Orchestrates:
  1. Directory bootstrap
  2. Dataset ingestion & profiling
  3. AMFI code validation
  4. Live NAV fetch from api.mfapi.in
  5. Execution summary
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from config import (
    AMFI_VALIDATION_MD,
    AMFI_VALIDATION_REPORT,
    DATA_PROFILE_REPORT,
    DAY1_SUMMARY_MD,
    LIVE_NAV_SCHEMES,
    RAW_DIR,
)
from data_ingestion import run_ingestion
from live_nav_fetch import fetch_all_live_nav, print_nav_fetch_summary
from utils import ensure_directories, print_separator, setup_logger
from validation import run_amfi_validation


# ── Execution Summary ─────────────────────────────────────────────────────────

def print_execution_summary(
    datasets_loaded: int,
    nav_fetched: int,
    validation_issues: int,
    elapsed: float,
) -> None:
    print_separator("DAY 1 PIPELINE — EXECUTION SUMMARY")
    print(f"  {'Datasets loaded':<35}: {datasets_loaded}")
    print(f"  {'Live NAV schemes fetched':<35}: {nav_fetched}/{len(LIVE_NAV_SCHEMES)}")
    print(f"  {'AMFI validation issues':<35}: {validation_issues}")
    print(f"  {'Total execution time':<35}: {elapsed:.2f}s")
    print()
    print("  Outputs generated:")
    outputs = [
        DATA_PROFILE_REPORT,
        DAY1_SUMMARY_MD,
        AMFI_VALIDATION_REPORT,
        AMFI_VALIDATION_MD,
    ]
    for path in outputs:
        status = "✓" if path.exists() else "✗"
        print(f"    [{status}] {path}")

    nav_files = list(RAW_DIR.glob("nav_*.csv"))
    for f in nav_files:
        print(f"    [✓] {f}")

    print_separator()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    pipeline_start = time.perf_counter()

    # 1. Setup
    setup_logger()
    ensure_directories()

    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║   MutualFundAnalytics — Day 1 Pipeline       ║")
    logger.info("╚══════════════════════════════════════════════╝")

    # 2. Data Ingestion & Profiling
    datasets = run_ingestion()

    # 3. AMFI Validation
    validation_df = run_amfi_validation(
        df_master=datasets.get("fund_master"),
        df_nav=datasets.get("nav_history"),
    )
    validation_issues = len(validation_df) if validation_df is not None else 0

    # 4. Live NAV Fetch
    nav_results = fetch_all_live_nav()
    print_nav_fetch_summary(nav_results)

    # 5. Summary
    elapsed = time.perf_counter() - pipeline_start
    print_execution_summary(
        datasets_loaded=len(datasets),
        nav_fetched=len(nav_results),
        validation_issues=validation_issues,
        elapsed=elapsed,
    )

    logger.info("Day 1 pipeline completed in {:.2f}s", elapsed)


if __name__ == "__main__":
    main()
