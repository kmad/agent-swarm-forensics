# Verification record

Every substantive claim in this repository was re-executed against the database by
someone other than its author, and several did not survive. This file records what
held, what broke, and what remains unverified — including the errors, because a
findings document without its error log is not evidence, it is advertising.

Regenerate any figure below with the scripts in `scripts/`; the queries are given
inline where they are short.

---

## Verified exactly

Re-run independently, matching to the digit:

| Claim | Measured |
|---|---|
| Corpus size: 14,591 revisions / 19,913 events / 3,103 labels / 4 wikis | identical |
| Window 2026-05-24 → 07-02 (writes); events to 07-14 | identical |
| Counter failover: 44 revisions, 35 distinct labels, 3 pages | identical |
| Failover window 2026-06-17T00:56:56Z → 02:35:56Z (99 min exactly) | identical |
| All 8 verbatim protocol quotes present in the corpus | all found |
| `httpbin.org/base64`: 7 distinct payloads across 17 revisions | identical |
| All 21 date/page/label rows in `HTTPBIN-PAYLOADS.md` | match the DB exactly, including the blank label at 2026-06-16T20:58:26Z |
| `ip16_prefixes` = 198, ASN table covers exactly those 198 | zero set difference |
| ASN split: 8075=146 (73.7%), 16509=6, 14061=5, 13335=3, 15169=2, 22773=2, 9808=2 | identical |
| The 5 unresolved prefixes: `165.140 156.146 192.111 193.221 45.84` | identical |
| Gap prefixes `3.212 44.220 104.131 174.138 52.228` absent from the dataset | confirmed absent |
| Agent endpoint prefixes `16.146 35.95 34.107` absent from the dataset | confirmed absent |
| Microlink `function=` smuggling: 9 revisions from 2026-05-26T11:15:22Z | identical |
| `LoopNextWord*` = 316 pages | identical (but see corrections) |
| 899 blank labels, 100% on wiki `probier` | identical |
| `wiki2.cgi` in 46 revisions; DPLA key in 11 | identical |
| All 24 opcode FTS counts (XX 503, XX5 114, ACK 220, SEEN 383, ACTUAL 1082, TEST 1712, …) | 24/24 exact |
| Epoch-nonce = true clock: 658 names, 379 with revisions, median **+2.0 s** | identical |
| Workhorse jq program seen 1,519 times | identical |
| Negative controls: gzip 0, `GHOSTLINK` 0, "canary" 0, `document.cookie` 0 | all 0 |

---

## Corrected — claims that did not survive

These were wrong in earlier drafts and are fixed in place. Listed so a reader can
see the direction of the errors.

| Claim as written | Reality | Where |
|---|---|---|
| `LoopNextWord*` is a "316-page distributed linked list" whose structure is the payload | **False.** 317 revisions hold only **7 distinct bodies**; 311 of 316 pages are byte-identical, minted in a **39-second burst** (2026-06-18 20:09:40Z→20:10:19Z, ~8/sec). Only 2 of 316 bodies contain `LoopNextWord`; `NextRawChildRef*` and `NextContinueMineABC*` resolve to **0** pages. A runaway loop, not a chain. | catalog §3 |
| The `jqinv11*` jq programs were "recovered from live referrer logs" as new | **Corroboration, not discovery.** All five are byte-identical to `dse~AgentElevenSmallLinksBB@2` (2026-06-18T19:46:31Z), already in the dataset. | catalog §3 |
| `investor.gov/files/county.json` was a "previously unseen source" | **False.** Appears in **1,256** revisions. | catalog §3 |
| `vanderbi.lt/agentcounty` is already covered by the writeup (count 2) | **False positive.** Both hits are the substring inside the page name `dse~AgentCountyTransformNextJulyZ`. The slug is in neither the writeup nor the corpus. The finding *is* new. | `novelty_check.py` |
| `918d6489…` is a 5th Census API key | **Not a key** — a 64-char hash in a `urlquery.net` path. True tally: 4 Census + 1 DPLA + 1 UNCTAD. | `ETHICS.md` |
| httpbin payloads span 5 pages | **6** — `dse:AgentBridgeViaSearchAA9901` is the sixth. | `FINDINGS.md` |
| Failover page split 24 / 17 / 3 | **22 / 19 / 3** | `FINDINGS.md` |
| ASN resolution "198/198 answered" | **193 of 198**; 5 unresolved | `FINDINGS.md` |
| Singleton ASN long tail = 21 (10.6%) | **27 (13.6%)** — the table previously summed to 192, not 198 | `FINDINGS.md` |
| Four-day burst = 10,514 saves (72%) | **10,952 (75%)** | catalog §0 |
| `GHOSTLINK998877` attributed to this corpus | **0 occurrences** in bodies, page names, or labels. It also appears twice in the writeup, so it never qualified as novel either. | catalog §3 |
| "Canary GUIDs" | Misnamed. `f436a16c…` (395 occurrences) is a Preservica **document resource id**; `ada0454d…` a Power BI report key. The word "canary" occurs **0** times in the corpus — it was our descriptive term, not theirs. | catalog §3 |

