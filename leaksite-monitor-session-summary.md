# Session summary — leaksite-india-monitor

Date: 2026-08-23 · Repo: `github.com/mr-dinesh/digital-notebook` (monorepo, branch `master`)
Project directory: `leaksite-india-monitor/`

Written to be read cold, in a separate chat, by someone who was not here.

---

## What was built

A local, metadata-only pull of ransomware leak-site victim posts from two public feeds,
filtered to an India view over a rolling 90-day window.

| file | what it is |
|---|---|
| `leaksite_india_monitor.py` | the whole tool: fetch, cache, normalise, flag, join, store, report (~990 lines, single file) |
| `review_editor.html` + `review_server.py` | local editor for adjudicating ambiguous victims by hand |
| `review_queue.csv` | 66 hand-adjudicated verdicts — the one artifact that cannot be regenerated |
| `README.md` | caveats, field semantics, why each decision was made |
| `.claude/skills/ransomware-leaks-analysis/SKILL.md` | the durable feed knowledge, at monorepo level |
| `run_weekly.sh` + crontab | Mondays 06:30, live fetch, locking, log deltas, cache pruning |

Outputs per run: `victims.duckdb`, `victims_export.csv`, `review_queue.csv`,
`raw/<source>/<timestamp>__<tag>.json`.

Never downloads leaked archives. Onion `link` and torrent `magnet` values are stored as
strings and never dereferenced. Only two hosts are ever contacted (verified by grep).

## Current results (window 2026-05-25 → 2026-08-23)

- ransomware.live 2,589 records · RansomLook 2,723 · both feeds fresh to 2026-08-23
- Join: 2,394 in both · 188 only ransomware.live · 311 only RansomLook
- India after hand verdicts: **72** (ransomware.live) + **41** (RansomLook) = 113 records,
  **74 distinct victims**
- Top group: The Gentlemen 35, then krybit 9, morpheus 6, nova 5, dragonforce 5
- Sectors: Manufacturing 20, Technology 15, Healthcare 10 — and 41 unknown
- Multi-group claims: 81 records across 32 victims

## API facts established by probing (not assumed)

The user's instruction was explicit: read the docs before writing code. Both `/docs` pages
are Swagger UI shells that render nothing useful; the specs are at
`api-pro.ransomware.live/swagger.json` and `www.ransomlook.io/swagger.json`.

**ransomware.live** — free v2 at `api.ransomware.live/v2`, no key, **1 req/min per
endpoint**. Used `/victims/{year}/{month}`, one call per month in window. PRO tier exists
(`X-API-KEY`, 500k/month, free key) but was not needed. Fields on the monthly endpoint:
`victim, group, discovered, attackdate, country, activity, domain, data_size, description,
claim_url, url, press, ransom, screenshot, infostealer`.

**Field names differ per endpoint** — `/countryvictims/{cc}` returns legacy names
(`post_title, group_name, published, website, post_url`). Parsing goes through an explicit
alias map; unmapped keys raise a schema-drift warning.

**RansomLook** — `www.ransomlook.io/api`, no key. `/api/posts/period/{start}/{end}` covers
the whole window in one call. Fields: `post_title, discovered, description, link, magnet,
screen, private, misp_uuid, group_name`. `discovered` has no timezone (UTC).
**No country field, no sector field**, and `website` is documented but absent in practice.

## Decisions and their reasons

