"""CLI entry point for brief generation.

Examples:
  python -m brief_generator.run --kind daily_market_brief
  python -m brief_generator.run --kind trading_angle --topic "long bonds"
  python -m brief_generator.run --kind podcast_outline --ids ID1,ID2
"""
from __future__ import annotations

import argparse
import json

from .module import generate_daily_brief, generate_trading_angle, generate_podcast_outline
from dashboard_publisher.module import publish_brief_cards


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["daily_market_brief", "trading_angle", "podcast_outline"])
    ap.add_argument("--topic", help="for trading_angle")
    ap.add_argument("--ids", help="comma-separated content_item ids for podcast_outline")
    args = ap.parse_args()

    if args.kind == "daily_market_brief":
        brief = generate_daily_brief()
    elif args.kind == "trading_angle":
        if not args.topic:
            ap.error("--topic required for trading_angle")
        brief = generate_trading_angle(args.topic)
    else:
        ids = [s.strip() for s in (args.ids or "").split(",") if s.strip()]
        brief = generate_podcast_outline(ids)

    publish_brief_cards(brief)
    print(json.dumps(brief, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