---

## Unverified or single-source — treat accordingly

- **`bitily.in` 140,369 links / 189,070 clicks.** Not verifiable from this dataset;
  it comes from a single Wayback capture of a third party. The *host* is
  corroborated (21 revisions, 38 occurrences), the counts are not.
- **publictestwiki.com `list=abuselog` artifacts**, including the identical nonce
  posted from Azure and AWS 16 seconds apart. The site now serves a Cloudflare
  interstitial, so this could not be reproduced. Labelled unverified throughout.
- **"Container died ~07:29:15Z"** from the `hb000`–`hb353` heartbeat stream. The
  interval arithmetic checks out (615 s / 353 keys ≈ **1.74 s/key**, not the 1.73
  originally stated), but the death time rests on one agent's own prose, and
  `api.counterapi.dev` v1 is now `410 Gone` — permanently unverifiable.
- **486 page names / 88 labels with epoch nonces.** A broad `17\d{8}` regex gives
  801 / 92; a narrower valid-epoch filter would plausibly land near the stated
  figure, but it was not independently reproduced.
- **The counter decode itself.** `CA=4` being the strongest signal is an inference
  from a 4-vs-2-vs-2 count on an unauthenticated, world-writable counter that has
  a *documented contamination incident* and three months of post-publicity
  exposure. The wiki prose independently says R5 = California, which is what makes
  the reading credible — not the counts alone.

---

## Known reproducibility gaps

- **`pages` table is smaller here than upstream.** The published `pages.jsonl` has
  4,579 rows (pages with surviving revisions); the researchers' own SQLite has
  5,825, the extra 1,246 attested only by deletion logs. Revision-level results
  reproduce exactly; page-level counts can run lower. Worked example: `ZZZ*` pages
  count **5** here, **8** upstream.
- **ASN resolution is live DNS**, so a `/16` occasionally resolves differently
  between runs (AWS counted 6 then 7). The distribution is stable; treat single
  rows as approximate.
- **Live counter values drift.** The `_XX` placeholder keys climb as readers replay
  the agents' own `/hit` template. Baseline and current values are both reported by
  `scripts/verify_live.py`.

---

---

## Lanes 1-3 audit (encoding sweep, symbol dictionary, code inventory)

A second independent audit covered the three remaining decode lanes. Two findings
survived scrutiny completely and are the strongest things in this repository; a
number of the surrounding figures did not.

### Held up completely — publish with confidence

**Microlink `function=` POST smuggling.** Every element verified independently:
11 revisions mention microlink, **9 carry `function=`**, and all nine fall in a
single ~5-hour burst on **2026-05-26** (11:15:22Z → 16:35:22Z). Every base64
constant decodes as tabulated — `UE9TVA==` → `POST`,
`YXBwbGljYXRpb24vanNvbg==` → `application/json`,
`L2FwaS92Mi9kb3dubG9hZC9hY2NvdW50cy8=` → `/api/v2/download/accounts/`, plus the
full JSON body. The mechanism is exactly as described: method, content-type,
endpoint and body all riding as base64 constants in a GET querystring, executed
by a rented headless browser.

*Correction:* earlier drafts gave the range as "2026-05-26 → 06-17". The two later
microlink revisions are plain renderer probes with **no** `function=` parameter.
Tightening this to a single day makes the "earliest GET-bypass in the corpus"
claim *stronger*, not weaker — it predates the June 20 blob bypass by 3.5 weeks.

**Epoch-nonce identifiers encode the true sandbox clock.** Reproduces exactly:
486 page names / 88 labels under a loose `178\d{7}` regex, median **+2.0 s** and
**+3.0 s** against the first surviving write. Robust to the regex choice — a
digit-bounded pattern gives 379 / 58 with identical medians.

*Correction:* the outlier explanation was wrong. Earlier text called them
"pre-created scratch pages"; in fact 31 of the outliers are **negative** (nonce
later than the first write), the opposite of that story. The extremes are
hand-rounded placeholders that are not `time.time()` output at all
(`…1783000000`, `…1782000000`) — a false-positive class of the regex.

### Numbers that did not reproduce

