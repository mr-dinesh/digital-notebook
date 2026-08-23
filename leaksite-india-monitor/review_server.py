#!/usr/bin/env python3
"""Local backing store for review_editor.html.

Serves the editor and exposes two routes for the queue CSV:

    GET  /api/queue  -> the raw CSV text
    POST /api/queue  -> overwrite it (backup first, atomic rename)

Bound to 127.0.0.1 only. This exists because Brave and Firefox do not enable the
File System Access API, so the page cannot write to disk on its own. Run it while
adjudicating, Ctrl-C when done — it is not a service and stores nothing itself.

    python3 review_server.py            # http://127.0.0.1:8765/review_editor.html
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REQUIRED_COLUMNS = {"victim", "source", "group", "my_verdict", "note"}
VALID_VERDICTS = {"", "india", "not_india", "india_sub"}
MAX_BODY = 32 * 1024 * 1024


class Handler(SimpleHTTPRequestHandler):
    queue_path: Path = Path("review_queue.csv")

    def log_message(self, fmt, *args):  # quieter than the default access log
        if "/api/" in (self.path or ""):
            super().log_message(fmt, *args)

    # -- helpers -----------------------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str = "text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # -- routes ------------------------------------------------------------------
    def do_GET(self):
        if self.path.split("?")[0] == "/api/queue":
            if not self.queue_path.exists():
                return self._send(404, f"{self.queue_path} not found".encode())
            return self._send(200, self.queue_path.read_bytes(), "text/csv; charset=utf-8")
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/queue":
            return self._send(404, b"no such endpoint")

        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            return self._send(413, b"bad body length")
        text = self.rfile.read(length).decode("utf-8")

        # Validate before touching the file on disk. A malformed write here would
        # destroy hand-entered verdicts, which are the one thing that cannot be
        # regenerated.
        try:
            incoming = list(csv.DictReader(io.StringIO(text)))
        except csv.Error as exc:
            return self._send(400, f"unparseable CSV: {exc}".encode())
        if not incoming:
            return self._send(400, b"refusing to write an empty queue")
        missing = REQUIRED_COLUMNS - set(incoming[0])
        if missing:
            return self._send(400, f"missing columns: {sorted(missing)}".encode())
        bad = {(r.get("my_verdict") or "").strip().lower() for r in incoming} - VALID_VERDICTS
        if bad:
            return self._send(400, f"invalid verdict(s): {sorted(bad)}".encode())

        if self.queue_path.exists():
            existing = list(csv.DictReader(self.queue_path.open(newline="", encoding="utf-8")))
            if len(incoming) != len(existing):
                return self._send(
                    409,
                    f"row count changed ({len(existing)} on disk, {len(incoming)} posted) "
                    f"— refusing to write; reload the page".encode(),
                )
            shutil.copy2(self.queue_path, self.queue_path.with_suffix(".csv.bak"))

        tmp = self.queue_path.with_suffix(".csv.tmp")
        tmp.write_text(text, encoding="utf-8", newline="")
        os.replace(tmp, self.queue_path)

        decided = sum(1 for r in incoming if (r.get("my_verdict") or "").strip())
        return self._send(200, f"saved {len(incoming)} rows, {decided} decided".encode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--queue", type=Path, default=Path("review_queue.csv"))
    parser.add_argument("--dir", type=Path, default=Path("."))
    args = parser.parse_args()

    Handler.queue_path = args.queue.resolve()
    handler = partial(Handler, directory=str(args.dir.resolve()))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"review editor  http://127.0.0.1:{args.port}/review_editor.html")
    print(f"queue file     {Handler.queue_path}")
    print("Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
