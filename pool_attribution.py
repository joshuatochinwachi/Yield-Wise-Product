import sqlite3
import pandas as pd

conn = sqlite3.connect("solana_pools.db")

query = """
SELECT
    Project AS Protocol,
    "Pool Address",
    Symbol AS Asset,
    APY,
    "APY Base" AS "Base APY",
    "APY Reward" AS "Reward APY",
    "TVL USD" AS "TVL ($)",
    "Reward Tokens",
    "APY % 1D" AS "APY (1D)",
    "APY % 7D" AS "APY (7D)",
    "APY % 30D" AS "APY (30D)",
    Image,
    "App Link"
FROM pools_enriched
"""

df = pd.read_sql_query(query, conn)
print(df.to_string(index=False))

conn.close()