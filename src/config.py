"""
config.py — Central configuration for MutualFundAnalytics pipeline.
"""

from pathlib import Path

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
REPORTS_DIR: Path = BASE_DIR / "reports"
LOGS_DIR: Path = BASE_DIR / "logs"
SQL_DIR: Path = BASE_DIR / "sql"
NOTEBOOKS_DIR: Path = BASE_DIR / "notebooks"
DASHBOARD_DIR: Path = BASE_DIR / "dashboard"

# ── Dataset filenames ─────────────────────────────────────────────────────────
DATASETS: dict[str, str] = {
    "fund_master":         "01_fund_master.csv",
    "nav_history":         "02_nav_history.csv",
    "aum_by_fund_house":   "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows":    "05_category_inflows.csv",
    "industry_folio":      "06_industry_folio_count.csv",
    "scheme_performance":  "07_scheme_performance.csv",
    "investor_transactions":"08_investor_transactions.csv",
    "portfolio_holdings":  "09_portfolio_holdings.csv",
    "benchmark_indices":   "10_benchmark_indices.csv",
}

# ── Live NAV Fetch Config ─────────────────────────────────────────────────────
MFAPI_BASE_URL: str = "https://api.mfapi.in/mf"

LIVE_NAV_SCHEMES: dict[str, str] = {
    "125497": "nav_hdfc_top100.csv",
    "119551": "nav_sbi_bluechip.csv",
    "120503": "nav_icici_bluechip.csv",
    "118632": "nav_nippon_largecap.csv",
    "119092": "nav_axis_bluechip.csv",
    "120841": "nav_kotak_bluechip.csv",
}

# ── Report Filenames ──────────────────────────────────────────────────────────
DATA_PROFILE_REPORT: Path = REPORTS_DIR / "data_profile_report.csv"
DAY1_SUMMARY_MD: Path = REPORTS_DIR / "day1_summary.md"
AMFI_VALIDATION_REPORT: Path = REPORTS_DIR / "amfi_validation_report.csv"
AMFI_VALIDATION_MD: Path = REPORTS_DIR / "amfi_validation_summary.md"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE: Path = LOGS_DIR / "day1_pipeline.log"
LOG_ROTATION: str = "10 MB"
LOG_RETENTION: str = "7 days"
LOG_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# ── API / Request Settings ────────────────────────────────────────────────────
REQUEST_TIMEOUT: int = 30
REQUEST_RETRIES: int = 3
REQUEST_DELAY_SEC: float = 0.5
