#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import io
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from rank import rank_candidates
from src.reasoning import build_reason


FORM = """<!doctype html>
<html>
<head>
<title>Redrob Ranker Sandbox</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1100px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
  h1 { color: #1a1a2e; }
  .subtitle { color: #666; margin-bottom: 20px; }
  textarea { width: 100%; font-family: monospace; font-size: 13px; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
  button { background: #2563eb; color: white; padding: 10px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; margin-top: 10px; }
  button:hover { background: #1d4ed8; }
  .info { background: #e8f4fd; padding: 12px; border-radius: 6px; margin: 16px 0; font-size: 14px; }
</style>
</head>
<body>
<h1>Redrob Ranker Sandbox</h1>
<p class="subtitle">Paste JSONL candidate records below. Ranking runs locally, CPU-only, offline.</p>
<div class="info">
  <strong>Supported fields:</strong> candidate_id, profile (headline, summary, current_title, current_company, years_of_experience, location, country), career_history (title, company, description, duration_months, is_current), skills (name, duration_months, proficiency, endorsements), redrob_signals (all 23 fields).
</div>
<form method="post">
<textarea name="jsonl" rows="18" cols="120" placeholder='{"candidate_id":"CAND_0000001","profile":{"current_title":"ML Engineer",...},...}'></textarea><br>
<button type="submit">Rank Candidates</button>
</form>
</body>
</html>"""


def _build_results_html(ranked: list[dict]) -> str:
    rows_html = []
    for rank, row in enumerate(ranked[:10], start=1):
        candidate = row["candidate"]
        features = row["features"]
        parts = row["score_parts"]
        profile = candidate.get("profile", {})
        reasoning = build_reason(candidate, features, row["score"])

        score_bar_width = min(100, max(5, row["score"] * 100))
        evidence_pct = f"{parts['evidence']:.3f}"
        semantic_pct = f"{parts['semantic']:.3f}"
        behavior_pct = f"{parts['behavior']:.3f}"
        penalty_val = parts.get("penalty", 0)
        penalty_str = f"-{penalty_val:.3f}" if penalty_val > 0 else "0.000"

        anomaly_badge = ""
        if features.get("anomaly_confidence", 0) > 0:
            anomaly_badge = f' <span style="color:#dc2626;font-size:12px;">[{features["anomaly_action"]}]</span>'

        title = html.escape(profile.get("current_title", "Unknown"))
        company = html.escape(profile.get("current_company", "Unknown"))
        years = profile.get("years_of_experience", "?")
        name = html.escape(profile.get("anonymized_name", ""))

        rows_html.append(f"""
        <tr>
          <td style="text-align:center;font-weight:bold;font-size:18px;color:#2563eb;">{rank}</td>
          <td>
            <div style="font-weight:600;">{html.escape(candidate['candidate_id'])}</div>
            <div style="font-size:13px;color:#555;">{name}</div>
            <div style="font-size:13px;">{title} @ {company} ({years}yr)</div>
          </td>
          <td style="text-align:right;font-weight:600;font-size:16px;">{row['score']:.4f}</td>
          <td>
            <div style="background:#e5e7eb;border-radius:4px;height:8px;width:100px;">
              <div style="background:#2563eb;border-radius:4px;height:8px;width:{score_bar_width}px;"></div>
            </div>
          </td>
          <td style="font-size:12px;">
            <div>Evidence: {evidence_pct}</div>
            <div>Semantic: {semantic_pct}</div>
            <div>Behavior: {behavior_pct}</div>
            <div>Penalty: {penalty_str}{anomaly_badge}</div>
          </td>
          <td style="font-size:12px;color:#444;max-width:400px;">{html.escape(reasoning[:200])}{'...' if len(reasoning) > 200 else ''}</td>
        </tr>""")

    return f"""<!doctype html>
<html>
<head>
<title>Ranking Results</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8f9fa; }}
  h1 {{ color: #1a1a2e; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background: #1a1a2e; color: white; padding: 10px 12px; text-align: left; font-size: 13px; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #eee; vertical-align: top; }}
  tr:hover {{ background: #f0f4ff; }}
  .back {{ display: inline-block; margin: 16px 0; color: #2563eb; text-decoration: none; }}
  .back:hover {{ text-decoration: underline; }}
  .summary {{ background: white; padding: 16px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .download {{ display: inline-block; background: #16a34a; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 600; }}
  .download:hover {{ background: #15803d; }}
</style>
</head>
<body>
<h1>Ranking Results</h1>
<div class="summary">
  <strong>{len(ranked)}</strong> candidates ranked. Top 10 shown below.
  <a class="download" href="/download" style="margin-left:16px;">Download Full CSV</a>
  <a class="back" href="/" style="margin-left:16px;">Rank more candidates</a>
</div>
<table>
<tr>
  <th>#</th>
  <th>Candidate</th>
  <th>Score</th>
  <th>Bar</th>
  <th>Breakdown</th>
  <th>Reasoning</th>
</tr>
{''.join(rows_html)}
</table>
<div style="margin-top:16px;">
  <a class="back" href="/">Rank more candidates</a>
</div>
</body>
</html>"""


class SandboxHandler(BaseHTTPRequestHandler):
    _last_ranked: list[dict] | None = None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/download" and self._last_ranked:
            self._send_csv(self._last_ranked)
        else:
            self._send_html(FORM)

    def do_POST(self) -> None:  # noqa: N802
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
                ranked = rank_candidates(sample_path, keep=100, apply_coarse_filter=False)
            except Exception as exc:  # pragma: no cover
                self._send_html(f"<p>Ranking failed: {html.escape(str(exc))}</p>" + FORM, status=400)
                return

        if not ranked:
            self._send_html(
                "<p>No rankable candidates found. Check that the input is valid JSONL.</p>" + FORM,
                status=400,
            )
            return

        SandboxHandler._last_ranked = ranked
        self._send_html(_build_results_html(ranked))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_csv(self, ranked: list[dict]) -> None:
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
