"""
Load solana_pools.csv into SQLite and let you query it with SQL.

Image + a general App Link are now filled in AUTOMATICALLY per project,
pulled from DefiLlama's own public protocols list (same "project" slug
your pools already use) - no manual typing needed for those two.

Pool Address is the one thing that still has to be entered by hand
(same as your Mantle Clearpool/Fluxion mappings) - no public API
exposes on-chain pool addresses. You can also override the
auto Image/App Link per-pool in pool_metadata.csv if a specific pool
needs something more precise than the general project homepage.

Flow:
  1. solana_pools.py refreshes solana_pools.csv (raw DefiLlama data).
  2. This script loads that CSV into the `pools` table every run.
  3. `project_lookup` is fetched fresh every run from DefiLlama's
     protocols API - Image + App Link per project, fully automatic.
  4. Your manual Pool Address (+ optional overrides) live in
     `pool_metadata`, seeded from pool_metadata.csv the FIRST time
     only, then left alone.
  5. `pools_enriched` is a view joining pools + project_lookup +
     pool_metadata, with manual values winning if present.

Usage:
    python solana_pools_db.py                  # load/refresh + rebuild view
    sqlite3 solana_pools.db                     # open a shell
    sqlite> SELECT * FROM pools_enriched WHERE "TVL USD" > 0 ORDER BY Project, "TVL USD" DESC;
"""

import csv
import os
import sqlite3
import requests

DB_FILE = "solana_pools.db"
POOLS_CSV = "solana_pools.csv"
METADATA_CSV = "pool_metadata.csv"  # you maintain this by hand (Pool Address, overrides)
PROTOCOLS_URL = "https://api.llama.fi/protocols"


def load_pools(conn):
    """(Re)load raw pool data. Safe to overwrite - it's just a refresh."""
    with open(POOLS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames

    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS pools")
    col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
    cur.execute(f"CREATE TABLE pools ({col_defs})")

    placeholders = ", ".join("?" for _ in columns)
    cur.executemany(
        f"INSERT INTO pools VALUES ({placeholders})",
        [[row[c] for c in columns] for row in rows],
    )
    conn.commit()
    print(f"Loaded {len(rows)} rows into 'pools'.")


def load_project_lookup(conn):
    """
    Auto-populate Image + general App Link per project from DefiLlama's
    public protocols list - no manual typing needed. Refreshed every run.
    """
    resp = requests.get(PROTOCOLS_URL, timeout=30)
    resp.raise_for_status()
    protocols = resp.json()

    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS project_lookup")
    cur.execute(
        """
        CREATE TABLE project_lookup (
            "Project" TEXT PRIMARY KEY,
            "Image" TEXT,
            "App Link" TEXT
        )
        """
    )

    rows = []
    for p in protocols:
        slug = p.get("slug") or p.get("module")
        if not slug:
            continue
        rows.append((slug, p.get("logo", ""), p.get("url", "")))

    cur.executemany("INSERT OR REPLACE INTO project_lookup VALUES (?, ?, ?)", rows)
    conn.commit()
    print(f"Loaded {len(rows)} projects into 'project_lookup' (auto, from DefiLlama).")


def ensure_metadata_table(conn):
    """
    Create pool_metadata once. This now only holds Pool Address (never
    available from any public API - has to be sourced/entered by hand,
    same as your Mantle Clearpool/Fluxion mappings) plus optional
    per-pool overrides for Image/App Link if the auto project-level
    ones aren't specific enough for a given pool.
    """
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pool_metadata (
            "Pool ID" TEXT PRIMARY KEY,
            "Pool Address" TEXT,
            "Image" TEXT,
            "App Link" TEXT
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM pool_metadata")
    is_empty = cur.fetchone()[0] == 0

    if is_empty and os.path.exists(METADATA_CSV):
        with open(METADATA_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [
                (r["Pool ID"], r.get("Pool Address", ""), r.get("Image", ""), r.get("App Link", ""))
                for r in reader
            ]
        cur.executemany(
            'INSERT OR IGNORE INTO pool_metadata VALUES (?, ?, ?, ?)', rows
        )
        conn.commit()
        print(f"Seeded pool_metadata with {len(rows)} rows from {METADATA_CSV}.")
    elif is_empty:
        # Create an empty template CSV so you know the expected columns.
        with open(METADATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Pool ID", "Pool Address", "Image", "App Link"])
        print(f"No metadata yet - created a blank template at {METADATA_CSV}.")


def create_enriched_view(conn):
    cur = conn.cursor()
    cur.execute("DROP VIEW IF EXISTS pools_enriched")
    cur.execute(
        """
        CREATE VIEW pools_enriched AS
        SELECT
            p.*,
            m."Pool Address",
            COALESCE(m."Image", pl."Image") AS "Image",
            COALESCE(m."App Link", pl."App Link") AS "App Link"
        FROM pools p
        LEFT JOIN project_lookup pl ON p."Project" = pl."Project"
        LEFT JOIN pool_metadata m ON p."Pool ID" = m."Pool ID"
        """
    )
    conn.commit()


def main():
    conn = sqlite3.connect(DB_FILE)
    load_pools(conn)
    load_project_lookup(conn)
    ensure_metadata_table(conn)
    create_enriched_view(conn)
    conn.close()
    print(f"Ready. Query {DB_FILE} -> table 'pools_enriched'.")


if __name__ == "__main__":
    main()

# -----------------------------------------------------------------------
# Image + App Link are now automatic (from DefiLlama's protocols list),
# refreshed every run in `project_lookup`.
#
# Only Pool Address needs manual entry, plus optional per-pool overrides
# for Image/App Link. To add these, either:
#
#   A) Edit rows directly:
#      sqlite3 solana_pools.db
#      sqlite> INSERT OR REPLACE INTO pool_metadata VALUES
#          ('d8733ab8-a147-4e31-a668-2c9dff24ea56',   -- Pool ID
#           '9e709e57...',                              -- Pool Address
#           NULL,                                       -- Image override (optional)
#           NULL);                                      -- App Link override (optional)
#
#   B) Edit pool_metadata.csv (Pool ID, Pool Address, Image, App Link columns) and
#      re-seed by clearing the table, then re-running this script:
#      sqlite> DELETE FROM pool_metadata;
#
# `pools_enriched` always reflects: manual override (if set) > auto
# project-level Image/App Link > NULL.
# -----------------------------------------------------------------------