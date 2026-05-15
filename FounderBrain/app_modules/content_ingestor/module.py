"""Content ingestor: the orchestrator the rest of the pipeline plugs into.

Responsibilities:
  - Resolve a URL (or pull a watchlist).
  - Dispatch to the correct fetcher.
  - Apply permission checks (see youtube-intake-policy.md).
  - Write `content_items`, `content_transcripts`, `content_chunks`.
  - Hand off to embedding_writer.
  - Hand off to dashboard_publisher.
"""
from __future__ import annotations

import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Iterable

from _shared import (
    ContentItem,
    DashboardStatus,
    EmbeddingStatus,
    PermissionStatus,
    SourceType,
    SummaryStatus,
    TranscriptStatus,
    get_logger,
    get_supabase,
)
from source_normalizer.module import classify_url, normalize_url, lookup_or_register_source
from youtube_metadata_fetcher.module import fetch_video_metadata
from youtube_transcript_fetcher.module import fetch_transcript
from rss_feed_ingestor.module import fetch_feed_entries
from market_news_ingestor.module import (
    fetch_fed_rss,
    fetch_sec_rss,
    fetch_gdelt,
    fetch_fred_series,
)
from content_chunker.module import chunk_text, chunk_transcript_segments
from embedding_writer.module import write_embeddings_for_item
from dashboard_publisher.module import publish_intake_card, record_source_health

log = get_logger("content_ingestor")


# --------------- public API ---------------

def ingest_url(url: str, *, project_tags: list[str] | None = None) -> dict | None:
    """Ingest a single URL through the full pipeline. Returns the content_item row or None."""
    canonical = normalize_url(url)
    source_type, _platform = classify_url(canonical)
    source_row = lookup_or_register_source(canonical, auto_register=True)

    item: ContentItem | None
    if source_type == SourceType.YOUTUBE_VIDEO:
        item = fetch_video_metadata(canonical)
    elif source_type in (SourceType.FED_RSS, SourceType.SEC_RSS, SourceType.RSS):
        # one-off RSS URL — treat as a single feed pull
        entries = fetch_feed_entries(canonical, source_name=_source_name(source_row), source_type=source_type)
        return _persist_first_or_none(entries, project_tags, source_row)
    elif source_type == SourceType.GDELT_QUERY:
        entries = fetch_gdelt(query=canonical, timespan="24h")
        return _persist_first_or_none(entries, project_tags, source_row)
    elif source_type == SourceType.FRED_SERIES:
        sid = source_row.get("source_external_id") if source_row else None
        if not sid:
            log.warning("FRED source missing source_external_id; refusing to ingest")
            return None
        entries = fetch_fred_series(sid)
        return _persist_first_or_none(entries, project_tags, source_row)
    else:
        # Generic web article: store the URL metadata only; full scrape is the
        # job of a separate, opt-in scraper (Firecrawl). Keeping this honest.
        item = ContentItem(
            source_type=source_type,
            source_name=_source_name(source_row) or "Web",
            source_url=canonical,
            citation_url=canonical,
            platform=_platform,
            title=canonical,
            permission_status=PermissionStatus.METADATA_ONLY,
        )

    if not item:
        return None
    if project_tags:
        item.project_tags = list(set([*item.project_tags, *project_tags]))
    if source_row:
        item.source_id = source_row["id"]
        item.project_tags = list(set([*item.project_tags, *(source_row.get("project_tags") or [])]))

    row = _persist_item(item)
    if row is None:
        return None

    # Transcript pass (YouTube only, captions only)
    if item.source_type == SourceType.YOUTUBE_VIDEO:
        _try_transcript(row)

    # Chunk + embed
    _chunk_and_embed(row)

    # Dashboard
    publish_intake_card(row)
    return row


def ingest_watchlist(limit_per_source: int = 10) -> dict:
    """Scan every enabled, auto-scan source. Returns summary stats."""
    sb = get_supabase()
    sources = (
        sb.table("content_sources")
        .select("*")
        .eq("auto_scan", True)
        .eq("enabled", True)
        .execute()
        .data
        or []
    )

    stats = {"sources_scanned": 0, "items_seen": 0, "items_new": 0, "failures": 0}
    for src in sources:
        stats["sources_scanned"] += 1
        t0 = time.time()
        try:
            new_items = _scan_one_source(src, limit_per_source)
            stats["items_seen"] += new_items["seen"]
            stats["items_new"] += new_items["new"]
            record_source_health(
                src["id"],
                status="healthy",
                latency_ms=int((time.time() - t0) * 1000),
                items_found=new_items["seen"],
            )
        except Exception as e:
            stats["failures"] += 1
            log.warning("source scan failed %s: %s", src.get("source_url"), e)
            record_source_health(
                src["id"],
                status="unhealthy",
                latency_ms=int((time.time() - t0) * 1000),
                last_error=str(e),
            )
    return stats


