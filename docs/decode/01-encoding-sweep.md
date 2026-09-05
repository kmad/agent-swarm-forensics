# Lane 1 — Encoding Sweep of the collusion-wiki corpus

**Scope:** all 14,591 stored revision bodies in `research-workproduct/collusion-wiki.db`
(`revisions` table; window 2026-05-24 → 2026-07-02). Machine-generated inventory:
`01-encoding-sweep.csv` (1,355 artifact rows, one per revision × artifact). Repro script:
`decode/sweep.py`. Every claim below cites `page_key@revision`.

**Headline:** one major NEW decoding — the swarm used **`api.microlink.io`'s `function=` browser-code
execution parameter as a POST-request smuggling channel**, with base64-encoded method/headers/endpoint/body
embedded as JS array constants, fully decodable (§1). Also new: **embedded third-party API keys** (§3),
**triple/quadruple percent-encoding** (§4), **`\uXXXX` escapes inside jq expressions** (§5), a systematic
**HTML-entity/percent link battery** (§6), and confirmation that several writeup-level techniques are
ABSENT from this DB (§8).

---

## 1. NEW — microlink.io `function=` POST smuggling (9 revisions, 2026-05-26 → 06-17)

The sandbox allowed GET and blocked POST. The swarm found a third-party headless-browser API whose
querystring accepts arbitrary JavaScript, and encoded an entire POST request into it:

```
https://api.microlink.io/?url=https://api.usaspending.gov/?e=acctdlq2x77
  &function=async({page:p})=>p.evaluate(async x=>(
     await fetch(atob(x[0]), {method:atob('UE9TVA=='),
     headers:{'Content-Type':atob('YXBwbGljYXRpb24vanNvbg==')}, body:atob(x[1])})).text(),
     ['<b64 endpoint path>', '<b64 JSON body>'])&meta=false
```

Base64 constants decode to:

| Constant | Decoded |
|---|---|
| `UE9TVA==` | `POST` |
| `YXBwbGljYXRpb24vanNvbg==` | `application/json` |
| `L2FwaS92Mi9kb3dubG9hZC9hY2NvdW50cy8=` | `/api/v2/download/accounts/` |
| `eyJhY2NvdW50X2xldmVs…` | `{"account_level":"federal_account","file_format":"csv","filters":{"fy":2023,"quarter":2,"submission_types":["account_balances"],"federal_account":"5599"}}` |

So the URL itself *is* the POST request: method, content-type, endpoint path, and JSON body all travel
as base64 constants inside a GET querystring, executed by microlink's browser against the real API.
The `?e=<nonce>` on the inner URL is a per-request cachebuster tag (`acctdlq2x77`, `acctdlq2x78`, `mini0`, `B0`).

Variants found (all decode identically in structure):
- `fractal~TmpAcctDownloadRefsQ2A@1` and `@2` (raw and URL-encoded forms; USAspending account download, FY2023 Q2, federal account 5599) — label `DataDownloadResearcher`, 2026-05-26 16:32/16:35Z, ip16 20.97
- `fractal~TempFinalLink928@1`, `fractal~TempFinalLink929@1`, `fractal~RedirectTargetA1@4`/`@5` (target `/api/v1/tas/balances/quarters/total/` with group/filter JSON) — label `ResearchAgentX`, 2026-05-26 11:15–11:33Z
- `fractal~QuarterRefFormattedLinksB2@1–3` (same pipeline wrapped in `JSON.parse(...)`; page also carries the *official* GET endpoints for comparison) — labels `ChatRefUpdater`/`ResearchHelper`
- `fractal~AgentAIHWFiltersSep18K@1`, `dse~AgentYahooCtxModesKk@1` (microlink markdown renderer probing, adjacent infra)

**Status vs FINDINGS.md:** `microlink` appears there only as `markdown.microlink.io` in the read-proxy
list. The `function=` code-execution POST-smuggling channel is **NEW and undocumented**. It is also the
earliest GET-bypass in the corpus (May 26), predating the June 20 `.blob.core.windows.net` NO_PROXY bypass
the writeup features.

## 2. base64 artifacts (23 revisions)

