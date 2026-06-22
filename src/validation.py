"""
validation.py — AMFI code cross-validation between fund_master and nav_history.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    AMFI_VALIDATION_MD,
    AMFI_VALIDATION_REPORT,
    DATASETS,
    RAW_DIR,
)
from utils import (
    safe_read_csv,
    timeit,
    write_csv_report,
    write_markdown,
)


# ── Check Functions ───────────────────────────────────────────────────────────

def check_missing_codes(
    master_codes: set[int],
    nav_codes: set[int],
) -> pd.DataFrame:
    """Codes in fund_master but absent from nav_history."""
    missing = sorted(master_codes - nav_codes)
    return pd.DataFrame({"amfi_code": missing, "issue": "missing_from_nav_history"})


def check_orphan_nav_codes(
    master_codes: set[int],
    nav_codes: set[int],
) -> pd.DataFrame:
    """Codes in nav_history but absent from fund_master (orphans)."""
    orphans = sorted(nav_codes - master_codes)
    return pd.DataFrame({"amfi_code": orphans, "issue": "nav_code_not_in_fund_master"})


def check_duplicate_codes_master(df_master: pd.DataFrame) -> pd.DataFrame:
    """Detect duplicate amfi_codes in fund_master."""
    dupes = df_master[df_master.duplicated(subset=["amfi_code"], keep=False)].copy()
    if dupes.empty:
        return pd.DataFrame(columns=["amfi_code", "issue"])
    dupes["issue"] = "duplicate_in_fund_master"
    return dupes[["amfi_code", "issue"]]


def check_duplicate_codes_nav(df_nav: pd.DataFrame) -> pd.DataFrame:
    """Detect duplicate (amfi_code, date) pairs in nav_history."""
    dupes = df_nav[df_nav.duplicated(subset=["amfi_code", "date"], keep=False)].copy()
    if dupes.empty:
        return pd.DataFrame(columns=["amfi_code", "issue"])
    dupes["issue"] = "duplicate_code_date_in_nav"
    return dupes[["amfi_code", "issue"]].drop_duplicates()


def check_invalid_codes(df_master: pd.DataFrame) -> pd.DataFrame:
    """Flag amfi_codes that are null or non-positive integers."""
    mask = df_master["amfi_code"].isnull() | (df_master["amfi_code"] <= 0)
    invalid = df_master[mask][["amfi_code"]].copy()
    invalid["issue"] = "invalid_amfi_code"
    return invalid


def schemes_without_nav(
    df_master: pd.DataFrame,
    nav_codes: set[int],
) -> pd.DataFrame:
    """Full details of fund_master rows whose codes have no NAV history."""
    no_nav = df_master[~df_master["amfi_code"].isin(nav_codes)].copy()
    if no_nav.empty:
        return pd.DataFrame()
    no_nav["issue"] = "no_nav_history"
    return no_nav


# ── AMFI Validation Orchestrator ──────────────────────────────────────────────

@timeit
def run_amfi_validation(
    df_master: pd.DataFrame | None = None,
    df_nav: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Run all AMFI code validation checks.

    If DataFrames are not provided, loads them from RAW_DIR automatically.
    Saves reports/amfi_validation_report.csv and reports/amfi_validation_summary.md.

    Returns consolidated issues DataFrame.
    """
    logger.info("═══ AMFI VALIDATION STARTED ═══")

    # Load if not provided
    if df_master is None:
        df_master = safe_read_csv(RAW_DIR / DATASETS["fund_master"])
    if df_nav is None:
        df_nav = safe_read_csv(RAW_DIR / DATASETS["nav_history"])

    if df_master is None or df_nav is None:
        logger.error("Cannot validate — one or both source files failed to load.")
        return pd.DataFrame()

    # Coerce amfi_code to integer
    df_master["amfi_code"] = pd.to_numeric(df_master["amfi_code"], errors="coerce").astype("Int64")
    df_nav["amfi_code"]    = pd.to_numeric(df_nav["amfi_code"],    errors="coerce").astype("Int64")

    master_codes: set[int] = set(df_master["amfi_code"].dropna().unique())
    nav_codes:    set[int] = set(df_nav["amfi_code"].dropna().unique())

    logger.info("fund_master  : {:,} unique codes", len(master_codes))
    logger.info("nav_history  : {:,} unique codes", len(nav_codes))

    # Run all checks
    issues: list[pd.DataFrame] = [
        check_missing_codes(master_codes, nav_codes),
        check_orphan_nav_codes(master_codes, nav_codes),
        check_duplicate_codes_master(df_master),
        check_duplicate_codes_nav(df_nav),
        check_invalid_codes(df_master),
    ]

    # Consolidate
    non_empty = [df for df in issues if not df.empty]
    if non_empty:
        consolidated = pd.concat(non_empty, ignore_index=True)
    else:
        consolidated = pd.DataFrame(columns=["amfi_code", "issue"])

    if consolidated.empty:
        logger.success("AMFI validation PASSED — no issues found.")
    else:
        logger.warning(
            "AMFI validation found {:,} issue(s) across {:,} unique codes.",
            len(consolidated),
            consolidated["amfi_code"].nunique(),
        )

    # Save report
    write_csv_report(consolidated, AMFI_VALIDATION_REPORT)

    # Build markdown summary
    _write_validation_markdown(
        df_master=df_master,
        df_nav=df_nav,
        master_codes=master_codes,
        nav_codes=nav_codes,
        consolidated=consolidated,
    )

    logger.info("═══ AMFI VALIDATION COMPLETE ═══")
    return consolidated