**Three India flags, never collapsed** — `country_tagged` (source's own country field),
`tld_in` (domain ends `.in`), `needs_review` (text signal only). Kept separate to show how
much the country tags miss. `india_final` layers hand verdicts on top; the raw flags stay
visible beside it.

**A missing field is NULL, never 0.** RansomLook has no country field, so `country_tagged`
reports `n/a` there. Printing `0` would read as "found no Indian victims", which is a
different claim. `tld_in` is decided per row: real wherever a domain was recovered
(including from the post title), NULL only where there is nothing to answer with.

**`ai_generated` is a blanket per-source flag** — the user assumed ransomware.live labels
AI-generated descriptions. **It does not.** No such field exists in either API and the v2
docs never mention it. Its descriptions visibly mix LLM prose with scraped text,
indistinguishably. Chosen approach: mark every ransomware.live description and sector as
enrichment, mark RansomLook's as scraped, and document that this is our assumption rather
than a source claim.

**Cross-fill country** — where a RansomLook victim matches a ransomware.live victim by
name, that country is copied into a separate `country_borrowed` column (2,220 rows). It
never sets `country_tagged`.

**Review queue with persistent verdicts** — ambiguous rows land in `review_queue.csv` with
a blank `my_verdict` (`india` / `not_india` / `india_sub`). Existing rows are preserved
verbatim on every run; only new ambiguous records are appended. Two failure modes are
routed there deliberately: companies with "India" in the name that are not Indian
(Kenaitze Indian Tribe, Indian Motos Inmot in Ecuador), and Indian entities carrying a
foreign parent's country tag (a Kolkata freight firm tagged US).

## Bugs found and fixed during the session

1. **Group-name spelling faked multi-group claims.** The feeds spell groups differently
   (`thegentlemen` / `the gentlemen`, `cmdorganization` / `cmd organization`,
   `crpx0` / `crpxo`). Result: 673 victims looked multi-group when only 32 were. Fixed by
   comparing punctuation-stripped names plus a small `GROUP_ALIASES` table. Genuinely
   distinct but related brands (`leakeddata`/`silentransomgroup`,
   `bavacai`/`medusalocker`) are deliberately **not** aliased — a rebrand or affiliate
   repost is the finding.
2. **The same bug leaked into the report's group table**, splitting The Gentlemen into
   18 + 17 so it read as two mid-size actors rather than one dominant one at 35. Now
   aggregates on the normalised name and prints the spellings it merged.
3. **DuckDB `executemany` stalled the machine.** Every INSERT autocommits and fsyncs, so
   8.7k rows meant 8.7k fsyncs — 12 minutes in uninterruptible disk wait before it was
   killed. Fixed by loading the bulk table from CSV in one `read_csv` statement (0.5s) and
   wrapping the small tables in one transaction.
4. **`normalise_name` kept the scheme on URL-shaped titles** (`https://www.nitrex.in`), so
   those never matched the same company under a plain name. Stripping scheme and `www`
   moved 21 victims from single-feed to `in_both` — the join had been overstating how much
   the two feeds diverge.
5. **The first editor did nothing in Brave.** It used the File System Access API, which
   Brave and Firefox ship disabled, so the picker never opened and the page sat at "no
   file loaded". Rebuilt around a localhost POST endpoint (`review_server.py`) that
   validates before writing and refuses empty files, unknown verdicts, changed row counts,
   or missing columns.

## Verification performed

- Live end-to-end run (exit 0) and `--offline` re-run producing identical output
- CSV round-trip through the editor's own JS is byte-identical to the Python-written file
- Hand verdict written via the editor's code path, read by Python, applied by the monitor
- All 66 verdicts matched a record — zero orphans (audited explicitly)
- DuckDB counts cross-checked against the printed report
- Network surface grepped: only the two documented hosts; `link`/`magnet` never fetched
- `run_weekly.sh` executed for real: fetched live, verdicts survived byte-identical

## Verdict outcome

66 rows adjudicated: 45 `india`, 21 `not_india`. The automation agreed on 51; 15 records
changed. India totals moved 78 → 72 (ransomware.live) and, at that time, 44 → 37 for
RansomLook — now 48 → 41 after title-domain recovery. Seven `not_india` calls were no-ops
because a verdict keys on (victim, source, group) and so covers re-posts on other dates
whose empty description never tripped a flag.

## Automation

`crontab`: `30 6 * * 1 /home/tester/Desktop/Vibecoding/leaksite-india-monitor/run_weekly.sh`
(Mondays 06:30 local; cron daemon confirmed active). The wrapper takes an exclusive lock,
runs a **live** fetch (a cron running `--offline` would re-analyse the same cache forever),
logs to `logs/`, prints new-queue-row and verdict deltas, prunes raw files older than 120
days keeping the newest per tag, and keeps 26 logs.

## Known limitations — read before quoting any number

- **RansomLook's 41 is soft, and this was investigated rather than assumed.** Domains are
  now recovered from post titles where the title *is* a domain (562 rows), but that does
  **not** close the gap: of 546 title-derived domains only 5 are `.in`, and all 5 belong to
  victims ransomware.live already reports. Cross-filling domains from ransomware.live is
  worse — it fires only where a twin exists, which is never the gap. The 311 victims
  RansomLook alone sees are still screened by text signal only, because the feed does not
  carry the information. Description-text extraction was measured and rejected: it yields
  unrelated hosts (`Login.gov`), sentence artifacts (`data.The`) and attacker out-of-band
  callback domains (`*.oast.me`).
- **41 of 113 India records have no sector**, nearly all RansomLook. Any sector cut is
  really a cut of the ransomware.live subset, whose sector tags are inferred enrichment.
- **May and August are partial months** in the window; the August "drop" is truncation.
- **`data_size` is sparse** — 26 of 926 rows in a sampled month.
- Descriptions from ransomware.live are unlabelled enrichment, possibly LLM-written, and
  must never be quoted as sourced fact.
- Feeds rename fields (ransomware.live already did once). The alias map warns on drift, but
  field lists should be re-verified against the live spec, not trusted from this document.

## Open items

1. ~~Fix the RansomLook India recall gap.~~ **Attempted and closed as not fixable from
   that feed's data** — see the limitation above. Title-domain recovery shipped anyway
   (it makes `tld_in` answerable for 562 rows and improved the join), but the gap itself
   stands and any output must say so.
2. Decide what the dataset is for. If it becomes a mrdee.in post, the story is the method
   — the country tags missed 14 of 72, and one feed cannot answer the question at all.
3. `review_server.py` may still be running on 127.0.0.1:8765. Stop with
   `pkill -f "[r]eview_server.py"` (brackets required, or `pkill -f` matches its own shell).

## Environment notes

- Debian trixie, externally managed Python: `duckdb` and `tldextract` installed with
  `pip install --user --break-system-packages`. `python3-venv` is not installed.
- Commits went directly to `master`, matching this repo's existing history. No
  `Co-Authored-By` trailer, per standing preference.
- Session commits: `5c7287b` (tool + skill), `aab62c3` (README caveat), `8aa14cf` (editor +
  server), `5c10c6f` (verdicts + group-table fix). All pushed.
