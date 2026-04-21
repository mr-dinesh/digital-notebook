# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of independent projects ("Vibe Coding" series):

| Project | Purpose | Stack |
|---|---|---|
| `APKanalysis/` | Android APK static security analysis | Python 3 + Flask |
| `kagga_bot/` | Kannada poetry scraper / Mastodon bot data | Python 3 + BeautifulSoup |
| `StreamingServer/radiostack/` | Self-hosted personal radio server | Docker, Node.js, Liquidsoap, Icecast2 |
| `WealthOfNationsReader/` | Password-protected LLM reader for The Wealth of Nations | Python 3 + Flask + Google Gemini |
| `whatsapp_links/` | Extract and categorize unique links from WhatsApp chat export ZIPs → Excel | Python 3 + Flask |
| `ciso_articulator/` | Communication drill tool for security leaders (board, interview, CV modes) | Python 3 + Flask + Google Gemini |
| `yaraweave/` | Browser-only YARA rule generator from threat intel feeds | Vanilla HTML/JS (no server) |
| `argus/` | Argument intelligence tool — steelman/strawman/synthesis analysis · [live](https://argus-proxy.mrdinesh.workers.dev/) | Cloudflare Worker + Workers AI |
| `npp_quotes/` | 247 Notepad++ quotes extracted from C++ source → JSON/txt | Python 3 (single script) |
| `hn_blackout/` | Blackout poetry generated from Hacker News front-page headlines · [live](https://hn-blackout.pages.dev/) | Vanilla HTML/JS (no server) |
| `juicesec/` | OWASP Top 10 interactive vulnerability lab with AI tutor · [live](https://juicesec.mrdinesh.workers.dev/) | Cloudflare Worker + Workers AI |
| `checklist/` | Personal essay (non-code, no runnable components) | Markdown + image |

---

## APKanalysis

### Running
```bash
# v2 (preferred) — must run from Flask_App_files/ so Flask finds templates/
cd APKanalysis/Flask_App_files
python3 -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
python app.py   # runs on http://localhost:5000

# v1 (original — no Androguard dependency)
cd APKanalysis && python app.py
```

### Architecture
- `Flask_App_files/app.py` is the primary implementation (v2); root `app.py` is the older v1. The v1 does pure regex/ZIP parsing with no Androguard; v2 tries Androguard first and falls back to regex.
- Upload limit: 150 MB. Reports cached in-memory (`_report_cache`, max 10 entries).
- Analysis pipeline runs sequentially: hash → manifest parsing → permissions → secrets → DEX classes → SDK fingerprinting → crypto controls → network security.
- `parse_manifest()` tries Androguard first, falls back to regex over raw `AndroidManifest.xml` bytes from the ZIP.
- Permissions are classified CRITICAL for: `BACKGROUND_LOCATION`, `BIND_ACCESSIBILITY_SERVICE`, `READ_SMS`, `RECEIVE_SMS`, `PROCESS_OUTGOING_CALLS`.
- SDK fingerprinting covers 30+ SDKs via package name prefix matching in DEX class list.
- JADX decompiler binary is included at `APKanalysis/jadx/` but not yet integrated into the app (listed as a next step). For manual deep analysis after export:
  ```bash
  jadx -d src/ app.apk
  grep -r "onReceivedSslError" src/ --include="*.java" -A 5
  grep -r "MD5\|getInstance.*MD5" src/ --include="*.java"
  grep -r "trackAction" src/ --include="*.java" -A 3
  grep -r "DataCollectionLevel" src/ --include="*.java"
  ```
- `apk-analyzer-v2/` exists as scaffolding only (templates/uploads directories, no app.py yet) — a planned rewrite.

---

## kagga_bot

### Running
```bash
cd kagga_bot
pip install requests beautifulsoup4
python scraper.py --resume                        # resume from checkpoint
python scraper.py --start 1 --end 945 --delay 1.5  # full run
```

- Checkpoint state persists in `scraper_checkpoint.json`.
- All 945 verses are already collected in `kagga_verses.py` (1.9 MB data file).
- Bot is live on Mastodon at `mastodon.social/@browncoolie`, posting twice daily.

---

## StreamingServer (radiostack)

### Running
```bash
cd StreamingServer/radiostack
docker compose up -d
docker compose logs -f liquidsoap   # debug audio issues
docker compose logs -f icecast
docker compose restart liquidsoap   # apply .liq config changes
docker compose down
```

### Endpoints
| Service | URL |
|---|---|
| Web admin UI | http://localhost:3000 |
| Listener player | http://localhost:3000/listen.html |
| Raw stream | http://localhost:8000/stream |
| Icecast admin | http://localhost:8000/admin |
| Navidrome (music indexer) | http://localhost:4533 |
| Liquidsoap telnet | localhost:1234 |

### Architecture
- **Liquidsoap** (`liquidsoap/radio.liq`): reads `/playlists/default.m3u`, normalizes audio, encodes MP3 128 kbps, streams to Icecast. Reloads playlist every 10 seconds. Exposes telnet on port 1234 for runtime control. Paths inside `.m3u` files must use the Docker container path (`/music/filename.mp3`), not the host path.
- **Icecast** (`icecast/icecast.xml`): receives stream from Liquidsoap, serves to listeners on `/stream` mount. Max 25 clients, 5 sources.
- **Node.js Express** (`web/server.js`): playlist manager UI. Key API routes:
  - `POST /api/control/skip` — sends telnet command to Liquidsoap (`main_playlist.skip`)
  - `GET /api/control/nowplaying` — returns currently playing track via telnet
  - `GET /api/music` — lists music files; `POST /api/music/upload` — accepts uploads (multer); `DELETE /api/music/:filename`
  - `GET/POST /api/playlists/*` — read/write `.m3u` files
  - `GET /api/status` — proxies Icecast status XML
- **Navidrome**: music library indexer with Subsonic-compatible API (auto-indexes `/music` volume).
- All services communicate over Docker bridge network `radionet`.
- Music files are mounted from `/home/tester/Music` on the host into all relevant containers. The `scripts/duckdns.sh` script handles dynamic DNS updates for external access.

### Important: Credentials in Config Files
`icecast.xml` and `radio.liq` contain hardcoded passwords (`radio123`, `Admin_tester@123`). Change these before any external deployment.

---

## WealthOfNationsReader

### Running
```bash
cd WealthOfNationsReader
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in GOOGLE_API_KEY, SECRET_KEY, ACCESS_PASSWORD
python app.py   # runs on http://localhost:7842
```

### Deploying (Render.com)
`render.yaml` is pre-configured. Set `GOOGLE_API_KEY` and `ACCESS_PASSWORD` as env vars in the Render dashboard; `SECRET_KEY` is auto-generated.

For a Cloudflare Tunnel instead, see `cloudflare/SETUP.md`.

### Architecture
- `app.py`: Flask app. Loads `book_data.json` once at startup into `BOOK_DATA` / `CHAPTER_INDEX`. All routes except `/login` and `/blog` require session auth (password set by `ACCESS_PASSWORD` env var).
- `book_data.json`: pre-parsed structured book data — **do not regenerate unless the source text changes**. Each entry has `id`, `book`, `title`, `short_title`, `paragraphs[]`.
- `parse_book.py`: one-time script that reads `wealth_of_nations_raw.txt` and produces `book_data.json`. Re-run only if the raw text or parsing logic changes.
- LLM calls use Google Gemini (`gemini-2.0-flash`) via `google-genai`. The `/api/ask` endpoint sends the full chapter context (truncated at 12 000 chars) + selected paragraph + question. `/api/summarize` truncates at 14 000 chars.
- API routes: `GET /api/chapters`, `GET /api/chapter/<id>`, `POST /api/ask`, `POST /api/summarize`.

---

## whatsapp_links

### Running
```bash
cd whatsapp_links
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Web UI (upload a WhatsApp export .zip via browser)
python app.py   # runs on http://localhost:5001

# CLI (uses default ZIP path, or pass an explicit path)
python extract_links.py
python extract_links.py "/path/to/WhatsApp Chat with X.zip"
```

### Architecture
- `app.py`: Flask web UI. Upload a WhatsApp export `.zip` → parse → display categorized links → download Excel. Runs on port 5001. Temp files stored under `/tmp/whatsapp_links_ui/`; session-keyed by UUID.
- `extract_links.py`: core parsing logic. Reads a WhatsApp export ZIP directly (default path: `/home/tester/Desktop/WhatsApp Chat with Clear Writing Community.zip`). Parses message boundaries for Android/iOS and 12h/24h formats, extracts and deduplicates URLs, categorizes by domain (YouTube, Instagram, Google Docs, etc.), writes `whatsapp_links.xlsx` to Desktop.
- Output columns: **Date** | **Sender** | **URL** (clickable hyperlink) | **Message** (≤2 lines / 180 chars) | **Category**.
- No Google Drive or OAuth dependency — WhatsApp export ZIP must be obtained manually from the phone.

---

## ciso_articulator

### Running
```bash
cd ciso_articulator
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in GOOGLE_API_KEY
python app.py   # runs on http://localhost:5002
```

### Architecture
- `app.py`: Flask app with two routes. `GET /api/scenarios/<mode>` serves scenarios from `scenarios.json` for the selected mode (`daily_drill`, `interview_prep`, `cv_interrogation`). `POST /api/coach` takes scenario, context, and user response, sends a structured prompt to `gemini-2.0-flash`, returns fixed-format coaching (what worked / what to fix / rewrite opening).
- `scenarios.json`: 26 scenarios total — 12 daily drill, 8 interview prep, 6 CV interrogation. Each has `id`, `scenario`, `context`, `tags[]`. Tag `"HARD"` renders with filled black background in the UI.
- Frontend is vanilla JS (no framework). Timer is a `setInterval` loop with CSS progress bar. Word count updates on keystroke. Session count persists in `localStorage`.
- App runs without a key (scenarios and timer work), but `/api/coach` returns 500 if `GOOGLE_API_KEY` is missing.

---

## yaraweave

### Running
```bash
# No server needed — open directly in any browser
xdg-open yaraweave/yaraweave.html
```

### Architecture
- Fully static single-file app (`yaraweave.html`). All logic runs in the browser; no backend.
- Queries up to 5 threat intel sources in parallel (MalwareBazaar, URLhaus, ThreatFox require no key; VirusTotal and OTX AlienVault accept optional free keys).
- Two-pass LLM flow: first pass generates the YARA rule, second pass produces a structured explanation (THREAT_CONTEXT, RULE_LOGIC, STRING_RATIONALE, DEPLOYMENT_NOTES, CONFIDENCE).
- Supports Groq (`llama-3.3-70b-versatile`, default) and Gemini as LLM providers. Provider and API keys stored in `localStorage` — never hardcoded.
- Input: SHA256 hash or malware family name. CORS note: VirusTotal/OTX may require a proxy in some browser environments.
- `yaraweave_v1.html` is the original single-pass version (kept for reference); `yaraweave.html` is current.

---

## argus

### Deploying
```bash
cd argus
npm install -g wrangler   # if not already installed
wrangler deploy           # deploys to Cloudflare Workers
wrangler dev              # local dev at http://localhost:8787
```

### Architecture
- Single Cloudflare Worker (`worker.js`) that both serves the UI and handles API routes.
- `GET /` — serves the full Argus HTML app (inlined into the worker).
- `POST /fetch` — proxies article URLs server-side to avoid CORS issues, returns cleaned text.
- `POST /analyse` — calls Cloudflare Workers AI (`env.AI`) with a structured prompt; returns JSON with `core_thesis`, `steelman`, `steelman_crux`, `strawman`, `strawman_crux`, `synthesis`, `real_crux`, `evidence_that_changes_it`, `actionable`.
- Uses the `[ai]` binding in `wrangler.toml` — no external LLM API key needed; billed through Cloudflare Workers AI.

---

## npp_quotes

### Running
```bash
cd npp_quotes
python extract.py                          # re-extract from npp_quotes_raw.txt
python extract.py path/to/other_raw.txt   # extract from a different source
```

- `npp_quotes_raw.txt` → `extract.py` → `npp_quotes.txt` (newlines rendered) + `quotes.json` (structured array).
- `quotes.json` format: `[{"author": "...", "quote": "..."}, ...]`, 247 entries.
- Data is already fully extracted; re-running `extract.py` is only needed if the source changes.

---

## hn_blackout

### Running
```bash
# No server needed — open directly in any browser
xdg-open hn_blackout/blackout.html

# If you hit CORS issues with the HN Firebase API:
python3 -m http.server 8080   # then open http://localhost:8080/blackout.html
```

### Architecture
- Fully static single-file app (`blackout.html`). All logic runs in the browser; no backend.
- Fetches top 20 stories from the public HN Firebase API (no key needed).
- Sends headlines to Groq (`llama-3.3-70b-versatile`, default) or Gemini; LLM returns JSON `{title, poem: [words]}`.
- Tokenizer splits each headline into word tokens; matcher finds poem words via exact → case-insensitive → strip-punctuation fallback.
- Non-selected words are blacked out with a CSS marker-stroke keyframe animation staggered over ~3.6 seconds.
- Provider and API keys stored in `localStorage` — never hardcoded.

---

## juicesec

### Deploying
```bash
cd juicesec
npm install -g wrangler   # if not already installed
wrangler deploy           # deploys to Cloudflare Workers
wrangler dev              # local dev at http://localhost:8787
```

### Architecture
- Single Cloudflare Worker (`worker.js`) serving the full app at `GET /` and a tutor endpoint at `POST /tutor`.
- `POST /tutor` — proxies challenge context + user question to Workers AI (`@cf/meta/llama-3.1-8b-instruct`). Two modes: `hint` (Socratic nudge) and `explain` (post-solve root cause + mitigation).
- All 10 challenges simulate OWASP Top 10 2021 vulnerabilities entirely in browser JS — no real backend attack surface.
- Challenge state (solved flags, score) is session-only (JS memory, not localStorage).
- Uses the `[ai]` binding in `wrangler.toml` — no external API key needed.

### Challenges implemented
| # | Title | OWASP | Detection logic |
|---|---|---|---|
| 01 | SQL Injection | A03 | Regex for `'OR`, `'--`, `'#` patterns |
| 02 | Reflected XSS | A03 | HTML tag + event handler in search input |
| 03 | Broken Authentication | A07 | Matches against hardcoded weak cred pairs |
| 04 | IDOR | A01 | User changes order ID away from their own (42) |
| 05 | Security Misconfiguration | A05 | Navigates to path disclosed in robots.txt |
| 06 | Sensitive Data Exposure | A02 | Hits `/api/v1/users` unauthenticated |
| 07 | JWT None Algorithm | A02 | Constructs JWT with alg:none + role:admin |
| 08 | Command Injection | A03 | Shell metachar + file-reading command |
| 09 | SSRF | A10 | Internal IP / cloud metadata URL |
| 10 | Stored XSS | A03 | Script tag or event handler in comment board |

---

## Blog (digital-journal)

The mrdee.in blog is a separate repo at `/home/tester/Desktop/repos/digital-journal/`. It is a Hugo site using the Congo theme, deployed via Cloudflare Pages on push to `main`.

### Adding a post

```bash
cd /home/tester/Desktop/repos/digital-journal
# create content/notes/<slug>.md or content/vibecoding/vibecoding-0NN-<slug>.md
git add . && git commit -m "..." && git push   # Cloudflare Pages auto-deploys
```

### Frontmatter format
```yaml
---
title: "Post Title"
date: YYYY-MM-DD
description: "One sentence shown in list view."
tags: ["tag1", "tag2"]
---
```

### Structure
- `content/notes/` — short technical notes (no series numbering).
- `content/vibecoding/` — numbered project write-ups (`vibecoding-0NN-slug.md`).
- `content/journal/` and `content/reading/` — other sections.
- `static/images/notes/` and `static/images/writing/` — post images; reference in markdown as `/images/notes/filename.jpg`.
- `static/_headers` — Cloudflare Pages security headers (HSTS, CSP, etc.).
