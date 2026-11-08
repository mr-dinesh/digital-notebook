#!/usr/bin/env python3
"""Weekly check that the AI models behind the live projects still exist.

Two kinds of check, both driven by watch.json:
  1. Catalog: is each model still offered by its provider, and is a
     retirement date announced? (Workers AI publishes these dates ahead of
     time; Groq and Gemini only tell us whether the model is still listed.)
  2. Probe: send one small real request to each deployed AI endpoint.

A catalog whose API key is missing is skipped, not failed. Writes a Markdown
report to stdout (and to $REPORT if set). Exits 1 if anything failed.

Env: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID (Workers AI Read),
     GROQ_API_KEY, GOOGLE_API_KEY. Standard library only.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
WARN_DAYS = 60          # flag a Workers AI retirement this far ahead
UA = "model-watch/1.0"


def http(url, data=None, headers=None, timeout=60):
    """Return (status, parsed JSON or text). Never raises on HTTP errors."""
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, **(headers or {})})
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    except Exception as e:  # DNS, timeout, TLS
        return 0, f"{type(e).__name__}: {e}"
    text = raw.decode("utf-8", "replace")
    try:
        return status, json.loads(text)
    except ValueError:
        return status, text


# ---------- catalogs: model name -> retirement date ("" if none announced) ----------

def workers_ai_catalog(args):
    if args.workers_catalog:            # local testing: output of `wrangler ai models --json`
        models = json.loads(pathlib.Path(args.workers_catalog).read_text())
    else:
        token, acct = os.getenv("CLOUDFLARE_API_TOKEN"), os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not (token and acct):
            return None
        status, data = http(
            f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/models/search?per_page=1000",
            headers={"Authorization": f"Bearer {token}"})
        if status != 200 or not isinstance(data, dict):
            raise RuntimeError(f"Cloudflare catalog HTTP {status}")
        models = data["result"]
    out = {}
    for m in models:
        props = {p.get("property_id"): p.get("value") for p in m.get("properties", [])}
        out[m["name"]] = str(props.get("planned_deprecation_date") or "")
    return out


def groq_catalog(_args):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    status, data = http("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"})
    if status != 200 or not isinstance(data, dict):
        raise RuntimeError(f"Groq catalog HTTP {status}")
    return {m["id"]: "" for m in data["data"]}


def gemini_catalog(_args):
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    out, token = {}, ""
    while True:
        url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000"
        if token:
            url += f"&pageToken={token}"
        # key goes in a header, not the URL, so it never lands in logs
        status, data = http(url, headers={"x-goog-api-key": key})
        if status != 200 or not isinstance(data, dict):
            raise RuntimeError(f"Gemini catalog HTTP {status}")
        for m in data.get("models", []):
            out[m["name"].removeprefix("models/")] = ""
        token = data.get("nextPageToken")
        if not token:
            return out


CATALOGS = {"workers-ai": workers_ai_catalog, "groq": groq_catalog, "gemini": gemini_catalog}


def dig(obj, path):
    for part in path.split("."):
        if isinstance(obj, list) and part.isdigit() and int(part) < len(obj):
            obj = obj[int(part)]
        elif isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return None
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers-catalog", help="read the Workers AI catalog from this JSON file")
    ap.add_argument("--no-probes", action="store_true")
    args = ap.parse_args()

    cfg = json.loads((HERE / "watch.json").read_text())
    today = dt.date.today()
    rows, failed, warned = [], 0, 0

    # ---- catalogs ----
    catalogs = {}
    for provider in sorted({m["provider"] for m in cfg["models"]}):
        try:
            catalogs[provider] = CATALOGS[provider](args)
        except Exception as e:
            catalogs[provider] = e

    for m in cfg["models"]:
        cat = catalogs[m["provider"]]
        label = f"`{m['model']}` ({m['provider']})"
        if cat is None:
            rows.append(("⏭️ skipped", m["project"], label, "no API key set for this provider"))
        elif isinstance(cat, Exception):
            failed += 1
            rows.append(("❌ error", m["project"], label, str(cat)))
        elif m["model"] not in cat:
            failed += 1
            rows.append(("❌ gone", m["project"], label, "no longer in the provider's model list"))
        elif cat[m["model"]]:
            when = cat[m["model"]][:10]
            try:
                days = (dt.date.fromisoformat(when) - today).days
            except ValueError:
                days = 0
            if days <= WARN_DAYS:
                warned += 1
                rows.append(("⚠️ retiring", m["project"], label, f"retirement date {when} ({days} days)"))
            else:
                rows.append(("✅ ok", m["project"], label, f"retires {when}"))
        else:
            rows.append(("✅ ok", m["project"], label, ""))

    # ---- live probes ----
    if not args.no_probes:
        for p in cfg["probes"]:
            status, data = http(p["url"], data=p["body"])
            got = dig(data, p["expect"]) if isinstance(data, dict) else None
            if status == 200 and got:
                note = f"model `{data['model']}`" if isinstance(data, dict) and data.get("model") else ""
                rows.append(("✅ ok", p["project"], f"POST {p['url']}", note))
            else:
                failed += 1
                err = data.get("error") if isinstance(data, dict) else str(data)
                rows.append(("❌ failing", p["project"], f"POST {p['url']}", f"HTTP {status}: {str(err)[:200]}"))

    lines = [
        f"## Model watch: {today.isoformat()}",
        "",
        f"**{failed} failing, {warned} retiring within {WARN_DAYS} days.**",
        "",
        "| Status | Project | Check | Detail |",
        "|---|---|---|---|",
        *[f"| {s} | {p} | {c} | {d.replace('|', '/')} |" for s, p, c, d in rows],
        "",
        "Fix: swap the model in the project, redeploy, then update `model-watch/watch.json`. "
        "Current catalogs: `wrangler ai models`, https://console.groq.com/docs/deprecations, "
        "https://ai.google.dev/gemini-api/docs/models",
    ]
    report = "\n".join(lines)
    print(report)
    if os.getenv("REPORT"):
        pathlib.Path(os.environ["REPORT"]).write_text(report + "\n")
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"needs_attention={'true' if failed or warned else 'false'}\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
