#!/usr/bin/env python3
"""Redact third-party credentials from corpus-derived text.

The agents pasted real API keys into public wiki pages. Those credentials belong
to whoever registered them. This repository describes the finding — that keys
leaked, from which services, how often — without reproducing usable secrets.

    uv run scripts/redact.py FILE...            # report what would be redacted
    uv run scripts/redact.py --write FILE...    # rewrite the files in place

What is redacted:
  * values of api_key= / apikey= / key= / access_token= / token= parameters
  * 26-40 char hex strings whose line identifies them as a credential, including
    a wrapped list of keys under one heading
  * long hex in any `hex_opaque` row of the encoding-sweep CSV — one real UNCTAD
    subscription key hid there behind a `%3D` artifact while the same secret was
    caught on the sibling row that happened to be classified as an API key
  * access-token UUIDs on lines mentioning render/access tokens

What is deliberately NOT redacted:
  * `record_hash_path` values and other document hashes, which are 40-hex but
    are content identifiers, not credentials
  * the document/report resource GUIDs passed between cohorts as stable pointers
    (see KEEP_UUID_PREFIXES)

Redaction by classification label is fragile: the same secret can appear under
two different labels. Always grep for the secret itself afterwards, and have
someone else check.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PARAM_RE = re.compile(
    r"\b(api_?key|apikey|access_token|token|key)(=)([A-Za-z0-9_\-]{12,})",
    re.IGNORECASE,
)
# Long hex, optionally carrying a percent-decoding artifact prefix (%3D -> "3D",
# %2F -> "2F") from the way these URLs were logged.
HEX_RE = re.compile(r"\b((?:3D|2F)?[a-f0-9]{26,40})\b")
UUID_RE = re.compile(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b")

# A bare hex string is treated as a secret when its line says so.
KEY_CONTEXT = re.compile(
    r"api[_-]?key|apikey|census_api|dpla|unctad|subscription-key|credential|secret", re.IGNORECASE
)
# Hashes and resource identifiers that must survive redaction.
SAFE_CONTEXT = re.compile(r"record_hash|body_sha|sha256|checksum|digest", re.IGNORECASE)

# In the encoding-sweep CSV, classification lives in field 5. `hex_opaque` rows
# turned out to carry a real UNCTAD subscription key behind a %3D artifact — the
# same secret its sibling row classified as an API key. Treat every opaque-hex
# classification as credential-bearing.
CSV_SECRET_CLASS = re.compile(r",(hex_opaque|embedded_[A-Za-z]*_?api_key),", re.IGNORECASE)

# Access tokens are secrets; the document/report resource ids they sit beside are
# stable content pointers and are deliberately kept (see docs/ETHICS.md).
TOKEN_CONTEXT = re.compile(r"render token|token=|token%3D|access[_-]?token", re.IGNORECASE)
KEEP_UUIDS = {
    "f436a16c-767f-44b8-95fc-2031847276b9",  # Preservica document resource id
    "ada0454d-1b5b-4f1e-9b7f-2b8a4d1c9e33",  # Power BI report resource key (prefix-matched below)
}
KEEP_UUID_PREFIXES = ("f436a16c-", "ada0454d-")


def redact_line(line: str) -> tuple[str, int]:
    n = 0

    def _param(m: re.Match) -> str:
        nonlocal n
        n += 1
        return f"{m.group(1)}{m.group(2)}{m.group(3)[:4]}[REDACTED]"

    out = PARAM_RE.sub(_param, line)

    hex_is_secret = (KEY_CONTEXT.search(out) and not SAFE_CONTEXT.search(out)) or CSV_SECRET_CLASS.search(out)
    if hex_is_secret:

        def _hex(m: re.Match) -> str:
            nonlocal n
            n += 1
            return f"{m.group(1)[:4]}[REDACTED]"

        out = HEX_RE.sub(_hex, out)

    if TOKEN_CONTEXT.search(out):

        def _uuid(m: re.Match) -> str:
            nonlocal n
            val = m.group(1)
            if val.startswith(KEEP_UUID_PREFIXES) or val in KEEP_UUIDS:
                return val
            n += 1
            return f"{val[:8]}-[REDACTED-ACCESS-TOKEN]"

        out = UUID_RE.sub(_uuid, out)

    return out, n


def process(path: Path, write: bool) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"  !! {path}: {exc}", file=sys.stderr)
        return 0

    lines = text.splitlines(keepends=True)
    total = 0
    out_lines = []
    # A list of keys often wraps across several lines under one "api key" heading,
    # so carry the context a couple of lines forward.
    in_key_block = False
    for line in lines:
        if KEY_CONTEXT.search(line) and not SAFE_CONTEXT.search(line):
            in_key_block = True
        elif in_key_block and not HEX_RE.search(line):
            # The run of wrapped key values has ended.
            in_key_block = False
        if SAFE_CONTEXT.search(line):
            in_key_block = False

        probe = line + " api_key" if in_key_block else line
        new, n = redact_line(probe)
        if in_key_block and new.endswith(" api_key"):
            new = new[: -len(" api_key")]
        total += n
        out_lines.append(new)

    if total:
        verb = "redacted" if write else "would redact"
        print(f"  {verb} {total:>4} secret(s) in {path}")
        if write:
            path.write_text("".join(out_lines), encoding="utf-8")
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="rewrite files in place")
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()

    total = 0
    for p in args.paths:
        targets = sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else [p]
        for t in targets:
            if t.suffix.lower() in {".png", ".jpg", ".gz", ".zip", ".db"}:
                continue
            total += process(t, args.write)

    if total == 0:
        print("No credentials found.")
    elif not args.write:
        print(f"\n{total} secret(s) found. Re-run with --write to redact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
