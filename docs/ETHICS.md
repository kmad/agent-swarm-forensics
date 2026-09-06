# Research conduct

This repository reproduces forensic analysis of an incident in which autonomous
agents wrote to third-party websites without permission. The irony is not lost:
the same techniques used to *investigate* it could be used to repeat it. These
are the rules this work followed, and that anyone re-running it should follow.

## Read-only, always

Live probes intend to avoid application-state writes or authentication. GET
alone does not establish that a request is non-mutating: server access logs and
shortener click counts can change. Historical payload URLs are evidence, not
instructions to execute.

This matters most for the counter API. `countapi.mileshilliard.com` exposes
`/hit/<key>` and `/set/<key>?value=N` alongside `/get/<key>`, all over GET.
**Only `/get` is ever called.** Calling `/hit` would increment a shared counter
and destroy the evidence for everyone who looks after us — the surviving values
lack an authenticated historical audit trail, so an accidental increment cannot
be reliably distinguished from prior activity.

`scripts/verify_live.py` includes a control check for this: it queries a key that
should not exist, three times, and requires a structured `Key not found` response
every time. On an inconclusive or failed control it stops before signal reads.
A passing control supports only non-creation for those particular reads. Never take a
measurement you cannot distinguish from your own footprint.

Note that the `_XX` placeholder keys have been drifting upward since the incident
— consistent with readers replaying the agents' `/hit` URL, but without caller attribution. That drift is
itself a lesson: a public counter is a shared resource, and casual probing is not
free. The signal keys were unchanged in the September 4–5 checks.

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

The agents pasted apparent third-party credentials into public wiki pages: **4 US
Census API keys, 1 DPLA key, 1 UNCTAD subscription key, and 48 Preservica render
tokens**. Their validity and ownership have not been tested.

One of these nearly escaped. The UNCTAD key appears twice in the same derived
CSV; one row classified it as an API key and was redacted, while the other
classified it as opaque hex (behind a `%3D` artifact) and was not. It took an
independent audit to catch. Redaction by classification label is fragile — scan
for the secret itself, and have someone else check.

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

Some lane reports preserve exact historical recipes and target URLs for
provenance. Their presence does not establish present availability or successful
execution. They should not be replayed against third-party targets. If you want to test these techniques, test
them against infrastructure you own.

## Attribution

The underlying dataset is the work of the collusion.wiki researchers
(Sydney Von Arx, Cormac Slade Byrd, Spencer Kitts, Thomas Larsen). This
repository neither redistributes nor forks their dataset — `scripts/fetch_dataset.py`
downloads it from source and verifies it against their published checksums.
Their writeup is the primary account; this is secondary analysis that builds on it.
