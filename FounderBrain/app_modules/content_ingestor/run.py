"""CLI entry point for the content ingestor.

Examples:
  python -m content_ingestor.run --url "https://www.youtube.com/watch?v=..."
  python -m content_ingestor.run --watchlist
"""
from __future__ import annotations

import argparse
import json

from .module import ingest_url, ingest_watchlist


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="Ingest a single URL")
    ap.add_argument("--watchlist", action="store_true", help="Scan the auto-scan watchlist")
    ap.add_argument("--project", action="append", default=[], help="project tag (repeatable)")
    ap.add_argument("--limit-per-source", type=int, default=10)
    args = ap.parse_args()

    if args.url:
        row = ingest_url(args.url, project_tags=args.project)
        print(json.dumps(row, indent=2, default=str))
        return 0 if row else 1
    if args.watchlist:
        stats = ingest_watchlist(limit_per_source=args.limit_per_source)
        print(json.dumps(stats, indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
