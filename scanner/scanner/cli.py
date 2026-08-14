"""`python -m scanner <domain>` — standalone Collect + Judge with no DB or
web framework dependency. Useful for debugging a single rule/collector
without spinning up the whole stack. Deliberately stops at Judge: Explain
requires a Gemini key and a cache backend, neither of which this
framework-free package owns (see ai-engine/ and backend/).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict

from scanner.collect import collect_all
from scanner.enums import ScanTier
from scanner.rules import engine as judge_engine  # noqa: F401 — import registers every rule
from scanner.rules.scoring import compute_grade, severity_breakdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m scanner", description="Postura standalone scanner")
    parser.add_argument("hostname", help="Domain to scan, e.g. example.com")
    parser.add_argument("--tier", choices=["public", "verified"], default="public")
    parser.add_argument("--timeout", type=float, default=8.0, help="Per-collector HTTP timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print raw collector output as JSON instead of a summary")
    return parser


async def _run(args: argparse.Namespace) -> int:
    tier = ScanTier.VERIFIED if args.tier == "verified" else ScanTier.PUBLIC
    bundle = await collect_all(args.hostname, tier, http_timeout=args.timeout)
    findings = judge_engine.judge(bundle, tier)
    grade, score = compute_grade(findings)

    if args.json:
        payload = {
            "hostname": bundle.hostname,
            "tier": bundle.tier.value,
            "grade": grade.value,
            "score": score,
            "severityBreakdown": severity_breakdown(findings),
            "collectors": [
                {"collector": r.collector, "ok": r.ok, "data": r.data, "error": r.error} for r in bundle.results
            ],
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(f"Collected {bundle.signal_count} signals from {bundle.collector_count} collectors for {bundle.hostname}\n")
        for r in bundle.results:
            status = "OK" if r.ok else f"FAILED ({r.error})"
            print(f"  {r.collector:<20} {status}")

        print(f"\nGrade {grade.value} · {score} / 100 — {len(findings)} finding(s)\n")
        for f in findings:
            print(f"  [{f.severity.value:<8}] {f.rule_id:<32} {f.title}")

    return 0


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
