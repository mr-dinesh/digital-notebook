#!/usr/bin/env python3
"""Fetch every deployed page and flag missing social-card tags.

Checks the live HTML, not the local source -- the two drift whenever a
wrangler deploy is forgotten. Also HEADs each og:image so a card that 404s
is caught here rather than in a chat preview.

Usage: python3 tools/check_og.py
Exits non-zero if anything is missing.
"""

import re
import sys
import urllib.request

REQUIRED = ["og:title", "og:description", "og:image", "og:url", "twitter:card"]

URLS = [
    "https://mrdee.in/",
    "https://juicesec.mrdinesh.workers.dev/",
    "https://argus-proxy.mrdinesh.workers.dev/",
    "https://signal-feed-8pl.pages.dev/",
    "https://afl-masterclass.pages.dev/",
    "https://privyread.pages.dev/",
    "https://hn-blackout.pages.dev/",
    "https://s.mrdee.in/links",
]

UA = {"User-Agent": "og-check/1.0 (+https://mrdee.in)"}


def fetch(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.headers, (r.read() if method == "GET" else b"")


def main():
    failures = []
    for url in URLS:
        try:
            _, _, body = fetch(url)
        except Exception as e:
            print(f"FAIL  {url}\n        unreachable: {e}")
            failures.append(url)
            continue

        html = body.decode("utf-8", "replace")
        missing = [t for t in REQUIRED if t not in html]

        img_ok = ""
        m = re.search(r'og:image"\s+content="([^"]+)"', html)
        if m:
            img = m.group(1)
            if not img.startswith("https://"):
                missing.append("og:image is not absolute")
            else:
                try:
                    status, headers, _ = fetch(img, "HEAD")
                    size = int(headers.get("Content-Length") or 0)
                    img_ok = f"image {status} {headers.get('Content-Type')} {size / 1024:.0f}KB"
                    if status != 200:
                        missing.append(f"og:image returned {status}")
                    # WhatsApp quietly downgrades to a small thumbnail past ~300KB.
                    if size > 300 * 1024:
                        missing.append(f"og:image is {size / 1024:.0f}KB, over 300KB")
                except Exception as e:
                    missing.append(f"og:image unreachable: {e}")

        if missing:
            print(f"FAIL  {url}\n        missing: {', '.join(missing)}")
            failures.append(url)
        else:
            print(f"ok    {url}  ({img_ok})")

    if failures:
        print(f"\n{len(failures)} of {len(URLS)} pages need attention")
        return 1
    print(f"\nall {len(URLS)} pages have complete social cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
