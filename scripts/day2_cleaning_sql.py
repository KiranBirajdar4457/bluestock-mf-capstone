import pandas as pd
import sqlite3
from sqlalchemy import create_engine
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
SQL = Path("sql")
REPORTS = Path("reports")

PROCESSED.mkdir(parents=True, exist_ok=True)
SQL.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# =========================
# 1. LOAD DATASETS
# =========================

fund_master = pd.read_csv(RAW / "01_fund_master.csv")
nav_history = pd.read_csv(RAW / "02_nav_history.csv")
aum = pd.read_csv(RAW / "03_aum_by_fund_house.csv")
sip = pd.read_csv(RAW / "04_monthly_sip_inflows.csv")
category = pd.read_csv(RAW / "05_category_inflows.csv")
folio = pd.read_csv(RAW / "06_industry_folio_count.csv")
performance = pd.read_csv(RAW / "07_scheme_performance.csv")
transactions = pd.read_csv(RAW / "08_investor_transactions.csv")
holdings = pd.read_csv(RAW / "09_portfolio_holdings.csv")
benchmark = pd.read_csv(RAW / "10_benchmark_indices.csv")

# =========================
# 2. CLEAN NAV HISTORY
# =========================

nav_history["date"] = pd.to_datetime(nav_history["date"], errors="coerce")
nav_history["nav"] = pd.to_numeric(nav_history["nav"], errors="coerce")

nav_history = nav_history.drop_duplicates()
nav_history = nav_history.sort_values(["amfi_code", "date"])
nav_history["nav"] = nav_history.groupby("amfi_code")["nav"].ffill()
nav_history = nav_history[nav_history["nav"] > 0]

# daily return
nav_history["daily_return"] = nav_history.groupby("amfi_code")["nav"].pct_change()

# =========================
# 3. CLEAN INVESTOR TRANSACTIONS
# =========================

transactions["transaction_date"] = pd.to_datetime(
    transactions["transaction_date"],
    errors="coerce"
)

transactions["amount_inr"] = pd.to_numeric(
    transactions["amount_inr"],
    errors="coerce"
)

transactions["transaction_type"] = (
    transactions["transaction_type"]
    .astype(str)
    .str.strip()
    .str.title()
)

type_mapping = {
    "Sip": "SIP",
    "Lumpsum": "Lumpsum",
    "Redemption": "Redemption"
}

transactions["transaction_type"] = transactions["transaction_type"].replace(type_mapping)

valid_types = ["SIP", "Lumpsum", "Redemption"]
transactions = transactions[transactions["transaction_type"].isin(valid_types)]
transactions = transactions[transactions["amount_inr"] > 0]

transactions["kyc_status"] = (
    transactions["kyc_status"]
    .astype(str)
    .str.strip()
    .str.title()
)

valid_kyc = ["Verified", "Pending"]
transactions = transactions[transactions["kyc_status"].isin(valid_kyc)]

transactions = transactions.drop_duplicates()

# =========================
# 4. CLEAN SCHEME PERFORMANCE
# =========================

numeric_cols = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "benchmark_3yr_pct",
    "alpha",
    "beta",
    "sharpe_ratio",
    "sortino_ratio",
    "std_dev_ann_pct",
    "max_drawdown_pct",
    "expense_ratio_pct"
]

for col in numeric_cols:
    if col in performance.columns:
        performance[col] = pd.to_numeric(performance[col], errors="coerce")

if "expense_ratio_pct" in performance.columns:
    performance["expense_ratio_flag"] = performance["expense_ratio_pct"].apply(
        lambda x: "OK" if 0.1 <= x <= 2.5 else "CHECK"
    )

if "sharpe_ratio" in performance.columns:
    performance["sharpe_flag"] = performance["sharpe_ratio"].apply(
        lambda x: "NEGATIVE" if x < 0 else "OK"
    )

performance = performance.drop_duplicates()

# =========================
# 5. CLEAN OTHER DATASETS
# =========================

fund_master = fund_master.drop_duplicates()
aum = aum.drop_duplicates()
sip = sip.drop_duplicates()
category = category.drop_duplicates()
folio = folio.drop_duplicates()
holdings = holdings.drop_duplicates()
benchmark = benchmark.drop_duplicates()

# date columns if available
for df in [aum, sip, category, folio, holdings, benchmark]:
    for col in df.columns:
        if "date" in col.lower() or "month" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="ignore")

# =========================
# 6. CREATE DIM DATE
# =========================

