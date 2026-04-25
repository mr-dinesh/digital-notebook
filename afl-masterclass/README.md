# AFL Masterclass

A technical deep-dive into American Fuzzy Lop (AFL/AFL++) — from first principles to adversarial critique. Built as a self-paced learning module with progress tracking, theme switching, and gamification.

**Live:** [afl-masterclass.pages.dev](https://afl-masterclass.pages.dev)

## What it covers

10 sections, structured for progression:

| # | Section | Level |
|---|---------|-------|
| 01 | Mental Model — From First Principles | Intro |
| 02 | Algorithmic Deep Dive | Intermediate |
| 03 | Systems Engineering Decisions | Intermediate |
| 04 | Adversarial Critique — Where AFL Breaks | Advanced |
| 05 | Build Intuition — Concrete Examples | Intro |
| 06 | 7-Day Hands-On Curriculum | Lab |
| 07 | Code Reading Map | Advanced |
| 08 | Modern Relevance — OSS-Fuzz, Sanitizers, CI | Intro |
| 09 | Destroy Your Misconceptions (7 myth cards) | Intro |
| 10 | 30-Day Practice Roadmap | Full Program |
| REF | Primary sources, papers, video talks | — |

## Features

- **3 themes** — Dark / Light / Sepia, persisted to localStorage
- **Progress tracking** — XP system, section/day/myth completion buttons, live progress bar
- **Gamification** — 50 XP per section, 20 XP per curriculum day, 10 XP per myth busted
- **All state persists** — close the tab and pick up where you left off
- Single HTML file, no build step, no dependencies

## Sources

- Zalewski's `technical_details.txt` (primary source)
- AFL++ documentation and source code
- AFLFast (Böhme et al., CCS 2016)
- REDQUEEN / CMPLOG (Aschermann et al., NDSS 2019)
- AFL++ design paper (Fioraldi et al., WOOT 2020)

## Deploy

```bash
cp afl-masterclass.html /tmp/deploy/index.html
wrangler pages deploy /tmp/deploy --project-name afl-masterclass --branch main
```

Part of the [Vibecoding](https://mrdee.in/vibecoding/) series.
