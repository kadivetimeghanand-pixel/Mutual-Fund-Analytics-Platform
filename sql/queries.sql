-- ═══════════════════════════════════════════════════════════════════════════════
-- Bluestock MF Analytics — Analytical SQL Queries
-- 10 Business Intelligence Queries
-- ═══════════════════════════════════════════════════════════════════════════════

-- Query 1: Top 5 Funds by AUM
-- Shows the largest mutual funds by assets under management
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    aum_crore,
    ROUND(aum_crore / 100, 2) AS aum_lakh_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- Query 2: Average NAV per Month for Each Fund
-- Aggregates daily NAV to monthly averages
SELECT 
    amfi_code,
    strftime('%Y-%m', date) AS month,
    ROUND(AVG(nav), 2) AS avg_nav,
    COUNT(*) AS trading_days
FROM fact_nav
GROUP BY amfi_code, month
ORDER BY amfi_code, month;


-- Query 3: SIP Inflow Year-over-Year Growth
-- Shows monthly SIP trends with YoY comparison
SELECT 
    month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    yoy_growth_pct,
    CASE 
        WHEN yoy_growth_pct > 20 THEN 'Strong Growth'
        WHEN yoy_growth_pct > 10 THEN 'Moderate Growth'
        WHEN yoy_growth_pct > 0 THEN 'Slow Growth'
        ELSE 'Decline'
    END AS growth_category
FROM fact_sip_industry
ORDER BY month;


-- Query 4: Transactions by State
-- Geographic distribution of investor transactions
SELECT 
    state,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS total_amount_inr,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS total_amount_crore,
    AVG(amount_inr) AS avg_transaction_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- Query 5: Funds with Expense Ratio < 1%
-- Low-cost funds (typically Direct plans)
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    plan,
    expense_ratio_pct,
    return_3yr_pct,
    sharpe_ratio
FROM fact_performance
WHERE expense_ratio_pct < 1.0
ORDER BY sharpe_ratio DESC;


-- Query 6: Best Performing Funds by Category
-- Top fund in each category by 3-year returns
SELECT 
    category,
    scheme_name,
    fund_house,
    return_3yr_pct,
    sharpe_ratio,
    alpha
FROM (
    SELECT 
        category,
        scheme_name,
        fund_house,
        return_3yr_pct,
        sharpe_ratio,
        alpha,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY return_3yr_pct DESC) AS rank
    FROM fact_performance
    WHERE return_3yr_pct IS NOT NULL
)
WHERE rank = 1
ORDER BY return_3yr_pct DESC;


-- Query 7: Investor Demographics Analysis
-- Transaction patterns by age group and gender
SELECT 
    age_group,
    gender,
    COUNT(*) AS transaction_count,
    AVG(amount_inr) AS avg_amount,
    SUM(amount_inr) AS total_invested,
    COUNT(DISTINCT investor_id) AS unique_investors
FROM fact_transactions
WHERE transaction_type IN ('SIP', 'Lumpsum')
GROUP BY age_group, gender
ORDER BY total_invested DESC;


-- Query 8: Fund House Market Share by AUM
-- Shows dominance of top AMCs
SELECT 
    fund_house,
    SUM(aum_crore) AS total_aum_crore,
    ROUND(SUM(aum_crore) / 100, 2) AS total_aum_lakh_crore,
    COUNT(*) AS num_schemes,
    ROUND(AVG(expense_ratio_pct), 2) AS avg_expense_ratio,
    ROUND(AVG(sharpe_ratio), 2) AS avg_sharpe_ratio
FROM fact_performance
GROUP BY fund_house
ORDER BY total_aum_crore DESC;


-- Query 9: High Risk-Adjusted Return Funds
-- Funds with Sharpe Ratio > 1.0 and positive Alpha
SELECT 
    scheme_name,
    fund_house,
    category,
    return_3yr_pct,
    sharpe_ratio,
    alpha,
    beta,
    max_drawdown_pct,
    morningstar_rating
FROM fact_performance
WHERE sharpe_ratio > 1.0 
  AND alpha > 0
  AND return_3yr_pct IS NOT NULL
ORDER BY sharpe_ratio DESC
LIMIT 10;


-- Query 10: SIP vs Lumpsum Investment Analysis
-- Compares investment patterns
SELECT 
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount_inr) AS total_amount,
    ROUND(SUM(amount_inr) / 10000000.0, 2) AS total_crore,
    AVG(amount_inr) AS avg_amount,
    MIN(amount_inr) AS min_amount,
    MAX(amount_inr) AS max_amount,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_transactions), 2) AS pct_of_total
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount DESC;


-- Bonus Query 11: Monthly Net Inflows by Category
-- Shows which categories are attracting money
SELECT 
    strftime('%Y-%m', month) AS year_month,
    category,
    net_inflow_crore,
    SUM(net_inflow_crore) OVER (PARTITION BY category ORDER BY month) AS cumulative_inflow
FROM fact_category_inflows
ORDER BY year_month DESC, net_inflow_crore DESC;


-- Bonus Query 12: Top Portfolio Holdings Across All Funds
-- Identifies most popular stocks in MF portfolios
SELECT 
    stock_name,
    sector,
    COUNT(DISTINCT amfi_code) AS num_funds_holding,
    SUM(weight_pct) AS total_weight_across_funds,
    ROUND(AVG(weight_pct), 2) AS avg_weight_pct
FROM fact_portfolio
GROUP BY stock_name, sector
HAVING num_funds_holding >= 3
ORDER BY total_weight_across_funds DESC
LIMIT 20;
