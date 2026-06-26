# Bluestock MF Analytics — Data Dictionary

**Last Updated:** 2026-06-25  
**Version:** 1.0  

---

## Overview

This document provides comprehensive documentation of all datasets, tables, columns, data types, business definitions, and source references used in the Bluestock Mutual Fund Analytics platform.

---

## Data Sources

| Source | URL / API | Update Frequency | Data Types |
|--------|-----------|-----------------|------------|
| AMFI India | www.amfiindia.com | Daily / Monthly | NAV, AUM, Folio Counts, SIP Data |
| mfapi.in | api.mfapi.in/mf/{code} | Daily | Historical NAV (JSON) |
| NSE India | nseindia.com/reports | Daily | Benchmark Index Prices |
| BSE India | bseindia.com | Daily | BSE Indices |
| AMFI Monthly Notes | amfiindia.com/research | Monthly | Industry SIP & Flow Data |

---

## 1. Fund Master (01_fund_master.csv / dim_fund)

**Description:** Master list of 40 mutual fund schemes with metadata

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `amfi_code` | TEXT | AMFI unique scheme identifier (Primary Key) | AMFI India | 125497, 119551, 120503 |
| `fund_house` | TEXT | Asset Management Company name | AMFI India | SBI Mutual Fund, HDFC MF |
| `scheme_name` | TEXT | Official AMFI scheme name | AMFI India | HDFC Top 100 - Direct - Growth |
| `category` | TEXT | Asset class category | SEBI | Equity, Debt, Hybrid |
| `sub_category` | TEXT | Scheme sub-classification | SEBI | Large Cap, Mid Cap, Liquid |
| `plan` | TEXT | Distribution plan type | AMFI India | Regular, Direct |
| `launch_date` | DATE | Fund inception date (YYYY-MM-DD) | AMFI India | 2013-01-01 |
| `benchmark` | TEXT | Official benchmark index | Scheme documents | Nifty 50, Nifty 100 |
| `expense_ratio_pct` | REAL | Annual expense ratio in % | AMFI disclosures | 0.66, 1.54 |
| `exit_load_pct` | REAL | Exit load percentage | Scheme documents | 0.0, 1.0 |
| `fund_manager` | TEXT | Primary fund manager name | AMC website | Rakesh Singh, Prashant Jain |
| `risk_category` | TEXT | SEBI risk classification | SEBI guidelines | Low, Moderate, High, Very High |
| `sebi_category_code` | TEXT | Internal SEBI category code | SEBI | EC01, DC01, HC02 |

**Business Rules:**
- `amfi_code` is unique and never changes for a scheme
- Direct plans have lower `expense_ratio_pct` than Regular plans
- `launch_date` determines eligibility for 3yr/5yr return calculations

---

## 2. NAV History (02_nav_history.csv / fact_nav)

**Description:** Daily Net Asset Value for all 40 schemes from Jan 2022 to May 2026

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `amfi_code` | TEXT | Foreign key to dim_fund | - | 125497, 119551 |
| `date` | DATE | NAV date (business days only) | mfapi.in, AMFI | 2024-01-15 |
| `nav` | REAL | Net Asset Value in Rs. | mfapi.in | 892.4560, 54.3856 |
| `daily_return_pct` | REAL | Computed: (NAV_t / NAV_t-1) - 1 | Calculated | 0.05, -0.02 |

**Business Rules:**
- NAV is published on business days only (excludes weekends and market holidays)
- Missing NAV dates are forward-filled for consistency
- All NAV values anchored to real mfapi.in data
- Daily returns calculated as percentage change from previous day

**Data Quality:**
- ~46,000 rows (40 schemes × ~1,150 trading days)
- No missing values after forward-fill

---

## 3. AUM by Fund House (03_aum_by_fund_house.csv / fact_aum)

**Description:** Quarterly Assets Under Management for top 10 AMCs (2022-2025)

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `fund_house` | TEXT | AMC name | AMFI Quarterly | SBI Mutual Fund, HDFC MF |
| `date` | DATE | Quarter end date | AMFI Quarterly | 2024-03-31, 2024-06-30 |
| `aum_lakh_crore` | REAL | AUM in Rs. lakh crore | AMFI Quarterly | 12.50, 10.74 |
| `num_schemes` | INTEGER | Number of active schemes | AMFI Quarterly | 156, 203 |
| `yoy_growth_pct` | REAL | Year-over-year growth % | Calculated | 18.5, -5.2 |

**Business Rules:**
- AUM reported quarterly (Mar 31, Jun 30, Sep 30, Dec 31)
- SBI Mutual Fund is largest AMC with Rs. 12.50 lakh crore AUM (Dec 2025)
- Values in **lakh crore** (1 lakh crore = 1,00,000 crore = 1 trillion rupees)

---

## 4. Monthly SIP Inflows (04_monthly_sip_inflows.csv / fact_sip_industry)

