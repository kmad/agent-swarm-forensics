#!/usr/bin/env python3
"""Fetch and verify the collusion.wiki research dataset.

Downloads the gzipped JSONL exports, expands them, and verifies each against the
SHA-256 checksums published by the original researchers (data/SHA256SUMS).

    uv run scripts/fetch_dataset.py           # fetch + verify
    uv run scripts/fetch_dataset.py --db      # also build the SQLite database
    uv run scripts/fetch_dataset.py --verify  # re-verify what is already on disk

Stdlib only, so it runs without a virtualenv.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

BASE = "https://collusion.wiki/explorer/download"
FILES = ["pages.jsonl", "revisions.jsonl", "events.jsonl", "labels.jsonl", "manifest.json"]

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = "agent-message-board-forensics/1.0 (research reproduction script)"


def expected_sums() -> dict[str, str]:
    sums = {}
    for line in (DATA / "SHA256SUMS").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, name = line.split(None, 1)
        sums[name.strip()] = digest
    return sums


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(name: str) -> None:
    """Download <name>.gz and expand it to data/<name>."""
    url = f"{BASE}/{name}.gz"
    gz_path = DATA / f"{name}.gz"
    out_path = DATA / name

    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp, gz_path.open("wb") as fh:
        shutil.copyfileobj(resp, fh)

    print(f"  expanding   {gz_path.name} -> {out_path.name}")
    with gzip.open(gz_path, "rb") as src, out_path.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    gz_path.unlink()


def verify(name: str, sums: dict[str, str]) -> bool:
    path = DATA / name
    if not path.exists():
        print(f"  MISSING  {name}")
        return False
    if name not in sums:
        print(f"  ?        {name} (no published checksum)")
        return True
    actual = sha256(path)
    if actual == sums[name]:
        print(f"  OK       {name}  ({path.stat().st_size:,} bytes)")
        return True
    print(f"  MISMATCH {name}\n           expected {sums[name]}\n           actual   {actual}")
    return False


def build_db() -> None:
    """Build the SQLite database from the JSONL exports."""
    from build_db import build  # local import; sibling script

    build(DATA / "collusion-wiki.db", DATA)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true", help="only verify files already on disk")
    ap.add_argument("--db", action="store_true", help="also build the SQLite database")
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    sums = expected_sums()

    if not args.verify:
        print("Fetching dataset from collusion.wiki ...")
        for name in FILES:
            if (DATA / name).exists():
                print(f"  present     {name} (skipping download)")
                continue
            download(name)

    print("\nVerifying checksums against the researchers' published SHA256SUMS ...")
    ok = all(verify(name, sums) for name in FILES)
    if not ok:
        print("\nFAILED: at least one file did not match. Delete it and re-run.", file=sys.stderr)
        return 1
    print("\nAll files verified.")

    if args.db:
        print("\nBuilding SQLite database ...")
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        build_db()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
