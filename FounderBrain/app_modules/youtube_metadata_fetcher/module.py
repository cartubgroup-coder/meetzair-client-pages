"""YouTube metadata fetcher.

Uses YouTube channel RSS for discovery and the YouTube Data API v3 for full
metadata. No download paths exist in this module — that is intentional.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Iterable

import urllib.request
import xml.etree.ElementTree as ET
import json

from _shared import (
    ContentItem,
    Platform,
    SourceType,
    PermissionStatus,
    get_logger,
)
from source_normalizer.module import youtube_video_id

log = get_logger("youtube_metadata_fetcher")

_API_BASE = "https://www.googleapis.com/youtube/v3"


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "FounderBrain/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "FounderBrain/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_channel_rss(channel_id: str) -> list[dict]:
    """Return parsed entries from a YouTube channel RSS feed."""
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    log.info("fetching channel RSS %s", channel_id)
    xml_text = _http_get_text(feed_url)
    root = ET.fromstring(xml_text)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    entries = []
    for entry in root.findall("atom:entry", ns):
        vid = entry.findtext("yt:videoId", default="", namespaces=ns)
        title = entry.findtext("atom:title", default="", namespaces=ns)
        published = entry.findtext("atom:published", default="", namespaces=ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href") if link_el is not None else f"https://www.youtube.com/watch?v={vid}"
        author = entry.findtext("atom:author/atom:name", default="", namespaces=ns)
        entries.append(
            {
                "external_id": vid,
                "title": title,
                "url": link,
                "published_at": published,
                "channel_name": author,
            }
        )
    return entries


def fetch_video_metadata(url_or_id: str) -> ContentItem | None:
    """Fetch metadata for a single video. Returns None if API key missing or video not found.

    Strict: metadata only. No transcript, no audio, no download path.
    """
    video_id = url_or_id if len(url_or_id) == 11 else youtube_video_id(url_or_id)
    if not video_id:
        log.warning("could not extract video id from %s", url_or_id)
        return None

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        log.warning("YOUTUBE_API_KEY not set; falling back to minimal metadata")
        return ContentItem(
            source_type=SourceType.YOUTUBE_VIDEO,
            source_name="YouTube",
            source_url=f"https://www.youtube.com/watch?v={video_id}",
            platform=Platform.YOUTUBE,
            title=f"YouTube video {video_id}",
            citation_url=f"https://www.youtube.com/watch?v={video_id}",
            external_id=video_id,
            permission_status=PermissionStatus.METADATA_ONLY,
        )

    url = (
        f"{_API_BASE}/videos?part=snippet,contentDetails,statistics"
        f"&id={video_id}&key={api_key}"
    )
    try:
        payload = _http_get_json(url)
    except Exception as e:  # network, quota, etc.
        log.warning("YouTube API error for %s: %s", video_id, e)
        return None

    items = payload.get("items") or []
    if not items:
        log.info("video %s not found", video_id)
        return None

    v = items[0]
    snippet = v.get("snippet", {}) or {}
    content = v.get("contentDetails", {}) or {}

    published_at = None
    if snippet.get("publishedAt"):
        published_at = datetime.fromisoformat(
            snippet["publishedAt"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)

    return ContentItem(
        source_type=SourceType.YOUTUBE_VIDEO,
        source_name=snippet.get("channelTitle", "YouTube"),
        source_url=f"https://www.youtube.com/watch?v={video_id}",
        citation_url=f"https://www.youtube.com/watch?v={video_id}",
        platform=Platform.YOUTUBE,
        title=snippet.get("title", f"YouTube video {video_id}"),
        description=snippet.get("description"),
        original_author=snippet.get("channelTitle"),
        published_at=published_at,
        external_id=video_id,
        duration_seconds=_iso8601_duration_to_seconds(content.get("duration")),
        thumbnail_url=(snippet.get("thumbnails", {}).get("high") or {}).get("url"),
        permission_status=PermissionStatus.METADATA_ONLY,
        raw_payload=v,
    )


def _iso8601_duration_to_seconds(d: str | None) -> int | None:
    if not d or not d.startswith("PT"):
        return None
    import re

    total = 0
    for value, unit in re.findall(r"(\d+)([HMS])", d):
        n = int(value)
        if unit == "H":
            total += n * 3600
        elif unit == "M":
            total += n * 60
        elif unit == "S":
            total += n
    return total or None
