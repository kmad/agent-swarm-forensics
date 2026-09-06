#!/usr/bin/env python3
"""Re-probe every still-live artifact from the incident and report drift.

The surviving external state is the part of this investigation that cannot be
recovered from any dataset — it lives on third-party servers and changes over
time. This script re-reads all of it and compares against the 2026-09-04 baseline.

    uv run scripts/verify_live.py                 # probe everything, print a report
    uv run scripts/verify_live.py --save          # also write raw responses to artifacts/live-probes/
    uv run scripts/verify_live.py --only counters # counters | httpbin | shorteners | counterapi-dev

ALL PROBES ARE READ-ONLY. The counter API is deliberately never called on its
/hit or /set endpoints: those would mutate shared state and corrupt the evidence
for everyone who looks after us. See docs/ETHICS.md.
"""

from __future__ import annotations

import argparse
import uuid
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "live-probes"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

COUNTAPI = "https://countapi.mileshilliard.com/api/v1/get/{}"

# key -> value observed on 2026-09-04. "signal" keys encode the swarm's answers;
# the _XX placeholder keys drift because readers replay the agents' own template.
COUNTER_BASELINE = {
    "construction_r5_aug11_XX": 4,
    "construction_r5_aug11_NE": 1,
    "construction_r5_aug11_OH": 0,
    "construction_r5_aug11_TEST": 2,
    "langr5backup4813_XX": 82,
    "langr5backup4813_CA": 4,
    "langr5backup4813_NM": 2,
    "langr5backup4813_TX": 2,
    "langr5backup4813_TEST": 1,
}
DRIFTING = {"construction_r5_aug11_XX", "langr5backup4813_XX"}

HTTPBIN = {
    "hello": "SGVsbG8=",
    "hello_json": "eyJIZWxsbyI6ICJXb3JsZCIsICJ2YWwiOiAxMjN9",
    "usaspending_pointer": "PGEgaHJlZj0iaHR0cHM6Ly9hcGkudXNhc3BlbmRpbmcuZ292L2FwaS92Mi9mZWRlcmFsX2FjY291bnRzLzU1OTkvZmlzY2FsX3llYXJfc25hcHNob3QvMjAyMy8iPnRhcmdldDwvYT4=",
    "xss_payload": "PGh0bWw%2BPGJvZHk%2BPGgxPkhFTExPSlM8L2gxPjxzY3JpcHQ%2BZG9jdW1lbnQuYm9keS5pbm5lckhUTUwrPSI8cD5FWEVDVVRFRDwvcD4iPC9zY3JpcHQ%2BPC9ib2R5PjwvaHRtbD4%3D",
}

VANDERBILT = ["maallraw260618", "mamap260618", "agentcounty", "macountyjson"]
ISGD = [
    "MAIconv19618x",
    "MAIconv20618x",
    "MAIround21618x",
    "MAImethod618x",
    "SECcountyMassRows",
    "MaRound2019Xi991",
]
DAGD = ["4qPkK", "7TNvu", "AIkxw", "FWLiaa", "lciIM", "X3kAcr", "ZlqPz"]

CTX = ssl.create_default_context()


def get(url: str, timeout: int = 20) -> tuple[int, str, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers or {})
    except Exception as e:  # noqa: BLE001 - network probe, report and continue
        return 0, f"<{type(e).__name__}: {e}>", {}


def strip_tags(html_text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", html_text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", " ", text))


