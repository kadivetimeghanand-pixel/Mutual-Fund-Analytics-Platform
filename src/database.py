"""
database.py — SQLite database schema design and data loading.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))

from config import PROCESSED_DIR
from utils import timeit


# ── Database Schema ───────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- Dimension: Fund Master
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code TEXT PRIMARY KEY,
    fund_house TEXT,
    scheme_name TEXT,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id TEXT PRIMARY KEY,
    date TEXT,
    year INTEGER,
    month INTEGER,
    quarter INTEGER,
    is_weekday INTEGER
);

-- Fact: NAV History
CREATE TABLE IF NOT EXISTS fact_nav (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT,
    date TEXT,
    nav REAL,
    daily_return_pct REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi_date ON fact_nav(amfi_code, date);

-- Fact: Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT,
    transaction_date TEXT,
    amfi_code TEXT,
    transaction_type TEXT,
    amount_inr INTEGER,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE INDEX IF NOT EXISTS idx_fact_transactions_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_transactions_date ON fact_transactions(transaction_date);

-- Fact: Scheme Performance
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code TEXT PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    plan TEXT,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Fact: Portfolio Holdings
CREATE TABLE IF NOT EXISTS fact_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code TEXT,
    stock_symbol TEXT,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    holding_date TEXT,
    market_cap_category TEXT,
    quantity INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE INDEX IF NOT EXISTS idx_fact_portfolio_amfi ON fact_portfolio(amfi_code);

-- Fact: AUM by Fund House
CREATE TABLE IF NOT EXISTS fact_aum (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house TEXT,
    date TEXT,
    aum_lakh_crore REAL,
    num_schemes INTEGER,
    yoy_growth_pct REAL
);

CREATE INDEX IF NOT EXISTS idx_fact_aum_house_date ON fact_aum(fund_house, date);

-- Fact: Industry SIP Inflows
CREATE TABLE IF NOT EXISTS fact_sip_industry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT UNIQUE NOT NULL,
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

-- Fact: Category Inflows
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT,
    category TEXT,
    net_inflow_crore REAL
);

CREATE INDEX IF NOT EXISTS idx_fact_category_month ON fact_category_inflows(month, category);

-- Fact: Benchmark Indices
CREATE TABLE IF NOT EXISTS fact_benchmark (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name TEXT,
    date TEXT,
    close_value REAL
);

CREATE INDEX IF NOT EXISTS idx_fact_benchmark_index_date ON fact_benchmark(index_name, date);
"""


# ── Database Operations ───────────────────────────────────────────────────────

@timeit
def create_database(db_path: Path) -> None:
    """Create SQLite database with schema."""
    logger.info(f"Creating database: {db_path}")
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    with engine.connect() as conn:
        # Execute each statement separately
        for statement in SCHEMA_SQL.split(';'):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    
    logger.success(f"Database schema created: {db_path}")


@timeit
def load_data_to_database(db_path: Path, processed_dir: Path) -> None:
    """Load all cleaned datasets into SQLite database."""
    logger.info("Loading data into database...")
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    # Mapping of CSV files to database tables
    table_mapping = {
        'clean_01_fund_master.csv': 'dim_fund',
        'clean_nav.csv': 'fact_nav',
        'clean_transactions.csv': 'fact_transactions',
        'clean_performance.csv': 'fact_performance',
        'clean_09_portfolio_holdings.csv': 'fact_portfolio',
        'clean_03_aum_by_fund_house.csv': 'fact_aum',
        'clean_04_monthly_sip_inflows.csv': 'fact_sip_industry',
        'clean_05_category_inflows.csv': 'fact_category_inflows',
        'clean_10_benchmark_indices.csv': 'fact_benchmark'
    }
    
    for csv_file, table_name in table_mapping.items():
        file_path = processed_dir / csv_file
        
        if not file_path.exists():
            logger.warning(f"File not found: {csv_file}, skipping")
            continue
        
        try:
            df = pd.read_csv(file_path)
            
            # Load to database
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            
            logger.success(f"Loaded {len(df):,} rows into {table_name}")
            
        except Exception as e:
            logger.error(f"Error loading {csv_file} to {table_name}: {e}")
    
    logger.info("═══ DATABASE LOADING COMPLETE ═══")


@timeit
def verify_database(db_path: Path) -> None:
    """Verify database contents."""
    logger.info("Verifying database contents...")
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    tables = [
        'dim_fund', 'fact_nav', 'fact_transactions', 'fact_performance',
        'fact_portfolio', 'fact_aum', 'fact_sip_industry', 
        'fact_category_inflows', 'fact_benchmark'
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                logger.info(f"  {table}: {count:,} rows")
            except Exception as e:
                logger.warning(f"  {table}: Error - {e}")


if __name__ == "__main__":
    from utils import setup_logger, ensure_directories
    from config import DATA_DIR
    
    setup_logger()
    ensure_directories()
    
    db_path = DATA_DIR / 'bluestock_mf.db'
    
    create_database(db_path)
    load_data_to_database(db_path, PROCESSED_DIR)
    verify_database(db_path)
