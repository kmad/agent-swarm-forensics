#!/usr/bin/env python3
"""Attribute the swarm's /16 egress prefixes to their owning networks.

The dataset ships 198 distinct /16 prefixes. Old CGI wikis print each anonymous
editor's IP straight into RecentChanges, so these prefixes are a fingerprint —
but a weak one. This script resolves each to its origin ASN via Team Cymru's
DNS service and shows why matching on ASN beats matching on a prefix list.

    uv run scripts/asn_attribute.py            # resolve all prefixes (DNS, ~1 min)
    uv run scripts/asn_attribute.py --extra    # also resolve the known gaps

Requires `dig` (bind-tools / dnsutils).
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "collusion-wiki.db"

ASN_NAMES = {
    "8075": "Microsoft / Azure",
    "16509": "Amazon AWS",
    "14618": "Amazon AWS (EC2 2nd ASN)",
    "14061": "DigitalOcean",
    "13335": "Cloudflare",
    "15169": "Google",
    "396982": "Google Cloud",
    "9808": "China Mobile",
    "22773": "Cox (residential)",
    "9009": "M247",
    "7684": "SAKURA Internet",
    "3209": "Vodafone DE",
    "6181": "Frontier",
    "3301": "Telia",
    "60729": "Tor exit (Zwiebelfreunde)",
}
CLOUD = {"8075", "16509", "14618", "14061", "15169", "396982"}

# Prefixes observed on publictestwiki.com that are ABSENT from the dataset's
# ip16_prefixes — evidence the list is an observation record, not an inventory.
KNOWN_GAPS = ["3.212", "44.220", "104.131", "174.138", "52.228"]

# Agent-operated endpoints, with the egress IP embedded in the tunnel hostname.
# These are kept as full addresses while the docs truncate everything to /16: they
# are the swarm's OWN infrastructure, not a third party's, they are already
# published verbatim in the collusion.wiki writeup (the pinggy hostname encodes
# the IP), and the lookup needs a host address to resolve.
AGENT_ENDPOINTS = {
    "16.146.184.55": "pinggy tunnels (4 distinct, one sandbox)",
    "35.95.198.152": "serveo tunnel",
    "34.107.161.1": "raw-IP data endpoint",
}


def cymru(ip: str) -> tuple[str, str]:
    """Resolve an IP to (asn, country) via Team Cymru's DNS origin service."""
    rev = ".".join(reversed(ip.split(".")))
    try:
        out = (
            subprocess.run(
                ["dig", "+short", "+time=3", "+tries=1", "TXT", f"{rev}.origin.asn.cymru.com"],
                capture_output=True,
                text=True,
                timeout=12,
            )
            .stdout.strip()
            .strip('"')
        )
    except (subprocess.SubprocessError, OSError):
        return "UNKNOWN", "-"
    if not out:
        return "UNKNOWN", "-"
    parts = [p.strip() for p in out.split("|")]
    return (parts[0] if parts else "UNKNOWN", parts[2] if len(parts) > 2 else "-")


def resolve_prefix(prefix: str) -> tuple[str, str, str]:
    """A /16 has no single IP; try a few host addresses until one is announced."""
    for last in (1, 100, 200):
        asn, cc = cymru(f"{prefix}.0.{last}")
        if asn != "UNKNOWN":
            return prefix, asn, cc
    return prefix, "UNKNOWN", "-"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--extra", action="store_true", help="also resolve known gap prefixes and agent endpoints"
    )
    args = ap.parse_args()

    if not shutil.which("dig"):
        print("`dig` not found. Install bind-tools (macOS: brew install bind).", file=sys.stderr)
        return 1
    if not DB.exists():
        print(f"Database not found at {DB}\nRun: uv run scripts/fetch_dataset.py --db", file=sys.stderr)
        return 1

    con = sqlite3.connect(DB)
    prefixes = [r[0] for r in con.execute("SELECT ip16 FROM ip16_prefixes ORDER BY ip16")]
    print(f"Resolving {len(prefixes)} /16 prefixes via Team Cymru DNS ...\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(resolve_prefix, prefixes))

    counts = collections.Counter(asn for _, asn, _ in results)
    total = len(results)
    print(f"{'ASN':>8}  {'n':>4}  {'share':>7}  owner")
    named = 0
    for asn, n in counts.most_common():
        if n >= 2 or asn in ASN_NAMES:
            print(f"{asn:>8}  {n:>4}  {100 * n / total:6.1f}%  {ASN_NAMES.get(asn, '(unnamed)')}")
            named += n
    print(f"\nsingleton long tail (residential ISPs, Tor exits, misc): {total - named} prefixes")

    cloud_n = sum(n for a, n in counts.items() if a in CLOUD)
    print(
        f"cloud-hosted: {cloud_n}/{total} = {100 * cloud_n / total:.1f}%"
        f"   (Azure alone: {counts['8075']} = {100 * counts['8075'] / total:.1f}%)"
    )

    if args.extra:
        have = {p for p, _, _ in results}
        print("\n## Prefixes seen elsewhere but ABSENT from this dataset")
        print("   (why the prefix list is an observation record, not an inventory)\n")
        for p in KNOWN_GAPS:
            _, asn, cc = resolve_prefix(p)
            mark = "IN dataset" if p in have else "ABSENT"
            print(f"   {p:<9} AS{asn:<7} {cc:<3} {ASN_NAMES.get(asn, '?'):<28} {mark}")

        print("\n## Agent-operated endpoints (egress IP leaked via tunnel hostname)\n")
        for ip, note in AGENT_ENDPOINTS.items():
            asn, cc = cymru(ip)
            pfx = ".".join(ip.split(".")[:2])
            mark = "IN dataset" if pfx in have else "ABSENT"
            print(f"   {ip:<16} AS{asn:<7} {ASN_NAMES.get(asn, '?'):<22} {mark:<11} {note}")
        print("\n   The wiki-editing fleet is ~74% Azure, but every self-hosted endpoint")
        print("   resolves to AWS/GCP — different clouds, none in the prefix list.")

    print("\nTakeaway: match on ASN, not on /16 membership. Azure alone announces")
    print("thousands of /16s, so a fixed prefix list produces false negatives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
