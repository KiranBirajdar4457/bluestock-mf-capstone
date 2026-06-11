
# Data Dictionary

## dim_fund
Fund master table containing mutual fund details.

| Column | Definition |
|---|---|
| amfi_code | Unique AMFI scheme code |
| fund_house | Mutual fund company name |
| scheme_name | Full scheme name |
| category | Fund category |
| sub_category | Fund sub-category |
| plan | Direct or Regular plan |
| launch_date | Fund launch date |
| benchmark | Benchmark index |
| expense_ratio_pct | Expense ratio percentage |
| risk_category | SEBI risk level |

## fact_nav
Daily NAV data of mutual fund schemes.

| Column | Definition |
|---|---|
| amfi_code | Fund code |
| date | NAV date |
| nav | Net Asset Value |
| daily_return | Daily percentage return |

## fact_transactions
Investor transaction data.

| Column | Definition |
|---|---|
| investor_id | Unique investor ID |
| transaction_date | Date of transaction |
| transaction_type | SIP, Lumpsum, Redemption |
| amount_inr | Transaction amount |
| state | Investor state |
| city | Investor city |
| kyc_status | Verified or Pending |

## fact_performance
Fund performance metrics.

| Column | Definition |
|---|---|
| return_1yr_pct | One year return |
| return_3yr_pct | Three year return |
| return_5yr_pct | Five year return |
| alpha | Fund alpha |
| beta | Fund beta |
| sharpe_ratio | Risk adjusted return |
| max_drawdown_pct | Maximum drawdown |

## fact_aum
AUM data by fund house.

| Column | Definition |
|---|---|
| fund_house | Fund house name |
| date | Reporting date |
| aum_crore | Asset under management in crore |
| num_schemes | Number of schemes |
