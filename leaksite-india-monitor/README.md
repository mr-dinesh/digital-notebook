# leaksite-india-monitor

Local, metadata-only pull of ransomware leak-site victim posts from two public feeds,
with an India view over a rolling 90-day window.

**This tool never downloads leaked data.** It reads two JSON APIs. Onion post URLs
(`claim_url`) and torrent magnets (`magnet`) are stored as metadata strings and are never
dereferenced. No Tor, no scraping of leak sites, no direct contact with any group
infrastructure. The only hosts contacted are `api.ransomware.live` and
`www.ransomlook.io`.

## Install

```bash
pip install --user requests duckdb tldextract
```

## Run

```bash
python3 leaksite_india_monitor.py            # live pull (~4 min: rate limit, see below)
python3 leaksite_india_monitor.py --offline  # re-run from ./raw cache, zero network calls
```

Useful flags: `--days 90`, `--freshness-gap-days 7`, `--sleep 60`, `--db`, `--csv`,
`--review-queue`, `--raw-dir`.

Outputs: `victims.duckdb`, `victims_export.csv`, `review_queue.csv`, `raw/<source>/*.json`.

## Sources, as verified against the live APIs

| | ransomware.live (free v2) | RansomLook |
|---|---|---|
| Base | `https://api.ransomware.live/v2` | `https://www.ransomlook.io/api` |
| Auth | none | none (only `/api/export/{db}` needs a key) |
| Rate limit | **1 request/min per endpoint** | polite use |
| Endpoint used | `/victims/{year}/{month}` — one call per month in window | `/posts/period/{start}/{end}` — one call for the whole window |
| Country field | yes (`country`, ISO-3166 alpha-2) | **none** |
| Sector field | yes (`activity`), enriched/inferred | **none** (sometimes inside post text) |
| Date shape | ISO-8601 with `+00:00` | `YYYY-MM-DD HH:MM:SS`, no timezone (treated as UTC) |

ransomware.live returns **different key names on different endpoints** — `/victims/{y}/{m}`
uses `victim/group/attackdate/domain`, while `/countryvictims/{cc}` uses the legacy
`post_title/group_name/published/website`. Parsing goes through an explicit alias map
(`RW_LIVE_ALIASES`), and unmapped keys raise a schema-drift warning rather than being
silently dropped.

No API key is read from source. If a future endpoint needs one, it is read from an
environment variable.

## Read this before quoting any number

