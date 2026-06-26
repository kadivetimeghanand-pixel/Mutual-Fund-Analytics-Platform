"""
data_cleaning.py — Clean and validate all raw datasets.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))

from config import RAW_DIR
from utils import timeit, print_separator


# ── Clean NAV History ─────────────────────────────────────────────────────────

@timeit
def clean_nav_history(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Clean nav_history.csv:
    - Parse dates to datetime
    - Sort by amfi_code + date
    - Forward-fill missing NAV (holidays/weekends)
    - Remove duplicates
    - Validate NAV > 0
    """
    logger.info("Cleaning nav_history.csv...")
    df = pd.read_csv(input_path)
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Remove rows with invalid dates
    before_count = len(df)
    df = df.dropna(subset=['date'])
    if len(df) < before_count:
        logger.warning(f"Dropped {before_count - len(df)} rows with invalid dates")
    
    # Sort by amfi_code and date
    df = df.sort_values(['amfi_code', 'date']).reset_index(drop=True)
    
    # Validate NAV > 0
    invalid_nav = df[df['nav'] <= 0]
    if not invalid_nav.empty:
        logger.warning(f"Found {len(invalid_nav)} rows with NAV <= 0, removing them")
        df = df[df['nav'] > 0]
    
    # Remove exact duplicates
    before_dup = len(df)
    df = df.drop_duplicates(subset=['amfi_code', 'date'], keep='first')
    if len(df) < before_dup:
        logger.warning(f"Removed {before_dup - len(df)} duplicate rows")
    
    # Forward-fill missing NAV for each fund (handles holidays/weekends)
    # Create complete date range for each fund
    all_dates = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    
    cleaned_frames = []
    for amfi_code in df['amfi_code'].unique():
        fund_df = df[df['amfi_code'] == amfi_code].copy()
        
        # Reindex to full date range
        fund_df = fund_df.set_index('date')
        fund_df = fund_df.reindex(all_dates)
        fund_df['amfi_code'] = amfi_code
        
        # Forward fill NAV
        fund_df['nav'] = fund_df['nav'].ffill()
        
        fund_df = fund_df.reset_index()
        fund_df.rename(columns={'index': 'date'}, inplace=True)
        cleaned_frames.append(fund_df)
    
    df = pd.concat(cleaned_frames, ignore_index=True)
    df = df.sort_values(['amfi_code', 'date']).reset_index(drop=True)
    
    # Save cleaned data
    df.to_csv(output_path, index=False)
    logger.success(f"Cleaned nav_history saved: {len(df):,} rows → {output_path}")
    
    return df


# ── Clean Investor Transactions ───────────────────────────────────────────────