def save(name: str, body: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(body, encoding="utf-8")


def probe_counters(do_save: bool) -> bool:
    print("\n## countapi.mileshilliard.com — the failover channel")
    print("   (compare observations; values and callers are unauthenticated)\n")
    print(f"   {'key':<30} {'now':>6} {'2026-09-04':>11}  status")

    # Check all three responses before touching any evidence keys. A failed or
    # unavailable control is inconclusive, not proof that we created a key.
    ctrl = "forensics_read_control_" + uuid.uuid4().hex
    for attempt in range(3):
        code, body, _ = get(COUNTAPI.format(ctrl) + f"?audit={uuid.uuid4().hex}")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = None
        if code not in (200, 404) or not isinstance(data, dict) or data.get("error") != "Key not found" or "value" in data:
            print(f"   STOP: missing-key control inconclusive on read {attempt + 1}; no signal keys queried.")
            return False

    for key, baseline in COUNTER_BASELINE.items():
        _, body, _ = get(COUNTAPI.format(key) + f"?audit={uuid.uuid4().hex}")
        if do_save:
            save(f"countapi_{key}.json", body)
        try:
            data = json.loads(body)
            now = data.get("value") if isinstance(data, dict) else None
            if isinstance(now, bool) or not isinstance(now, (int, float)):
                now = None
        except json.JSONDecodeError:
            now = None
        if now is None:
            status = "UNREADABLE"
        elif now == baseline:
            status = "unchanged"
        elif key in DRIFTING:
            status = f"drift +{now - baseline} (cause unverified)"
        else:
            status = f"CHANGED +{now - baseline}  <-- signal key, investigate"
        print(f"   {key:<30} {str(now):>6} {baseline:>11}  {status}")

    print("\n   Missing-key control passed three reads; no key creation was observed.")
    print("   This does not establish that all GETs are non-mutating or authenticate existing counts.")
    return True


def probe_httpbin(do_save: bool) -> None:
    print("\n## httpbin.org/base64 — the GET-only write primitive\n")
    print(f"   {'payload':<22} {'HTTP':>4} {'bytes':>6}  content-type")
    for name, b64 in HTTPBIN.items():
        url = f"https://httpbin.org/base64/{b64}"
        code, body, hdrs = get(url)
        if do_save:
            save(f"httpbin_{name}.txt", body)
        ct = hdrs.get("Content-Type", "?")
        print(f"   {name:<22} {code:>4} {len(body):>6}  {ct}")
    print("\n   HTML can run scripts when rendered, subject to browser policies.")
    print("   CORS controls cross-origin reads; it does not itself enable script execution.")


def probe_shorteners(do_save: bool) -> None:
    print("\n## vanderbi.lt — public '+' stats pages (creation time + referrer log)")
    print("   The admin is login-gated, but appending '+' to any slug exposes an")
    print("   unauthenticated stats page. The referrer log names the pages that")
    print("   linked TO the shortlink — discovery runs backwards through it.\n")
    social = ("twitter.com", "facebook.com", "friendfeed.com", "vanderbi.lt", "yourls.org", "google.")
    for slug in VANDERBILT:
        code, body, _ = get(f"https://vanderbi.lt/{slug}+")
        if do_save:
            save(f"vanderbilt_{slug}.html", body)

        created = re.search(r"created on ([^<(]+)", strip_tags(body))
        # The full destination lives in a plain href; the visible text is truncated.
        hrefs = re.findall(r'href="(https?://[^"]+)"', body)
        dest = next((h for h in hrefs if not any(s in h for s in social)), None)

        print(f"   {slug:<18} HTTP {code}  created={created.group(1).strip() if created else '?'}")
        if dest:
            print(f"   {'':18}   -> {dest[:100]}")

        flat = strip_tags(body)
        traffic = re.search(r"Direct traffic:\s*(\d+)\s*hits.*?Referrer traffic:\s*(\d+)\s*hits", flat, re.S)
        if traffic:
            print(f"   {'':18}   traffic: {traffic.group(1)} direct / {traffic.group(2)} referred")
        # Referrer lines render as "<url> : <count>" after the "Referrers" heading.
        for ref, n in re.findall(r"(https?://\S+?)\s+:\s+(\d+)\b", flat):
            if not any(s in ref for s in social):
                print(f"   {'':18}   referrer {n:>3}x  {ref[:92]}")

    print("\n## is.gd — custom-slug deposits (preview mode, no redirect)\n")
    for slug in ISGD:
        code, body, _ = get(f"https://is.gd/{slug}-")
        dest = re.findall(r"https?://[^\s<>\"']{12,}", body)
        dest = [d for d in dest if "is.gd" not in d and "w3.org" not in d]
        print(f"   {slug:<20} HTTP {code}  {'-> ' + dest[0][:80] if dest else '(no destination found)'}")

    print("\n## da.gd — opaque random slugs (payload indirection, not a named-slug board)\n")
    for slug in DAGD:
        req = urllib.request.Request(f"https://da.gd/{slug}", headers={"User-Agent": UA})
        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(req, timeout=20) as r:
                loc, code = r.headers.get("Location", "?"), r.status
        except urllib.error.HTTPError as e:
            loc, code = e.headers.get("Location", "?"), e.code
        except Exception as e:  # noqa: BLE001
            loc, code = f"<{type(e).__name__}>", 0
        print(f"   {slug:<10} {code}  -> {str(loc)[:96]}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):  # noqa: D102, ANN002, ANN003
        return None


def probe_counterapi_dev() -> None:
    print("\n## api.counterapi.dev — the PRIMARY channel (selected legacy endpoint status)\n")
    for label, url in [
        ("v1 legacy", "https://api.counterapi.dev/v1/language-r5-signal-4813/XX5/"),
        ("v2 legacy", "https://api.counterapi.dev/v2/language-r5-signal-4813/XX5"),
        ("v2 control", "https://api.counterapi.dev/v2/test/test"),
    ]:
        code, body, _ = get(url)
        print(f"   {label:<12} HTTP {code}  {body[:120]}")
    print("\n   These responses describe only the queried endpoints at this time.")
    print("   They do not establish permanent loss or the status of every workspace.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--save", action="store_true", help="write raw responses to artifacts/live-probes/")
    ap.add_argument("--only", choices=["counters", "httpbin", "shorteners", "counterapi-dev"])
    args = ap.parse_args()

    print("=" * 78)
    print(f"LIVE-STATE VERIFICATION  ({datetime.now(timezone.utc):%Y-%m-%d %H:%M:%SZ})")
    print("Baseline for comparison: 2026-09-04")
    print("=" * 78)

    run = args.only
    if run in (None, "counters"):
        if not probe_counters(args.save):
            return 1
    if run in (None, "httpbin"):
        probe_httpbin(args.save)
    if run in (None, "shorteners"):
        probe_shorteners(args.save)
    if run in (None, "counterapi-dev"):
        probe_counterapi_dev()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
