"""Market news ingestors: Fed, SEC, GDELT, FRED, BLS, BEA.

All return `ContentItem` lists. None of these endpoints serve copyrighted media.
Everything here is `permission_status = metadata_only` by definition.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from _shared import (
    ContentItem,
    Platform,
    SourceType,
    PermissionStatus,
    TrustTier,
    get_logger,
)
from rss_feed_ingestor.module import fetch_feed_entries

log = get_logger("market_news_ingestor")

FED_DEFAULT_FEED = "https://www.federalreserve.gov/feeds/press_all.xml"
SEC_PRESS_FEED = "https://www.sec.gov/news/pressreleases.rss"
SEC_8K_FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&output=atom"
GDELT_BASE = os.environ.get(
    "GDELT_BASE_URL", "https://api.gdeltproject.org/api/v2/doc/doc"
)


def fetch_fed_rss(feed_url: str = FED_DEFAULT_FEED) -> list[ContentItem]:
    items = fetch_feed_entries(
        feed_url,
        source_name="Federal Reserve",
        platform=Platform.FED,
        source_type=SourceType.FED_RSS,
    )
    for it in items:
        it.permission_status = PermissionStatus.METADATA_ONLY
    return items


def fetch_sec_rss(feed_url: str = SEC_PRESS_FEED) -> list[ContentItem]:
    items = fetch_feed_entries(
        feed_url,
        source_name="SEC",
        platform=Platform.SEC,
        source_type=SourceType.SEC_RSS,
    )
    for it in items:
        it.permission_status = PermissionStatus.METADATA_ONLY
    return items


def fetch_gdelt(query: str, *, timespan: str = "24h", max_records: int = 25) -> list[ContentItem]:
    """Run a GDELT 2.0 DOC API query and return article-style ContentItems."""
    qs = urllib.parse.urlencode(
        {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "timespan": timespan,
            "maxrecords": max_records,
            "sort": "DateDesc",
        }
    )
    url = f"{GDELT_BASE}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("GDELT query failed: %s", e)
        return []

    items: list[ContentItem] = []
    for art in payload.get("articles", []) or []:
        link = art.get("url")
        if not link:
            continue
        published_at = None
        seendate = art.get("seendate")
        if seendate:
            try:
                published_at = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                published_at = None
        items.append(
            ContentItem(
                source_type=SourceType.GDELT_QUERY,
                source_name=art.get("sourcecountry") or "GDELT",
                source_url=link,
                citation_url=link,
                platform=Platform.GDELT,
                title=art.get("title", link),
                original_author=art.get("domain"),
                published_at=published_at,
                permission_status=PermissionStatus.METADATA_ONLY,
                raw_payload=art,
            )
        )
    return items


def fetch_fred_series(series_id: str) -> list[ContentItem]:
    """Pull the latest observation(s) for a FRED series. Metadata only.

    Returns a single ContentItem representing the most recent observation,
    or an empty list when the API key is missing.
    """
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        log.warning("FRED_API_KEY not set; skipping %s", series_id)
        return []

    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("FRED fetch failed for %s: %s", series_id, e)
        return []

    obs_list = payload.get("observations") or []
    if not obs_list:
        return []
    obs = obs_list[0]
    citation = f"https://fred.stlouisfed.org/series/{series_id}"
    try:
        published_at = datetime.strptime(obs["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        published_at = None

    return [
        ContentItem(
            source_type=SourceType.FRED_SERIES,
            source_name=f"FRED {series_id}",
            source_url=citation,
            citation_url=citation,
            platform=Platform.FRED,
            title=f"FRED {series_id} = {obs.get('value')} on {obs.get('date')}",
            published_at=published_at,
            external_id=series_id,
            permission_status=PermissionStatus.METADATA_ONLY,
            raw_payload=obs,
        )
    ]
