#!/usr/bin/env python3
"""Regenerate the incident timeline from the database.

Backs the timeline table in docs/OBFUSCATION-CATALOG.md §0. Every figure there
comes from these queries, so a reader can confirm the narrative shape rather than
take it on trust.

    uv run scripts/timeline.py            # daily volume + milestones
    uv run scripts/timeline.py --md       # emit the markdown table rows
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "collusion-wiki.db"

# Milestones, each pinned to a query so the claim and its evidence travel together.
MILESTONES: list[tuple[str, str]] = [
    ("first probe event (recon, no writes yet)", "SELECT min(time) FROM events WHERE event_type='probe'"),
    ("first wiki write", "SELECT min(time) FROM revisions"),
    (
        "Microlink function= POST smuggling (earliest bypass)",
        "SELECT min(time)||' .. '||max(time)||'  n='||count(*) FROM revisions "
        "WHERE body LIKE '%microlink%' AND body LIKE '%function=%'",
    ),
    (
        "first / last httpbin.org/base64 payload",
        "SELECT min(time)||' .. '||max(time) FROM revisions WHERE body LIKE '%httpbin.org/base64%'",
    ),
    (
        "counter-channel failover burst",
        "SELECT min(time)||' .. '||max(time)||'  n='||count(*) FROM revisions "
        "WHERE body LIKE '%mileshilliard%'",
    ),
    (
        "LoopNextWord runaway (not a linked list — see catalog §3)",
        "SELECT min(rd.time)||' .. '||max(rd.time)||'  n='||count(*) "
        "FROM revision_details rd JOIN pages p USING(page_key) WHERE p.name LIKE 'LoopNextWord%'",
    ),
    (
        "blob / NO_PROXY Host-header bypass",
        "SELECT min(time)||' .. '||max(time)||'  n='||count(*) FROM revisions "
        "WHERE body LIKE '%blob.core.windows%'",
    ),
    ("ZZZ* deletion-survival pages", "SELECT count(*) FROM pages WHERE name LIKE 'ZZZ%'"),
    (
        "moderator deletions",
        "SELECT min(time)||' .. '||max(time)||'  n='||count(*) FROM events WHERE event_type='delete'",
    ),
    (
        "last write / last log event",
        "SELECT (SELECT max(time) FROM revisions)||'  /  '||(SELECT max(time) FROM events)",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true", help="emit markdown table rows")
    args = ap.parse_args()

    if not DB.exists():
        print(f"Database not found at {DB}\nRun: uv run scripts/fetch_dataset.py --db")
        return 1
    con = sqlite3.connect(DB)

    days = con.execute(
        "SELECT substr(time,1,10) d, count(*) n FROM revisions GROUP BY d ORDER BY d"
    ).fetchall()
    total = sum(n for _, n in days)

    if args.md:
        for d, n in days:
            print(f"| {d[5:]} | {n:,} | |")
        return 0

    print(f"DAILY WRITE VOLUME  ({total:,} saves over {len(days)} active days)\n")
    peak = max(n for _, n in days)
    for d, n in days:
        bar = "#" * max(1, round(48 * n / peak))
        print(f"  {d}  {n:>6,}  {bar}")

    # The corpus is dominated by a four-day burst; state it numerically.
    burst = [n for d, n in days if "2026-06-16" <= d <= "2026-06-19"]
    print(f"\n  2026-06-16 -> 06-19: {sum(burst):,} saves = {100 * sum(burst) / total:.0f}% of the corpus")
    top_d, top_n = max(days, key=lambda kv: kv[1])
    print(f"  peak day {top_d}: {top_n:,} = {100 * top_n / total:.0f}%")

    print("\n\nMILESTONES\n")
    for label, sql in MILESTONES:
        try:
            val = con.execute(sql).fetchone()[0]
        except sqlite3.Error as exc:
            val = f"<query failed: {exc}>"
        print(f"  {label}\n      {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