# --------------- helpers ---------------

def _source_name(source_row: dict | None) -> str:
    return (source_row or {}).get("source_name", "")


def _scan_one_source(src: dict, limit: int) -> dict:
    st = src["source_type"]
    items: list[ContentItem] = []
    if st == "fed_rss":
        items = fetch_fed_rss(src["source_url"])
    elif st == "sec_rss":
        items = fetch_sec_rss(src["source_url"])
    elif st in ("rss", "podcast_feed", "youtube_channel"):
        items = fetch_feed_entries(
            src["source_url"],
            source_name=src.get("source_name", st),
            source_type=SourceType(st),
        )
    elif st == "gdelt_query":
        items = fetch_gdelt(src["source_url"], timespan="24h", max_records=limit)
    elif st == "fred_series":
        sid = src.get("source_external_id")
        if sid:
            items = fetch_fred_series(sid)
    else:
        log.info("skipping unsupported source_type %s", st)
        return {"seen": 0, "new": 0}

    seen = len(items)
    new = 0
    for it in items[:limit]:
        it.source_id = src["id"]
        it.project_tags = list(set([*it.project_tags, *(src.get("project_tags") or [])]))
        row = _persist_item(it)
        if row:
            new += 1
            if it.source_type == SourceType.YOUTUBE_VIDEO:
                _try_transcript(row)
            _chunk_and_embed(row)
            publish_intake_card(row)
    return {"seen": seen, "new": new}


def _persist_item(item: ContentItem) -> dict | None:
    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable: %s", e)
        return None

    row = {
        "source_id": item.source_id,
        "source_type": item.source_type.value,
        "source_name": item.source_name,
        "source_url": item.source_url,
        "original_author": item.original_author,
        "platform": item.platform.value,
        "title": item.title,
        "description": item.description,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "project_tags": item.project_tags,
        "content_tags": item.content_tags,
        "permission_status": item.permission_status.value,
        "transcript_status": item.transcript_status.value,
        "summary_status": item.summary_status.value,
        "dashboard_status": item.dashboard_status.value,
        "citation_url": item.citation_url,
        "storage_path": item.storage_path,
        "embedding_status": item.embedding_status.value,
        "external_id": item.external_id,
        "duration_seconds": item.duration_seconds,
        "thumbnail_url": item.thumbnail_url,
        "raw_payload": item.raw_payload,
    }
    try:
        res = sb.table("content_items").upsert(row, on_conflict="source_url").execute()
    except Exception as e:
        log.warning("content_items upsert failed: %s", e)
        return None
    return res.data[0] if res.data else None


def _try_transcript(content_item: dict) -> None:
    result = fetch_transcript(content_item["source_url"])
    sb = get_supabase()
    if result.status in (TranscriptStatus.EXTRACTED,):
        sb.table("content_transcripts").insert(
            {
                "content_item_id": content_item["id"],
                "transcript_status": result.status.value,
                "transcript_text": result.text,
                "language": result.language,
                "source_kind": "youtube_captions",
            }
        ).execute()
    sb.table("content_items").update(
        {
            "transcript_status": result.status.value,
        }
    ).eq("id", content_item["id"]).execute()


def _chunk_and_embed(content_item: dict) -> None:
    sb = get_supabase()
    tr = (
        sb.table("content_transcripts")
        .select("transcript_text,language")
        .eq("content_item_id", content_item["id"])
        .limit(1)
        .execute()
        .data
        or []
    )
    text = (tr[0]["transcript_text"] if tr else None) or content_item.get("description") or ""
    if not text.strip():
        sb.table("content_items").update({"embedding_status": EmbeddingStatus.SKIPPED.value}).eq(
            "id", content_item["id"]
        ).execute()
        return

    chunks = chunk_text(text)
    rows = [
        {
            "content_item_id": content_item["id"],
            "chunk_index": i,
            "chunk_text": c.text,
            "token_count": c.token_count,
        }
        for i, c in enumerate(chunks)
    ]
    if rows:
        sb.table("content_chunks").upsert(rows, on_conflict="content_item_id,chunk_index").execute()
    status = write_embeddings_for_item(content_item["id"])
    sb.table("content_items").update({"embedding_status": status.value}).eq(
        "id", content_item["id"]
    ).execute()


def _persist_first_or_none(
    entries: list[ContentItem],
    project_tags: list[str] | None,
    source_row: dict | None,
) -> dict | None:
    if not entries:
        return None
    item = entries[0]
    if project_tags:
        item.project_tags = list(set([*item.project_tags, *project_tags]))
    if source_row:
        item.source_id = source_row["id"]
    row = _persist_item(item)
    if row:
        publish_intake_card(row)
    return row
