"""
Fetch Solana yield pools from DefiLlama and save to CSV.

Run manually:
    python solana_pools.py

Or schedule it to refresh automatically (see notes at the bottom of this file).
"""

import csv
import requests
from datetime import datetime, timezone

URL = "https://yields.llama.fi/pools"
OUTPUT_FILE = "solana_pools.csv"

COLUMNS = [
    "Project",
    "Symbol",
    "APY",
    "APY Base",
    "APY Reward",
    "Reward Tokens",
    "Pool ID",
    "APY % 1D",
    "APY % 7D",
    "APY % 30D",
    "Stablecoin",
    "APY Base 7D",
    "TVL USD",
    "Underlying Tokens",
]


def get_solana_pools():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    pools = response.json().get("data", [])

    rows = []
    for pool in pools:
        if pool.get("chain") == "Solana":
            rows.append({
                "Project": pool.get("project", ""),
                "Symbol": pool.get("symbol", ""),
                "APY": pool.get("apy", 0) or 0,
                "APY Base": pool.get("apyBase", 0) or 0,
                "APY Reward": pool.get("apyReward", 0) or 0,
                "Reward Tokens": ", ".join(pool.get("rewardTokens") or []),
                "Pool ID": pool.get("pool", ""),
                "APY % 1D": pool.get("apyPct1D", 0) or 0,
                "APY % 7D": pool.get("apyPct7D", 0) or 0,
                "APY % 30D": pool.get("apyPct30D", 0) or 0,
                "Stablecoin": pool.get("stablecoin", False),
                "APY Base 7D": pool.get("apyBase7d", 0) or 0,
                "TVL USD": pool.get("tvlUsd", 0) or 0,
                "Underlying Tokens": ", ".join(pool.get("underlyingTokens") or []),
            })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[{datetime.now(timezone.utc).isoformat()}] "
          f"Wrote {len(rows)} Solana pools to {OUTPUT_FILE}")


if __name__ == "__main__":
    get_solana_pools()

# -----------------------------------------------------------------------
# Automating the refresh (pick one):
#
# 1) Windows Task Scheduler (simplest, no cloud needed):
#    - Create a Basic Task -> Trigger: Daily / hourly -> Action: Start a program
#    - Program: path to python.exe, Arguments: full path to this script
#
# 2) GitHub Actions (if you want the CSV hosted/versioned in a repo,
#    matches the automation pattern you already use for other pipelines):
#    - Put this script in a repo, add a workflow with a `schedule: cron`
#      trigger, run the script, then commit the updated CSV back
#      (or upload it as an artifact) each run.
# -----------------------------------------------------------------------