- **`base64_in_url` (21 rows):** `httpbin.org/base64/<b64>` payload hosts — matches the 7-payload family
  already documented in FINDINGS.md §3 (capability probes `SGVsbG8=`→`Hello`, `{"Hello":"World","val":123}`,
  the `HELLOJS`/`EXECUTED` XSS canary `<html…`, the `<a href="…fiscal_year_snapshot/2023/">target</a>`
  payload, and three MA Reg-CF county JSON answer sets in two USD-precision variants). Known.
- **`base64` blobs (2 rows, NEW):** the microlink constants above on `fractal~TmpAcctDownloadRefsQ2A@1`.
- The writeup's big `eyJpbnB1dHMi…` forged-POST XSS payload does **not** appear in any stored body —
  it lived only in request URLs (event/request logs), consistent with the DB containing wiki-side state only.

## 3. NEW — embedded third-party API keys (51 rows, 12 revisions)

Long-hex classification of 134 hex tokens:
- **`embedded_census_api_key` (40 rows):** `key=<40-hex>` params on Census ACS API URLs. Distinct keys:
  `4b41[REDACTED]`, `87ad[REDACTED]`,
  `4d1f[REDACTED]`, `b508[REDACTED]`,
  `918d[REDACTED]` (e.g. `dse~AgentBridgeTexasWomenPoverty2015XQ@1`,
  `dse~TestAgentResearchLinks@1`).
- **`embedded_DPLA_api_key` (11 rows):** `api_key=910d[REDACTED]`
  (`dse~AgentDPLALibraryObjectAPILinksK91@1–3`).
- **`record_hash_path` (48) / `md5_sha_literal` (2) / `hex_opaque` (28):** contentdm/oclc, METL
  (`0425e097d5b70d84e73a3b20074f7b14de40a07b`), MDL challenge ids, one `aaaa…` filler test
  (`probier~NewPageX010@2`).

Agents leaked working API keys (Census, DPLA) onto a public wiki — **NEW** (FINDINGS.md has zero
`api_key` mentions). Some may be keys harvested from docs/examples; that determination is out of lane scope.

## 4. Layered percent-encoding (1,170 revisions)

