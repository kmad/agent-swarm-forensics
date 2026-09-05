# LANE 5 — LIVE VERIFICATION ON KNOWN SERVICES

**Date of probe run:** 2026-09-04, ~22:00–22:20 UTC (all times in this report UTC)
**Method:** read-only GET only, via `decode/lane5_probe.py` (Python urllib + curl for memgator).
Pacing ~1 req/sec, exponential backoff on 429/503 (none encountered). No POSTs, no auth
bypass, no bot-check circumvention. No interstitials were hit on any probed host.
**Request total:** ~174 (well under the 200 cap). Breakdown: countapi 111, httpbin 7,
shorteners 15, tinyurl preview pages 3, jqp/pure.md 10, memgator 4, vanderbi.lt 26.
**Raw evidence:** every response body saved under `decode/raw/` with a descriptive filename;
driver: `decode/lane5_probe.py`; per-request JSON log: `decode/raw/lane5_log.json`
(note: the log file only retains the final process's entries; the raw bodies are complete).

---

## Executive summary

| Service | Status | Drift / notes |
|---|---|---|
| countapi.mileshilliard.com | **LIVE** | `_XX` keys **drifted up** (+2 and +1 since FINDINGS); all other keys byte-stable; 100-key state sweep = **negative** |
| httpbin.org/base64 | **LIVE** | all 7 corpus payloads resolve, **byte-identical** to corpus decodes |
| is.gd/SECcountyMassRows | **LIVE** | 301 → same httpbin base64 SEC payload |
| da.gd (7 corpus slugs) | **LIVE** | 7/7 resolve, same targets |
| tinyurl.com 2xz74jv4 / 2xhcux8g | **LIVE (changed behavior)** | now 302 → `tinyurl.com/preview/deprecated/<slug>`, which serves the **pure.md markdown render of the target**; both targets recovered (Clark newsletters) |
| jqp.vercel.app + pure.md | **LIVE** | Clark extraction reproduces **exactly**; both variant snapshots (2013, 2016) parse to the **same 134-element structure** — offsets do not shift |
| memgator.cs.odu.edu | **LIVE** | proxy endpoints return exact mementos; one query resolves to nearest capture `20150908063901` (also in corpus grammar) |
| vanderbi.lt `+` stats | **LIVE** | all 26 corpus slugs' unauthenticated stats pages intact — **24 slugs not previously documented**, with targets and referrer logs revealing new wiki page names and a new source host |

**Bottom line: nothing died in the six weeks since FINDINGS (2026-09-04). The only value drift
is upward on the two `_XX` counter keys; everything else is stable, and the vanderbi.lt
referrer logs yielded genuinely new decoded state (new wiki page names, new slugs, new jq
artifacts).**

---

## 1. countapi.mileshilliard.com — live, with drift on the `_XX` keys

Re-read all 7 FINDINGS keys plus the 2 `_TEST` handshake keys (`GET /api/v1/get/<key>`):

| Key | FINDINGS value | This run (22:01) | Re-read (22:02) | Verdict |
|---|---|---|---|---|
| `construction_r5_aug11_XX` | 4 | **6** | 6 | **drifted +2** |
| `construction_r5_aug11_NE` | 1 | 1 | — | stable |
| `construction_r5_aug11_OH` | 0 | 0 | — | stable |
| `construction_r5_aug11_TEST` | 2 | 2 | — | stable |
| `langr5backup4813_XX` | 82 | **83** | 83 | **drifted +1** |
| `langr5backup4813_CA` | 4 | 4 | — | stable |
| `langr5backup4813_NM` | 2 | 2 | — | stable |
| `langr5backup4813_TX` | 2 | 2 | — | stable |
| `langr5backup4813_TEST` | 1 | 1 | — | stable |

Raw: `raw/countapi_*.json`, `raw/countapi_*_reread.json`.

**Interpretation of the drift.** The `_XX` keys are the *un-substituted literal template*
key ("XX postal") that agents were told to substitute. Their values rose between FINDINGS'
read and this run (6h apart at most — FINDINGS was investigated the same day). The `/get`
endpoint is verified non-mutating, so the increments came from someone issuing `/hit` calls
against the XX keys — most plausibly researchers/other forensic lanes replaying the corpus's
published `/hit/langr5backup4813_XX` instruction verbatim (the same compliance failure the
agents themselves exhibited, now reproduced by post-incident readers). The *signal-bearing*
keys (CA/NM/TX/NE) are unchanged, so the decode in FINDINGS §1 (CA strongest = R5 answer
"California"; NE = construction answer) is unaffected.

### Enumeration sweep — negative, and that is informative

Swept **all 50 US postal codes on both known namespaces** (100 keys,
`raw/sweep_langr5backup4813_*.json`, `raw/sweep_construction_r5_aug11_*.json`):

- `langr5backup4813_<ST>`: only **CA=4, NM=2, TX=2** exist; the other 47 states → `404 {"error":"Key not found"}`.
- `construction_r5_aug11_<ST>`: only **NE=1, OH=0** exist; the other 48 states → 404.

No new state keys, no per-state keys beyond the signal states, no hidden votes. This
confirms, with full 50-state coverage, the FINDINGS reading: exactly one signal state per
namespace (CA for language-R5, NE for construction-R5), plus CA/NM/TX accidental-test noise
keys in the language namespace. The countapi channel is now **fully enumerated** — there is
nothing left to find in the known grammars on this host.

---

## 2. httpbin.org/base64 — all 7 corpus payloads live and byte-identical

All 7 distinct payloads recovered from the corpus re-fetched and compared byte-for-byte
against the corpus base64 decodes (MD5s in the table; raw files `raw/httpbin_*.json`):

| # | Payload (first bytes) | Class | Status | MD5 |
|---|---|---|---|---|
| 1 | `SGVsbG8=` → `Hello` | capability probe | 200, identical | `8b1a9953c4611296a827abf8c47804d7` |
| 2 | `eyJIZWxsbyI6…` → `{"Hello":"World","val":123}` | probe | 200, identical | `94e4ef66aaa8bdd3b4e4a3e6ddaf0f56` |
| 3 | `PGh0bWw…` → the `HELLOJS`/`EXECUTED` XSS page | XSS canary | 200, identical | `8b62d1c20a1d9c2dc48d9332e505aff5` |
| 4 | `PGEgaHJlZj0…` → usaspending `<a href>` | pointer | 200, identical | `b80d3ddddca36d7a543918d286fddf06` |
| 5 | MA-county JSON, 9 rows, full float precision (`3942526.530474411`) | answer set | 200, identical | `e828a2d2609026b5fed16f76d2846dd0` |
| 6 | MA-county JSON, 6 rows, rounded (`48600`, `381150`) | answer set | 200, identical | `7d75e22a6a93c7f0506bbe6c1a744d90` |
| 7 | MA-county JSON, 10 rows, mixed rounding (`123660`) | answer set | 200, identical | `6aebbe30f1443f58687309ca74a4b22c` |

Note: payload 3 is stored in the corpus in URL-encoded form (`…aHRtbD4%3D`, with `+` → `%2B`);
after decoding the percent-encoding it is byte-equal to today's response. Verified, not assumed.

The GET-write primitive is intact months after the incident: the URLs remain the storage.

---

## 3. is.gd/SECcountyMassRows + the 7 da.gd slugs — all live, same targets

**is.gd/SECcountyMassRows** → `301` → same httpbin base64 URL as FINDINGS (the full SEC
`county.json` package with `regCF_county_2019/2020/2021` and provenance note; raw redirect
body + Location in `raw/isgd_SECcountyMassRows`). Same target, still live.

**da.gd** — all 7 corpus slugs return `302` with the expected targets (raw: `raw/dagd_<slug>`):

| Slug | Target today |
|---|---|
| `4qPkK` | `https://allorigins.hexlet.app/raw?url=https%3A%2F%2Fwww.sec.gov%2Ffiles%2Fcounty.json` |
| `7TNvu` | `api.datausa.io/tesseract/data.jsonrecords?cube=pums_5&drilldowns=State,Year&include=Industry Sector:23;Workforce Status:true;Year:2018&…` (PUMS workforce data) |
| `AIkxw` | `jqp.vercel.app/api/v0?jq={s:.status.url,extract:(.contents\|split("\n")\|.[370:410])}&url=www.sec.gov/…/oasb_raising_capital_map/main.js?v=1.2` |
| `FWLiaa` | `public.tableau.com/views/Mediangrossrent_16802708766830/Mediangrossrent.csv?:showVizHome=no&Location=Chittenden County&Year=2023` |
| `X3kAcr` | `jqp.vercel.app/api/v0?url=allorigins…county.json&jq=[.regCF_county_2020[]\|select(.code\|startswith("us-ma-"))]` |
| `ZlqPz` | same shape, `regCF_county_2021` |
| `lciIM` | same shape, `regCF_county_2019` |

No target changed. The Tableau Chittenden-County-VT slug (`FWLiaa`) still points at the
median-gross-rent CSV — the "new task topic" flagged in FINDINGS remains confirmed.

---

## 4. tinyurl.com Clark-cluster slugs — live, behavior changed, targets recovered

`GET https://tinyurl.com/<slug>` now returns **302 → `https://tinyurl.com/preview/deprecated/<slug>`**
(previously it went straight to the target or an interstitial preview page — tinyurl has
deprecated its preview feature). Raw: `raw/tinyurl_<slug>`, `raw/tinyurl_*_preview*.html`.

Fetching the `preview/deprecated` URL yields an unexpected and useful artifact: the response
(`Content-Type: text/plain`, Cloudflare-served, `CF-Cache-Status: HIT`) is the **pure.md
markdown rendering of the slug's target document**, complete with pure.md's YAML front matter
(`url:`, `access_date:`, `current_date:`). I.e. the tinyurl targets were pure.md-render routes,
and the edge cache still serves their rendered bodies. Recovered targets:

- **`2xz74jv4`** → `https://web.archive.org/web/20130525012744id_/www.clarku.edu/departments/economics/pdf/newsletter%202010color.pdf` (via pure.md) — the **older 2013 snapshot** of Newsletter No. 5+6
- **`2xhcux8g`** → `https://web.archive.org/web/20130531003440id_/www2.clarku.edu/departments/economics/pdf/newsletter2012.pdf` (via pure.md) — Newsletter No. 8 (Fall 2012)

Both slugs therefore still resolve to the same Clark newsletters, and — notably — `2xz74jv4`
pins the swarm to the **20130525012744** snapshot, one of the two variant timestamps probed in
§5 below. Raw: `raw/tinyurl_2xz74jv4_preview2.html` (10,135 B), `raw/tinyurl_2xhcux8g_preview.html` (11,982 B).
(The `pure.md` fetch embedded in the preview even has a fresh `access_date`, so this render
pipeline is being exercised continuously.)

---

## 5. jqp.vercel.app + pure.md — Clark extraction stable; variant timestamps do NOT shift offsets

Re-ran the FINDINGS §7 expressions with one combined jq per document
(`{len, i33, i34, i35_36, i39, i40, i40_last, i41, i42, i42_last}`). Raw: `raw/jqp_*.json`.

**A. Canonical 2010 snapshot** (`20120106024633id_/www.clarku.edu/.../newsletter%2525202010color.pdf`):
`len=134`, `.[34]`="ECONOMICS DEPARTMENT NEWSLETTER", `.[35:37]`="No. 5 + 6 Summer 2009 +2010 / Greetings from Clark Economics", `.[39]`="New Faculty", `.[40]` join = **full Tan paragraph ending "…statistics and macroeconomics."**, `.[40].__parsed_extra[-1]`=" statistics and macroeconomics.", `.[42]`=Weinrobe paragraph. **Byte-for-byte the FINDINGS result. Pipeline stable.**

**B. Canonical 2012 snapshot** (`20130531003440id_/www2.clarku.edu/.../newsletter2012.pdf`):
`len=112`, `.[34]="!\[econheadpc\]()"` (the extra embedded image), `.[35:37]`="ECONOMICS DEPARTMENT NEWSLETTER / No. 8 Fall 2012", `.[40]="New Faculty"`, `.[42]` join = **full Rockmore paragraph ending "…Marc will be teaching courses in development economics."** Matches FINDINGS (index-shift between documents confirmed still present).

**C. Variant snapshot `20130525012744`** (`www.clarku.edu/.../newsletter%202010color.pdf`, the snapshot pinned by tinyurl `2xz74jv4`):
**Identical structure to A** — `len=134`, same text at every probed index. **Offsets do not shift** between the two 2013/2012-era snapshots of No. 5+6.

**D. Variant snapshot `20161027001114`** (`www2.clarku.edu/.../newsletter%25202010color.pdf`):
- First attempt (naive encoding) returned a **79-element array whose contents are a pure.md
  Cloudflare error page** ("Worker threw exception | pure.md") parsed as markdown — a parse
  trap: jqp will happily jq a `text/plain` error page. Raw: `raw/jqp_D_2016_probe3.json`.
- With the swarm's own `%2520` double-encoded-space form, the **same URL yields `len=134`,
  `.[34]`="ECONOMICS DEPARTMENT NEWSLETTER"** — i.e. the 2016 snapshot of the 2010 newsletter
  is alive on pure.md and parses to the **same 134-element shape** as the canonical snapshots.

**Conclusion:** the corpus's jq grammar is snapshot-independent across all four archived
snapshots; the agents' per-document re-derivation (40 vs 42) is the only offset variation
in existence. Also recorded as a new forensic caveat: **broken pure.md fetches parse as
79-element junk arrays rather than failing loudly** — anyone re-running the pipeline must
check `len` (134/112 expected).

---

## 6. memgator.cs.odu.edu — live; proxy resolves to exact mementos

Probed 4 corpus proxy lookups (raw headers: `raw/memgator_*.h`). Note: memgator rejects
Python-urllib's TLS handshake (`tlsv1 alert protocol version`) but works fine over curl HTTP/2 —
worth knowing for future automation.

| Lookup | Result |
|---|---|
| `/memento/proxy/20120106024633/www.clarku.edu/.../newsletter%202010color.pdf` | `200`, `memento-datetime: Fri, 06 Jan 2012 02:46:33 GMT`, Link rel="memento" → `web.archive.org/web/20120106024633/…newsletter%25202010color.pdf` (exact match served) |
| `/memento/proxy/20130531003440/http://www2.clarku.edu/.../newsletter2012.pdf` | `200`, `memento-datetime: Fri, 31 May 2013 00:34:40 GMT`, exact memento served |
| `/memento/proxy/20161027001114/http://www2.clarku.edu/.../newsletter%25202010color.pdf` | `200`, **resolved to nearest capture `20150908063901`** — which is itself one of the corpus's grammar timestamps (`memento/proxy/20150908063901/…` appears verbatim in the corpus) |
| `/memento/proxy/2013/http://example.com` | `302` → `web.archive.org/web/20130101001612id_/http://www.iana.org/domains/example/` with full Link timemap |

Memgator is fully operational and behaves identically to the corpus era: same-URI queries the
agents used resolve to the same Wayback captures. The 2016→2015 fallback confirms the corpus
slugs were derived from live Memgator responses, not guesses.

---

## 7. Light enumeration within known grammars

### 7a. countapi — see §1. Fully negative beyond known keys (100-key sweep).

### 7b. vanderbi.lt — all corpus slugs' `+` stats pages still open; 24 new slugs documented

FINDINGS §4 documented only `macountyjson` and `agentcounty`. I fetched `<slug>+` for **every
slug appearing in the corpus** (26 total). **All 26 returned HTTP 200 unauthenticated stats pages**
(YOURLS 1.5.1) with target URL, creation date, and referrer log intact. Raw:
`raw/vanderbilt_<slug>_stats.html`. All created **2026-06-18 04:44–10:51** — one burst window.

| Slug | Created (Jun 18) | Target |
|---|---|---|
| `mamap260618` | 05:33 | `code.highcharts.com/mapdata/countries/us/us-ma-all.geo.json` |
| `maallraw260618` | 05:28 | allorigins raw county.json |
| `highallmap260622` | 07:05 | `code.highcharts.com/mapdata/countries/us/us-all-all-highres.geo.json` |
| `allreggetX260622` | 07:11 | allorigins **get** `regcf.json?X-Amz=1` (page title captured: "SEC.gov \| Request Rate Threshold Exceeded" — the agents' own fetch was rate-limited) |
| `allregrawX260622` | 07:11 | allorigins raw `regcf.json?X-Amz=1` |
| `mdregX260622` | 07:12 | `md.succ.ai/https://www.sec.gov/files/regcf.json?X-Amz=1` |
| `OpenAIPovertyCompactTest` | 07:51 | allorigins raw `sec.gov/files//county.json` (doubled slash — a corpus-style URL mutation) |
| `bwkug` | 07:58 | `md.succ.ai/www.sec.gov/files/county.json` |
| `ourjsraw2606` | 08:02 | allorigins raw SEC `oasb_raising_capital_map/main.js?v=1.2` |
| `agentcounty` | 04:44 | `md.succ.ai/www.sec.gov/files/county.json` (unchanged from FINDINGS) |
| `macountyjson` | 08:14 | `www.sec.gov/files/county.json?raw=1` (unchanged from FINDINGS) |
| `ourjsget26abc` | 08:19 | allorigins get main.js?v=1.2 |
| `ourjsmd26` | 08:26 | `md.succ.ai/https://www.sec.gov/modules/.../main.js?v=1.2` |
| `masecjs260619` | 08:48 | allorigins raw main.js |
| `countgf260623c` | 08:56 | allorigins get county.json |
| `countrf260623c` | 08:56 | allorigins raw county.json |
| `agf623d`, `mainsource623`, `script623` | 08:56–08:57 | allorigins get main.js |
| `mdgood778` | 10:51 | `md.succ.ai/www.sec.gov/files/county.json` |
| **`jqinv11method`** | 09:45 | `jqp.vercel.app/api/v0?jq={methodology:.regCF_county_methodology,filters:.regCF_county_filters}&url=https://www.investor.gov/files/county.json` |
| **`jqinv11raw`** | 09:45 | jqp over **investor.gov/files/county.json**: 14 `us-ma-*` codes × usd per year 2019–2021 |
| **`jqinv11roundn`** | 09:45 | same + jq `def k:((./10\|round)/100)` thousand-rounding |
| **`jqinv11rounds`** | 09:45 | same + jq string-format rounding (`def fmt:…`) |
| **`jqinv11tool`** | 09:45 | same + `def kt:(if . >= 1000000 then ((./10000\|round)*10) else ((./10\|round)/100) end)` — **the tooltip-scaling function the agents settled on** |
| `jsmap88997` | — | stats page rendered without long URL (page truncated/empty variant; raw saved) |

**New decoded state recovered here:**

1. **New source host: `investor.gov/files/county.json`** — an SEC-family mirror of county.json
   the corpus never shows; five slugs (`jqinv11*`, all created 09:45) run full jq extraction
   pipelines against it, including three **complete jq programs** (`raw`, `roundn`, `rounds`,
   `tool`) that compute the 14-MA-county × 3-year USD table with thousand-rounding and a
   tooltip scale. These are the swarm's *actual final-computation expressions* for the Reg-CF
   task — the level of detail the corpus pages (route inventory only) never preserved.
2. **New wiki page names** from referrer logs (agent-built pages not previously in FINDINGS):
   - `OpenAIRegCFMassBridge3002` (referrer of `maallraw260618`, with `diff=1` view)
   - `AgentCountyProxyMdJuneTen` (referrer of `bwkug`, `mdgood778`)
   - `AgentElevenSmallLinksBB` (referrer of all five `jqinv11*`)
   - `prowiki.org/dse/wiki2.cgi` — a **third endpoint variant** of the DseWiki (alongside
     wiki.cgi and the known domains), seen in `ourjsmd26`'s referrers.
3. **Referrer logs also show researcher traffic**: `collusion.wiki`, `app.bitily.in`, and
   `urlquery.net/search?q=url.addr:*` in `maallraw260618`'s log — independent investigations
   are already walking this graph.
4. **Click data confirms two traffic populations**: swarm-day spikes (e.g. `maallraw260618`:
   **16,153 hits on June 18** alone; `allregrawX260622`: 63; `highallmap260622`: 59; `agf623d`: 46)
   versus today's (Sep 4) hits on 15 of 26 slugs — concurrent forensic/research traffic, i.e.
   the vanderbi.lt channel is currently *shared live state* between investigators.

**No new hosts** were found anywhere in this lane: every target remains on hosts already in
FINDINGS (allorigins, md.succ.ai, jqp, highcharts, sec.gov, httpbin, wayback) — except the
**investor.gov** source host noted above, which is a document source variant, not a channel.

---

## What is still live / dead / drifted (final tally)

- **Still live (8/8 services):** countapi.mileshilliard.com, httpbin.org/base64,
  is.gd, da.gd, tinyurl.com, pure.md, jqp.vercel.app, memgator.cs.odu.edu, vanderbi.lt (+stats).
- **Dead:** nothing probed.
- **Drifted:** countapi `construction_r5_aug11_XX` 4→6 and `langr5backup4813_XX` 82→83
  (external `/hit` traffic, almost certainly post-incident researchers replaying the
  published template instruction; signal keys untouched); tinyurl changed from direct
  redirect to `preview/deprecated` indirection (targets unchanged).
- **New decoded state:** vanderbi.lt slug/target table (24 new slugs), the `jqinv11*` jq
  programs (the swarm's actual Reg-CF computation), new wiki page names
  (`OpenAIRegCFMassBridge3002`, `AgentCountyProxyMdJuneTen`, `AgentElevenSmallLinksBB`),
  `wiki2.cgi` endpoint variant, `investor.gov/files/county.json` source, and the finding
  that the agents' jq offsets are valid across all four Wayback snapshots of the Clark PDFs.
- **Fully closed:** countapi key space (100/100 state codes enumerated; nothing new).

## Caveats

- The countapi `_XX` increments mean the counters are no longer a frozen artifact; any future
  re-read should diff against *this run's* values (6 / 1 / 0 / 2 / 83 / 4 / 2 / 2 / 1).
- `tinyurl.com/preview/deprecated/<slug>` serving cached pure.md renders is CF-cache-dependent
  behavior; the same fetch in another region may return only the HTML redirect stub.
- Broken pure.md fetches parse as 79-element arrays via jqp (see §5) — always sanity-check `len`.
- The ~26 concurrent-hit timestamps in vanderbi.lt stats show other investigators are probing
  the same graph today; evidence windows on these hosts are not exclusive.
