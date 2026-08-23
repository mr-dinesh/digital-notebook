---
name: ransomware-leaks-analysis
description: Pull, normalise, or analyse ransomware leak-site victim data from the ransomware.live or RansomLook APIs — victim counts, group activity, country/sector breakdowns, feed comparison, freshness checks. Use when the task mentions leak sites, ransomware victims, extortion posts, double extortion, a named group's victim list, or these two APIs. Carries verified endpoints and field names, plus the normalisation traps that silently corrupt these comparisons.
---

# Ransomware leak-site data analysis

Reference implementation: `leaksite-india-monitor/leaksite_india_monitor.py` in this
monorepo. Read it before writing a new fetcher — the parsing, review-queue persistence
and reporting are already solved there.

## Hard rules

Metadata only. Never download leaked archives, never dereference a post's onion `link` or
its `magnet`, never scrape a leak site directly, never route through Tor. These feeds are
JSON APIs and that is the entire attack surface this work needs. Store `link`/`magnet` as
strings if they are useful as identifiers; do not fetch them.

## Verified API facts

Re-verify against the live spec before relying on anything here — these feeds change.
Specs: `https://api-pro.ransomware.live/swagger.json`, `https://www.ransomlook.io/swagger.json`.
Both `/docs` pages are Swagger UI shells that render nothing useful to a fetch; go to the
JSON. As of 2026-08-23:

### ransomware.live

| tier | base | auth | rate limit |
|---|---|---|---|
| free v2 | `https://api.ransomware.live/v2` | none | **1 req/min per endpoint** |
| PRO | `https://api-pro.ransomware.live` | `X-API-KEY` header, free key | 500k/month |

Free v2 endpoints: `/victims/{year}/{month}`, `/countryvictims/{cc}`, `/recentvictims`,
`/groupvictims/{group}`, `/searchvictims/{kw}`, `/sectorvictims/{sector}`, `/groups`,
`/allcyberattacks`, `/certs/{cc}`, `/yara/{group}`.
PRO adds `/victims/` with combined filters (`year` alone is rejected — pair with `month`),
`/victims/search`, `/listsectors`, `/negotiations`, `/ransomnotes`, `/iocs`, `/press`.

Victim fields on `/victims/{y}/{m}`: `victim, group, discovered, attackdate, country,
activity, domain, data_size, description, claim_url, url, press, ransom, screenshot,
infostealer`.

**Field names differ per endpoint.** `/countryvictims/{cc}` returns the legacy set:
`post_title, group_name, published, website, post_url`. Parse through an explicit alias
map and warn on unmapped keys — otherwise a renamed field silently becomes an empty
column and the analysis quietly loses rows.

### RansomLook

`https://www.ransomlook.io/api`, no key except `/api/export/{db}`.
`/api/posts/period/{start}/{end}` (YYYY-MM-DD, inclusive) covers any window in one call.
Also `/api/last/{days}`, `/api/recent/{n}`, `/api/group/{name}`, `/api/search`.

Post fields: `post_title, discovered, description, link, magnet, screen, private,
misp_uuid, group_name`. `discovered` is `YYYY-MM-DD HH:MM:SS` with **no timezone** (UTC).
`website` is documented but absent in practice.

**No country field. No sector field.** Sector sometimes sits inside free-text
`description` ("Sectors: Manufacturing").

## Traps that corrupt these comparisons

**Group name spelling across feeds.** The two feeds spell the same group differently —
`thegentlemen`/`the gentlemen`, `cmdorganization`/`cmd organization`, `crpx0`/`crpxo`,
`3am`/`threeam`. Left alone this fakes a second claimant on *every* victim present in both
feeds: one real run showed 673 "multi-group" victims where only 32 were real. Compare
group names punctuation-stripped, plus a small alias table for versioning variants
(`killsec3`→`killsec`). Do **not** alias distinct brands with a real relationship
(`leakeddata`/`silentransomgroup`, `bavacai`/`medusalocker`) — a rebrand or affiliate
repost is the finding. Always report how many were collapsed.

**A missing field is not a zero.** RansomLook has no country field and, in practice, no
domain either. Reporting `0` India-tagged victims for it reads as "found none"; the truth
is "cannot answer". Use NULL and print `n/a`. Decide per payload, not per source, so the
flag goes live if the field starts arriving.

**Nothing in either API labels AI-generated or inferred content.** No such field exists
and no doc mentions it. ransomware.live descriptions visibly mix LLM prose ("X is an
India-based healthcare technology company…") with scraped text ("Sector: Banking | Data
leaked: 0.8 GB"), indistinguishably. Its `activity` sector tag is likewise enrichment.
Flag the whole class per source and never quote either as sourced fact.

**Sparse fields.** In one sampled month: `data_size` non-null on 26/926 rows,
`description` empty or "N/A" on 129/926, `country` blank on 45/926. Any "by data size"
cut is a cut of 3% of the data. Keep regex-derived values (size parsed from description
text) in their own column so a guess is never mistaken for a source field.

**Freshness before coverage.** Always print the newest `discovered` per source first and
compare. If one feed has stalled or its parser broke, every join count measures the
outage, not coverage. Make the warning loud and repeat it after the report.

**Country tags answer a different question** than "is this an Indian victim". They reflect
the listed entity, missing Indian subsidiaries of foreign parents and over-claiming
foreign firms with "India" in the name. Keep the signals as separate flags (source tag /
domain TLD / text signal), never OR them into one number, and route ambiguity to a
human-editable queue whose verdicts persist across runs and override the automation.

## Working conventions

- Cache every raw response to `raw/<source>/<timestamp>__<tag>.json` **before** parsing,
  and support an `--offline` flag that reruns from cache. Iterating against a 1 req/min
  feed is otherwise unbearable, and it keeps you off the API while debugging a parser.
- `tldextract.TLDExtract(suffix_list_urls=())` uses the bundled snapshot — needed for
  `.co.in` to resolve, and keeps `--offline` genuinely offline. Its `registered_domain`
  is deprecated in 5.x; prefer `top_domain_under_public_suffix`.
- DuckDB autocommits (and fsyncs) per INSERT. `executemany` over a few thousand rows will
  stall the machine in uninterruptible disk wait — one 8.7k-row load took 12 minutes
  before it was killed. Load bulk tables from a CSV in a single `read_csv` statement and
  wrap small ones in an explicit transaction.
- Persist hand verdicts through temp-file + atomic rename, back up first, and never
  rewrite an existing row. Hand corrections are the one artifact here that cannot be
  regenerated.