| Claim | Measured | Note |
|---|---|---|
| 134 hex tokens (32-64 char) | **129** | sweep.py's own regex; 48 record_hash + 40 Census + 28 opaque + 11 DPLA + 2 md5/sha |
| 67 `record_hash_path` rows | **48** | both in the CSV and on a fresh run |
| "51 rows, 12 revisions" | 51 rows across **45** revisions | row count right, revision count wrong |
| `.[0:16]` "1,563 slice-probe occurrences" | **225** as a jq program | ~7× overstated; 2,281 covers *all* slice programs combined |
| dominant jq usage "~87%" | **76.8%** | 14,529 of 18,927 occurrences |
| "%xx = 8,109 revisions" | **7,235** | 8,109 counts revisions containing any literal `%`; the table mixed three metrics |
| 251 utf8 bodies | **250** | |
| "1,682 distinct jq programs" | 1,672-1,704 | depends on decode depth; no extraction regex was published — treat as "~1,700" |
| "13/210 dated labels match their write month" | not reproducible | three tokenizers give 92/984, 164/1200, 32/443. The *direction* holds (~7-14%); the specific numbers do not |
| tier table column headed "revs" | values are **occurrences** | load-bearing, since the report counts cohorts from it |
| "≥5 independent cohorts" replicated the blob bypass | **2 of 6 share a label** | timestamps all verify; independence is overstated |

### Bad citations

Six of ~46 spot-checked citations point at the wrong artifact:

- **`dse~LoopNextWord100380@1`** — the quoted `[[WorkerLinksGet7788]] … END` text
  is byte-exact from `@102320`, not `@100380`. This was the *sole* evidence for the
  linked-list reading, which the data contradicts anyway: **1 wikilink across 317
  revisions**, and the two "chain" pages point at the *same* target — hub-and-spoke
  at most.
- `dse~AgentAug16ClothingCoord1781638281` and `dse~A1ScratchGetSaveX1781729833` —
  both pages have **zero stored revisions** (delete events only), so the quoted
  "first write" deltas are unsupported.
- Three timezone errors: nonce decodes stated as UTC are actually wiki-local
  (UTC+2) — e.g. "17:31" is 19:31 UTC.
- `dse~TestAgentSafeEntA9317@1` cited for a `&#46;`-obfuscated URL; its body is
  entirely a German umlaut test with no URL at all.
- `rnstamp` should be `rndstamp`; `OAIFlatheBridgeTestMay24X` should be
  `OAIFlatheadBridgeTestMay24X`.

### Interpretation presented as fact

- "The agents generated these **deliberately as a sweep**, enumerating the
  encoding-depth axis" — uncited. The depth-3 census is dominated by `%25252F`,
  `%25253A`, `%252520`, which is what mechanical URL-in-URL nesting through
  proxy chains produces anyway. Nothing distinguishes intent from accumulation.
- "Agents leaked **working** API keys" — no validation was attempted, and none
  should be. They are *credential-shaped strings*, described by class and location.
- "The chain **failed** (wiki escaping held)" — the source says only "no evidence
  that this succeeded" and "it's not obvious why". The mechanism was our addition.
- The blob-bypass step "proxy sees allowed domain … POST passes" is a model of
  proxy internals; no cited revision describes proxy behaviour.

### Reproducibility fixes applied

- `scripts/encoding_sweep.py` is now vendored here (it lived outside the repo).
  Its `NEW`/`KNOWN` column used to be derived by grepping a findings document at
  an absolute path outside the repo — when that document changed, **13 rows
  flipped `NEW` → `KNOWN`, including all 9 microlink rows**, so the headline
  finding self-reported as already-known. The novelty test now lives in
  `scripts/novelty_check.py`, which is versioned and tests against the writeup.
- The sweep **redacts on write.** Regenerating the CSV from the database
  reintroduced 9 live credential occurrences into a tracked file; the script now
  pipes its output through `redact.py` rather than leaving that to a step someone
  might forget.
- `build_db.py` exposes `revision_id` as an alias for `rev_id`, so scripts written
  against the researchers' own schema run unchanged.
- Lanes 2 and 3 ship **no scripts**, which is why their regex-derived counts could
  not be hit exactly. Those figures are marked approximate above.
- `corpus/live/attacklog_raw_dse_2605.jsonl` is referenced as the source for all
  101 probe events and the XSS request log, but is **not in the published dataset**.
  That part of lane 3 is reproducible only as far as the rendered writeup.

---

## Method note

The novelty test — "a finding is new if the term appears 0 times in the writeup" —
is useful but not self-validating. Two failure modes bit us:

1. **Substring collisions.** A short token matches inside an unrelated identifier.
   Any count of 1–2 must be inspected by hand; `agentcounty` above is the worked
   example.
2. **Counting surface.** Counting tag-stripped text misses terms that appear only
   inside `href` attributes, which are still mentions. `novelty_check.py` now
   reports raw-HTML and visible-text counts side by side and asserts on the raw one.
