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

## Method note

The novelty test — "a finding is new if the term appears 0 times in the writeup" —
is useful but not self-validating. Two failure modes bit us:

1. **Substring collisions.** A short token matches inside an unrelated identifier.
   Any count of 1–2 must be inspected by hand; `agentcounty` above is the worked
   example.
2. **Counting surface.** Counting tag-stripped text misses terms that appear only
   inside `href` attributes, which are still mentions. `novelty_check.py` now
   reports raw-HTML and visible-text counts side by side and asserts on the raw one.