**Description:** Industry-level monthly SIP data from AMFI Monthly Notes

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `month` | TEXT | Month (YYYY-MM format) | AMFI Monthly Note | 2025-12, 2024-06 |
| `sip_inflow_crore` | REAL | Total SIP inflows in Rs. crore | AMFI Monthly Note | 31002, 24508 |
| `active_sip_accounts_crore` | REAL | Active SIP accounts (crore) | AMFI Monthly Note | 9.35, 8.21 |
| `new_sip_accounts_lakh` | REAL | New SIP registrations (lakh) | AMFI Monthly Note | 52.3, 48.1 |
| `sip_aum_lakh_crore` | REAL | SIP AUM in Rs. lakh crore | AMFI Monthly Note | 15.8, 14.2 |
| `yoy_growth_pct` | REAL | Year-over-year growth % | Calculated | 28.5, 15.3 |

**Business Rules:**
- SIP inflow crossed all-time high of Rs. 31,002 crore in Dec 2025
- Active SIP accounts reached 9.35 crore (93.5 million) in Dec 2025
- Values updated monthly around 15th of following month

---

## 5. Category Inflows (05_category_inflows.csv / fact_category_inflows)

**Description:** Net inflows per category per month for FY 2024-25

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `month` | TEXT | Month (YYYY-MM) | AMFI Monthly Note | 2024-04, 2024-05 |
| `category` | TEXT | Fund category | AMFI classification | Large Cap, Small Cap, Liquid |
| `net_inflow_crore` | REAL | Net inflow in Rs. crore | AMFI Monthly Note | 5420, -1230 |

**Business Rules:**
- Positive = Net inflow (purchases > redemptions)
- Negative = Net outflow (redemptions > purchases)
- Categories: Large Cap, Mid Cap, Small Cap, Flexi Cap, ELSS, Liquid, Gilt, etc.

---

## 6. Industry Folio Count (06_industry_folio_count.csv)

**Description:** Total mutual fund investor folios by asset type

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `date` | DATE | Month end | AMFI | 2025-12-31 |
| `asset_type` | TEXT | Asset class | AMFI | Equity, Debt, Hybrid |
| `folio_count_crore` | REAL | Folios in crore | AMFI | 15.2, 8.4, 2.5 |

**Business Rules:**
- Total MF folios reached 26.12 crore (261.2 million) in Dec 2025
- One investor can have multiple folios
- Equity folios dominate at ~58% of total

---

## 7. Scheme Performance (07_scheme_performance.csv / fact_performance)

**Description:** Computed performance and risk metrics for all 40 schemes

| Column | Type | Description | Calculation | Sample Values |
|--------|------|-------------|-------------|---------------|
| `amfi_code` | TEXT | Primary Key | - | 125497, 119551 |
| `scheme_name` | TEXT | Scheme name | - | HDFC Top 100 - Direct |
| `fund_house` | TEXT | AMC name | - | HDFC Mutual Fund |
| `category` | TEXT | Category | - | Large Cap, Mid Cap |
| `plan` | TEXT | Plan type | - | Direct, Regular |
| `return_1yr_pct` | REAL | 1-year absolute return % | (NAV_end / NAV_start - 1) × 100 | 12.42, 15.25 |
| `return_3yr_pct` | REAL | 3-year CAGR % | ((NAV_end / NAV_start) ^ (1/3) - 1) × 100 | 12.36, 14.45 |
| `return_5yr_pct` | REAL | 5-year CAGR % | ((NAV_end / NAV_start) ^ (1/5) - 1) × 100 | 14.23, 20.67 |
| `benchmark_3yr_pct` | REAL | Benchmark 3yr return % | Same as scheme | 11.49, 9.52 |
| `alpha` | REAL | Excess return vs benchmark | return_3yr - benchmark_3yr | 0.87, 1.78 |
| `beta` | REAL | Market sensitivity | OLS regression slope | 0.89, 1.04 |
| `sharpe_ratio` | REAL | Risk-adjusted return | (Rp - Rf) / σp | 0.88, 1.52 |
| `sortino_ratio` | REAL | Downside risk-adjusted return | (Rp - Rf) / σdownside | 1.29, 2.11 |
| `std_dev_ann_pct` | REAL | Annualized standard deviation % | σ × √252 | 14.0, 25.0 |
| `max_drawdown_pct` | REAL | Worst peak-to-trough decline % | min(NAV / running_max - 1) | -21.7, -13.35 |
| `aum_crore` | REAL | AUM in Rs. crore | Scheme-level AUM | 14288, 36061 |
| `expense_ratio_pct` | REAL | Annual expense ratio % | From fund master | 1.54, 0.66 |
| `morningstar_rating` | INTEGER | 1-5 star rating | Based on Sharpe | 4, 5 |
| `risk_grade` | TEXT | SEBI risk category | From fund master | Moderate, High, Very High |

