# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This monorepo lives at [github.com/mr-dinesh/digital-notebook](https://github.com/mr-dinesh/digital-notebook).

| Project | Purpose | Stack | GitHub |
|---|---|---|---|
| `APKanalysis/` | Android APK static security analysis | Python 3 + Flask | [Offline-APK-Analyzer](https://github.com/mr-dinesh/Offline-APK-Analyzer) |
| `kagga_bot/` | Kannada poetry scraper / Mastodon bot data | Python 3 + BeautifulSoup | [Kagga-Bot](https://github.com/mr-dinesh/Kagga-Bot) |
| `StreamingServer/` | Self-hosted personal radio server (`radiostack/` subdir) | Docker, Liquidsoap, Icecast2, Navidrome | [home-media-player](https://github.com/mr-dinesh/home-media-player) |
| `WealthOfNationsReader/` | Password-protected LLM reader for The Wealth of Nations | Python 3 + Flask + Google Gemini | [Wealth_of_Nations_Reader_App](https://github.com/mr-dinesh/Wealth_of_Nations_Reader_App) |
| `whatsapp_links/` | Extract and categorize unique links from WhatsApp chat export ZIPs → Excel | Python 3 + Flask | [link-archive](https://github.com/mr-dinesh/link-archive) |
| `ciso_articulator/` | Communication drill tool for security leaders (board, interview, CV modes) | Python 3 + Flask + Google Gemini | [ciso-articulator](https://github.com/mr-dinesh/ciso-articulator) |
| `yaraweave/` | Browser-only YARA rule generator from threat intel feeds | Vanilla HTML/JS (no server) | [yaraweave](https://github.com/mr-dinesh/yaraweave) |
| `argus/` | Argument intelligence tool — steelman/strawman/synthesis analysis · [live](https://argus-proxy.mrdinesh.workers.dev/) | Cloudflare Worker + Groq | [argus](https://github.com/mr-dinesh/argus) |
| `npp_quotes/` | 247 Notepad++ quotes extracted from C++ source → JSON/txt | Python 3 (single script) | [npp-quotes](https://github.com/mr-dinesh/npp-quotes) |
| `hn_blackout/` | Blackout poetry generated from Hacker News front-page headlines · [live](https://hn-blackout.pages.dev/) | Cloudflare Pages + Pages Function + Workers AI | [hn-blackout](https://github.com/mr-dinesh/hn-blackout) |
| `juicesec/` | OWASP Top 10 interactive vulnerability lab with AI tutor · [live](https://juicesec.mrdinesh.workers.dev/) | Cloudflare Worker + Workers AI | [juicesec](https://github.com/mr-dinesh/juicesec) |
| `checklist/` | Personal essay (non-code, no runnable components) | Markdown + image | — |
| `afl-masterclass/` | Interactive AFL++ fuzzing tutorial with XP gamification · [live](https://afl-masterclass.pages.dev/) | Vanilla HTML/JS (no server) | [afl-masterclass](https://github.com/mr-dinesh/afl-masterclass) |
| `curl-fuzzer/` | Coverage-guided fuzzing harnesses for curl (CVE research) | C + AFL++ + ASAN + Python | — |
| `bitwarden-fuzz/` | Coverage-guided fuzzing harnesses for Bitwarden components (crypto + parsing) | AFL++ + ASAN | — |
| `live-social-stream/` | Real-time Bluesky + Mastodon infosec keyword feed · [live](https://signal-feed-8pl.pages.dev/) | Cloudflare Worker + Vanilla HTML/JS | [signal-live](https://github.com/mr-dinesh/signal-live) |
| `mindful/` | Privacy-respecting mood/mindfulness check-in PWA | Cloudflare Worker + D1 SQLite + Vanilla HTML/JS | — |
| `privyRead/` | Privacy-first article reader with tracker stripping · [live](https://privyread.pages.dev/) | Cloudflare Worker + @mozilla/readability + PWA | — |
| `url-shortener/` | Custom-slug URL shortener at s.mrdee.in + HTML admin UI · [live](https://s.mrdee.in/) | Cloudflare Worker + KV | — |
| `links-inbox/` | Phone share target → KV queue → nightly commit of a daily links page to the blog · [live](https://mrdee.in/links/) | Cloudflare Worker + KV + PWA | [links-inbox](https://github.com/mr-dinesh/links-inbox) |
| `leaksite-india-monitor/` | India-focused ransomware leak-site victim pull from ransomware.live + RansomLook, 90-day window | Python 3 + DuckDB | — |
| `model-watch/` | Weekly GitHub Action: checks every AI model the projects use is still offered, and probes the live AI endpoints; opens an issue on failure | Python 3 (stdlib) + GitHub Actions | — |
| `lab-scripts/` | Lab-box control scripts (Hermes gateway, low-power mode, Tailscale), two-letter ssh aliases, MATE launchers; `install.sh` symlinks them into `~/.local/bin` | Bash | [lab-scripts](https://github.com/mr-dinesh/lab-scripts) (private) |
| `diwali-card/` | Animated Deepavali greeting card (Kannada + English), diyas light in sequence · [live](https://s.mrdee.in/diwali) | Vanilla HTML/JS (no server), Cloudflare Pages `diwali-2026` | [diwali-card](https://github.com/mr-dinesh/diwali-card) |
| `wisdombot/` | Private Telegram bot: answers a real-life problem with one verbatim Stoic quote (Marcus, Seneca, Epictetus) + a short "Do:" line | Cloudflare Worker + Workers AI + Vectorize | [wisdombot](https://github.com/mr-dinesh/wisdombot) |
| `slashsec` ¹ | Slashdot-style cybersecurity news dashboard — live RSS + AI summaries · [live](https://slashsec.mrdinesh.workers.dev/) | Cloudflare Worker + Workers AI | [SlashSec...](https://github.com/mr-dinesh/SlashSec_style-Infosec-RSS-Dashboard) |

¹ `slashsec` is a separate repo, not a subdirectory — local path: `/home/tester/Desktop/repos/SlashSec_style-Infosec-RSS-Dashboard/`

### Standalone repos (not in this monorepo)

| Repo | Description | Local path |
|---|---|---|
| [digital-journal](https://github.com/mr-dinesh/digital-journal) | mrdee.in blog — Hugo/Congo, deployed via Cloudflare Pages | `/home/tester/Desktop/repos/digital-journal/` |
| [SlashSec_style-Infosec-RSS-Dashboard](https://github.com/mr-dinesh/SlashSec_style-Infosec-RSS-Dashboard) | Slashdot-style infosec news dashboard (see `slashsec` row above) | `/home/tester/Desktop/repos/SlashSec_style-Infosec-RSS-Dashboard/` |
| [wodehouse-bot](https://github.com/mr-dinesh/wodehouse-bot) | P.G. Wodehouse quote bot posting to Bluesky twice daily | `/home/tester/Desktop/repos/wodehouse-bot/` |
| [Vibecoding001-PureLink_browser_addon](https://github.com/mr-dinesh/Vibecoding001-PureLink_browser_addon) | Browser extension for URL sanitisation | — |
| [Vibecoding_002_VIZMIX](https://github.com/mr-dinesh/Vibecoding_002_VIZMIX--Winamp-inspired-3D-audio-visualize) | Winamp-inspired 3D audio visualiser | — |
| [Vibecoding_003_Webscraping-Podcast](https://github.com/mr-dinesh/Vibecoding_003_Webscraping-Podcast-) | Think Fast Talk Smart podcast scraper | — |
| [Vibecoding-004-Interview-Simulator](https://github.com/mr-dinesh/Vibecoding-004-Interview-Simulator-Webapp) | Interview simulator and prep tool | — |
| [android-tab-tweak](https://github.com/mr-dinesh/android-tab-tweak) | Root Lenovo TB-X605LC for zRAM / memory pressure fix | — |
| [eie-recommendations](https://github.com/mr-dinesh/eie-recommendations) | EiE podcast book/music/article recommendations | — |
| [parliamentwatch](https://github.com/mr-dinesh/parliamentwatch) | Indian Parliamentary Committee report tracker | — |

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

Shortcut: `radio up|down|status|now|skip|play [name]|toggle` (`scripts/radio.sh`, symlinked to `~/.local/bin/radio`; "Home Radio" desktop icon runs `toggle`). `up` re-applies the icecast.xml read ACL if missing, waits for `/stream` to serve `audio/mpeg`, and prints the LAN and Tailscale listen URLs. `play <name>` rewrites the playlist line in `radio.liq` and restarts Liquidsoap. It manages icecast, liquidsoap and navidrome, the whole stack (the Node.js web admin UI was removed 2026-11-13; `radio` replaces it).

### Endpoints
| Service | URL |
|---|---|
| Raw stream | http://localhost:8000/stream |
| Icecast admin | http://localhost:8000/admin |
| Navidrome (music indexer) | http://localhost:4533 |
| Liquidsoap telnet | localhost:1234 |

### Architecture
- **Liquidsoap** (`liquidsoap/radio.liq`): reads one playlist (currently `/playlists/Sivers.m3u`, Derek Sivers' free tracks in `~/Music-Sivers`, mounted at `/sivers` in Liquidsoap only so Navidrome doesn't index them; `default.m3u` is the original mix), shuffled, normalizes audio, encodes MP3 128 kbps, streams to Icecast. Reloads playlist every 10 seconds. Exposes telnet on port 1234 for runtime control. Paths inside `.m3u` files must use the Docker container path (`/music/filename.mp3`), not the host path.
- **Icecast** (`icecast/icecast.xml`): receives stream from Liquidsoap, serves to listeners on `/stream` mount. Max 25 clients, 5 sources.
- **Navidrome**: music library indexer with Subsonic-compatible API (auto-indexes `/music` volume).
- All services communicate over Docker bridge network `radionet`.
- Music files are mounted from `/home/tester/Music` on the host into all relevant containers. Remote listening is over Tailscale only (no port forwarding, no dynamic DNS).

### Credentials
Secrets live in `radiostack/.env` (gitignored) — nothing is hardcoded in the configs.

```bash
cd StreamingServer/radiostack
cp .env.example .env          # then fill in with: openssl rand -base64 24
./scripts/gen-icecast-config.sh   # renders icecast/icecast.xml from the template
docker compose up -d
```

- `icecast/icecast.xml.template` is the committed source; `icecast/icecast.xml` is generated (mode 600, gitignored). Re-run the script after any `.env` change.
- Icecast in the container runs as uid 101 (`icecast2` in `moul/icecast`), so mode 600 alone makes it exit with `Permission denied` / `XML config parsing error`. The script adds a read ACL for that uid (`setfacl -m u:101:r`, needs the `acl` package); override with `ICECAST_CONTAINER_UID` if the image changes. On this host uid 101 is `uuidd`.
- `radio.liq` reads `ICECAST_SOURCE_PASSWORD` from the environment via `environment.get()` and shuts down if it's empty. Docker Compose passes it through from `.env` and fails fast if unset.
- Values must not contain `&`, `<`, or `>` — they land in XML text nodes unescaped. The generator rejects them.

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
`render.yaml` is pre-configured — uses `gunicorn app:app` as the start command (not `python app.py`). Set `GOOGLE_API_KEY` and `ACCESS_PASSWORD` as env vars in the Render dashboard; `SECRET_KEY` is auto-generated.

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
- `POST /analyse` — calls Groq API (`llama-3.3-70b-versatile`); returns JSON with `core_thesis`, `steelman`, `steelman_crux`, `strawman`, `strawman_crux`, `synthesis`, `real_crux`, `evidence_that_changes_it`, `actionable`.
- Requires `GROQ_API_KEY` Wrangler secret (`wrangler secret put GROQ_API_KEY`). No `[ai]` binding needed.
- Rate limiting via KV: `RATE_LIMIT` KV namespace (configured in `wrangler.toml`) enforces 20 req/90 s on `/fetch` and 10 req/90 s on `/analyse` per IP. If `RATE_LIMIT` binding is absent, rate limiting is silently skipped.

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

### Running / deploying
```bash
cd hn_blackout
wrangler pages dev     # http://localhost:8788 — AI binding hits real Workers AI
wrangler pages deploy --project-name hn-blackout --branch main
```

### Architecture
- `site/blackout.html` is the UI; `site/index.html` is a meta-redirect shim to it. `wrangler.toml` sets `pages_build_output_dir = "site"`, so only `site/` and `functions/` are published. Keep bot files, README etc. out of `site/`. Pages answers unknown paths with `index.html` and a 200, so check content types, not status codes, when confirming a file isn't served.
- Fetches top 20 stories from the public HN Firebase API in the browser (no key needed).
- `functions/api/poem.js` (Pages Function): `POST /api/poem` with `{titles: [...]}` (1–30 strings, each capped at 300 chars). The prompt is built server-side, so the endpoint isn't a general LLM proxy. It calls Workers AI via the `AI` binding in `wrangler.toml`, trying `@cf/meta/llama-3.3-70b-instruct-fp8-fast` and then `@cf/mistralai/mistral-small-3.1-24b-instruct`, and returns `{title, poem: [words], model}`. Keep `model-watch/watch.json` in sync.
- Tokenizer splits each headline into word tokens; matcher finds poem words via exact → case-insensitive → strip-punctuation fallback.
- Non-selected words are blacked out with a CSS marker-stroke keyframe animation staggered over ~3.6 seconds.
- Throttle (30 s cooldown, 10/day) is client-side only, in `localStorage`. The endpoint has no server-side rate limit.
- **Daily bot**: `.github/workflows/post-poem.yml` (09:00 IST, with backup slots at 10:10 and 11:40 IST because GitHub delays or drops scheduled runs) runs `bot/post_poem.py`. GitHub's cron has started runs ~8 h late, so the lab box also fires `gh workflow run` at 09:00 IST from the user systemd timer `hn-blackout-trigger.timer` (`~/.config/systemd/user/`). A Cloudflare cron Worker replacement is drafted in `trigger/`, not yet deployed; it needs a `GH_DISPATCH_TOKEN` PAT (hn-blackout only, Actions RW). Checkout uses `ref: main` so a queued backup run sees the earlier run's `posted.json` commit and skips. It screenshots the live HN front page with Playwright Chromium (620px viewport, so HN's mobile layout fills the panel) and reads the headlines from that page, falling back to the API and a drawn panel. It then calls the live `/api/poem` and renders a 3-panel Pillow image (screenshot / blacked out / poem) with fonts vendored in `bot/fonts/`, and posts it to Bluesky (`BSKY_HANDLE`, `BSKY_APP_PASSWORD`; posts as @ishm0.bsky.social) and Mastodon (`MASTODON_ACCESS_TOKEN`, `MASTODON_INSTANCE_URL`; posts as @browncoolie@mastodon.social via its own "HN Blackout" app with write:statuses + write:media only, shared with KaggaBot). A platform is skipped if its secrets are unset. `--force --only mastodon` (or the workflow's `only` input) posts to one platform without repeating the other. It commits `bot/posted.json`, which makes a second same-day run skip and keeps the schedule from being auto-disabled. Preview without posting: `CHROME_PATH=/usr/bin/chromium python bot/post_poem.py --dry-run` → `bot/out/preview.png`, or run the workflow with the `dry_run` input, which uploads the image as an artifact. Pushes that touch `.github/workflows/` need SSH (`git push git@github.com:mr-dinesh/hn-blackout.git main`), because the `gh` token lacks the `workflow` scope.

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

## afl-masterclass

### Running
```bash
cd afl-masterclass
python3 -m http.server 8000   # then open http://localhost:8000/afl-masterclass.html
```

### Deploying (Cloudflare Pages)
```bash
wrangler pages deploy afl-masterclass --project-name afl-masterclass --branch main
```
Live at https://afl-masterclass.pages.dev

### Architecture
- Single HTML file (`afl-masterclass.html`), no build step, no dependencies.
- 10 sections covering AFL++ from first principles through adversarial critique. XP gamification (50 XP/section) and progress tracking persisted in `localStorage`.
- Three themes (Dark/Light/Sepia) also persisted in `localStorage`.

---

## curl-fuzzer

### Running
```bash
cd curl-fuzzer
./install.sh          # install AFL++, LLVM 15, build deps (run once)
./build_asan.sh       # build ASAN-instrumented curl (crash detection)
./build_afl.sh        # build AFL++-instrumented curl (coverage)
./run_afl.sh url      # start fuzzing; also: cookies, socks5
./validate_cve38545.py  # reproduce CVE-2023-38545
```
`run_afl.sh` requires root for system tuning (`/proc/sys/kernel/core_pattern`, CPU governor).

### Architecture
- Three harnesses in `harnesses/`: `fuzz_url.c` (URL parsing), `fuzz_cookies.c` (cookie handling), `fuzz_socks5.c` (SOCKS5 hostname — target for CVE-2023-38545).
- ASAN build finds crashes; AFL++ build explores coverage space. Use ASAN first to confirm a crash, then AFL++ for discovery.
- `fuzz_socks5.c` uses a socketpair + POSIX thread greeter to drive curl's SOCKS5 state machine through handshake stages.
- Crashes output to `crashes/<harness>-<timestamp>/`; deduplicate by stack trace, not count.
- `curl-fuzzing-plan.html` at repo root is a standalone research planning doc (open in browser) — not part of the build.

---

## bitwarden-fuzz

### Running
```bash
cd bitwarden-fuzz
./install.sh   # install AFL++, build deps
./build.sh     # build instrumented target
./run.sh       # start fuzzing
```

### Architecture
- Coverage-guided fuzzing harnesses for Bitwarden's crypto and parsing components using AFL++ + ASAN.
- `sdk/` contains the Bitwarden SDK source used as the fuzzing target.
- Has its own `.git` repo (separate from the Vibecoding monorepo).

---

## live-social-stream

### Deploying
```bash
cd live-social-stream
wrangler deploy   # deploys signal-proxy.worker.js (CORS proxy)

# Frontend: update the WORKER_URL constant in live-feed.html to your deployed Worker URL, then:
mkdir site && cp live-feed.html site/index.html
wrangler pages deploy site --project-name signal-feed --branch main
```
Live at https://signal-feed-8pl.pages.dev

### Architecture
- `live-feed.html`: vanilla JS frontend. Searches Bluesky (`api.bsky.app`) and Mastodon (`mastodon.social/infosec.exchange`) in parallel, deduplicates by post ID, merges by recency. Auto-refreshes every 20 seconds.
- `signal-proxy.worker.js`: allow-listed CORS proxy — only `api.bsky.app` and `mastodon.social` hostnames can be forwarded. Per-source error handling so one network failure doesn't blank the feed.
- Mastodon hashtag search works without auth; keyword search requires a Mastodon auth token added client-side.

---

## mindful

### Deploying
```bash
cd mindful
wrangler deploy   # Worker serves both the HTML and the API
```

### Architecture
- Single Cloudflare Worker (`worker.js`) embeds the full frontend HTML inline — no separate Pages deployment.
- D1 SQLite database binding `DB` (see `wrangler.toml` for `database_id`). Schema in `schema.sql`: one `checkins` table with `UNIQUE(date, slot) ON CONFLICT REPLACE`. Columns include `breath_chip`, `breath_custom`, `mind_chip`, `mind_custom`, and `shift` (for shift-work context tracking).
- 5 time slots per day: morning, noon, evening, night, sleep.
- API routes: `POST /api/checkin`, `GET /api/stats` (streak + heatmap + top moods), `GET /api/stats/public`, `POST /api/pin-check`.
- Env vars: `MINDFUL_PIN` (optional — if set, all API calls require `X-Pin` header); `MINDFUL_PUBLIC_STATS` (optional — enables the public stats endpoint).

---

## privyRead

For a full step-by-step deployment walkthrough, see `privyRead/privyread-deploy.md`.

### Deploying
```bash
# Step 1: deploy the Worker
cd privyRead/privyread-worker
npm install   # @mozilla/readability + linkedom
wrangler deploy

# Step 2: update WORKER_URL constant in privyread-index.html to your Worker URL, then:
mkdir pages && cp ../privyread-index.html pages/index.html && cp ../privyread-manifest.json pages/manifest.json
wrangler pages deploy pages --project-name privyread
```

### Architecture
- Worker (`privyread-worker/worker.js`): fetches the target URL server-side, strips 29 tracking params (utm_*, fbclid, gclid, etc.), follows redirects (≤5 hops), runs Mozilla Readability + linkedom to extract clean article HTML.
- Requires `compatibility_flags = ["nodejs_compat"]` in `wrangler.toml` (uses Node.js APIs).
- Frontend (`privyread-index.html`): PWA. `privyread-manifest.json` registers an Android share target so links shared from other apps open directly in PrivyRead.
- Install on Android: open the Pages URL in Brave/Chrome → menu → "Add to Home Screen".

---

## url-shortener

### Setup (run once)
```bash
cd url-shortener
# Create KV namespace and paste the IDs into wrangler.toml
wrangler kv namespace create URL_SHORTENER
wrangler kv namespace create URL_SHORTENER --preview
# Set admin password as a secret (prompted interactively)
wrangler secret put ADMIN_PASSWORD
```

### Deploying
```bash
cd url-shortener
wrangler deploy                              # worker → s.mrdee.in

# Admin UI: update WORKER_URL in admin/index.html, then:
mkdir -p pages && cp admin/index.html pages/index.html
wrangler pages deploy pages --project-name go-admin --branch main
```

### Architecture
- `worker.js`: handles all traffic at `s.mrdee.in`.
  - `GET /<slug>` — KV lookup → `301` redirect or branded `404` HTML page.
  - `GET /api/links` — lists all slugs + destinations (auth required).
  - `POST /api/links` — `{slug, url}` — creates/overwrites a slug (auth required). Sanitises slug to `[a-z0-9_-]`.
  - `DELETE /api/links/<slug>` — removes a slug (auth required).
- Auth: `Authorization: Bearer <password>` header checked against `ADMIN_PASSWORD` secret (env var). Defaults to `"changeme"` if unset — always set the secret before deploying.
- KV namespace binding: `URL_SHORTENER` (configure IDs in `wrangler.toml` after `wrangler kv namespace create`).
- `admin/index.html`: single-file admin UI for Cloudflare Pages. Password stored in `sessionStorage` (cleared on tab close). Update the `WORKER_URL` constant before deploying.

---

## links-inbox

### Deploying
```bash
cd links-inbox
wrangler deploy        # https://links-inbox.mrdinesh.workers.dev
wrangler dev --local   # needs .dev.vars with ADMIN_PASSWORD (gitignored)
```

### Architecture
- `worker.js` serves `/api/*`; `public/` (static assets) is the installable PWA whose manifest `share_target` puts "Links" in the Android share sheet.
- Shares are queued in KV `LINKS` as `q:<IST date>:<ms>-<rand>`. Cron `0 18 * * *` (23:30 IST) commits each date's queue to `digital-journal` as `content/links/<date>.md` via the GitHub contents API, authored as M R Dinesh (noreply). The queue is deleted only after the commit succeeds. **Publish now** in the app does the same on demand.
- Secrets: `ADMIN_PASSWORD` (Bearer auth; fails closed if unset) and `GITHUB_TOKEN` (fine-grained PAT, digital-journal only, Contents RW).
- Titles and notes are HTML- and Markdown-escaped because the blog has goldmark `unsafe = true`.
- `compatibility_date` is capped at what local `workerd` supports (2026-04-22 with wrangler 4.83).
- `public/index.html` loads `style.css?v=<date>` and `app.js?v=<date>`. **Bump the date (add `-2` for a second deploy that day) whenever either file changes**, or the installed PWA keeps serving its cached copy.

---

## leaksite-india-monitor

### Running
```bash
cd leaksite-india-monitor
pip install --user requests duckdb tldextract
python3 leaksite_india_monitor.py            # live pull, ~4 min (1 req/min rate limit)
python3 leaksite_india_monitor.py --offline  # rerun from ./raw cache, no network
```

- Single file, no keys. Outputs `victims.duckdb`, `victims_export.csv`, `review_queue.csv`,
  `categories.csv`.
- `review_queue.csv` holds hand verdicts (`india` / `not_india` / `india_sub`) per record;
  `categories.csv` holds the hand-assigned vendor taxonomy per entity, plus `same_as` for
  merging entities normalisation split apart. Both persist across runs and override the
  automation. They are the only artifacts here that cannot be regenerated, but they are
  **gitignored, not committed** — they name real organisations against unverified attacker
  claims and this repo is public. Back them up outside git after any adjudication session.
- Count entities via the `india_entities` DuckDB view, not `count(distinct victim_norm)`:
  the view folds `same_as` aliases together. The feeds' own `sector` field is inferred and
  labels vendors by their customers' industry — never use it in place of `vendor_category`.
- `python3 review_server.py` serves both hand-editors on 127.0.0.1:8765
  (`review_editor.html` for verdicts, `category_editor.html` for categories).
- Metadata only: no archives, no onion fetches, no magnets followed.
- **Before touching the fetch or normalisation logic, use the `ransomware-leaks-analysis`
  skill** (`.claude/skills/`) — it carries the verified endpoints, the per-endpoint field
  aliases, and the normalisation traps that silently corrupt these comparisons.

---

## model-watch

Weekly check (`.github/workflows/model-watch.yml`, Mondays 09:00 IST, or run by hand from the Actions tab) that the AI models behind the live projects still exist.

- `model-watch/watch.json` lists every model per project and one live request per deployed AI endpoint. **Update it whenever a project changes models.**
- `check.py` (stdlib only) asks each provider's model list whether the model is still offered, flags any Workers AI model with a retirement date within 60 days, and probes the endpoints. A provider with no key set is skipped, not failed.
- On failure or upcoming retirement it opens or comments on one issue labelled `model-watch`; it closes that issue once everything passes.
- Repo secrets: `CLOUDFLARE_API_TOKEN` (Workers AI Read) + `CLOUDFLARE_ACCOUNT_ID`, `GROQ_API_KEY`, `GOOGLE_API_KEY`.
- Local run: `wrangler ai models --json > /tmp/wai.json && python3 model-watch/check.py --workers-catalog /tmp/wai.json`

---

## wisdombot

### Running / deploying
```bash
cd wisdombot
python3 -I build/fetch.py /tmp/wisdom-raw         # Gutenberg + Wikisource (429s; ~15 min)
python3 -I build/split.py /tmp/wisdom-raw corpus   # passages, units, public/p/*.json shards
wrangler deploy                                    # https://wisdombot.mrdinesh.workers.dev
INGEST_TOKEN=... python3 -I build/ingest.py https://wisdombot.mrdinesh.workers.dev
```

### Architecture
- `worker.js`: `POST /tg` (Telegram webhook; `X-Telegram-Bot-Api-Secret-Token` + `ALLOWED_USER_IDS`, strangers ignored silently), `/health` (model-watch probe), `POST /admin/ingest` (Bearer `INGEST_TOKEN`; embeds units into Vectorize).
- **The model never writes quote text.** Query → `@cf/baai/bge-small-en-v1.5` → Vectorize `wisdombot-stoic` (384 dims, top 50, max 7 per author → 20 candidates) → `llama-3.3-70b-instruct-fp8-fast` (fallback `mistral-small-3.1-24b-instruct`) picks one candidate number and writes the `Do:` line → the Worker prints the stored text. Keep `model-watch/watch.json` in sync.
- Corpus: Long's Meditations (Gutenberg **15877**; #2680 is Casaubon), Long's Epictetus (10661), Gummere's Seneca Letters (Wikisource). Units are 1–2 sentences of 8–40 words, cut only at sentence boundaries. Units that lean on context (start with "For", "But", "This"…), questions and dialogue fragments are not indexed.
- Safety: `corpus/excluded.txt` plus the `HARMFUL` regex in `split.py` keep out passages that present suicide as a way out. A crisis message gets the Tele-MANAS helpline (14416) and no quote.
- Full passages for `/source` are static assets (`corpus/public/p/<shard>.json`), not KV: the free plan allows only 1,000 KV writes a day. KV `STATE` holds only the last question (1 h TTL) for `/more`.
- Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `ALLOWED_USER_IDS` (plural; a typo makes the bot silent), `INGEST_TOKEN`. Set them in a normal terminal; `wrangler secret put` prompts don't work through `!`.
- Replies only when asked: one quote + `Do:`; small talk gets a one-line nudge; there is no cron.

---

## slashsec

Lives in a separate repo at `/home/tester/Desktop/repos/SlashSec_style-Infosec-RSS-Dashboard/`.

### Deploying
```bash
cd /home/tester/Desktop/repos/SlashSec_style-Infosec-RSS-Dashboard
wrangler deploy   # deploys to https://slashsec.mrdinesh.workers.dev
wrangler dev      # local dev at http://localhost:8787
```

### Architecture
- Single Cloudflare Worker (`worker.js`) serving the full UI and all API routes.
- `GET /` — serves the inlined HTML/CSS/JS dashboard.
- `POST /fetch` — server-side RSS proxy; allowlisted to 7 domains (isc.sans.edu, schneier.com, krebsonsecurity.com, bleepingcomputer.com, feedburner.com, this.weekinsecurity.com, techcrunch.com).
- `POST /groq` — runs AI summarisation via Workers AI (`@cf/meta/llama-3.1-8b-instruct`) using the `[ai]` binding; no external API key needed.
- No secrets required — `[ai]` binding in `wrangler.toml` handles auth automatically.
- `SlashSec_Dashboard.html` is the canonical HTML source; the inlined copy in `worker.js` is kept in sync manually.

---

## Testing

No test suite exists in any project. There are no pytest, jest, or other test frameworks configured anywhere in this repo.

---

## Blog (digital-journal)

`rajni/` in this repo is a standalone Hugo 404 page template (PaperMod theme) — just `404.html` with Hugo frontmatter, no runnable components.

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
- `functions/` — Pages Functions: `_middleware.js` (strips the Cloudflare beacon) and `api/blr-weather.js` (see below).
- `static/<app>/` — standalone pages served as-is, outside Hugo: `radio/` (RadioOS), `weather/`, `mandala/`.

### Weather view (mrdee.in/weather)

Customisable Bangalore daily weather page · [live](https://mrdee.in/weather/) · write-up: `content/vibecoding/vibecoding-032-bangalore-weather.md`. Nav link "Weather" lives in `hugo.toml` `[menu]`.

- Files: `static/weather/` (`index.html`, `weather.js`, `weather.css`, `theme.js`, `favicon.svg`) + `functions/api/blr-weather.js`. Social card: `static/og/weather.png` (a screenshot of the live page, quantised with Pillow).
- Data: the daily CSV (`DT,High,Low,Rain`, one row per day since 1981) from Karthik S's [bangalore-weather](https://github.com/skthewimp/bangalore-weather) (MIT, Oikolab data), served at `https://weather.karthiks.co/data/bangalore_daily_weather.csv`. That host sends no CORS header, so the page fetches the same-origin proxy `GET /api/blr-weather` instead. The proxy has a fixed upstream URL with no parameters, keeps a 3 h fresh copy and a 30-day stale copy in the Cache API, and reports `x-blr-weather: hit|miss|stale`. Don't switch to the GitHub copy of the CSV: it stopped updating on 2026-10-14.
- All stats are computed in the browser. Normal = median high/low for the calendar date over all years (matches upstream's chart); record = max/min for the date in other years; hot day > P90 of highs within ±7 days; rainy day ≥ 2.5 mm (IMD). Feb 29 folds into Feb 28 for normals, but the day card ranks a date only against the same exact date.
- View state (window, custom range, day, up to 3 compare years, panel order/visibility) lives in the URL hash; panels and theme are also saved in `localStorage`.
- Two looks, Almanac (light) and Instrument (dark), switched by `data-theme` on `<html>`; `theme.js` sets it in `<head>` before first paint. CSP is `script-src 'self'`, so no inline JS. Compare-year colours (`--c1..--c3`) were checked for colour-blind separation in both themes; re-validate if you change them.
- Bump the `?v=` query on the CSS/JS links in `index.html` when either file changes.
- Local run (no Hugo needed): `cd /home/tester/Desktop/repos/digital-journal && wrangler pages dev static --compatibility-date=2026-04-22` → `http://localhost:8788/weather/`. Local workerd rejects newer compatibility dates.
