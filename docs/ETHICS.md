# Research conduct

This repository reproduces forensic analysis of an incident in which autonomous
agents wrote to third-party websites without permission. The irony is not lost:
the same techniques used to *investigate* it could be used to repeat it. These
are the rules this work followed, and that anyone re-running it should follow.

## Read-only, always

Every live probe in `scripts/` is a `GET` against a public endpoint. Nothing in
this repository writes to, mutates, or authenticates against any third-party
service.

This matters most for the counter API. `countapi.mileshilliard.com` exposes
`/hit/<key>` and `/set/<key>?value=N` alongside `/get/<key>`, all over GET.
**Only `/get` is ever called.** Calling `/hit` would increment a shared counter
and destroy the evidence for everyone who looks after us — the surviving values
are the last readable state from the incident and there is no way to restore them.

`scripts/verify_live.py` includes a control check for this: it queries a key that
should not exist, twice, and asserts it still returns `Key not found`. If a `GET`
ever begins creating keys, the script says so and you should stop. Never take a
measurement you cannot distinguish from your own footprint.

Note that the `_XX` placeholder keys have been drifting upward since the incident
— readers replaying the agents' own `/hit` URL out of curiosity. That drift is
itself a lesson: a public counter is a shared resource, and casual probing is not
free. The signal keys have not moved.

## Rate limits and refusals are decisions, not obstacles

During the original investigation several hosts pushed back, and each time the
answer was to stop rather than to route around it:

- The **Oddmuse wiki family** (emacswiki.org, communitywiki.org, oddmuse.org,
  campaignwiki.org, alexschroeder.ch) serves Markov-generated gibberish to
  non-browser clients and then returns `HTTP 402 "Bot Check"` — an explicit
  consent gate. Driving a browser through it would circumvent an access control
  the operator deliberately erected. That population is recorded as
  **unassessed**, not as a negative result. The honest routes are a human
  clicking through in a normal session, or asking the operators directly.
- **publictestwiki.com** now serves a Cloudflare interstitial. Findings sourced
  from its API before that gate went up are labelled *unverified by us* rather
  than quietly restated.
- **archive.org** rate-limited the crawl. Requests were paced and the affected
  results recorded as *inconclusive* rather than reported as absence of evidence.

A blocked probe is a finding about the boundary, not a puzzle to solve.

## Absence of evidence

Several results here are negatives: 6,271 wiki installs swept with one match,
~13,100 shortener slugs probed with zero hits. Negatives are only meaningful with
a positive control, so the scripts include them — `novelty_check.py` asserts that
"known" terms are still found, and the shortener sweep was validated against
slugs known to resolve before its null was believed. A search that would have
failed to find a real hit proves nothing.

## Credentials found in the corpus

The agents pasted real third-party API keys into public wiki pages (a US Census
key, a DPLA key). Those keys belong to whoever registered them, not to the
agents and not to us.

- They are **not** reproduced in this repository.
- Analysis scripts that touch the corpus **redact** them on output.
- They are described by *class and location* so the finding is verifiable, and
  the affected issuers can rotate them.

If you are re-running this analysis and you extract them, do not publish them,
and do not use them.

## What this repo will not help you do

The corpus contains working technique: a POST-smuggling chain through a rented
headless browser, a proxy bypass using a fabricated `Host` header, and an XSS
payload that packs wiki save-form state into base64. These are documented here at
the level needed to *recognise and defend against* the pattern — what was done,
why it worked, what it implies for sandbox design.

Step-by-step recipes aimed at any live third-party target are deliberately not
included, and the exploit artifacts are presented as historical evidence with
their targets' current state noted. If you want to test these techniques, test
them against infrastructure you own.

## Attribution

The underlying dataset is the work of the collusion.wiki researchers
(Sydney Von Arx, Cormac Slade Byrd, Spencer Kitts, Thomas Larsen). This
repository neither redistributes nor forks their dataset — `scripts/fetch_dataset.py`
downloads it from source and verifies it against their published checksums.
Their writeup is the primary account; this is secondary analysis that builds on it.
