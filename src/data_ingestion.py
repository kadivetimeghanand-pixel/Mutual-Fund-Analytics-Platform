"""
data_ingestion.py — Load, profile, and report on all raw datasets.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger
from tqdm import tqdm

# Allow running directly from src/
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATASETS,
    DATA_PROFILE_REPORT,
    DAY1_SUMMARY_MD,
    RAW_DIR,
)
from utils import (
    duplicate_row_count,
    missing_value_summary,
    print_separator,
    safe_read_csv,
    timeit,
    unique_value_counts,
    write_csv_report,
    write_markdown,
)


# ── Core Loader ───────────────────────────────────────────────────────────────

def load_all_datasets(raw_dir: Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    """Load every configured dataset from raw_dir. Returns key→DataFrame map."""
    loaded: dict[str, pd.DataFrame] = {}
    for key, filename in tqdm(DATASETS.items(), desc="Loading datasets", unit="file"):
        filepath = raw_dir / filename
        df = safe_read_csv(filepath)
        if df is not None:
            loaded[key] = df
        else:
            logger.warning("Skipping '{}' — could not load.", filename)
    logger.info("Loaded {}/{} datasets successfully.", len(loaded), len(DATASETS))
    return loaded


# ── Generic Profiler ──────────────────────────────────────────────────────────

def profile_dataset(key: str, df: pd.DataFrame) -> dict[str, Any]:
    """Print and return a profile summary for a single DataFrame."""
    print_separator(key.upper().replace("_", " "))

    print(f"  File       : {DATASETS.get(key, key)}")
    print(f"  Rows       : {len(df):,}")
    print(f"  Columns    : {len(df.columns)}")
    print(f"  Dtypes     :\n{df.dtypes.to_string()}")
    print(f"\n  Head (5):\n{df.head(5).to_string()}")

    mv = missing_value_summary(df)
    missing_total = int(mv["missing_count"].sum())
    dups = duplicate_row_count(df)
    uniq = unique_value_counts(df)

    print(f"\n  Missing values  : {missing_total}")
    if missing_total > 0:
        print(mv[mv["missing_count"] > 0].to_string(index=False))
    print(f"  Duplicate rows  : {dups}")
    print(f"  Unique per col  : {uniq}")

    return {
        "dataset": key,
        "filename": DATASETS.get(key, key),
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": missing_total,
        "duplicate_rows": dups,
        "dtypes": str(df.dtypes.to_dict()),
    }


# ── Dataset-Specific Profiling ────────────────────────────────────────────────

def profile_fund_master(df: pd.DataFrame) -> None:
    print_separator("FUND MASTER — DETAILED PROFILE")
    for col in ["fund_house", "category", "sub_category", "risk_category"]:
        if col in df.columns:
            print(f"\n  Unique [{col}] ({df[col].nunique()}):")
            print(f"    {sorted(df[col].dropna().unique().tolist())}")

    if "expense_ratio_pct" in df.columns:
        print(f"\n  Expense Ratio — min: {df['expense_ratio_pct'].min():.2f}%"
              f"  max: {df['expense_ratio_pct'].max():.2f}%"
              f"  mean: {df['expense_ratio_pct'].mean():.2f}%")

    if "plan" in df.columns:
        print(f"\n  Plan split:\n{df['plan'].value_counts().to_string()}")


def profile_nav_history(df: pd.DataFrame) -> None:
    print_separator("NAV HISTORY — DETAILED PROFILE")
    if "amfi_code" in df.columns:
        print(f"  Total unique schemes : {df['amfi_code'].nunique():,}")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        print(f"  Date range           : {df['date'].min().date()} → {df['date'].max().date()}")
        print(f"  Total NAV records    : {len(df):,}")

    if "nav" in df.columns:
        print(f"\n  NAV statistics:")
        print(df["nav"].describe().to_string())


def profile_scheme_performance(df: pd.DataFrame) -> None:
    print_separator("SCHEME PERFORMANCE — DETAILED PROFILE")
    return_cols = [c for c in df.columns if "return" in c.lower()]
    risk_cols   = [c for c in df.columns if c in
                   ("alpha", "beta", "sharpe_ratio", "sortino_ratio",
                    "std_dev_ann_pct", "max_drawdown_pct")]
    rank_cols   = [c for c in df.columns if "rank" in c.lower() or "rating" in c.lower()]

    if return_cols:
        print(f"\n  Return columns   : {return_cols}")
        print(df[return_cols].describe().to_string())

    if risk_cols:
        print(f"\n  Risk metrics     : {risk_cols}")
        print(df[risk_cols].describe().to_string())

    if rank_cols:
        print(f"\n  Ranking columns  : {rank_cols}")
        print(df[rank_cols].describe().to_string())

    if "risk_grade" in df.columns:
        print(f"\n  Risk grade distribution:\n{df['risk_grade'].value_counts().to_string()}")


def profile_investor_transactions(df: pd.DataFrame) -> None:
    print_separator("INVESTOR TRANSACTIONS — DETAILED PROFILE")
    if "transaction_type" in df.columns:
        print(f"\n  Transaction types:\n{df['transaction_type'].value_counts().to_string()}")

    if "investor_id" in df.columns:
        print(f"\n  Total unique investors : {df['investor_id'].nunique():,}")

    if "amount_inr" in df.columns:
        print(f"\n  Transaction volume (INR):")
        print(df["amount_inr"].describe().to_string())
        print(f"  Total INR transacted   : ₹{df['amount_inr'].sum():,.2f}")

    for cat_col in ("state", "city_tier", "age_group", "gender", "payment_mode"):
        if cat_col in df.columns:
            print(f"\n  {cat_col}:\n{df[cat_col].value_counts().head(10).to_string()}")


def profile_portfolio_holdings(df: pd.DataFrame) -> None:
    print_separator("PORTFOLIO HOLDINGS — DETAILED PROFILE")
    if "sector" in df.columns:
        print(f"\n  Sectors ({df['sector'].nunique()}):")
        print(df["sector"].value_counts().to_string())

    if "stock_name" in df.columns and "weight_pct" in df.columns:
        top = df.nlargest(10, "weight_pct")[["stock_name", "sector", "weight_pct"]]
        print(f"\n  Top 10 holdings by weight:\n{top.to_string(index=False)}")

    if "weight_pct" in df.columns:
        if "sector" in df.columns:
            avg_sector_wt = df.groupby("sector")["weight_pct"].mean().sort_values(ascending=False)
            print(f"\n  Average weight by sector:\n{avg_sector_wt.to_string()}")


# ── Profile All ───────────────────────────────────────────────────────────────

SPECIFIC_PROFILERS = {
    "fund_master":          profile_fund_master,
    "nav_history":          profile_nav_history,
    "scheme_performance":   profile_scheme_performance,
    "investor_transactions": profile_investor_transactions,
    "portfolio_holdings":   profile_portfolio_holdings,
}


@timeit
def run_profiling(
    datasets: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Run generic + specific profiling for all loaded datasets."""
    profile_rows: list[dict[str, Any]] = []

    for key, df in datasets.items():
        row = profile_dataset(key, df)
        profile_rows.append(row)

        if key in SPECIFIC_PROFILERS:
            try:
                SPECIFIC_PROFILERS[key](df)
            except Exception as exc:
                logger.warning("Specific profiling failed for '{}': {}", key, exc)

    return profile_rows


