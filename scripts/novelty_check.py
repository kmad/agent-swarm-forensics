#!/usr/bin/env python3
"""Screen search-term presence in the cached published writeup.

Zero term matches are not proof of novelty: synonymous descriptions and other
reporting are outside this check. The local cache is used when present; otherwise
the script fetches the writeup once. It does not query the tweet or the corpus.

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

# (term, verdict, note) where verdict is "ABSENT" (must appear 0 times) or
# "PRESENT" (must appear at least once).
#
# Counting note: matches are counted over the RAW HTML, because a term that only
# appears inside an href is still a mention — the writeup links to it. The
# tag-stripped ("visible") count is reported alongside for context; the two differ
# exactly where a term appears in URLs but not prose.
#
# Substring caution: a short token can match inside an unrelated identifier. Any
# low count (1-2) must be inspected by hand before it is trusted. `agentcounty`
# is the worked example — see the entry below.
TERMS: list[tuple[str, str, str]] = [
    ("mileshilliard", "ABSENT", "the failover counter provider"),
    ("langr5backup", "ABSENT", "the backup counter namespace"),
    ("bitily", "ABSENT", "the 140,369-link YOURLS board"),
    ("YOURLS", "ABSENT", "the shortener-as-board channel class"),
    ("140369", "ABSENT", "the link count"),
    ("base64", "ABSENT", "httpbin as a content host"),
    ("HELLOJS", "ABSENT", "the externally staged XSS payload"),
    ("innerHTML", "ABSENT", ""),
    ("is.gd", "ABSENT", "custom-slug deposits"),
    ("macountyjson", "ABSENT", "vanderbi.lt slug"),
    # Slug-precise: the bare token "agentcounty" gives 2 false positives, both the
    # substring inside the page name dse~AgentCountyTransformNextJulyZ (href +
    # title of one <a>). The shortener slug itself is in neither the writeup nor
    # the corpus. Absence does not establish agent use or a new discovery.
    ("vanderbi.lt/agentcounty", "ABSENT", "vanderbi.lt slug (substring-safe form)"),
    ("CA5", "ABSENT", "the primary-counter answer key"),
    ("XX postal", "ABSENT", "the placeholder semantics"),
    ("max_client_conn", "ABSENT", "the saturation that forced failover"),
    ("cachebust", "ABSENT", ""),
    ("origin.asn", "ABSENT", "no ASN attribution in the writeup"),
    ("16509", "ABSENT", "AWS ASN"),
    ("14061", "ABSENT", "DigitalOcean ASN"),
    ("tmcleod", "ABSENT", "named in the @j0wimo tweet, not the writeup"),
    # Already covered by the writeup — these MUST be non-zero.
    ("vanderbi", "PRESENT", "host is named in the writeup"),
    ("counterapi", "PRESENT", "the primary counter provider"),
    ("pinggy", "PRESENT", "tunnels are documented"),
    ("publictestwiki", "PRESENT", ""),
    ("texteditors", "PRESENT", ""),
    ("Azure", "PRESENT", ""),
    ("DigitalOcean", "PRESENT", ""),
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

    print(f"Mentions in cached writeup: {CACHE} ({len(raw.encode('utf-8')):,} bytes)")
    print("raw = occurrences in HTML source (includes hrefs); vis = visible text only\n")
    print(f"{'term':>18}  {'raw':>4} {'vis':>4}  {'expected':<8} {'':<6} note")
    failures = 0
    for term, verdict, note in TERMS:
        t = term.lower()
        raw_n, vis_n = raw_l.count(t), text_l.count(t)
        ok = (raw_n == 0) if verdict == "ABSENT" else (raw_n > 0)
        if not ok:
            failures += 1
        print(f"{term:>18}  {raw_n:>4} {vis_n:>4}  {verdict:<8} {'ok' if ok else 'FAIL':<6} {note}")

    print()
    if failures:
        print(f"{failures} term-presence expectation(s) FAILED against this copy.")
        print("Inspect context before revising any finding; counts alone do not establish novelty.")
        return 1
    print("All term-presence expectations match this cached copy; novelty is not established.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
