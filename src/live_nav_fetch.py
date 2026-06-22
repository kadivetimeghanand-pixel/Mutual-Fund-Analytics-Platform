"""
live_nav_fetch.py — Fetch live NAV data from api.mfapi.in and save as CSV.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    LIVE_NAV_SCHEMES,
    MFAPI_BASE_URL,
    RAW_DIR,
    REQUEST_DELAY_SEC,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
)
from utils import timeit, write_csv_report


# ── Fetch Single Scheme ───────────────────────────────────────────────────────

def fetch_scheme_nav(scheme_code: str) -> pd.DataFrame | None:
    """
    Fetch complete NAV history for a single AMFI scheme code.

    Returns a DataFrame with columns: amfi_code, date, nav, scheme_name
    Returns None on failure after all retries.
    """
    url = f"{MFAPI_BASE_URL}/{scheme_code}"

    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            logger.debug("Fetching scheme {} (attempt {}/{})", scheme_code, attempt, REQUEST_RETRIES)
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()

            if payload.get("status") != "SUCCESS":
                logger.warning("API returned non-SUCCESS status for scheme {}: {}", scheme_code, payload.get("status"))
                return None

            scheme_name: str = payload.get("meta", {}).get("scheme_name", "Unknown")
            raw_data: list[dict] = payload.get("data", [])

            if not raw_data:
                logger.warning("No NAV data returned for scheme {}", scheme_code)
                return None

            df = pd.DataFrame(raw_data)
            df.rename(columns={"date": "date", "nav": "nav"}, inplace=True)
            df["amfi_code"] = int(scheme_code)
            df["scheme_name"] = scheme_name
            df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
            df.sort_values("date", inplace=True)
            df.reset_index(drop=True, inplace=True)

            logger.info(
                "Fetched scheme {} — '{}' → {} NAV records ({} to {})",
                scheme_code,
                scheme_name,
                len(df),
                df["date"].min().date(),
                df["date"].max().date(),
            )
            return df

        except requests.exceptions.Timeout:
            logger.warning("Timeout on scheme {} attempt {}", scheme_code, attempt)
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Connection error on scheme {}: {}", scheme_code, exc)
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error on scheme {}: {}", scheme_code, exc)
            return None  # No point retrying 4xx/5xx
        except Exception as exc:
            logger.exception("Unexpected error fetching scheme {}: {}", scheme_code, exc)

        if attempt < REQUEST_RETRIES:
            backoff = REQUEST_DELAY_SEC * (2 ** (attempt - 1))
            logger.debug("Waiting {:.1f}s before retry...", backoff)
            time.sleep(backoff)

    logger.error("All {} retries exhausted for scheme {}", REQUEST_RETRIES, scheme_code)
    return None


# ── Fetch All Schemes ─────────────────────────────────────────────────────────

@timeit
def fetch_all_live_nav(
    schemes: dict[str, str] | None = None,
    output_dir: Path = RAW_DIR,
) -> dict[str, pd.DataFrame]:
    """
    Fetch NAV history for all configured schemes and save to CSV.

    Args:
        schemes: Optional override dict {scheme_code: output_filename}.
                 Defaults to LIVE_NAV_SCHEMES from config.
        output_dir: Directory to save CSV files.

    Returns:
        Dict mapping scheme_code → DataFrame.
    """
    if schemes is None:
        schemes = LIVE_NAV_SCHEMES

    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, pd.DataFrame] = {}

    logger.info("═══ LIVE NAV FETCH STARTED — {} schemes ═══", len(schemes))

    for scheme_code, filename in tqdm(schemes.items(), desc="Fetching NAV", unit="scheme"):
        df = fetch_scheme_nav(scheme_code)

        if df is not None:
            out_path = output_dir / filename
            write_csv_report(df, out_path)
            results[scheme_code] = df
        else:
            logger.warning("Skipping save for scheme {} — no data.", scheme_code)

        # Rate limiting courtesy pause
        time.sleep(REQUEST_DELAY_SEC)

    logger.info(
        "═══ LIVE NAV FETCH COMPLETE — {}/{} succeeded ═══",
        len(results),
        len(schemes),
    )
    return results


# ── Summary Printer ───────────────────────────────────────────────────────────

def print_nav_fetch_summary(results: dict[str, pd.DataFrame]) -> None:
    """Print a table summarising fetched NAV data."""
    if not results:
        print("  No NAV data was fetched.")
        return

    print(f"\n  {'Scheme Code':<12} {'Scheme Name':<55} {'Records':>8} {'From':<12} {'To':<12}")
    print("  " + "─" * 103)
    for code, df in results.items():
        name = df["scheme_name"].iloc[0] if "scheme_name" in df.columns else "N/A"
        records = len(df)
        from_dt = df["date"].min().date() if "date" in df.columns else "N/A"
        to_dt   = df["date"].max().date() if "date" in df.columns else "N/A"
        print(f"  {code:<12} {name[:54]:<55} {records:>8,} {str(from_dt):<12} {str(to_dt):<12}")


if __name__ == "__main__":
    from utils import setup_logger, ensure_directories
    setup_logger()
    ensure_directories()
    results = fetch_all_live_nav()
    print_nav_fetch_summary(results)
