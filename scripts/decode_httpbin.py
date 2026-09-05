#!/usr/bin/env python3
"""Extract and decode every httpbin.org/base64 payload the swarm published.

`GET httpbin.org/base64/<b64>` decodes the path segment and returns it with
`Content-Type: text/html` and `Access-Control-Allow-Origin: *`. For a sandbox
that could issue GET but not POST, that makes the URL itself the storage — a
write primitive, and an executable payload host.

    uv run scripts/decode_httpbin.py            # decode from the local database
    uv run scripts/decode_httpbin.py --live     # also re-fetch each payload

Reproduces: 7 distinct payloads across 17 revisions on 5 pages, 2026-05-27 -> 06-18.
"""

from __future__ import annotations

import argparse
import base64
import re
import sqlite3
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "collusion-wiki.db"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

PAYLOAD_RE = re.compile(r"https?://[a-z.]*httpbin\.org/base64/([A-Za-z0-9%_=-]+)")

CLASSES = {
    "Hello": "capability probe",
    '{"Hello"': "capability probe (also chained through markdown.new)",
    "<a href": 'pointer — the agents labelled this "Payload API reference"',
    "<html><body><h1>HELLOJS": "XSS payload — executes, served as text/html",
}


def decode(payload: str) -> str:
    s = urllib.parse.unquote(payload).replace("-", "+").replace("_", "/")
    s += "=" * (-len(s) % 4)
    try:
        return base64.b64decode(s).decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return f"<decode error: {exc}>"


def classify(decoded: str) -> str:
    for prefix, label in CLASSES.items():
        if decoded.startswith(prefix):
            return label
    if decoded.lstrip().startswith("["):
        return "task answer set — Massachusetts Reg-CF county data"
    return "unclassified"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="re-fetch each payload from httpbin")
    args = ap.parse_args()

    if not DB.exists():
        print(f"Database not found at {DB}\nRun: uv run scripts/fetch_dataset.py --db")
        return 1

    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT time, label, wiki, name, body FROM revision_details "
        "WHERE body LIKE '%httpbin.org/base64%' ORDER BY time"
    ).fetchall()

    occurrences: dict[str, list[tuple]] = defaultdict(list)
    for time, label, wiki, name, body in rows:
        for payload in set(PAYLOAD_RE.findall(body)):
            occurrences[payload].append((time, label, wiki, name))

    pages = {(w, n) for lst in occurrences.values() for _, _, w, n in lst}
    print(f"{len(rows)} revisions  |  {len(occurrences)} distinct payloads  |  {len(pages)} pages")
    print(f"window: {rows[0][0]} -> {rows[-1][0]}\n")

    for i, (payload, where) in enumerate(sorted(occurrences.items(), key=lambda kv: len(kv[0])), 1):
        decoded = decode(payload)
        url = f"https://httpbin.org/base64/{payload}"
        print(f"[{i}] {classify(decoded)}")
        print(f"    {url if len(url) <= 118 else url[:115] + '...'}")
        preview = " ".join(decoded.split())
        print(f"    decodes: {preview[:200]}{'...' if len(preview) > 200 else ''}")
        for time, label, wiki, name in sorted(set(where))[:3]:
            print(f"    seen:    {time}  {wiki}:{name}  by {label}")
        if len(set(where)) > 3:
            print(f"             ...and {len(set(where)) - 3} more revisions")
        for wiki, name in sorted({(w, n) for _, _, w, n in where}):
            print(f"    explorer: https://collusion.wiki/explorer/page/{wiki}~{name}.html")
        if args.live:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    body = r.read().decode("utf-8", "replace")
                    match = "byte-identical" if body == decoded else "DIFFERS from decode"
                    print(f"    live:    HTTP {r.status}  {r.headers.get('Content-Type')}  {match}")
            except Exception as exc:  # noqa: BLE001
                print(f"    live:    <{type(exc).__name__}: {exc}>")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
