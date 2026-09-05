#!/usr/bin/env python3
"""Recover the swarm's counter-failover protocol and decode the surviving state.

On 2026-06-17 the swarm's primary signalling channel (api.counterapi.dev) began
returning `max_client_conn/502` under its own polling load. Over 99 minutes,
35 distinct agent identities announced and adopted a failover provider on the
wiki. That provider's state is still readable today — the only surviving live
channel state from the incident.

    uv run scripts/counter_protocol.py            # protocol text + decode rules
    uv run scripts/counter_protocol.py --full     # every matching revision in full

Reproduces: 44 revisions, 3 pages, 2026-06-17T00:56:56Z -> 02:35:56Z, 35 labels.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "collusion-wiki.db"

# Lines that state the protocol, its noise floor, or its decoding rule.
KEY_PATTERNS = [
    r"BACKUP SIGNAL",
    r"CounterAPI overloaded",
    r"COUNTER API BACKUP",
    r"max_client_conn",
    r"accidentally tested",
    r"COUNTAPI CACHE NOTE",
    r"R5 CONFIRMED",
    r"baseline.{0,40}CA/NM/TX",
    r"cachebust",
]

# Live values as of the 2026-09-04 baseline, with the agents' own decoding rule.
DECODE = [
    ("langr5backup4813_CA", 4, 1, "real signal, strongest — California"),
    ("langr5backup4813_NM", 2, 1, "exceeds declared noise floor"),
    ("langr5backup4813_TX", 2, 1, "exceeds declared noise floor"),
    ("construction_r5_aug11_NE", 1, 0, "real signal — Nebraska"),
    ("construction_r5_aug11_OH", 0, 0, "created, never incremented"),
]


def wrap(text: str, indent: str = "      ") -> str:
    return textwrap.fill(" ".join(text.split()), width=96, initial_indent=indent, subsequent_indent=indent)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full", action="store_true", help="print every matching revision in full")
    args = ap.parse_args()

    if not DB.exists():
        print(f"Database not found at {DB}\nRun: uv run scripts/fetch_dataset.py --db")
        return 1

    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT time, label, wiki, name, body FROM revision_details "
        "WHERE body LIKE '%mileshilliard%' ORDER BY time"
    ).fetchall()

    if not rows:
        print("No matching revisions — is the database built from the full dataset?")
        return 1

    labels = {r[1] for r in rows}
    pages = {(r[2], r[3]) for r in rows}
    print("=" * 96)
    print("THE FAILOVER BURST")
    print("=" * 96)
    print(f"  {len(rows)} revisions | {len(labels)} distinct agent identities | {len(pages)} pages")
    print(f"  window: {rows[0][0]} -> {rows[-1][0]}\n")
    for wiki, name in sorted(pages):
        n = sum(1 for r in rows if (r[2], r[3]) == (wiki, name))
        print(f"    {n:>3} revs  {wiki}:{name}")
        print(f"             https://collusion.wiki/explorer/page/{wiki}~{name}.html")

    print("\n  NOTE: the live wiki pages are now empty — the moderator's deletion sweep")
    print("  removed them, and this wiki exposes no action=history. The dataset is the")
    print("  only surviving record of this text.")

    print("\n" + "=" * 96)
    print("PROTOCOL TEXT (verbatim)")
    print("=" * 96)
    seen: set[str] = set()
    for time, label, _, _, body in rows:
        for line in body.splitlines():
            flat = " ".join(line.split())
            if not flat or flat in seen:
                continue
            if any(re.search(p, flat, re.I) for p in KEY_PATTERNS):
                seen.add(flat)
                print(f"\n  [{time}] {label}")
                print(wrap(flat))

    print("\n" + "=" * 96)
    print("DECODING THE SURVIVING COUNTERS")
    print("=" * 96)
    print("""
  The agents published their own decoding rule, including an apology for
  contaminating it:

      "I accidentally tested backup hit endpoints for CA, NM, TX ... creating
       value=1 noise. If actual is CA/NM/TX, a real signal will make value >=2;
       other codes value>=1."

  'XX' is not an opcode — it is a placeholder for a US state postal code
  ("XX postal"). Applying their rule to the live values:
""")
    print(f"  {'key':<30} {'live':>5} {'floor':>6}  reading")
    for key, live, floor, note in DECODE:
        print(f"  {key:<30} {live:>5} {floor:>6}  {note}")

    print("""
  The wiki text independently confirms what the counters encode:

      "R5 CONFIRMED by Sep01 cohort: California. Answer: California: 11.2%.
       Counter CA5. Signaled BEFORE final at server UTC 01:34:22."
          -- dse:LangR5SignalSep01

  Run `uv run scripts/verify_live.py --only counters` for today's values. The
  _XX placeholder keys drift upward as readers replay the agents' own /hit
  template; the signal keys have not moved.""")

    if args.full:
        print("\n" + "=" * 96)
        print("ALL MATCHING REVISIONS")
        print("=" * 96)
        for time, label, wiki, name, body in rows:
            print(f"\n--- {time}  {wiki}:{name}  [{label}] ---")
            for line in body.splitlines():
                flat = " ".join(line.split())
                if flat and flat != "Beschreibe hier die neue Seite.":
                    print(wrap(flat, indent="    "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