@timeit
def clean_investor_transactions(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Clean investor_transactions.csv:
    - Standardise transaction_type (SIP/Lumpsum/Redemption)
    - Validate amount > 0
    - Fix date formats
    - Check KYC status values
    """
    logger.info("Cleaning investor_transactions.csv...")
    df = pd.read_csv(input_path)
    
    # Parse dates
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    
    # Remove rows with invalid dates
    before_count = len(df)
    df = df.dropna(subset=['transaction_date'])
    if len(df) < before_count:
        logger.warning(f"Dropped {before_count - len(df)} rows with invalid transaction dates")
    
    # Standardise transaction_type
    valid_types = ['SIP', 'Lumpsum', 'Redemption']
    df['transaction_type'] = df['transaction_type'].str.strip().str.title()
    
    # Map variations
    type_mapping = {
        'Sip': 'SIP',
        'Lump Sum': 'Lumpsum',
        'Redeem': 'Redemption'
    }
    df['transaction_type'] = df['transaction_type'].replace(type_mapping)
    
    invalid_types = df[~df['transaction_type'].isin(valid_types)]
    if not invalid_types.empty:
        logger.warning(f"Found {len(invalid_types)} rows with invalid transaction_type, removing them")
        df = df[df['transaction_type'].isin(valid_types)]
    
    # Validate amount > 0
    invalid_amount = df[df['amount_inr'] <= 0]
    if not invalid_amount.empty:
        logger.warning(f"Found {len(invalid_amount)} rows with amount <= 0, removing them")
        df = df[df['amount_inr'] > 0]
    
    # Check KYC status values
    valid_kyc = ['Verified', 'Pending']
    df['kyc_status'] = df['kyc_status'].str.strip()
    invalid_kyc = df[~df['kyc_status'].isin(valid_kyc)]
    if not invalid_kyc.empty:
        logger.warning(f"Found {len(invalid_kyc)} rows with invalid kyc_status, setting to 'Pending'")
        df.loc[~df['kyc_status'].isin(valid_kyc), 'kyc_status'] = 'Pending'
    
    # Sort by date
    df = df.sort_values('transaction_date').reset_index(drop=True)
    
    # Save cleaned data
    df.to_csv(output_path, index=False)
    logger.success(f"Cleaned investor_transactions saved: {len(df):,} rows → {output_path}")
    
    return df


# ── Clean Scheme Performance ──────────────────────────────────────────────────

@timeit
def clean_scheme_performance(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Clean scheme_performance.csv:
    - Validate return values are numeric
    - Flag negative Sharpe ratios
    - Check expense_ratio range (0.1% – 2.5%)
    """
    logger.info("Cleaning scheme_performance.csv...")
    df = pd.read_csv(input_path)
    
    # Validate numeric columns
    numeric_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 
                    'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 
                    'std_dev_ann_pct', 'max_drawdown_pct', 'expense_ratio_pct']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"Column '{col}' has {null_count} non-numeric values, setting to NaN")
    
    # Flag negative Sharpe ratios (unusual but not invalid)
    negative_sharpe = df[df['sharpe_ratio'] < 0]
    if not negative_sharpe.empty:
        logger.info(f"Found {len(negative_sharpe)} schemes with negative Sharpe ratio (underperforming risk-free rate)")
    
    # Check expense_ratio range
    if 'expense_ratio_pct' in df.columns:
        out_of_range = df[(df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)]
        if not out_of_range.empty:
            logger.warning(f"Found {len(out_of_range)} schemes with expense_ratio outside typical range (0.1-2.5%)")
            for idx, row in out_of_range.iterrows():
                logger.debug(f"  {row['scheme_name']}: {row['expense_ratio_pct']}%")
    
    # Save cleaned data
    df.to_csv(output_path, index=False)
    logger.success(f"Cleaned scheme_performance saved: {len(df):,} rows → {output_path}")
    
    return df


# ── Clean All Datasets ────────────────────────────────────────────────────────

@timeit
def clean_all_datasets(raw_dir: Path, processed_dir: Path) -> dict[str, pd.DataFrame]:
    """
    Clean all datasets that require transformation.
    """
    logger.info("═══ DATA CLEANING STARTED ═══")
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    cleaned_data = {}
    
    # Clean NAV history
    cleaned_data['nav_history'] = clean_nav_history(
        raw_dir / '02_nav_history.csv',
        processed_dir / 'clean_nav.csv'
    )
    
    # Clean investor transactions
    cleaned_data['investor_transactions'] = clean_investor_transactions(
        raw_dir / '08_investor_transactions.csv',
        processed_dir / 'clean_transactions.csv'
    )
    
    # Clean scheme performance
    cleaned_data['scheme_performance'] = clean_scheme_performance(
        raw_dir / '07_scheme_performance.csv',
        processed_dir / 'clean_performance.csv'
    )
    
    # Copy other datasets that don't need cleaning
    other_files = [
        '01_fund_master.csv',
        '03_aum_by_fund_house.csv',
        '04_monthly_sip_inflows.csv',
        '05_category_inflows.csv',
        '06_industry_folio_count.csv',
        '09_portfolio_holdings.csv',
        '10_benchmark_indices.csv'
    ]
    
    for filename in other_files:
        src = raw_dir / filename
        dst = processed_dir / f"clean_{filename}"
        if src.exists():
            df = pd.read_csv(src)
            df.to_csv(dst, index=False)
            logger.info(f"Copied {filename} → {dst.name}")
    
    logger.info("═══ DATA CLEANING COMPLETE ═══")
    
    return cleaned_data


if __name__ == "__main__":
    from utils import setup_logger, ensure_directories
    from config import PROCESSED_DIR
    
    setup_logger()
    ensure_directories()
    
    clean_all_datasets(RAW_DIR, PROCESSED_DIR)
