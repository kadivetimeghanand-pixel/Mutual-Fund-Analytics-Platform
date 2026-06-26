"""
day2_pipeline.py — Master script for Day 2: Data Cleaning + SQL Database Design

Runs all Day 2 tasks:
1. Clean nav_history.csv
2. Clean investor_transactions.csv
3. Clean scheme_performance.csv
4. Design SQLite schema
5. Load data to database
6. Execute analytical queries
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger
from sqlalchemy import create_engine, text

from config import DATA_DIR, RAW_DIR, PROCESSED_DIR, SQL_DIR
from utils import setup_logger, ensure_directories, print_separator
from data_cleaning import clean_all_datasets
from database import create_database, load_data_to_database, verify_database


def execute_sql_queries(db_path: Path, queries_file: Path) -> None:
    """Execute all analytical queries and print results."""
    logger.info("Executing analytical SQL queries...")
    
    if not queries_file.exists():
        logger.warning(f"Queries file not found: {queries_file}")
        return
    
    # Read queries file
    with open(queries_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split into individual queries (separated by double newlines)
    queries = []
    current_query = []
    query_name = ""
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Skip empty lines and start of file comments
        if not line or line.startswith('--═'):
            continue
        
        # Capture query name from comments
        if line.startswith('-- Query'):
            if current_query:
                queries.append((query_name, '\n'.join(current_query)))
                current_query = []
            query_name = line.replace('--', '').strip()
            continue
        
        # Skip descriptive comments
        if line.startswith('--'):
            continue
        
        # Accumulate query lines
        current_query.append(line)
        
        # Execute when we hit a semicolon
        if line.endswith(';'):
            if current_query:
                queries.append((query_name, '\n'.join(current_query)))
                current_query = []
                query_name = ""
    
    # Execute queries
    engine = create_engine(f'sqlite:///{db_path}')
    
    for i, (name, query) in enumerate(queries[:10], 1):  # First 10 queries
        if not query.strip():
            continue
        
        print_separator(f"Query {i}: {name}")
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                if rows:
                    # Print column headers
                    headers = result.keys()
                    col_widths = [max(len(str(h)), 15) for h in headers]
                    
                    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
                    print(f"  {header_line}")
                    print(f"  {'-' * len(header_line)}")
                    
                    # Print rows (limit to first 10)
                    for row in rows[:10]:
                        row_line = " | ".join(str(v)[:w].ljust(w) for v, w in zip(row, col_widths))
                        print(f"  {row_line}")
                    
                    if len(rows) > 10:
                        print(f"  ... ({len(rows) - 10} more rows)")
                    
                    print(f"\n  Total rows: {len(rows)}")
                else:
                    print("  No results returned")
                
        except Exception as e:
            logger.error(f"Query {i} failed: {e}")
            print(f"  ERROR: {e}")
        
        print()


def main() -> None:
    """Run complete Day 2 pipeline."""
    setup_logger()
    ensure_directories()
    
    print_separator("DAY 2 PIPELINE — DATA CLEANING + SQL DATABASE")
    
    # Task 1-3: Clean datasets
    logger.info("Step 1: Data Cleaning")
    cleaned_data = clean_all_datasets(RAW_DIR, PROCESSED_DIR)
    
    # Task 4-5: Create database and load data
    logger.info("Step 2: Database Creation")
    db_path = DATA_DIR / 'bluestock_mf.db'
    create_database(db_path)
    load_data_to_database(db_path, PROCESSED_DIR)
    verify_database(db_path)
    
    # Task 6: Execute analytical queries
    logger.info("Step 3: Analytical Queries")
    queries_file = SQL_DIR / 'queries.sql'
    execute_sql_queries(db_path, queries_file)
    
    print_separator("DAY 2 PIPELINE COMPLETE")
    logger.success("All Day 2 tasks completed successfully!")
    logger.info(f"  ✓ Cleaned datasets → {PROCESSED_DIR}")
    logger.info(f"  ✓ Database → {db_path}")
    logger.info(f"  ✓ Schema → {SQL_DIR / 'schema.sql'}")
    logger.info(f"  ✓ Queries → {SQL_DIR / 'queries.sql'}")
    logger.info(f"  ✓ Data Dictionary → data_dictionary.md")


if __name__ == "__main__":
    main()
