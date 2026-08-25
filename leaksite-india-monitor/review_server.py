#!/usr/bin/env python3
"""Local backing store for review_editor.html and category_editor.html.

Serves the editors and exposes a read/overwrite route per hand-maintained CSV:

    GET  /api/queue       -> review_queue.csv  (India verdicts, per record)
    POST /api/queue
    GET  /api/categories  -> categories.csv    (vendor taxonomy, per entity)
    POST /api/categories

Bound to 127.0.0.1 only. This exists because Brave and Firefox do not enable the
File System Access API, so the page cannot write to disk on its own. Run it while
adjudicating, Ctrl-C when done — it is not a service and stores nothing itself.

    python3 review_server.py            # http://127.0.0.1:8765/review_editor.html
                                        # http://127.0.0.1:8765/category_editor.html
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

MAX_BODY = 32 * 1024 * 1024


class Dataset:
    """One hand-maintained CSV, plus the shape a valid write must have.

    `choice_column` / `choices` guard the one field the editor sets, so a bad client
    cannot write a label the pipeline would later drop with a warning.
    """

    def __init__(self, path: Path, required: set[str], choice_column: str, choices: set[str],
                 key_column: str | None = None, pointer_column: str | None = None):
        self.path = path
        self.required = required
        self.choice_column = choice_column
        self.choices = choices
        self.key_column = key_column
        self.pointer_column = pointer_column

    def validate(self, incoming: list[dict]) -> str | None:
        if not incoming:
            return "refusing to write an empty file"
        missing = self.required - set(incoming[0])
        if missing:
            return f"missing columns: {sorted(missing)}"
        bad = {(r.get(self.choice_column) or "").strip().lower()
               for r in incoming} - self.choices
        if bad:
            return f"invalid {self.choice_column}: {sorted(bad)}"
        # A pointer column must hold a key from this same file. Catching this here is
        # what distinguishes a real merge from a column-shifted write dumping prose
        # into the field — the failure mode that silently corrupted this file once.
        if self.pointer_column and self.key_column:
            keys = {(r.get(self.key_column) or "").strip() for r in incoming}
            dangling = sorted({(r.get(self.pointer_column) or "").strip()
                               for r in incoming} - keys - {""})
            if dangling:
                return (f"{self.pointer_column} must name a {self.key_column} in this file; "
                        f"{len(dangling)} value(s) do not, e.g. {dangling[:3]}")
        return None


DATASETS = {
    "/api/queue": Dataset(
        Path("review_queue.csv"),
        {"victim", "source", "group", "my_verdict", "note"},
        "my_verdict",
        {"", "india", "not_india", "india_sub"},
    ),
    "/api/categories": Dataset(
        Path("categories.csv"),
        {"victim_norm", "vendor_category", "note"},
        "vendor_category",
        {"", "it_services_bpo", "product_software", "manufacturing_industrial",
         "healthcare_life_sciences", "financial_services", "other"},
        key_column="victim_norm",
        pointer_column="same_as",
    ),
}


class Handler(SimpleHTTPRequestHandler):

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
        dataset = DATASETS.get(self.path.split("?")[0])
        if dataset:
            if not dataset.path.exists():
                return self._send(404, f"{dataset.path} not found".encode())
            return self._send(200, dataset.path.read_bytes(), "text/csv; charset=utf-8")
        return super().do_GET()

    def do_POST(self):
        dataset = DATASETS.get(self.path.split("?")[0])
        if not dataset:
            return self._send(404, b"no such endpoint")

        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            return self._send(413, b"bad body length")
        text = self.rfile.read(length).decode("utf-8")

        # Validate before touching the file on disk. A malformed write here would
        # destroy hand-entered judgments, which are the one thing that cannot be
        # regenerated.
        try:
            incoming = list(csv.DictReader(io.StringIO(text)))
        except csv.Error as exc:
            return self._send(400, f"unparseable CSV: {exc}".encode())
        problem = dataset.validate(incoming)
        if problem:
            return self._send(400, problem.encode())

        if dataset.path.exists():
            existing = list(csv.DictReader(dataset.path.open(newline="", encoding="utf-8")))
            if len(incoming) != len(existing):
                return self._send(
                    409,
                    f"row count changed ({len(existing)} on disk, {len(incoming)} posted) "
                    f"— refusing to write; reload the page".encode(),
                )
            shutil.copy2(dataset.path, dataset.path.with_suffix(".csv.bak"))

        tmp = dataset.path.with_suffix(".csv.tmp")
        tmp.write_text(text, encoding="utf-8", newline="")
        os.replace(tmp, dataset.path)

        decided = sum(1 for r in incoming if (r.get(dataset.choice_column) or "").strip())
        return self._send(200, f"saved {len(incoming)} rows, {decided} set".encode())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--queue", type=Path, default=Path("review_queue.csv"))
    parser.add_argument("--categories", type=Path, default=Path("categories.csv"))
    parser.add_argument("--dir", type=Path, default=Path("."))
    args = parser.parse_args()

    DATASETS["/api/queue"].path = args.queue.resolve()
    DATASETS["/api/categories"].path = args.categories.resolve()
    handler = partial(Handler, directory=str(args.dir.resolve()))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"review editor    http://127.0.0.1:{args.port}/review_editor.html")
    print(f"category editor  http://127.0.0.1:{args.port}/category_editor.html")
    for route, dataset in DATASETS.items():
        print(f"  {route:18} {dataset.path}"
              f"{'' if dataset.path.exists() else '   [missing]'}")
    print("Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