dim_date = pd.DataFrame({
    "date": pd.date_range(
        start=nav_history["date"].min(),
        end=nav_history["date"].max()
    )
})

dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["is_weekday"] = dim_date["date"].dt.weekday < 5

# =========================
# 7. SAVE CLEANED CSV FILES
# =========================

fund_master.to_csv(PROCESSED / "clean_fund_master.csv", index=False)
nav_history.to_csv(PROCESSED / "clean_nav_history.csv", index=False)
aum.to_csv(PROCESSED / "clean_aum_by_fund_house.csv", index=False)
sip.to_csv(PROCESSED / "clean_monthly_sip_inflows.csv", index=False)
category.to_csv(PROCESSED / "clean_category_inflows.csv", index=False)
folio.to_csv(PROCESSED / "clean_industry_folio_count.csv", index=False)
performance.to_csv(PROCESSED / "clean_scheme_performance.csv", index=False)
transactions.to_csv(PROCESSED / "clean_investor_transactions.csv", index=False)
holdings.to_csv(PROCESSED / "clean_portfolio_holdings.csv", index=False)
benchmark.to_csv(PROCESSED / "clean_benchmark_indices.csv", index=False)
dim_date.to_csv(PROCESSED / "dim_date.csv", index=False)

print("Cleaned CSV files saved successfully.")

# =========================
# 8. CREATE SQLITE DATABASE
# =========================

engine = create_engine("sqlite:///data/processed/bluestock_mf.db")

fund_master.to_sql("dim_fund", engine, if_exists="replace", index=False)
dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
nav_history.to_sql("fact_nav", engine, if_exists="replace", index=False)
transactions.to_sql("fact_transactions", engine, if_exists="replace", index=False)
performance.to_sql("fact_performance", engine, if_exists="replace", index=False)
aum.to_sql("fact_aum", engine, if_exists="replace", index=False)
sip.to_sql("fact_sip_industry", engine, if_exists="replace", index=False)
category.to_sql("fact_category_inflows", engine, if_exists="replace", index=False)
folio.to_sql("fact_folio_count", engine, if_exists="replace", index=False)
holdings.to_sql("fact_portfolio", engine, if_exists="replace", index=False)
benchmark.to_sql("fact_benchmark_indices", engine, if_exists="replace", index=False)

print("SQLite database created successfully.")

# =========================
# 9. VERIFY ROW COUNTS
# =========================

tables = [
    "dim_fund",
    "dim_date",
    "fact_nav",
    "fact_transactions",
    "fact_performance",
    "fact_aum",
    "fact_sip_industry",
    "fact_category_inflows",
    "fact_folio_count",
    "fact_portfolio",
    "fact_benchmark_indices"
]

conn = sqlite3.connect("data/processed/bluestock_mf.db")

print("\nRow Counts:")
for table in tables:
    count = pd.read_sql(f"SELECT COUNT(*) AS count FROM {table}", conn)
    print(table, ":", count["count"][0])

conn.close()

# =========================
# 10. CREATE SCHEMA.SQL
# =========================

schema_sql = """
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT,
    scheme_name TEXT,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date DATE,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    fund_manager TEXT,
    risk_category TEXT
);

CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY,
    date DATE,
    year INTEGER,
    month INTEGER,
    month_name TEXT,
    quarter INTEGER,
    is_weekday BOOLEAN
);

CREATE TABLE fact_nav (
    amfi_code INTEGER,
    date DATE,
    nav REAL,
    daily_return REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_transactions (
    investor_id TEXT,
    transaction_date DATE,
    amfi_code INTEGER,
    transaction_type TEXT,
    amount_inr REAL,
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

CREATE TABLE fact_performance (
    amfi_code INTEGER,
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
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    fund_house TEXT,
    date DATE,
    aum_crore REAL,
    num_schemes INTEGER
);
"""

with open(SQL / "schema.sql", "w") as f:
    f.write(schema_sql)

print("schema.sql created.")

# =========================
# 11. CREATE QUERIES.SQL
# =========================

queries_sql = """
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
"""

with open(SQL / "queries.sql", "w") as f:
    f.write(queries_sql)

print("queries.sql created.")

# =========================
# 12. CREATE DATA DICTIONARY
# =========================

data_dictionary = """
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
"""

with open(REPORTS / "data_dictionary.md", "w") as f:
    f.write(data_dictionary)

print("data_dictionary.md created.")

print("\nDay 2 completed successfully.")