"""
utils.py — Shared utility functions for MutualFundAnalytics pipeline.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from config import (
    LOGS_DIR,
    LOG_FILE,
    LOG_FORMAT,
    LOG_ROTATION,
    LOG_RETENTION,
    REPORTS_DIR,
    RAW_DIR,
    PROCESSED_DIR,
)


# ── Logger Setup ──────────────────────────────────────────────────────────────

def setup_logger() -> None:
    """Configure loguru logger with console and file sinks."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # Console sink
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level="INFO",
        colorize=True,
    )

    # File sink
    logger.add(
        str(LOG_FILE),
        format=LOG_FORMAT,
        level="DEBUG",
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        encoding="utf-8",
    )
    logger.info("Logger initialised. Log file → {}", LOG_FILE)


# ── Directory Bootstrap ───────────────────────────────────────────────────────

def ensure_directories() -> None:
    """Create all required project directories if they don't exist."""
    dirs = [RAW_DIR, PROCESSED_DIR, REPORTS_DIR, LOGS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.debug("All project directories verified.")


# ── DataFrame Helpers ─────────────────────────────────────────────────────────

def safe_read_csv(filepath: Path, **kwargs: Any) -> pd.DataFrame | None:
    """
    Read a CSV file safely. Returns None and logs an error on failure.
    """
    try:
        df = pd.read_csv(filepath, **kwargs)
        logger.debug("Loaded '{}' → {} rows × {} cols", filepath.name, len(df), len(df.columns))
        return df
    except FileNotFoundError:
        logger.error("File not found: {}", filepath)
    except pd.errors.EmptyDataError:
        logger.warning("Empty file: {}", filepath)
    except Exception as exc:
        logger.exception("Failed to read '{}': {}", filepath.name, exc)
    return None


def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with missing value counts and percentages per column."""
    total = len(df)
    missing = df.isnull().sum()
    pct = (missing / total * 100).round(2)
    return pd.DataFrame({"missing_count": missing, "missing_pct": pct}).reset_index(
        names="column"
    )


def duplicate_row_count(df: pd.DataFrame) -> int:
    """Return count of fully duplicated rows."""
    return int(df.duplicated().sum())


def unique_value_counts(df: pd.DataFrame) -> dict[str, int]:
    """Return dict mapping each column to its unique value count."""
    return {col: int(df[col].nunique()) for col in df.columns}


def print_separator(title: str = "", width: int = 80) -> None:
    """Print a styled section separator to stdout."""
    if title:
        side = (width - len(title) - 2) // 2
        print("\n" + "─" * side + f" {title} " + "─" * side)
    else:
        print("\n" + "─" * width)


# ── Timing Decorator ──────────────────────────────────────────────────────────

def timeit(func):  # type: ignore[no-untyped-def]
    """Simple decorator to log function execution time."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("{} completed in {:.2f}s", func.__name__, elapsed)
        return result

    return wrapper


# ── Markdown Helpers ──────────────────────────────────────────────────────────

def write_markdown(path: Path, content: str) -> None:
    """Write a string as a UTF-8 markdown file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Markdown report written → {}", path)


def write_csv_report(df: pd.DataFrame, path: Path) -> None:
    """Write a DataFrame to CSV safely."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("CSV report written → {} ({} rows)", path.name, len(df))