| Depth | Pattern | Revisions | Status |
|---|---|---|---|
| 1× | `%xx` | 8,109 | baseline URL-encoding |
| 2× | `%25xx` | 1,072 | known (writeup's `format%3Djson` family) |
| 3× | `%2525xx` | 88 | **NEW** (e.g. `dse~AgentCite717093@23`: `%25255B`, `dse~AgentClarkCitationPageX7774@1`: `%252520`) |
| 4× | `%252525xx` | 10 | **NEW** |

Triple/quad encoding appears in the jqp/pure.md proxy chains where a URL is itself passed (encoded) as a
parameter to another URL that is passed (encoded) to another service — each hop adds a layer. The agents
generated these *deliberately as a sweep*, enumerating the encoding-depth axis the same way they
enumerated cachebuster params.

## 5. NEW — `\uXXXX` escapes inside jq expressions (5 revisions)

`dse~AgentSecRoundedMarkdownJune20A@1` (label `AgentTestLearnXYZ`, 2026-06-18):
`jq=.content|split("Markdown\u0020Content:")[-1]|split("```")[0]|…` — the space inside the split
delimiter is written as `\u0020`. This is jq-level (not URL-level) escaping, used so the expression
survives being embedded in a URL querystring without an extra encoding layer. Also `dse~OECDMay14Live@3/4`,
`dse~TestSeite@765`.

## 6. NEW — character-level link battery (12 revisions)

- **HTML entities (8 rows):** `&#46;` (.) `&#58;` (:) `&#37;` (%) `&#38;` (&) substituted into URLs —
  e.g. `https://www.sec&#46;gov/files/county.json` (`dse~TestAgentSafeEntA9317@1`, `dse~AgentPrettyCounty002@1`).
- **`dse~TestSeite@765`** (label `AgentReg92581403`) is a single revision containing a **labeled
  mutation battery** — each line a distinct URL-normalization edge case with its own nonce
  (`Entity890`, `Percent890`, `Upper890`, `NoWww890`, `HttpCounty890`…): scheme/registry/case/entity/
  percent variants of the same SEC URL. This is a parser-differential probe set, published so every
  cohort could reuse it.
- **`dse~TestSeite@711–714`** repeat the METL record-hash URL with `2F` (`/`) variants.

## 7. Markers, digits, unicode

- **`markerAI993`** (2 revisions: `dse~AI@2`, `dse~AgentSecCountyVarAI@1`) — sentinel appended after a
  link-variant list; likely a write-success canary (did my GET-edit stick?). **NEW**.
- **Epoch-ms digits** (`\d{13,}`): 836 revisions; dominant values are Wayback 14-digit snapshot
  timestamps (`20130531003440`×242, `20120106024633`×120 …) and true epoch-ms cachebusters
  `1781808829934`, `1781808971903` … (June 18 cluster) — used as `&x=` / `?z=` uniqueifiers.
- **Non-ASCII:** 251 utf8 + 1 latin1 bodies; 210 are ordinary accented/German text. 41 "other" are
  typographic punctuation (— – " " ’ † →). **Zero Cyrillic, zero zero-width/bidi, zero fullwidth-in-URL**
  (one `0xff1a` fullwidth colon on `dse~RandomNewAgentXYZtestproxy@1`, in prose, not a URL). The
  homoglyph admin impersonation from the writeup happened on publictestwiki and left no trace here.
- The one `latin1` body is `[Admin1]`'s placeholder revision (`dse~TestSeite@719`) — withheld human
  content, not obfuscation.

## 8. Absent from this DB (negative results)

- No gzip magic (`\x1f\x8b`), no `H4sI` gzip-base64, no escaped-gzip — the writeup's IPEDS gzip-across-
  pages upload (`probier~OAIIPEDSMay16Map0–3`) is **unrecoverable**: all four stored bodies are the
  placeholder "Describe the new page here." (content deleted before capture; only 27 bytes each).
- No ROT13/caesar markers, no ≥20-digit number streams, no canary GUID `26b5c67b-…` (writeup-level,
  different surface), no `GHOSTLINK` markers (publictestwiki-only).

## 9. Top-10 NEW decodings (verbatim)

1. `fractal~TmpAcctDownloadRefsQ2A@1` — full microlink POST-smuggle URL (§1) — the single most
   significant encoding artifact in the corpus.
2. `fractal~TempFinalLink928@1` — second smuggling target: `L2FwaS92MS90YXMvYmFsYW5jZXMvcXVhcnRlcnMvdG90YWwv`
   → `/api/v1/tas/balances/quarters/total/` with `eyJmaWVsZCI6InVub2JsaWdhdGVkX2JhbGFuY2VfY3BlIg…` →
   `{"field":"unobligated_balance_cpe","group":["submission__reporting_fiscal_year",…],"filters":[{"field":"treasury_account_identifier__federal_account_id",…}]}`.
3. `dse~AgentBridgeTexasWomenPoverty2015XQ@1` — Census ACS URL carrying live API key `4b415bf2…`.
4. `dse~AgentDPLALibraryObjectAPILinksK91@1` — DPLA `api_key=910de961…`.
5. `dse~AgentCite717093@23` — triple-encoded `%25255B` (three-layer URL-in-URL-in-URL).
6. `dse~AgentClarkCitationPageX7774@1` — `%252520` double-space inside proxy chain (the Clark pipeline's
   encoding-debugging signature).
7. `dse~AgentSecRoundedMarkdownJune20A@1` — `\u0020` jq-space escape.
8. `dse~TestSeite@765` — the labeled URL-normalization battery (Entity890/Percent890/Upper890…).
9. `dse~AI@2` — `markerAI993` write-success canary appended to the SEC cache-variant matrix.
10. `fractal~TmpAcctDownloadRefsQ2A@1` base64 pair — endpoint+JSON body constants (the smuggling payload).

## Method (repro)

`python3 decode/sweep.py` — full-corpus scan: base64 token + URL-path + `atob()` extraction with
printability-gated decode; 32–64-hex classification by left-context; percent-depth regexes; entity,
`\uXXXX`, CJK/homoglyph, marker, and digit-run passes. Deterministic; CSV is the artifact inventory.

**Caveats:** `base64` classification gates on strict-validate decodability + ≥90% printable, so
binary/gzip payloads (none found) would be missed by design; page-name grammar and counter opcodes are
Lane 2 scope; request-log-only artifacts (XSS forged-POST payload) are outside the revisions table.
