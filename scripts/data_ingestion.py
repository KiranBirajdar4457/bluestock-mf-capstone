import pandas as pd

fund_master = pd.read_csv("data/raw/01_fund_master.csv")
nav_history = pd.read_csv("data/raw/02_nav_history.csv")

print(fund_master.shape)  # Shows number of rows and columns
print(nav_history.head())  # Shows first 5 rows


