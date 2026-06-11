import sqlite3
import pandas as pd

conn = sqlite3.connect("data/processed/bluestock_mf.db")

query = """
SELECT name 
FROM sqlite_master 
WHERE type='table';
"""

tables = pd.read_sql(query, conn)
print(tables)

conn.close()