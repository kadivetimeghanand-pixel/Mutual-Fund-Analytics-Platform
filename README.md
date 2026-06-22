# MutualFundAnalytics — Capstone Project

A production-ready Python pipeline for ingesting, profiling, validating, and analysing Indian Mutual Fund data from AMFI and the MF API.

---

## Project Overview

This capstone project builds a full analytics stack around 10 AMFI-sourced datasets covering fund metadata, NAV history, AUM, SIP inflows, investor transactions, portfolio holdings, and benchmark indices.

**Day 1** focuses on:
- Automated dataset ingestion and profiling
- Live NAV fetching from [api.mfapi.in](https://api.mfapi.in)
- AMFI code cross-validation between fund master and NAV history
- Structured report generation (CSV + Markdown)

---

## Project Structure

```
MutualFundAnalytics/
│
├── data/
│   ├── raw/                   # Source CSVs + downloaded live NAV files
│   └── processed/             # Cleaned / transformed datasets
│
├── src/
│   ├── config.py              # Centralised paths, constants, and settings
│   ├── utils.py               # Shared helpers (logger, readers, writers)
│   ├── data_ingestion.py      # Load, profile, and report all datasets
│   ├── live_nav_fetch.py      # Live NAV download from api.mfapi.in
│   └── validation.py          # AMFI code cross-validation
│
├── dashboard/
│   └── main.py                # Pipeline entry point — runs everything
│
├── reports/                   # Auto-generated CSV & Markdown reports
├── logs/                      # Loguru log files
├── notebooks/                 # Jupyter notebooks for EDA
├── sql/                       # SQL queries and schema definitions
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Datasets

| # | File | Description |
|---|------|-------------|
| 01 | `01_fund_master.csv` | Scheme metadata — fund house, category, benchmark, expense ratio |
| 02 | `02_nav_history.csv` | Daily NAV time-series per scheme |
| 03 | `03_aum_by_fund_house.csv` | AUM per fund house over time |
| 04 | `04_monthly_sip_inflows.csv` | Industry-level monthly SIP inflow data |
| 05 | `05_category_inflows.csv` | Net inflows per category per month |
| 06 | `06_industry_folio_count.csv` | Folio counts segmented by equity / debt / hybrid |
| 07 | `07_scheme_performance.csv` | Returns, alpha, beta, Sharpe, Sortino, drawdown per scheme |
| 08 | `08_investor_transactions.csv` | Individual SIP / lumpsum / redemption transactions |
| 09 | `09_portfolio_holdings.csv` | Stock-level holdings per scheme with weights |
| 10 | `10_benchmark_indices.csv` | Daily close values for NIFTY50, NIFTY100, etc. |

---

## Setup

### Prerequisites
- Python 3.11+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Place raw CSVs

Copy all 10 source CSV files into:

```
data/raw/
```

---

## Run the Pipeline

```bash
python dashboard/main.py
```

This will:
1. Load and profile all 10 datasets
2. Run AMFI code cross-validation
3. Download live NAV data for 6 bluechip schemes
4. Generate all reports
5. Print an execution summary

---

## Outputs Generated

| Output | Path | Description |
|--------|------|-------------|
| Data Profile Report | `reports/data_profile_report.csv` | Row/column/missing/duplicate counts per dataset |
| Day 1 Summary | `reports/day1_summary.md` | Markdown pipeline summary |
| AMFI Validation CSV | `reports/amfi_validation_report.csv` | All AMFI code issues found |
| AMFI Validation MD | `reports/amfi_validation_summary.md` | Human-readable validation summary |
| Live NAV CSVs | `data/raw/nav_*.csv` | Downloaded NAV history per scheme |
| Pipeline Log | `logs/day1_pipeline.log` | Full structured execution log |

---

## Live NAV Schemes (Day 1)

| AMFI Code | Scheme |
|-----------|--------|
| 125497 | HDFC Top 100 Direct |
| 119551 | SBI Bluechip |
| 120503 | ICICI Bluechip |
| 118632 | Nippon Large Cap |
| 119092 | Axis Bluechip |
| 120841 | Kotak Bluechip |

---

## Code Standards

- Python 3.11+ with full type hints
- PEP 8 compliant
- Modular architecture — each module has a single responsibility
- Structured logging via [loguru](https://github.com/Delgan/loguru)
- Graceful error handling and retry logic on API calls
- Production-ready, GitHub-ready

---

## License

MIT