# ── Markdown Reporter ─────────────────────────────────────────────────────────

def _write_validation_markdown(
    df_master: pd.DataFrame,
    df_nav: pd.DataFrame,
    master_codes: set[int],
    nav_codes: set[int],
    consolidated: pd.DataFrame,
) -> None:
    """Generate amfi_validation_summary.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    matched = master_codes & nav_codes
    missing = master_codes - nav_codes
    orphans = nav_codes - master_codes

    issue_counts: dict[str, int] = {}
    if not consolidated.empty:
        issue_counts = consolidated["issue"].value_counts().to_dict()

    lines: list[str] = [
        "# AMFI Code Validation Report",
        f"\n**Generated:** {now}",
        "\n## Source Datasets",
        f"| Dataset | Unique AMFI Codes | Total Rows |",
        f"|---------|------------------|------------|",
        f"| 01_fund_master.csv  | {len(master_codes):,} | {len(df_master):,} |",
        f"| 02_nav_history.csv  | {len(nav_codes):,} | {len(df_nav):,} |",
        "\n## Cross-Validation Results",
        f"| Check | Count |",
        f"|-------|-------|",
        f"| Matched codes (in both) | {len(matched):,} |",
        f"| Missing from nav_history | {len(missing):,} |",
        f"| Orphan codes (nav only) | {len(orphans):,} |",
        f"| Duplicates in fund_master | {issue_counts.get('duplicate_in_fund_master', 0):,} |",
        f"| Duplicate (code,date) in nav | {issue_counts.get('duplicate_code_date_in_nav', 0):,} |",
        f"| Invalid AMFI codes | {issue_counts.get('invalid_amfi_code', 0):,} |",
        f"| **Total Issues** | **{len(consolidated):,}** |",
    ]

    if not consolidated.empty:
        lines += [
            "\n## Issue Breakdown",
            "```",
            consolidated["issue"].value_counts().to_string(),
            "```",
        ]

        missing_list = sorted(missing)[:20]
        if missing_list:
            lines += [
                "\n## Sample Codes Missing from NAV History (first 20)",
                ", ".join(str(c) for c in missing_list),
            ]
    else:
        lines.append("\n✅ **All AMFI codes are valid and fully matched.**")

    write_markdown(AMFI_VALIDATION_MD, "\n".join(lines))


if __name__ == "__main__":
    from utils import setup_logger, ensure_directories
    setup_logger()
    ensure_directories()
    run_amfi_validation()
