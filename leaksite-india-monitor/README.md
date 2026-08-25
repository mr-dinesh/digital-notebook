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
`--review-queue`, `--categories`, `--raw-dir`.

Outputs: `victims.duckdb`, `victims_export.csv`, `review_queue.csv`, `categories.csv`,
`raw/<source>/*.json`.

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
would be false.

`tld_in` is decided **per row**, not per source. RansomLook's documented `website` field is
absent from the live payload, but many of its post titles *are* the victim's domain
(`acehospital.in`, `bits-pilani.ac.in`), so a domain is recovered from the title where the
whole title parses as one — 562 rows in a recent window. `domain_source` records where each
domain came from (`field`, `title`, or empty), so a parsed value is never mistaken for one
the feed supplied. `tld_in` is NULL only where there is genuinely nothing to answer with.

Domains were **not** extracted from description text. That was measured and rejected: the
corpus yields unrelated hosts (`Login.gov`), sentence artifacts (`data.The`) and attacker
out-of-band callback domains (`*.oast.me`), which would attribute a stranger's domain to a
victim.

**This does not close the RansomLook recall gap.** Of 546 title-derived domains, 5 were
`.in` and all 5 belonged to victims ransomware.live already reports. Cross-filling domains
from ransomware.live is worse still — it can only fire where a twin already exists, which
is never the gap. The ~300 victims RansomLook alone sees are still screened by text signal
only, and no amount of parsing its payload changes that: the feed does not carry the
information.

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

### Filling it in

Editing 66 rows of quoted CSV by hand is miserable, so there is a small local editor:

```bash
python3 review_server.py     # then open http://127.0.0.1:8765/review_editor.html
                             #      or http://127.0.0.1:8765/category_editor.html
```

One row per queue entry, showing the name, group, domain, the source's country tag and
the reason the automation punted — plus the description where one exists, labelled so
ransomware.live's unlabelled enrichment is never mistaken for evidence. Keys: `1` india,
`2` not_india, `3` india_sub, `0` clear, `j`/`k` move, `n` note, `d` expand description,
`Ctrl+S` save. Your notes are appended after `||` rather than overwriting the routing
reason.

The page talks to `review_server.py` instead of using the browser's File System Access
API, because Brave and Firefox ship that API disabled and a picker-based editor silently
does nothing there. The server binds `127.0.0.1` only, exists for the length of the
session (Ctrl-C to stop), and refuses any POST that would damage the queue: empty file,
unknown verdict, changed row count, or missing columns. It backs up to
`review_queue.csv.bak` and writes through a temp file plus atomic rename.

Stop it with `pkill -f "[r]eview_server.py"` — the brackets matter, or `pkill -f` matches
the shell you typed it in.

Nothing in the editor pre-fills or suggests a verdict. That column is yours.

---

`review_queue.csv` and `categories.csv` are **not** committed, and are gitignored. They
name real organisations against unverified attacker claims, and this repo is public.

They are still the only two files here that cannot be regenerated, so they need a backup
that isn't git. Copy them somewhere outside the working tree after any adjudication
session. Losing them costs every hand verdict and every category label.

## Vendor categories

`review_queue.csv` answers "is this India?" per record. `categories.csv` answers "what
kind of business is this?" per entity, and is kept separate so categorising never means
re-touching a row already adjudicated for India.

Every `india_final` entity gets a row, keyed on `victim_norm`. The feeds' own `sector`
field is carried alongside as `inferred_sector` for reference only: it is inferred rather
than reported, and it labels vendors by their customers' industry — an engineering
services provider comes through as Manufacturing, a healthcare BPO as Healthcare. That
is precisely the distinction the taxonomy exists to make, so never let it stand in for a
hand judgement.

| Category | Test |
|---|---|
| `it_services_bpo` | Sells engineering/IT/BPO capacity to other firms |
| `product_software` | Sells its own software or platform to end users |
| `manufacturing_industrial` | Makes physical goods |
| `healthcare_life_sciences` | Clinical, diagnostics, pharma |
| `financial_services` | Banking, NBFC, payments, capital markets |
| `other` | Everything else — education, government, logistics, retail |

Edit it at `http://127.0.0.1:8765/category_editor.html`. Keys `1`-`6` set the category,
`0` clears, `j`/`k` move, `n` note, `Ctrl+S` save. The header live-counts each bucket's
share as you work. Unlike the review editor, **these rows may carry a pre-filled guess**
— the page marks them, and the filter defaults to the borderline and uncertain ones.

### same_as

Normalisation cannot always tell that two leak-post titles are one company: a title that
is a bare URL and one that is the plain company name strip to different keys. Merging on
shared domain is not safe, because some records carry a lookup-site domain rather than
the victim's own. So the merge is a hand judgement — set `same_as` to the canonical
`victim_norm` and the alias inherits its category and stops being counted. Chains
collapse to their endpoint; cycles and dangling pointers warn and are ignored.

Count entities through the `india_entities` view, never `count(distinct victim_norm)` —
the view folds merged aliases together. One merge in the current data is the difference
between 74 and 73.

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
status), `review_queue` and `categories` (snapshots of the two hand-maintained CSVs), and the
`india_entities` view (one row per India entity, aliases already folded, with per-entity
flag provenance and record counts).

```bash
duckdb victims.duckdb "SELECT source, count(*) FROM victims_norm GROUP BY 1"
```
