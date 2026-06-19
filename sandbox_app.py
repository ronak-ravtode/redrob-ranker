#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from rank import rank_candidates
from src.reasoning import build_reason


FORM = """
<!doctype html>
<html>
<head><title>Redrob Ranker Sandbox</title></head>
<body>
<h1>Redrob Ranker Sandbox</h1>
<p>Paste up to 100 JSONL candidate records. Ranking is local, CPU-only, and offline.</p>
<form method="post">
<textarea name="jsonl" rows="25" cols="120"></textarea><br>
<button type="submit">Rank sample</button>
</form>
</body>
</html>
"""


class SandboxHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler method
        self._send_html(FORM)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler method
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        payload = parse_qs(body).get("jsonl", [""])[0]
        lines = [line for line in payload.splitlines() if line.strip()]
        if not lines:
            self._send_html("<p>No JSONL records supplied.</p>" + FORM, status=400)
            return
        if len(lines) > 100:
            self._send_html("<p>Sample limit is 100 candidates.</p>" + FORM, status=400)
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.jsonl"
            sample_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            try:
                ranked = rank_candidates(sample_path, keep=100)
            except Exception as exc:  # pragma: no cover - UI error path
                self._send_html(f"<p>Ranking failed: {html.escape(str(exc))}</p>" + FORM, status=400)
                return

        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=sample_ranking.csv")
        self.end_headers()
        writer = csv.DictWriter(
            _TextResponseWriter(self.wfile),
            fieldnames=["candidate_id", "rank", "score", "reasoning"],
        )
        writer.writeheader()
        for rank, row in enumerate(ranked, start=1):
            candidate = row["candidate"]
            writer.writerow({
                "candidate_id": candidate["candidate_id"],
                "rank": rank,
                "score": f"{row['score']:.8f}",
                "reasoning": build_reason(candidate, row["features"], row["score"]),
            })

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class _TextResponseWriter:
    def __init__(self, binary_writer):
        self.binary_writer = binary_writer

    def write(self, text: str) -> int:
        data = text.encode("utf-8")
        self.binary_writer.write(data)
        return len(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Redrob sample-ranking sandbox.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), SandboxHandler)
    print(f"Serving sandbox at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
