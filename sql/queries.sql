
-- 1. Top 5 funds by AUM
SELECT fund_house, MAX(aum_crore) AS max_aum
FROM fact_aum
GROUP BY fund_house
ORDER BY max_aum DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT 
    strftime('%Y-%m', date) AS month,
    amfi_code,
    AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY month, amfi_code
ORDER BY month;

-- 3. SIP YoY growth
SELECT 
    month,
    sip_inflow_crore,
    yoy_growth_pct
FROM fact_sip_industry
ORDER BY month;

-- 4. Transactions by state
SELECT 
    state,
    COUNT(*) AS total_transactions,
    SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense ratio less than 1%
SELECT 
    scheme_name,
    fund_house,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct;

-- 6. Top 5 funds by 3-year return
SELECT 
    f.scheme_name,
    p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f
ON p.amfi_code = f.amfi_code
ORDER BY p.return_3yr_pct DESC
LIMIT 5;

-- 7. Funds with negative Sharpe ratio
SELECT 
    f.scheme_name,
    p.sharpe_ratio
FROM fact_performance p
JOIN dim_fund f
ON p.amfi_code = f.amfi_code
WHERE p.sharpe_ratio < 0;

-- 8. Total amount by transaction type
SELECT 
    transaction_type,
    SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY transaction_type;

-- 9. Category-wise number of funds
SELECT 
    category,
    COUNT(*) AS total_funds
FROM dim_fund
GROUP BY category;

-- 10. Average NAV by fund
SELECT 
    amfi_code,
    AVG(nav) AS average_nav
FROM fact_nav
GROUP BY amfi_code
ORDER BY average_nav DESC;