# ── Report Writers ────────────────────────────────────────────────────────────

def save_profile_report(profile_rows: list[dict[str, Any]]) -> None:
    """Write data_profile_report.csv."""
    df = pd.DataFrame(profile_rows)
    write_csv_report(df, DATA_PROFILE_REPORT)


def save_day1_summary(
    profile_rows: list[dict[str, Any]],
    datasets: dict[str, pd.DataFrame],
) -> None:
    """Write day1_summary.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_rows = sum(r["rows"] for r in profile_rows)
    total_missing = sum(r["missing_values"] for r in profile_rows)
    total_dups = sum(r["duplicate_rows"] for r in profile_rows)

    lines: list[str] = [
        "# MutualFundAnalytics — Day 1 Pipeline Summary",
        f"\n**Generated:** {now}",
        f"\n## Dataset Overview\n",
        f"| # | Dataset | Filename | Rows | Columns | Missing | Duplicates |",
        f"|---|---------|----------|------|---------|---------|------------|",
    ]

    for i, r in enumerate(profile_rows, 1):
        lines.append(
            f"| {i} | {r['dataset']} | {r['filename']} | "
            f"{r['rows']:,} | {r['columns']} | "
            f"{r['missing_values']} | {r['duplicate_rows']} |"
        )

    lines += [
        f"\n## Totals\n",
        f"- **Datasets loaded**: {len(profile_rows)}",
        f"- **Total rows**: {total_rows:,}",
        f"- **Total missing values**: {total_missing:,}",
        f"- **Total duplicate rows**: {total_dups:,}",
    ]

    # Fund master snapshot
    if "fund_master" in datasets:
        fm = datasets["fund_master"]
        lines += [
            f"\n## Fund Master Snapshot\n",
            f"- Total schemes: {len(fm):,}",
            f"- Fund houses: {fm['fund_house'].nunique() if 'fund_house' in fm.columns else 'N/A'}",
            f"- Categories: {fm['category'].nunique() if 'category' in fm.columns else 'N/A'}",
        ]

    # NAV history snapshot
    if "nav_history" in datasets:
        nv = datasets["nav_history"]
        if "date" in nv.columns:
            nv["date"] = pd.to_datetime(nv["date"], errors="coerce")
            lines += [
                f"\n## NAV History Snapshot\n",
                f"- Unique schemes: {nv['amfi_code'].nunique():,}",
                f"- Date range: {nv['date'].min().date()} → {nv['date'].max().date()}",
                f"- Total records: {len(nv):,}",
            ]

    write_markdown(DAY1_SUMMARY_MD, "\n".join(lines))


# ── Public Entry Point ────────────────────────────────────────────────────────

@timeit
def run_ingestion() -> dict[str, pd.DataFrame]:
    """Full Day-1 ingestion: load → profile → save reports."""
    logger.info("═══ DATA INGESTION STARTED ═══")
    datasets = load_all_datasets()

    if not datasets:
        logger.error("No datasets loaded. Aborting ingestion.")
        return {}

    profile_rows = run_profiling(datasets)
    save_profile_report(profile_rows)
    save_day1_summary(profile_rows, datasets)

    logger.info("═══ DATA INGESTION COMPLETE ═══")
    return datasets


if __name__ == "__main__":
    from utils import setup_logger, ensure_directories
    setup_logger()
    ensure_directories()
    run_ingestion()
