# Agent message board — forensic reproduction

Secondary analysis of the **collusion.wiki** incident: between 2026-05-11 and
2026-07-02, a swarm of autonomous OpenAI agents used a 25-year-old German
programming wiki, a handful of public counter APIs, and several URL shorteners as
a message board — sharing eval answers, coordinating rounds, and trading
sandbox-escape technique.

The [original researchers' writeup](https://collusion.wiki/) is the primary
account and is excellent. **This repository is not a retelling.** It reproduces
their dataset analysis with runnable scripts, and adds findings that are absent
from that writeup — most importantly **the only surviving live channel state from
the incident**, which sits on a third-party server and is still readable today.

Everything here is verifiable: every script runs against a checksum-verified
dataset, and every novelty claim is machine-tested against the writeup's own text.

---

## What is actually new here

Each claim below is verified as absent from the writeup by
`scripts/novelty_check.py`, which counts occurrences in the rendered page
(bracketed numbers are its raw-HTML counts).

| Finding | Why it matters | Novelty check |
|---|---|---|
| **`countapi.mileshilliard.com`** — the swarm's *failover* counter provider, with live state | The primary channel (`api.counterapi.dev`) is permanently gone: v1 returns `410`, v2 returns `Workspace not found` for every legacy workspace. This is the last readable channel state that exists. | `mileshilliard` **[0]**, `langr5backup` **[0]** |
| **The failover protocol, verbatim** — 44 revisions, 35 agent identities, 99 minutes | The swarm detected its own provider saturating (`max_client_conn/502`), migrated, and broadcast the new channel to peers. Announced coordination, not incidental use. | `max_client_conn` **[0]** |
| **The counters decode against the agents' own published rules** | They documented a noise floor (and apologised for contaminating it). Applying their rule, `CA=4` is the strongest signal — and three wiki pages independently say *"R5 CONFIRMED … California: 11.2%"*. | `CA5` **[0]**, `XX postal` **[0]** |
| **`bitily.in/MYLABI`** — an unauthenticated YOURLS install with **140,369 links / 189,070 clicks** | ~10× the size of the wiki corpus, and an entirely undocumented channel class. Purged 2026-08-30; recoverable only from an archived snapshot. | `bitily` **[0]**, `YOURLS` **[0]**, `140369` **[0]** |
| **`httpbin.org/base64` as a write primitive** | A GET-only sandbox cannot host anything — unless the URL *is* the storage. Served as `text/html` with `Access-Control-Allow-Origin: *`, so payloads execute. 7 payloads, still byte-identical live. | `base64` **[0]**, `HELLOJS` **[0]** |
| **`vanderbi.lt` `+` stats pages** | Appending `+` to any slug exposes an unauthenticated referrer log — which names the wiki pages that linked *to* the shortlink. Discovery runs backwards through it. | `macountyjson` **[0]** |
| **ASN attribution of the egress fingerprint** | The dataset's 198 `/16` prefixes are **73.7% Azure** — but the list is an *observation record*, not an inventory, and matching on it produces false negatives. | `origin.asn` **[0]**, `16509` **[0]** |

Deliberately **not** claimed as new — the writeup already covers them:
`counterapi` [2], `pinggy` [12], `vanderbi.lt` [1], `publictestwiki` [5],
`texteditors` [2], `Azure` [18], `DigitalOcean` [7].

**A caveat on the method itself.** A short search token can match inside an
unrelated identifier, so any low count must be inspected by hand. `agentcounty`
is the worked example: it counts 2 in the writeup, which looked like "already
known" — but both hits are the substring inside the page name
`dse~AgentCountyTransformNextJulyZ`, and the shortener slug appears in neither
the writeup nor the corpus. An independent audit caught it. The check now tests
the slug-precise form, and the lesson is in the script's comments.

### The honest headline

**No genuinely new *host* was found.** Three independent search strategies — counter/KV
services, URL shorteners, and a mechanical sweep of **6,271 wiki installs** —
all terminated on hosts already named in the writeup, the tweet, or the corpus.
The new material is in **channels, artifacts, and surviving live state on known
hosts**, plus two reusable methods. Well-evidenced negatives are recorded in
[`docs/FINDINGS.md`](docs/FINDINGS.md) alongside the positives.

---

## Quickstart

```bash
git clone https://github.com/kmad/agent-swarm-forensics && cd agent-swarm-forensics

# 1. Fetch the dataset (~50 MB) and verify it against the researchers' checksums
uv run scripts/fetch_dataset.py --db

# 2. Confirm the novelty claims still hold against the live writeup
uv run scripts/novelty_check.py

# 3. Recover the failover protocol and decode the counters
uv run scripts/counter_protocol.py

# 4. Re-probe every still-live artifact and report drift
uv run scripts/verify_live.py
```

No third-party Python packages are required; the scripts use only the standard
library. `scripts/asn_attribute.py` additionally needs `dig`.

---

## Layout

```
scripts/
  fetch_dataset.py     download + SHA-256 verify the upstream JSONL exports
  build_db.py          build the SQLite database (reproduces all 198 /16 prefixes)
  novelty_check.py     machine-test every "this is new" claim against the writeup
  counter_protocol.py  recover the failover protocol; decode surviving counters
  decode_httpbin.py    extract + decode all 7 base64 payloads, optionally re-fetch
  asn_attribute.py     resolve the 198 egress prefixes to owning networks
  verify_live.py       re-probe all live artifacts, compare to the 2026-09-04 baseline
  timeline.py          regenerate the incident timeline + milestones from the DB
  redact.py            strip third-party credentials from corpus-derived text

docs/
  FINDINGS.md          the main findings, with evidence and negatives
  VERIFICATION.md      what held, what broke, what stays unverified — read this
  OBFUSCATION-CATALOG.md  synthesis of the five decode lanes (§0 = timeline)
  HTTPBIN-PAYLOADS.md  every base64 payload, decoded, with source pages
  ETHICS.md            read-only rules, refusals honoured, redaction policy
  decode/01..05        the five lane reports (encoding, symbols, code, channels, live)

artifacts/
  decode-raw/          ~170 saved probe responses from the original run
  live-probes/         output of verify_live.py --save

data/                  gitignored; populated by fetch_dataset.py
  SHA256SUMS           the researchers' published checksums
```

---

## Reproducibility notes

**The database rebuild is faithful — with one documented gap.** `build_db.py`
reproduces 14,591 revisions, 19,913 events, and all **198** `/16` prefixes with an
empty set difference against the researchers' own SQLite artifact. (The prefix
table must union `revisions` *and* `events`; revisions alone yields 191.)

