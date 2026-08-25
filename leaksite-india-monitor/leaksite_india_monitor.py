#!/usr/bin/env python3
"""leaksite-india-monitor — metadata-only India view of ransomware leak-site victim posts.

Sources (both public, metadata only):
  * ransomware.live free v2 API  — https://api.ransomware.live/v2
  * RansomLook API               — https://www.ransomlook.io/api

This tool NEVER downloads leaked archives. Onion post URLs (`link`) and torrent
magnets (`magnet`) are stored as metadata strings and are never dereferenced.
The only two hosts this program ever contacts are the two API hosts above.

See README.md for the field-level caveats, especially the blanket ai_generated flag.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
import tldextract

# --------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------

USER_AGENT = "leaksite-india-monitor/0.1"

RW_LIVE_BASE = "https://api.ransomware.live/v2"
RANSOMLOOK_BASE = "https://www.ransomlook.io/api"

SRC_RW = "ransomware_live"
SRC_RL = "ransomlook"

# ransomware.live free v2 allows 1 request per minute per endpoint.
RW_LIVE_SLEEP_SECONDS = 60

# Offline-safe suffix list: use the snapshot bundled with tldextract, never fetch the PSL.
_EXTRACT = tldextract.TLDExtract(suffix_list_urls=())

# Canonical field -> list of source key aliases, in priority order.
# ransomware.live returns DIFFERENT key names on different endpoints
# (/victims/{y}/{m} uses the new names, /countryvictims/{cc} the legacy ones),
# so parsing always goes through this map rather than through literal keys.
RW_LIVE_ALIASES: dict[str, list[str]] = {
    "victim": ["victim", "post_title"],
    "group": ["group", "group_name"],
    "discovered": ["discovered"],
    "attack_date": ["attackdate", "published"],
    "country": ["country"],
    "sector": ["activity"],
    "domain": ["domain", "website"],
    "data_size": ["data_size"],
    "description": ["description"],
    "claim_url": ["claim_url", "post_url"],
    "record_url": ["url", "permalink"],
}

RANSOMLOOK_ALIASES: dict[str, list[str]] = {
    "victim": ["post_title"],
    "group": ["group_name"],
    "discovered": ["discovered"],
    "description": ["description"],
    "domain": ["website"],
    "claim_url": ["link"],
    "magnet": ["magnet"],
}

# Keys we knowingly ignore. Anything outside alias-map + this set triggers a schema
# drift warning, so a renamed field is loud instead of silently dropped.
RW_LIVE_IGNORED = {"infostealer", "press", "ransom", "screenshot", "id", "permalink", "url"}
RANSOMLOOK_IGNORED = {"screen", "source", "private", "misp_uuid", "magnet", "link"}

LEGAL_SUFFIXES = [
    "private limited", "pvt ltd", "pvt. ltd.", "pvt limited", "p ltd",
    "limited", "ltd", "llp", "llc", "inc", "incorporated", "gmbh", "ag", "bv", "nv",
    "s.r.l.", "srl", "s.p.a.", "spa", "sa", "sl", "plc", "pty", "corp", "corporation",
    "company", "co", "group", "holdings", "holding",
]

# The two feeds spell some group names differently ("thegentlemen" vs "the gentlemen"),
# which would fake a multi-group claim on every shared victim. Punctuation/space stripping
# handles most of it; these are the remaining pure spelling/versioning variants observed
# in the live data. Only obvious same-group spellings belong here — genuine relationships
# (e.g. leakeddata / silentransomgroup, bavacai / medusalocker) stay separate, because a
# rebrand or an affiliate reposting is a finding, not noise.
GROUP_ALIASES: dict[str, str] = {
    "threeam": "3am",
    "crpx0": "crpxo",
    "eraleignapt73": "apt73",
    "boobateam": "boobaproject",
    "killsec3": "killsec",
    "iah6477": "iah647",
    "abyssdata": "abyss",
}

INDIA_CITIES = [
    "mumbai", "bombay", "delhi", "new delhi", "bengaluru", "bangalore", "hyderabad",
    "chennai", "madras", "kolkata", "calcutta", "pune", "ahmedabad", "surat", "jaipur",
    "lucknow", "kanpur", "nagpur", "indore", "thane", "bhopal", "visakhapatnam",
    "patna", "vadodara", "ghaziabad", "ludhiana", "coimbatore", "kochi", "cochin",
    "noida", "gurugram", "gurgaon", "chandigarh", "mysuru", "mysore", "trivandrum",
    "thiruvananthapuram", "bhubaneswar", "guwahati", "nashik", "faridabad", "rajkot",
]
INDIA_WORDS = ["india", "indian", "bharat", "pvt ltd", "private limited"]
INDIA_SIGNAL_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in INDIA_WORDS + INDIA_CITIES) + r")\b",
    re.IGNORECASE,
)

INDIA_COUNTRY_VALUES = {"in", "ind", "india"}

VERDICTS = {"india", "not_india", "india_sub", ""}

REVIEW_COLUMNS = ["victim", "source", "group", "domain", "country_tag", "my_verdict", "note"]

# Hand-assigned vendor taxonomy. Kept in its own CSV, keyed on victim_norm, because it
# answers a different question from the review queue: the queue adjudicates "is this
# India?" per record, this labels "what kind of business is it?" per entity. The upstream
# `sector` field is inferred and unverified, so it is a starting suggestion only.
VENDOR_CATEGORIES = {
    "it_services_bpo",          # sells engineering/IT/BPO capacity to other firms
    "product_software",         # sells its own software or platform to end users
    "manufacturing_industrial",
    "healthcare_life_sciences",
    "financial_services",
    "other",
    "",
}
CATEGORY_COLUMNS = ["victim_norm", "victim_example", "domain", "inferred_sector",
                    "vendor_category", "same_as", "note"]

# Column order for the flat export / DuckDB victims_norm table.
NORM_COLUMNS = [
    "source", "victim_original", "victim_norm", "group_name", "group_norm",
    "discovered_ts", "discovered_date", "attack_date",
    "domain", "domain_raw", "domain_source", "country_raw", "country_tagged",
    "country_borrowed", "country_borrowed_from",
    "sector", "sector_inferred",
    "data_size", "data_size_parsed",
    "description", "description_ai_generated",
    "claim_url", "magnet", "record_url",
    "tld_in", "needs_review", "india_any",
    "verdict", "india_final",
    "vendor_category", "entity_key",
    "multi_group_claim", "claiming_groups", "claim_dates",
]


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stamp() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def first_alias(record: dict, aliases: list[str]) -> Any:
    for key in aliases:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def parse_dt(value: Any) -> datetime | None:
    """Parse both feeds' date shapes into an aware UTC datetime."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text.upper() == "N/A":
        return None
    # ransomware.live: ISO-8601, usually with +00:00. RansomLook: 'YYYY-MM-DD HH:MM:SS'.
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        # RansomLook timestamps carry no timezone; the feed is UTC.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalise_name(name: str | None) -> str:
    """lowercase, strip legal suffixes, strip punctuation, collapse whitespace."""
    if not name:
        return ""
    text = name.lower()
    # Titles are sometimes URLs ("https://www.nitrex.in"). Strip the scheme and www so
    # they normalise to the same key as the plain company name in the other feed —
    # otherwise the join reports one victim twice, once per source.
    text = re.sub(r"^\s*[a-z]+://", "", text)
    text = re.sub(r"^www\.", "", text)
    text = text.rstrip("/")
    # Leak-post titles often carry a trailing descriptor after a colon or pipe.
    text = re.split(r"[|]", text)[0]
    text = re.sub(r"[^\w\s.&-]", " ", text)
    text = re.sub(r"[._-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    changed = True
    while changed:
        changed = False
        for suffix in sorted(LEGAL_SUFFIXES, key=len, reverse=True):
            token = " " + suffix.replace(".", "")
            if text.endswith(token):
                text = text[: -len(token)].strip()
                changed = True
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def registrable_domain(value: str | None) -> str:
    """Registrable domain from a bare host or an http(s) URL. Never called on onion/magnet."""
    if not value or not isinstance(value, str):
        return ""
    text = value.strip().lower()
    if not text or text in ("n/a", "-"):
        return ""
    text = re.sub(r"^[a-z]+://", "", text)
    text = text.split("/")[0].split("?")[0].split("@")[-1].split(":")[0]
    if not text or text.endswith(".onion"):
        return ""
    parts = _EXTRACT(text)
    # tldextract renamed this property in 5.x; prefer the new name, fall back on older ones.
    if hasattr(parts, "top_domain_under_public_suffix"):
        return parts.top_domain_under_public_suffix or ""
    return parts.registered_domain or ""


# RansomLook has no usable domain field, but many of its post titles ARE the victim's
# domain ("acehospital.in", "vcnyhome.com"). Only whole-title matches are accepted.
# Domains scraped out of description text were measured and rejected: that corpus is
# full of unrelated hosts (Login.gov) and attacker out-of-band callback domains
# (*.oast.me), which would attribute a stranger's domain to a victim.
TITLE_DOMAIN_RE = re.compile(r"^(?:https?://)?((?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,})/?$",
                             re.IGNORECASE)


def domain_from_title(title: str | None) -> str:
    match = TITLE_DOMAIN_RE.match((title or "").strip())
    return registrable_domain(match.group(1)) if match else ""


SIZE_RE = re.compile(r"\b(?:size|data\s*leaked|leaked\s*data)\s*[:\-]?\s*"
                     r"(\d+(?:[.,]\d+)?\s*(?:[KMGT]B|bytes))", re.IGNORECASE)


def parse_size_from_text(text: str | None) -> str:
    if not text:
        return ""
    match = SIZE_RE.search(text)
    return match.group(1).strip() if match else ""


SECTOR_RE = re.compile(r"\bsectors?\s*[:\-]\s*([A-Za-z][A-Za-z &/,'-]{2,60})", re.IGNORECASE)


def parse_sector_from_text(text: str | None) -> str:
    if not text:
        return ""
    match = SECTOR_RE.search(text)
    return match.group(1).strip().rstrip(".") if match else ""


def is_india_country(value: str | None) -> bool:
    return bool(value) and value.strip().lower() in INDIA_COUNTRY_VALUES


def india_signal_terms(*texts: str | None) -> list[str]:
    """Which India terms matched — recorded so a human can adjudicate without re-reading."""
    found: list[str] = []
    for text in texts:
        for term in INDIA_SIGNAL_RE.findall(text or ""):
            term = term.lower()
            if term not in found:
                found.append(term)
    return found


def months_in_window(start: date, end: date) -> list[tuple[int, int]]:
    out, year, month = [], start.year, start.month
    while (year, month) <= (end.year, end.month):
        out.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


# --------------------------------------------------------------------------------------
# Fetch + raw cache
# --------------------------------------------------------------------------------------

class Fetcher:
    """Fetches feeds, caching every raw response verbatim before anything parses it."""

    def __init__(self, raw_dir: Path, offline: bool, sleep_seconds: int):
        self.raw_dir = raw_dir
        self.offline = offline
        self.sleep_seconds = sleep_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        self._requests_made = 0

    # -- cache plumbing ------------------------------------------------------------
    def _dir(self, source: str) -> Path:
        path = self.raw_dir / source
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_raw(self, source: str, tag: str, body: bytes) -> Path:
        path = self._dir(source) / f"{stamp()}__{tag}.json"
        path.write_bytes(body)
        return path

    def _newest_cached(self, source: str, tag: str) -> Path | None:
        candidates = sorted(self._dir(source).glob(f"*__{tag}.json"))
        return candidates[-1] if candidates else None

    def _get_json(self, url: str, source: str, tag: str) -> Any:
        """Offline: newest cached file for this tag. Online: fetch, cache, then parse."""
        if self.offline:
            cached = self._newest_cached(source, tag)
            if cached is None:
                raise FileNotFoundError(
                    f"--offline: no cached response for {source}/{tag} under {self.raw_dir}. "
                    f"Run once without --offline to populate the cache."
                )
            print(f"  [offline] {source}/{tag} <- {cached.name}")
            return json.loads(cached.read_bytes())

        if self._requests_made and source == SRC_RW and self.sleep_seconds:
            print(f"  ... sleeping {self.sleep_seconds}s (ransomware.live free tier: 1 req/min)")
            time.sleep(self.sleep_seconds)

        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = self.session.get(url, timeout=90)
                self._requests_made += 1
                if response.status_code in (429, 500, 502, 503, 504):
                    wait = min(120, 15 * (attempt + 1))
                    print(f"  HTTP {response.status_code} from {url} — backing off {wait}s")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                body = response.content
                json.loads(body)  # validate before we claim the cache file is usable
                path = self._write_raw(source, tag, body)
                print(f"  [fetch] {url} -> {path.name} ({len(body):,} bytes)")
                return json.loads(body)
            except (requests.RequestException, json.JSONDecodeError) as exc:
                last_error = exc
                wait = min(120, 15 * (attempt + 1))
                print(f"  error on {url}: {exc} — retrying in {wait}s")
                time.sleep(wait)
        raise RuntimeError(f"giving up on {url}: {last_error}")

    # -- feeds ---------------------------------------------------------------------
    def ransomware_live(self, start: date, end: date) -> list[dict]:
        records: list[dict] = []
        for year, month in months_in_window(start, end):
            tag = f"victims_{year}-{month:02d}"
            data = self._get_json(f"{RW_LIVE_BASE}/victims/{year}/{month:02d}", SRC_RW, tag)
            if isinstance(data, list):
                records.extend(data)
            else:
                print(f"  WARNING: unexpected payload shape for {tag}: {type(data).__name__}")
        return records

    def ransomlook(self, start: date, end: date) -> list[dict]:
        tag = f"posts_period_{start:%Y-%m-%d}_{end:%Y-%m-%d}"
        url = f"{RANSOMLOOK_BASE}/posts/period/{start:%Y-%m-%d}/{end:%Y-%m-%d}"
        if self.offline and self._newest_cached(SRC_RL, tag) is None:
            # Window dates move with "today", so fall back to the newest period file.
            any_cached = sorted(self._dir(SRC_RL).glob("*__posts_period_*.json"))
            if any_cached:
                print(f"  [offline] {SRC_RL} <- {any_cached[-1].name} (window tag differs)")
                return json.loads(any_cached[-1].read_bytes())
        data = self._get_json(url, SRC_RL, tag)
        return data if isinstance(data, list) else []


# --------------------------------------------------------------------------------------
# Parse / normalise
# --------------------------------------------------------------------------------------

def warn_schema_drift(source: str, records: list[dict], aliases: dict, ignored: set[str]) -> None:
    known = {key for keys in aliases.values() for key in keys} | ignored
    unexpected = Counter(k for r in records for k in r if k not in known)
    if unexpected:
        print(f"  WARNING: {source} returned unmapped fields (schema drift?): "
              f"{', '.join(sorted(unexpected))}")
    for canonical, keys in aliases.items():
        if canonical in ("magnet",):
            continue
        if records and not any(any(k in r for k in keys) for r in records):
            print(f"  WARNING: {source} has no key for canonical field "
                  f"'{canonical}' (tried {keys}) — parser may have broken")


def normalise_records(source: str, records: list[dict], start: date, end: date) -> list[dict]:
    aliases = RW_LIVE_ALIASES if source == SRC_RW else RANSOMLOOK_ALIASES
    rows: list[dict] = []
    dropped_no_date = 0
    dropped_out_of_window = 0

    for record in records:
        victim_original = (first_alias(record, aliases["victim"]) or "").strip()
        group_name = (first_alias(record, aliases["group"]) or "").strip().lower()
        discovered = parse_dt(first_alias(record, aliases["discovered"]))
        if discovered is None:
            dropped_no_date += 1
            continue
        if not (start <= discovered.date() <= end):
            dropped_out_of_window += 1
            continue

        description = first_alias(record, aliases.get("description", [])) or ""
        if description.strip().upper() == "N/A":
            description = ""
        domain_raw = first_alias(record, aliases.get("domain", [])) or ""
        domain = registrable_domain(domain_raw)
        domain_source = "field" if domain else ""
        if not domain:
            domain = domain_from_title(victim_original)
            if domain:
                domain_source = "title"
        country_raw = (first_alias(record, aliases.get("country", [])) or "").strip()

        if source == SRC_RW:
            # Blanket per-source marking: ransomware.live enriches descriptions and
            # sector tags and labels neither. Nothing here is a source claim.
            description_ai = True
            sector = (first_alias(record, aliases["sector"]) or "").strip()
            sector_inferred = True
            data_size = (first_alias(record, aliases["data_size"]) or "").strip()
            data_size_parsed = parse_size_from_text(description)
            country_tagged: bool | None = is_india_country(country_raw)
            magnet = ""
        else:
            # RansomLook descriptions are the scraped leak post text, verbatim.
            description_ai = False
            sector = parse_sector_from_text(description)
            sector_inferred = False
            data_size = ""
            data_size_parsed = parse_size_from_text(description)
            # RansomLook has no country field at all: NULL, not False.
            country_tagged = None
            magnet = first_alias(record, aliases.get("magnet", [])) or ""

        attack_dt = parse_dt(first_alias(record, aliases.get("attack_date", [])))

        rows.append({
            "source": source,
            "victim_original": victim_original,
            "victim_norm": normalise_name(victim_original),
            "group_name": group_name,
            "discovered_ts": discovered,
            "discovered_date": discovered.date(),
            "attack_date": attack_dt.date() if attack_dt else None,
            "domain": domain,
            "domain_raw": domain_raw,
            "domain_source": domain_source,
            "country_raw": country_raw,
            "country_tagged": country_tagged,
            "country_borrowed": "",
            "country_borrowed_from": "",
            "sector": sector,
            "sector_inferred": sector_inferred,
            "data_size": data_size,
            "data_size_parsed": data_size_parsed,
            "description": description,
            "description_ai_generated": description_ai,
            # Stored as metadata only. Never fetched.
            "claim_url": first_alias(record, aliases.get("claim_url", [])) or "",
            "magnet": magnet,
            "record_url": first_alias(record, aliases.get("record_url", [])) or "",
        })

    if dropped_no_date:
        print(f"  note: {source}: {dropped_no_date} records dropped (unparseable discovered date)")
    print(f"  note: {source}: {dropped_out_of_window} records outside the window, "
          f"{len(rows)} kept")

    # One row per (source, victim, group, discovered_date).
    deduped: dict[tuple, dict] = {}
    for row in rows:
        key = (row["source"], row["victim_norm"], row["group_name"], row["discovered_date"])
        deduped.setdefault(key, row)
    if len(deduped) < len(rows):
        print(f"  note: {source}: {len(rows) - len(deduped)} exact "
              f"(source,victim,group,date) duplicates collapsed")
    return list(deduped.values())


# --------------------------------------------------------------------------------------
# Enrichment: multi-group claims, cross-fill, India flags
# --------------------------------------------------------------------------------------

def normalise_group(name: str | None) -> str:
    key = re.sub(r"[^a-z0-9]", "", (name or "").lower())
    return GROUP_ALIASES.get(key, key)


def mark_multi_group_claims(rows: list[dict]) -> int:
    """Flag victims claimed by more than one group. Returns spelling variants collapsed."""
    by_victim: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        row["group_norm"] = normalise_group(row["group_name"])
        if row["victim_norm"]:
            by_victim[row["victim_norm"]].append(row)
    collapsed = 0
    for victim_rows in by_victim.values():
        raw_groups = {r["group_name"] for r in victim_rows if r["group_name"]}
        norm_groups = {r["group_norm"] for r in victim_rows if r["group_norm"]}
        if len(raw_groups) > 1 and len(norm_groups) == 1:
            collapsed += 1
        groups = sorted(raw_groups)
        dates = sorted({str(r["discovered_date"]) for r in victim_rows})
        multi = len(norm_groups) > 1
        for row in victim_rows:
            row["multi_group_claim"] = multi
            row["claiming_groups"] = ", ".join(groups)
            row["claim_dates"] = ", ".join(dates)
    for row in rows:
        row.setdefault("multi_group_claim", False)
        row.setdefault("claiming_groups", row["group_name"])
        row.setdefault("claim_dates", str(row["discovered_date"]))
    return collapsed


def cross_fill_country(rows: list[dict]) -> int:
    """Copy ransomware.live's country onto matching RansomLook rows.

    Lands in its own column (country_borrowed). It never sets country_tagged —
    RansomLook has no country field, and a borrowed value is not a source tag.
    """
    rw_country: dict[str, str] = {}
    for row in rows:
        if row["source"] == SRC_RW and row["victim_norm"] and row["country_raw"]:
            rw_country.setdefault(row["victim_norm"], row["country_raw"])
    filled = 0
    for row in rows:
        if row["source"] == SRC_RL:
            borrowed = rw_country.get(row["victim_norm"], "")
            if borrowed:
                row["country_borrowed"] = borrowed
                row["country_borrowed_from"] = SRC_RW
                filled += 1
    return filled


def apply_india_flags(rows: list[dict], domain_available: dict[str, bool]) -> None:
    """Three independent flags. Never collapsed into one."""
    for row in rows:
        country_tagged = bool(row["country_tagged"])
        if row["domain"]:
            tld_in: bool | None = row["domain"].endswith(".in")
        elif not domain_available.get(row["source"], True):
            # No domain for this row and none anywhere in the payload: NULL, not False.
            # A False would read as "no Indian domain found", which is a different claim
            # from "this feed cannot answer".
            tld_in = None
        else:
            tld_in = False
        terms = india_signal_terms(row["victim_original"], row["description"])
        needs_review = bool(terms and not country_tagged and not tld_in)

        row["tld_in"] = tld_in
        row["needs_review"] = needs_review
        row["india_any"] = bool(country_tagged or tld_in or needs_review)
        row["india_signal_terms"] = ", ".join(terms)


# --------------------------------------------------------------------------------------
# Review queue (hand verdicts persist and always win)
# --------------------------------------------------------------------------------------

def review_key(row: dict) -> tuple[str, str, str]:
    return (row["victim_norm"] or row["victim_original"].lower(), row["source"], row["group_name"])


def load_review_queue(path: Path) -> dict[tuple[str, str, str], dict]:
    if not path.exists():
        return {}
    existing: dict[tuple[str, str, str], dict] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for entry in csv.DictReader(handle):
            key = (normalise_name(entry.get("victim", "")) or (entry.get("victim") or "").lower(),
                   entry.get("source", ""), (entry.get("group") or "").lower())
            verdict = (entry.get("my_verdict") or "").strip().lower()
            if verdict and verdict not in VERDICTS:
                print(f"  WARNING: review_queue.csv has unrecognised verdict "
                      f"{verdict!r} for {entry.get('victim')!r} — ignored "
                      f"(use india / not_india / india_sub)")
                entry["my_verdict"] = ""
            existing[key] = entry
    return existing


def review_reason(row: dict) -> str:
    reasons = []
    name = row["victim_original"].lower()
    if "india" in name and not row["country_tagged"] and not row["tld_in"]:
        reasons.append("'India' in name, no country tag or .in domain "
                       "— may not be an Indian entity")
    if (row["india_signal_terms"] or row["tld_in"]) and row["country_raw"] \
            and not is_india_country(row["country_raw"]):
        reasons.append(f"India signal but source country tag is "
                       f"{row['country_raw']} — possible foreign parent")
    if row["needs_review"] and not reasons:
        reasons.append("text signal only (no country tag, no .in domain)")
    if reasons and row["india_signal_terms"]:
        reasons.append(f"matched: {row['india_signal_terms']}")
    return "; ".join(reasons)


def sync_review_queue(path: Path, rows: list[dict]) -> tuple[dict, int]:
    """Load saved verdicts, apply them, append newly ambiguous records.

    Existing rows are never rewritten: my_verdict and note survive verbatim.
    """
    existing = load_review_queue(path)
    appended = 0
    ordered: list[dict] = list(existing.values())

    for row in rows:
        reason = review_reason(row)
        key = review_key(row)
        if key in existing:
            continue
        if not reason:
            continue
        ordered.append({
            "victim": row["victim_original"],
            "source": row["source"],
            "group": row["group_name"],
            "domain": row["domain"],
            "country_tag": row["country_raw"],
            "my_verdict": "",
            "note": reason,
        })
        existing[key] = ordered[-1]
        appended += 1

    if ordered:
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        tmp = path.with_suffix(path.suffix + ".tmp")
        fieldnames = list(REVIEW_COLUMNS)
        for entry in ordered:  # preserve any extra columns the user added by hand
            for key_name in entry:
                if key_name not in fieldnames:
                    fieldnames.append(key_name)
        with tmp.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for entry in ordered:
                writer.writerow(entry)
        os.replace(tmp, path)

    return existing, appended


def apply_verdicts(rows: list[dict], review: dict) -> None:
    for row in rows:
        entry = review.get(review_key(row))
        verdict = ((entry or {}).get("my_verdict") or "").strip().lower()
        verdict = verdict if verdict in VERDICTS else ""
        row["verdict"] = verdict
        if verdict == "not_india":
            row["india_final"] = False
        elif verdict in ("india", "india_sub"):
            row["india_final"] = True
        else:
            row["india_final"] = row["india_any"]


# --------------------------------------------------------------------------------------
# Vendor categories (hand-assigned, per entity, persist across runs)
# --------------------------------------------------------------------------------------

def load_categories(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    existing: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for entry in csv.DictReader(handle):
            key = (entry.get("victim_norm") or "").strip()
            if not key:
                continue
            category = (entry.get("vendor_category") or "").strip().lower()
            if category and category not in VENDOR_CATEGORIES:
                print(f"  WARNING: categories.csv has unrecognised vendor_category "
                      f"{category!r} for {key!r} — ignored (use "
                      f"{' / '.join(sorted(c for c in VENDOR_CATEGORIES if c))})")
                entry["vendor_category"] = ""
            existing[key] = entry
    return existing


def sync_categories(path: Path, rows: list[dict]) -> tuple[dict[str, dict], int]:
    """Load saved categories, append every newly-seen India entity, never rewrite a row.

    Only india_final entities are queued: categorising the whole feed is not the job.
    One row per victim_norm, so a victim appearing in both sources is labelled once.
    """
    existing = load_categories(path)
    ordered: list[dict] = list(existing.values())
    appended = 0

    for row in rows:
        if not row.get("india_final"):
            continue
        key = row["victim_norm"] or row["victim_original"].lower()
        if key in existing:
            # Fill in context that was blank when the row was first queued, without
            # ever touching the hand-set vendor_category or note.
            entry = existing[key]
            if not (entry.get("domain") or "").strip() and row.get("domain"):
                entry["domain"] = row["domain"]
            if not (entry.get("inferred_sector") or "").strip() and row.get("sector"):
                entry["inferred_sector"] = row["sector"]
            continue
        entry = {
            "victim_norm": key,
            "victim_example": row["victim_original"],
            "domain": row.get("domain") or "",
            "inferred_sector": row.get("sector") or "",
            "vendor_category": "",
            "note": "",
        }
        ordered.append(entry)
        existing[key] = entry
        appended += 1

    if ordered:
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        tmp = path.with_suffix(path.suffix + ".tmp")
        fieldnames = list(CATEGORY_COLUMNS)
        for entry in ordered:  # preserve any extra columns added by hand
            for name in entry:
                if name not in fieldnames:
                    fieldnames.append(name)
        with tmp.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for entry in sorted(ordered, key=lambda e: e["victim_norm"]):
                writer.writerow(entry)
        os.replace(tmp, path)

    return existing, appended


def resolve_same_as(categories: dict[str, dict]) -> dict[str, str]:
    """Map every victim_norm to its canonical entity key by following same_as.

    Normalisation cannot always tell that two leak-post titles name one company — a
    title that is a bare URL ("https://www.nitrex.in") and the plain company name
    ("Nitrex Chemicals India") strip to different keys, and merging on shared domain is
    unsafe because some records carry a lookup-site domain rather than the victim's own.
    So the merge is a hand judgment recorded in categories.csv, like the verdicts.
    """
    canonical: dict[str, str] = {}
    for key in categories:
        seen = [key]
        current = key
        while True:
            target = ((categories.get(current) or {}).get("same_as") or "").strip()
            if not target or target == current:
                break
            if target not in categories:
                print(f"  WARNING: categories.csv same_as for {current!r} points at "
                      f"{target!r}, which is not a known entity — ignored")
                break
            if target in seen:
                print(f"  WARNING: categories.csv same_as forms a cycle at {target!r} "
                      f"— ignored, {key!r} left standalone")
                current = key
                break
            seen.append(target)
            current = target
        canonical[key] = current
    return canonical


def apply_categories(rows: list[dict], categories: dict[str, dict]) -> None:
    canonical = resolve_same_as(categories)
    for row in rows:
        key = row["victim_norm"] or row["victim_original"].lower()
        entity = canonical.get(key, key)
        row["entity_key"] = entity
        # The category is read from the canonical entity, so a merged alias inherits
        # the label rather than needing its own.
        entry = categories.get(entity) or categories.get(key) or {}
        category = (entry.get("vendor_category") or "").strip().lower()
        row["vendor_category"] = category if category in VENDOR_CATEGORIES else ""


# --------------------------------------------------------------------------------------
# Join
# --------------------------------------------------------------------------------------

def join_sources(rows: list[dict]) -> tuple[dict[str, set[str]], list[dict]]:
    """Full outer join on normalised name, domain secondary. Entity = normalised name."""
    names = {SRC_RW: set(), SRC_RL: set()}
    domains = {SRC_RW: set(), SRC_RL: set()}
    name_domains: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if not row["victim_norm"]:
            continue
        names[row["source"]].add(row["victim_norm"])
        if row["domain"]:
            domains[row["source"]].add(row["domain"])
            name_domains[row["victim_norm"]].add(row["domain"])

    def matched(name: str, other: str) -> bool:
        if name in names[other]:
            return True
        return bool(name_domains[name] & domains[other])

    in_both = {n for n in names[SRC_RW] if matched(n, SRC_RL)}
    in_both |= {n for n in names[SRC_RL] if matched(n, SRC_RW)}
    only_rw = {n for n in names[SRC_RW] if n not in in_both}
    only_rl = {n for n in names[SRC_RL] if n not in in_both}

    joined = []
    for name in sorted(names[SRC_RW] | names[SRC_RL]):
        joined.append({
            "victim_norm": name,
            "in_ransomware_live": name in names[SRC_RW],
            "in_ransomlook": name in names[SRC_RL],
            "join_status": ("in_both" if name in in_both else
                            "only_ransomware_live" if name in names[SRC_RW] else
                            "only_ransomlook"),
        })
    return {"in_both": in_both, "only_ransomware_live": only_rw,
            "only_ransomlook": only_rl}, joined


# --------------------------------------------------------------------------------------
# Store
# --------------------------------------------------------------------------------------

def to_export_row(row: dict) -> dict:
    out = {}
    for column in NORM_COLUMNS:
        value = row.get(column)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        out[column] = value
    return out


# Explicit DuckDB types for victims_norm, so an all-empty column never silently
# becomes VARCHAR on a quiet week.
DUCKDB_TYPES: dict[str, str] = {
    "discovered_ts": "TIMESTAMPTZ", "discovered_date": "DATE", "attack_date": "DATE",
    "country_tagged": "BOOLEAN", "sector_inferred": "BOOLEAN",
    "description_ai_generated": "BOOLEAN", "tld_in": "BOOLEAN", "needs_review": "BOOLEAN",
    "india_any": "BOOLEAN", "india_final": "BOOLEAN", "multi_group_claim": "BOOLEAN",
}


def duckdb_column_spec() -> str:
    pairs = ", ".join(f"'{c}': '{DUCKDB_TYPES.get(c, 'VARCHAR')}'" for c in NORM_COLUMNS)
    return "{" + pairs + "}"


def store(db_path: Path, csv_path: Path, rows: list[dict], raw_counts: dict,
          joined: list[dict], review: dict, categories: dict) -> None:
    import duckdb

    export_rows = [to_export_row(r) for r in rows]

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORM_COLUMNS)
        writer.writeheader()
        writer.writerows(export_rows)

    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    try:
        # Every INSERT statement autocommits (and fsyncs) on its own, so a row-at-a-time
        # executemany over thousands of rows stalls the machine on disk I/O. Load the big
        # table straight from the CSV we just wrote, and wrap the small ones in one
        # explicit transaction.
        con.execute("SET threads=2")
        con.execute(
            "CREATE TABLE victims_norm AS SELECT * FROM read_csv(?, header=true, "
            "sample_size=-1, columns=" + duckdb_column_spec() + ")",
            [str(csv_path)],
        )
        con.execute("BEGIN TRANSACTION")
        con.execute("CREATE TABLE victims_raw (source TEXT, records BIGINT, fetched_at TIMESTAMP)")
        con.executemany("INSERT INTO victims_raw VALUES (?,?,?)",
                        [[s, n, utc_now()] for s, n in raw_counts.items()])
        con.execute("""CREATE TABLE joined (victim_norm TEXT, in_ransomware_live BOOLEAN,
                       in_ransomlook BOOLEAN, join_status TEXT)""")
        con.executemany("INSERT INTO joined VALUES (?,?,?,?)",
                        [[j["victim_norm"], j["in_ransomware_live"],
                          j["in_ransomlook"], j["join_status"]] for j in joined])
        con.execute("""CREATE TABLE review_queue (victim TEXT, source TEXT, group_name TEXT,
                       domain TEXT, country_tag TEXT, my_verdict TEXT, note TEXT)""")
        con.executemany("INSERT INTO review_queue VALUES (?,?,?,?,?,?,?)",
                        [[e.get("victim"), e.get("source"), e.get("group"), e.get("domain"),
                          e.get("country_tag"), e.get("my_verdict"), e.get("note")]
                         for e in review.values()])
        con.execute("""CREATE TABLE categories (victim_norm TEXT, victim_example TEXT,
                       domain TEXT, inferred_sector TEXT, vendor_category TEXT,
                       same_as TEXT, note TEXT)""")
        con.executemany("INSERT INTO categories VALUES (?,?,?,?,?,?,?)",
                        [[e.get("victim_norm"), e.get("victim_example"), e.get("domain"),
                          e.get("inferred_sector"), e.get("vendor_category"),
                          e.get("same_as"), e.get("note")]
                         for e in categories.values()])
        # Analysis should count entities, not normalised titles: entity_key already
        # folds the hand-merged aliases together, so this is the table to group by.
        con.execute("""CREATE VIEW india_entities AS
                       SELECT entity_key,
                              any_value(vendor_category)          AS vendor_category,
                              min(victim_original)                AS victim_example,
                              count(*)                            AS records,
                              bool_or(tld_in)                     AS tld_in,
                              bool_or(country_tagged)             AS country_tagged,
                              bool_or(tld_in OR country_tagged)   AS hard_flag,
                              count(DISTINCT group_norm)          AS groups,
                              count(DISTINCT source)              AS sources,
                              min(discovered_date)                AS first_seen,
                              max(discovered_date)                AS last_seen
                       FROM victims_norm WHERE india_final GROUP BY entity_key""")
        con.execute("COMMIT")
    finally:
        con.close()


# --------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------

def rule(title: str = "") -> None:
    print("\n" + ("── " + title + " ").ljust(100, "─") if title else "─" * 100)


def table(headers: list[str], data: Iterable[Iterable[Any]], max_width: int = 60) -> None:
    body = [[("" if c is None else str(c))[:max_width] for c in row] for row in data]
    if not body:
        print("  (none)")
        return
    widths = [max(len(h), *(len(r[i]) for r in body)) for i, h in enumerate(headers)]
    print("  " + "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  " + "  ".join("-" * w for w in widths))
    for row in body:
        print("  " + "  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


def freshness_banner(freshness: dict[str, date | None], gap_days: int) -> str | None:
    dates = [d for d in freshness.values() if d]
    if len(dates) < 2:
        return "!! only one source returned dated records — this is not a comparison !!"
    gap = (max(dates) - min(dates)).days
    if gap > gap_days:
        stale = [s for s, d in freshness.items() if d == min(dates)][0]
        return (f"!! FRESHNESS GAP: {gap} days between sources (newest {max(dates)}, "
                f"oldest {min(dates)} from {stale}).\n"
                f"!! A stalled feed or broken parser is likely. These counts measure an "
                f"OUTAGE, not coverage. Do not read the join numbers as coverage.")
    return None


def report(rows: list[dict], counts: dict, joins: dict, freshness: dict,
           gap_days: int, appended: int, borrowed: int, window: tuple[date, date],
           domain_available: dict[str, bool], collapsed_variants: int) -> None:
    banner = freshness_banner(freshness, gap_days)

    rule("WINDOW")
    print(f"  {window[0]} .. {window[1]}  (last {(window[1] - window[0]).days} days, "
          f"by discovered date)")

    rule("SOURCE TOTALS & FRESHNESS")
    table(["source", "records in window", "newest discovered"],
          [[s, counts.get(s, 0), freshness.get(s) or "n/a"] for s in (SRC_RW, SRC_RL)])
    if banner:
        print("\n" + banner)

    rule("JOIN (normalised name, domain secondary)")
    table(["bucket", "victims"],
          [[k, len(v)] for k, v in joins.items()])

    rule("INDIA FLAGS — three independent flags, per source")
    print("  country_tagged: source's own country field says India/IN/IND")
    print("  tld_in:         registrable domain ends .in (incl. .co.in)")
    print("  needs_review:   no tag and no .in domain, but India signal in name/description")
    print("  n/a means the field does not exist in that feed — it is NOT a zero.")
    print("  RansomLook carries no country field, and no domain field in this payload.\n")
    header = ["source", "country_tagged", "tld_in", "needs_review",
              "any (before verdicts)", "any (after verdicts)"]
    data = []
    for source in (SRC_RW, SRC_RL):
        subset = [r for r in rows if r["source"] == source]
        tagged = ("n/a" if source == SRC_RL
                  else sum(1 for r in subset if r["country_tagged"]))
        tld = ("n/a" if not domain_available.get(source, True)
               else sum(1 for r in subset if r["tld_in"]))
        data.append([source, tagged, tld,
                     sum(1 for r in subset if r["needs_review"]),
                     sum(1 for r in subset if r["india_any"]),
                     sum(1 for r in subset if r["india_final"])])
    table(header, data)
    changed = sum(1 for r in rows if r["india_any"] != r["india_final"])
    print(f"\n  saved verdicts changed {changed} record(s); "
          f"{appended} new record(s) appended to the review queue")
    print(f"  country_borrowed (RansomLook rows given ransomware.live's country via name "
          f"match): {borrowed} — separate column, never sets country_tagged")

    india = [r for r in rows if r["india_final"]]

    rule("INDIA VICTIMS BY SECTOR")
    print("  (ransomware.live sector is inferred enrichment; RansomLook sector is "
          "parsed from post text)")
    table(["sector", "victims"],
          Counter(r["sector"] or "(unknown)" for r in india).most_common())

    rule("INDIA VICTIMS BY GROUP")
    print("  (grouped on the normalised name — the feeds spell the same group differently,\n"
          "   which would otherwise split one actor across two rows)")
    # Label each cluster with its most common raw spelling.
    spellings: dict[str, Counter] = defaultdict(Counter)
    for r in india:
        spellings[r["group_norm"] or "(unknown)"][r["group_name"] or "(unknown)"] += 1
    table(["group", "victims", "spellings seen"],
          [[counts.most_common(1)[0][0], sum(counts.values()),
            ", ".join(sorted(counts)) if len(counts) > 1 else ""]
           for _, counts in sorted(spellings.items(),
                                   key=lambda kv: -sum(kv[1].values()))])

    rule("INDIA VICTIMS BY MONTH")
    table(["month", "victims"],
          sorted(Counter(r["discovered_date"].strftime("%Y-%m") for r in india).items()))

    rule("REPEAT / MULTI-GROUP CLAIMS")
    multi = [r for r in rows if r["multi_group_claim"]]
    print(f"  {len(multi)} record(s) across "
          f"{len({r['victim_norm'] for r in multi})} victim(s) claimed by >1 group")
    print(f"  ({collapsed_variants} victim(s) excluded: the two feeds spell one group's "
          f"name differently — cross-feed spelling, not a second claimant)")
    table(["victim", "groups", "dates"],
          sorted({(r["victim_original"], r["claiming_groups"], r["claim_dates"])
                  for r in multi})[:40])

    rule("INDIA-FLAGGED VICTIMS (eyeball attribution here)")
    print("  flags: C=country_tagged  T=tld_in  R=needs_review  B=country_borrowed\n")
    india_sorted = sorted(india, key=lambda r: (r["discovered_date"], r["victim_original"]),
                          reverse=True)
    table(["discovered", "victim", "group", "domain", "country", "sector", "flags", "verdict"],
          [[r["discovered_date"], r["victim_original"], r["group_name"], r["domain"],
            r["country_raw"] or (f"[{r['country_borrowed']}]" if r["country_borrowed"] else ""),
            r["sector"],
            "".join([("C" if r["country_tagged"] else ""), ("T" if r["tld_in"] else ""),
                     ("R" if r["needs_review"] else ""), ("B" if r["country_borrowed"] else "")]),
            r["verdict"]]
           for r in india_sorted],
          max_width=45)

    if banner:
        rule("FRESHNESS WARNING (repeated)")
        print(banner)


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=90, help="window size (default 90)")
    parser.add_argument("--offline", action="store_true",
                        help="work from ./raw cache, make no network requests")
    parser.add_argument("--raw-dir", type=Path, default=Path("raw"))
    parser.add_argument("--db", type=Path, default=Path("victims.duckdb"))
    parser.add_argument("--csv", type=Path, default=Path("victims_export.csv"))
    parser.add_argument("--review-queue", type=Path, default=Path("review_queue.csv"))
    parser.add_argument("--categories", type=Path, default=Path("categories.csv"))
    parser.add_argument("--freshness-gap-days", type=int, default=7)
    parser.add_argument("--sleep", type=int, default=RW_LIVE_SLEEP_SECONDS,
                        help="seconds between ransomware.live calls (free tier: 1 req/min)")
    args = parser.parse_args(argv)

    end = utc_now().date()
    start = end - timedelta(days=args.days)

    print(f"leaksite-india-monitor — window {start} .. {end}"
          f"{'  [OFFLINE]' if args.offline else ''}")
    print("metadata only: no archives, no onion fetches, no magnets followed\n")

    fetcher = Fetcher(args.raw_dir, args.offline, args.sleep)

    rule("FETCH")
    raw_rw = fetcher.ransomware_live(start, end)
    raw_rl = fetcher.ransomlook(start, end)

    rule("PARSE")
    warn_schema_drift(SRC_RW, raw_rw, RW_LIVE_ALIASES, RW_LIVE_IGNORED)
    warn_schema_drift(SRC_RL, raw_rl, RANSOMLOOK_ALIASES, RANSOMLOOK_IGNORED)
    rows = (normalise_records(SRC_RW, raw_rw, start, end)
            + normalise_records(SRC_RL, raw_rl, start, end))
    if not rows:
        print("\nNo records in window — nothing to report.")
        return 1

    counts = Counter(r["source"] for r in rows)
    freshness = {s: max((r["discovered_date"] for r in rows if r["source"] == s), default=None)
                 for s in (SRC_RW, SRC_RL)}

    banner = freshness_banner(freshness, args.freshness_gap_days)
    if banner:
        print("\n" + banner)

    # A feed that carries no domain field at all must not report tld_in = 0.
    domain_available = {s: any(r["domain"] for r in rows if r["source"] == s)
                        for s in (SRC_RW, SRC_RL)}
    for source, available in domain_available.items():
        if not available:
            print(f"  note: {source} returned no domain/website values in this payload — "
                  f"tld_in is n/a for it, not zero")

    collapsed_variants = mark_multi_group_claims(rows)
    borrowed = cross_fill_country(rows)
    apply_india_flags(rows, domain_available)
    review, appended = sync_review_queue(args.review_queue, rows)
    apply_verdicts(rows, review)
    # Categories are keyed on the India-final set, so this must run after the verdicts.
    categories, new_categories = sync_categories(args.categories, rows)
    apply_categories(rows, categories)

    joins, joined = join_sources(rows)
    store(args.db, args.csv, rows, dict(counts), joined, review, categories)

    report(rows, dict(counts), joins, freshness, args.freshness_gap_days,
           appended, borrowed, (start, end), domain_available, collapsed_variants)

    rule("OUTPUTS")
    print(f"  DuckDB       {args.db}")
    print(f"  CSV          {args.csv}")
    print(f"  review queue {args.review_queue}  "
          f"({sum(1 for e in review.values() if (e.get('my_verdict') or '').strip())} "
          f"verdict(s) saved, {len(review)} row(s) total)")
    merged = len(categories) - len(set(resolve_same_as(categories).values()))
    print(f"  categories   {args.categories}  "
          f"({sum(1 for e in categories.values() if (e.get('vendor_category') or '').strip())} "
          f"labelled, {len(categories) - merged} entities"
          f"{f' after merging {merged} alias(es)' if merged else ''}, "
          f"{new_categories} new)")
    print(f"  raw cache    {args.raw_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
