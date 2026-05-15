"""Generic RSS / Atom feed ingestor.

Used directly for podcasts and generic web feeds, and as the underlying primitive
for the Fed/SEC feeds in `market_news_ingestor`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
import urllib.request
import xml.etree.ElementTree as ET

from _shared import (
    ContentItem,
    Platform,
    SourceType,
    PermissionStatus,
    get_logger,
)

log = get_logger("rss_feed_ingestor")


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "FounderBrain/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def fetch_feed_entries(
    feed_url: str,
    *,
    source_name: str,
    platform: Platform = Platform.WEB,
    source_type: SourceType = SourceType.RSS,
) -> list[ContentItem]:
    """Parse an RSS 2.0 or Atom feed and return ContentItems (metadata only)."""
    try:
        data = _http_get(feed_url)
    except Exception as e:
        log.warning("feed fetch failed %s: %s", feed_url, e)
        return []

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        log.warning("feed parse failed %s: %s", feed_url, e)
        return []

    items: list[ContentItem] = []
    tag = root.tag.lower()

    if tag.endswith("rss") or root.find("channel") is not None:
        channel = root.find("channel") or root
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub = item.findtext("pubDate")
            published_at = _parse_rss_date(pub)
            author = (item.findtext("author") or item.findtext("{http://purl.org/dc/elements/1.1/}creator") or "").strip()
            if not link:
                continue
            items.append(
                ContentItem(
                    source_type=source_type,
                    source_name=source_name,
                    source_url=link,
                    citation_url=link,
                    platform=platform,
                    title=title or link,
                    description=description or None,
                    original_author=author or None,
                    published_at=published_at,
                    permission_status=PermissionStatus.METADATA_ONLY,
                )
            )
    else:
        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            pub = entry.findtext("atom:published", default=None, namespaces=ns) or \
                  entry.findtext("atom:updated", default=None, namespaces=ns)
            published_at = _parse_iso_date(pub)
            author = entry.findtext("atom:author/atom:name", default="", namespaces=ns)
            if not link:
                continue
            items.append(
                ContentItem(
                    source_type=source_type,
                    source_name=source_name,
                    source_url=link,
                    citation_url=link,
                    platform=platform,
                    title=title or link,
                    description=summary or None,
                    original_author=author or None,
                    published_at=published_at,
                    permission_status=PermissionStatus.METADATA_ONLY,
                )
            )

    log.info("parsed %d items from %s", len(items), feed_url)
    return items


def _parse_rss_date(s: str | None) -> datetime | None:
    if not s:
        return None
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(s).astimezone(timezone.utc)
    except Exception:
        return None


def _parse_iso_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None
