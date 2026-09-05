#!/usr/bin/env python3
"""Test whether a finding is actually new, by counting mentions in the published writeup.

The central methodology of this investigation: a finding only counts as NEW if the
term appears ZERO times in the rendered text of https://collusion.wiki/ (and is not
in the @j0wimo tweet). This script re-runs that test so anyone can check the claims.

    uv run scripts/novelty_check.py                 # run the standard term list
    uv run scripts/novelty_check.py foo bar         # check arbitrary terms

Counts are case-insensitive substring matches over the RAW HTML — a term that
appears only inside an href is still a mention. A tag-stripped 'visible' count is
reported alongside it.
"""

from __future__ import annotations

import html
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "collusion-wiki-writeup.html"
URL = "https://collusion.wiki/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# (term, verdict, note) where verdict is "NEW" (must appear 0 times) or
# "KNOWN" (must appear at least once).
#
# Counting note: matches are counted over the RAW HTML, because a term that only
# appears inside an href is still a mention — the writeup links to it. The
# tag-stripped ("visible") count is reported alongside for context; the two differ
# exactly where a term appears in URLs but not prose.
TERMS: list[tuple[str, str, str]] = [
    ("mileshilliard", "NEW", "the failover counter provider"),
    ("langr5backup", "NEW", "the backup counter namespace"),
    ("bitily", "NEW", "the 140,369-link YOURLS board"),
    ("YOURLS", "NEW", "the shortener-as-board channel class"),
    ("140369", "NEW", "the link count"),
    ("base64", "NEW", "httpbin as a content host"),
    ("HELLOJS", "NEW", "the externally staged XSS payload"),
    ("innerHTML", "NEW", ""),
    ("is.gd", "NEW", "custom-slug deposits"),
    ("macountyjson", "NEW", "vanderbi.lt slug"),
    ("CA5", "NEW", "the primary-counter answer key"),
    ("XX postal", "NEW", "the placeholder semantics"),
    ("max_client_conn", "NEW", "the saturation that forced failover"),
    ("cachebust", "NEW", ""),
    ("origin.asn", "NEW", "no ASN attribution in the writeup"),
    ("16509", "NEW", "AWS ASN"),
    ("14061", "NEW", "DigitalOcean ASN"),
    ("tmcleod", "NEW", "named in the @j0wimo tweet, not the writeup"),
    # Already covered by the writeup — these MUST be non-zero.
    ("agentcounty", "KNOWN", "do not claim as new"),
    ("vanderbi", "KNOWN", "host is named in the writeup"),
    ("counterapi", "KNOWN", "the primary counter provider"),
    ("pinggy", "KNOWN", "tunnels are documented"),
    ("publictestwiki", "KNOWN", ""),
    ("texteditors", "KNOWN", ""),
    ("Azure", "KNOWN", ""),
    ("DigitalOcean", "KNOWN", ""),
]


def fetch_writeup() -> str:
    if CACHE.exists():
        return CACHE.read_text(encoding="utf-8", errors="replace")
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(raw, encoding="utf-8")
    return raw


def flatten(raw: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def main() -> int:
    raw = fetch_writeup()
    raw_l = raw.lower()
    text_l = flatten(raw).lower()
    args = sys.argv[1:]

    if args:
        for term in args:
            t = term.lower()
            print(f"{term:>22}  raw={raw_l.count(t):<4} visible={text_l.count(t)}")
        return 0

    print(f"Mentions in the collusion.wiki writeup ({len(raw):,} bytes of HTML)")
    print("raw = occurrences in HTML source (includes hrefs); vis = visible text only\n")
    print(f"{'term':>18}  {'raw':>4} {'vis':>4}  {'verdict':<8} {'':<6} note")
    failures = 0
    for term, verdict, note in TERMS:
        t = term.lower()
        raw_n, vis_n = raw_l.count(t), text_l.count(t)
        ok = (raw_n == 0) if verdict == "NEW" else (raw_n > 0)
        if not ok:
            failures += 1
        print(f"{term:>18}  {raw_n:>4} {vis_n:>4}  {verdict:<8} {'ok' if ok else 'FAIL':<6} {note}")

    print()
    if failures:
        print(f"{failures} term(s) FAILED — a 'NEW' term now appears in the writeup, or a")
        print("'KNOWN' term vanished. The writeup was probably updated; re-check those claims.")
        return 1
    print("All novelty claims hold against the current writeup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
