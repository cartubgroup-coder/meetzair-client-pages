"""Source normalization: URL canonicalization, classification, source lookup."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse, urlunparse

from _shared import (
    Platform,
    SourceType,
    PermissionStatus,
    TrustTier,
    get_logger,
    get_supabase,
)

log = get_logger("source_normalizer")


_YT_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "ref", "ref_src", "si",
}


def normalize_url(url: str) -> str:
    """Canonicalize URL: strip trackers, normalize host, force https where safe."""
    parsed = urlparse(url.strip())
    scheme = "https" if parsed.scheme in ("http", "https", "") else parsed.scheme
    netloc = parsed.netloc.lower()

    query_pairs = []
    for k, v in parse_qs(parsed.query, keep_blank_values=False).items():
        if k.lower() in _TRACKING_PARAMS:
            continue
        for val in v:
            query_pairs.append(f"{k}={val}")
    query = "&".join(sorted(query_pairs))

    path = parsed.path.rstrip("/")
    if not path:
        path = "/"

    return urlunparse((scheme, netloc, path, "", query, ""))


def classify_url(url: str) -> tuple[SourceType, Platform]:
    """Best-effort classification from URL alone. The DB row remains authoritative."""
    host = urlparse(url).netloc.lower()
    path = urlparse(url).path.lower()

    if host in _YT_HOSTS:
        if "watch" in path or host == "youtu.be":
            return SourceType.YOUTUBE_VIDEO, Platform.YOUTUBE
        if "playlist" in path:
            return SourceType.YOUTUBE_PLAYLIST, Platform.YOUTUBE
        if "channel" in path or "feeds/videos.xml" in path:
            return SourceType.YOUTUBE_CHANNEL, Platform.YOUTUBE
        return SourceType.YOUTUBE_VIDEO, Platform.YOUTUBE

    if "federalreserve.gov" in host and "feeds" in path:
        return SourceType.FED_RSS, Platform.FED
    if "sec.gov" in host:
        return SourceType.SEC_RSS, Platform.SEC
    if "gdeltproject.org" in host:
        return SourceType.GDELT_QUERY, Platform.GDELT
    if "stlouisfed.org" in host:
        return SourceType.FRED_SERIES, Platform.FRED
    if "bls.gov" in host:
        return SourceType.BLS_SERIES, Platform.BLS
    if "bea.gov" in host:
        return SourceType.BEA_SERIES, Platform.BEA

    if path.endswith(".rss") or path.endswith(".xml") or "rss" in path or "feed" in path:
        return SourceType.RSS, Platform.WEB

    return SourceType.WEB_ARTICLE, Platform.WEB


def youtube_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from any common URL shape."""
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/") or None
    if parsed.netloc.endswith("youtube.com"):
        if parsed.path == "/watch":
            q = parse_qs(parsed.query)
            return q.get("v", [None])[0]
        m = re.search(r"/(?:embed|shorts)/([^/?#]+)", parsed.path)
        if m:
            return m.group(1)
    return None


def lookup_or_register_source(
    url: str,
    *,
    auto_register: bool = True,
) -> dict | None:
    """Find a `content_sources` row matching this URL; optionally register a new one.

    Returns the row as a dict, or None when registration is disabled and no
    match exists.
    """
    canonical = normalize_url(url)
    source_type, platform = classify_url(canonical)

    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable: %s", e)
        return None

    res = sb.table("content_sources").select("*").eq("source_url", canonical).execute()
    if res.data:
        return res.data[0]

    if not auto_register:
        return None

    new_row = {
        "source_type": source_type.value,
        "source_name": urlparse(canonical).netloc or canonical,
        "source_url": canonical,
        "platform": platform.value,
        "trust_tier": TrustTier.UNKNOWN.value,
        "permission_status": PermissionStatus.METADATA_ONLY.value,
        "auto_scan": False,
        "enabled": True,
    }
    inserted = sb.table("content_sources").insert(new_row).execute()
    log.info("registered new source %s", canonical)
    return inserted.data[0] if inserted.data else new_row