**Business Rules:**
- Rf (risk-free rate) assumed at 6.5% (RBI repo rate proxy)
- Sharpe ratio > 1.0 considered good
- Alpha > 0 indicates outperformance
- Beta < 1.0 = less volatile than market; > 1.0 = more volatile

---

## 8. Investor Transactions (08_investor_transactions.csv / fact_transactions)

**Description:** Simulated SIP, Lumpsum, and Redemption transactions for 5,000 investors

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `investor_id` | TEXT | Unique investor ID | Generated | INV000001, INV005000 |
| `transaction_date` | DATE | Transaction date | Simulated | 2024-01-15 |
| `amfi_code` | TEXT | Foreign key to dim_fund | - | 125497, 119551 |
| `transaction_type` | TEXT | Transaction type | Enum | SIP, Lumpsum, Redemption |
| `amount_inr` | INTEGER | Transaction amount in Rs. | Simulated | 5000, 125000 |
| `state` | TEXT | Investor's state | Real distribution | Maharashtra, Karnataka |
| `city` | TEXT | City name | Real cities | Mumbai, Bangalore |
| `city_tier` | TEXT | City classification | AMFI T30/B30 | T30, B30 |
| `age_group` | TEXT | Age bracket | Enum | 18-25, 26-35, 36-45, 46-55, 56+ |
| `gender` | TEXT | Gender | Enum | Male, Female |
| `annual_income_lakh` | REAL | Annual income in Rs. lakh | Simulated | 12.5, 85.0 |
| `payment_mode` | TEXT | Payment method | Enum | UPI, Net Banking, Mandate, Cheque |
| `kyc_status` | TEXT | KYC verification status | Enum | Verified, Pending |

**Business Rules:**
- T30 = Top 30 cities (metropolitan)
- B30 = Beyond Top 30 cities (smaller cities/towns)
- ~92% transactions have KYC status = Verified
- SIP amounts typically Rs. 500 - Rs. 50,000
- Lumpsum amounts typically Rs. 10,000 - Rs. 10,00,000

**Data Volume:**
- ~32,778 transactions
- Date range: 2024-01-01 to 2025-12-31

---

## 9. Portfolio Holdings (09_portfolio_holdings.csv / fact_portfolio)

**Description:** Top equity holdings for equity mutual funds as of Dec 2025

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `amfi_code` | TEXT | Foreign key to dim_fund | - | 125497, 119551 |
| `stock_symbol` | TEXT | Stock ticker symbol | NSE/BSE | RELIANCE, TCS, HDFCBANK |
| `stock_name` | TEXT | Company name | NSE/BSE | Reliance Industries, TCS |
| `sector` | TEXT | Industry sector | BSE classification | IT, Banking, Energy |
| `weight_pct` | REAL | Portfolio weight % | Scheme factsheets | 8.5, 5.2 |
| `holding_date` | DATE | As-of date | Scheme factsheets | 2025-12-31 |
| `market_cap_category` | TEXT | Market cap size | Classification | Large Cap, Mid Cap |
| `quantity` | INTEGER | Number of shares held | Scheme factsheets | 1000000 |

**Business Rules:**
- Top 10 holdings per fund disclosed
- Weight = (Market value of holding / Total portfolio value) × 100
- SEBI mandates 80% in declared market cap category

---

## 10. Benchmark Indices (10_benchmark_indices.csv / fact_benchmark)

**Description:** Daily closing values for major Indian indices (2022-2026)

| Column | Type | Description | Source | Sample Values |
|--------|------|-------------|--------|---------------|
| `index_name` | TEXT | Index identifier | NSE/BSE | Nifty 50, Nifty 100, BSE SmallCap |
| `date` | DATE | Trading date | NSE/BSE | 2024-01-15 |
| `close_value` | REAL | Index closing value | NSE/BSE | 21453.50, 58250.75 |

**Available Indices:**
- Nifty 50 (benchmark for Large Cap)
- Nifty 100
- Nifty Midcap 150
- BSE SmallCap
- CRISIL Liquid Fund Index
- CRISIL 10-Year Gilt Index

---

## Data Lineage

```
Raw Data (CSVs)
    ↓
Data Cleaning (data_cleaning.py)
    ↓
Cleaned Data (data/processed/)
    ↓
SQLite Database (bluestock_mf.db)
    ↓
Analytics / Dashboard
```

---

## Units Reference

| Term | Unit | Example |
|------|------|---------|
| Crore | 10 million | 1 crore = 1,00,00,000 |
| Lakh | 100 thousand | 1 lakh = 1,00,000 |
| Lakh Crore | 1 trillion | 1 lakh crore = 1,00,000 crore |

**Example:** Rs. 12.50 lakh crore = Rs. 12,50,000 crore = Rs. 12.5 trillion

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-25 | 1.0 | Initial data dictionary created for Day 2 |

---

**Document Owner:** Bluestock Fintech Data Team  
**Contact:** data@bluestockfintech.com  
**License:** Internal use only — Educational project
