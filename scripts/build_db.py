#!/usr/bin/env python3
"""Build a SQLite database from the collusion.wiki JSONL exports.

    uv run scripts/build_db.py

Produces data/collusion-wiki.db with tables `pages`, `revisions`, `events`,
`labels` and a `revision_details` view. Every column arrives from the JSONL as a
string; integer-ish and boolean-ish columns are coerced so that numeric
comparisons in the analysis scripts behave.

This reproduces the schema the analyses depend on. It is not a byte-identical
rebuild of the researchers' own SQLite artifact, which carries extra derived
tables (page_profiles, revision_fts, manifest_*) not needed here.
"""

from __future__ import annotations

import contextlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SOURCES = {
    "pages": "pages.jsonl",
    "revisions": "revisions.jsonl",
    "events": "events.jsonl",
    "labels": "labels.jsonl",
}

INT_COLS = {
    "seq",
    "body_len",
    "lines",
    "n_revs",
    "n_revs_before",
    "body_bytes",
    "n_deletions",
    "n_recreations",
    "n_labels",
    "n_ips",
    "n_ip16",
    "uncertainty_seconds",
}
BOOL_COLS = {"deleted_live", "head_differs_from_live", "success_observed"}


def coerce(col: str, val):
    if val is None or val == "None":
        return None
    if col in INT_COLS:
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
    if col in BOOL_COLS:
        return 1 if str(val) in ("True", "true", "1") else 0
    if isinstance(val, (list, dict)):
        # e.g. revisions.hunks, pages.labels, events.source_refs
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (str, int, float)):
        return val
    return str(val)


def load(path: Path) -> tuple[list[str], list[dict]]:
    rows = []
    cols: list[str] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append(obj)
            for k in obj:
                if k not in seen:
                    seen.add(k)
                    cols.append(k)
    return cols, rows


def build(db_path: Path, data_dir: Path = DATA) -> None:
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    for table, filename in SOURCES.items():
        src = data_dir / filename
        if not src.exists():
            print(f"  skip   {table:10} ({filename} not present)")
            continue
        cols, rows = load(src)
        quoted = ", ".join('"' + c.replace('"', '""') + '"' for c in cols)
        cur.execute(f"CREATE TABLE {table} ({quoted})")
        placeholders = ",".join("?" * len(cols))
        cur.executemany(
            f"INSERT INTO {table} VALUES ({placeholders})",
            [[coerce(c, r.get(c)) for c in cols] for r in rows],
        )
        print(f"  loaded {table:10} {len(rows):>6,} rows")

    # The analyses query `revision_details`; in the upstream artifact it is a
    # join, but revisions.jsonl is already flat, so a view suffices.
    cur.execute("""
        CREATE VIEW revision_details AS
        SELECT rev_id, page_key, wiki, name, seq, label, ip16, time, time_grade,
               change_summary, request_action, body, body_len, body_sha256
        FROM revisions
    """)

    for stmt in (
        "CREATE INDEX revisions_time  ON revisions(time)",
        "CREATE INDEX revisions_label ON revisions(label)",
        "CREATE INDEX revisions_page  ON revisions(page_key)",
        "CREATE INDEX revisions_wiki  ON revisions(wiki, name)",
        "CREATE INDEX pages_wiki      ON pages(wiki, name)",
        "CREATE INDEX events_time     ON events(time)",
    ):
        # An index is skipped when its source table was not present.
        with contextlib.suppress(sqlite3.OperationalError):
            cur.execute(stmt)

    # Convenience table used by the ASN / fingerprint analysis. The upstream
    # artifact's ip16_prefixes covers BOTH revision writes and the probe/request
    # event log, so union them — revisions alone yields 191 of the 198 prefixes.
    cur.execute("""
        CREATE TABLE ip16_prefixes AS
        SELECT DISTINCT ip16 FROM (
            SELECT ip16 FROM revisions WHERE ip16 IS NOT NULL AND ip16 <> ''
            UNION
            SELECT ip16 FROM events    WHERE ip16 IS NOT NULL AND ip16 <> ''
        )
    """)

    con.commit()
    n_rev = cur.execute("SELECT count(*) FROM revisions").fetchone()[0]
    n_ip = cur.execute("SELECT count(*) FROM ip16_prefixes").fetchone()[0]
    con.close()
    print(f"\n  wrote {db_path}  ({db_path.stat().st_size:,} bytes)")
    print(f"  revisions={n_rev:,}  distinct /16 prefixes={n_ip}")


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    missing = [f for f in SOURCES.values() if not (DATA / f).exists()]
    if len(missing) == len(SOURCES):
        print("No JSONL files found. Run: uv run scripts/fetch_dataset.py", file=sys.stderr)
        raise SystemExit(1)
    build(DATA / "collusion-wiki.db")