**Nothing in either API labels AI-generated or inferred content.** No such field exists,
and the ransomware.live v2 documentation never mentions it. ransomware.live descriptions
visibly mix LLM-written prose ("PappyJoe is an India-based healthcare technology
company…") with scraped leak-post text ("Sector: Banking | Data leaked: 0.8 GB"), and
nothing distinguishes them.

So this tool applies a **blanket, per-source** flag rather than guessing per record:

* every ransomware.live row: `description_ai_generated = TRUE`, `sector_inferred = TRUE`
* every RansomLook row: both `FALSE` (its `description` is the scraped post text, verbatim)

That flag is **our conservative assumption, not a source claim**. Never quote a
ransomware.live description or sector tag as sourced fact.

Other fields to treat with care:

* `data_size` — sparse on ransomware.live (26 of 926 rows in a sample month).
  `data_size_parsed` is our own regex over description text; kept in a separate column so
  a guess is never mistaken for a source field.
* `country` — blank on ~5% of ransomware.live rows, and reflects the *listed* entity, not
  necessarily where the affected operation is.

## The three India flags — deliberately not collapsed

| flag | meaning |
|---|---|
| `country_tagged` | the source's own country field says India/IN/IND |
| `tld_in` | registrable domain ends `.in` (including `.co.in`) |
| `needs_review` | neither of the above, but name or description carries an India signal (city list, "India", "Bharat", "Pvt Ltd") |

`india_any` is their OR, reported separately from `india_final` (after your saved
verdicts). The point of keeping all three is to show how much the country tags miss.

**RansomLook has no country field**, so its `country_tagged` is `NULL`, and the report
prints `n/a` — not `0`. A zero would read as "RansomLook found no Indian victims", which
would be false. The same applies to `tld_in`: RansomLook's documented `website` field is
absent from the live payload, so its domain column is empty and `tld_in` is `NULL`/`n/a`
too. If the field ever starts arriving, the flag switches to real values automatically —
the run decides per payload, not per source.

The `needs_review` matcher records which term fired (in the review-queue `note`), because
the term is usually the whole argument. Real example from a live run: a California golf
resort matched on "Indian" — from *Indian Wells*, the town it sits in.

`country_borrowed` is a **fourth, separate** column: where a RansomLook victim matches a
ransomware.live victim on normalised name, that country is copied across for context. It
never sets `country_tagged`, and the victim table marks those rows with flag `B` and
brackets the value.

## Review queue — your corrections always win

Ambiguous records land in `review_queue.csv`:

```
victim, source, group, domain, country_tag, my_verdict, note
```

> **`review_queue.csv` is unadjudicated input, not findings.** A company appears here
> because the automation could not decide, and rows with an empty `my_verdict` have had no
> human look at them at all. Several are in the file precisely because the tool suspects
> the *source feed* has misattributed them — a US tribal organisation and an Ecuadorean
> firm both landed here for having "Indian" in the name. Every row is republished from
> public leak-site feeds and none of it is a disclosure, but do not read the list as
> "Indian ransomware victims", and do not quote a row as a finding until its verdict is
> filled in.

Fill `my_verdict` with `india`, `not_india`, or `india_sub` (Indian subsidiary or delivery
centre of a foreign parent). `note` is prefilled with why the record was routed here on
first sight; edit it freely.

Two failure modes are routed here on purpose:

1. **"India" in the name but not Indian** — e.g. a foreign firm's product line.
2. **Indian entity carrying a foreign parent's country tag** — India signal present while
   the source country tag names another country.

On every run the file is loaded first, existing rows are preserved **verbatim** (verdict
and note are never rewritten or cleared), and only genuinely new ambiguous records are
appended. Writes go through a temp file plus atomic rename, and the previous file is
copied to `review_queue.csv.bak` first. Verdicts override the computed flags in
`india_final` only — the three raw flags stay untouched alongside it, so you can always
see what the automation thought.

Commit `review_queue.csv`. It is the accumulated hand judgement and the one file here
that cannot be regenerated.

## Freshness gate

Before anything else, the run prints the newest `discovered` date per source. If they
differ by more than `--freshness-gap-days` (default 7), a loud banner prints at the top
**and** repeats at the bottom of the report: a stalled feed or broken parser means the
join counts are measuring an outage, not coverage.

## Duplicate claims are findings, not noise

Dedupe is on normalised name for *matching* only. Repeat rows stay in the table, and
victims claimed by more than one group carry `multi_group_claim`, `claiming_groups` and
`claim_dates`. Re-extortion and rebrand reposting show up here.

One caveat worth knowing, because it dominated the first run: the two feeds spell some
group names differently ("thegentlemen" vs "the gentlemen", "cmdorganization" vs "cmd
organization"), which faked a second claimant on every shared victim — 673 victims looked
multi-group when only 121 were. Group names are therefore compared with punctuation and
spacing stripped, plus a short `GROUP_ALIASES` table for pure spelling/versioning variants
(`threeam`→`3am`, `killsec3`→`killsec`, …). The report prints how many victims were
excluded that way, so the collapse is never silent.

Deliberately **not** in that alias table: `leakeddata` / `silentransomgroup`,
`bavacai` / `medusalocker` and similar. Those are real relationships between distinct
brands, and collapsing them would delete the finding.

## Schema

`victims.duckdb` holds `victims_norm` (one row per source/victim/group/discovered date),
`victims_raw` (per-source record counts and fetch time), `joined` (per-victim join
status), and `review_queue` (a snapshot of the CSV).

```bash
duckdb victims.duckdb "SELECT source, count(*) FROM victims_norm GROUP BY 1"
```