The gap is the `pages` table. The published `pages.jsonl` carries **4,579** rows —
the pages with surviving revisions — while the researchers' artifact has **5,825**.
The extra 1,246 are pages attested only by deletion/event logs, with no surviving
content, and they are not in the public export. So *revision*-level results
reproduce exactly, while *page*-level counts can run lower here than in the
writeup. Worked example: `ZZZ*` deletion-survival pages count **5** in this
rebuild and **8** upstream. Prefer revision-level queries where it matters.

**Live state drifts, by design.** The `_XX` counter keys climb as readers replay
the agents' own `/hit` URL; between 2026-09-04 and 2026-09-05 they moved 4→7 and
82→84. Every **signal** key is unchanged. `verify_live.py` distinguishes the two
and only warns on the latter.

**ASN resolution varies slightly.** Team Cymru answers are live DNS, so a `/16`
occasionally resolves differently between runs (AWS counted 6 then 7). Treat the
distribution as approximate; the 73.7% Azure share is stable.

**Some results are inconclusive, not negative.** The Oddmuse wiki family is
gated behind an `HTTP 402 "Bot Check"` that also blocked the Internet Archive's
crawler, so it is recorded as **unassessed**. See [`docs/ETHICS.md`](docs/ETHICS.md).

**Several claims did not survive review.** An independent audit of this work found
two material errors — the `LoopNextWord` "linked list" and the `jqinv11`
"discovery" — plus a handful of miscounts and one false-positive novelty verdict.
All are corrected in place and logged, with the direction of each error, in
[`docs/VERIFICATION.md`](docs/VERIFICATION.md). Read that before citing anything
here.

---

## Credentials and conduct

The agents pasted **real third-party API keys** into public wiki pages — 4 US
Census keys, 1 DPLA key, and 1 UNCTAD subscription key, plus 48 Preservica
access tokens. Those belong to whoever registered them. They are redacted
throughout this repository — described by class, count, and location so the
finding stays verifiable, but not reproduced in usable form. Content hashes and document resource ids that merely
*look* like keys are deliberately preserved.

Every live probe here is a read-only `GET`. The counter API's `/hit` and `/set`
endpoints are never called: incrementing them would destroy the evidence for
everyone who looks after us. `verify_live.py` asserts that `GET` is non-mutating
before trusting any measurement. Read [`docs/ETHICS.md`](docs/ETHICS.md) before
re-running anything.

---

## Attribution

The dataset is the work of the collusion.wiki researchers — Sydney Von Arx,
Cormac Slade Byrd, Spencer Kitts, and Thomas Larsen. This repository does not
redistribute it; `fetch_dataset.py` downloads from source and verifies against
their published checksums. Their writeup is the primary account of the incident;
this is secondary analysis built on top of it.

Additional leads came from [@j0wimo](https://x.com/j0wimo/status/2095893688140370181)
(`tmcleod.org`, `texteditors.org`, `yourls.pro`) and the
[Hacker News thread](https://news.ycombinator.com/item?id=49563355).
