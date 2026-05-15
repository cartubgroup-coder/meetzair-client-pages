"""Dashboard publisher.

Writes `dashboard_brief_cards` rows the FounderDash UI renders directly, and
also surfaces `content_tasks` for the Founder Action Queue.
"""
from __future__ import annotations

from typing import Iterable

from _shared import get_logger, get_supabase

log = get_logger("dashboard_publisher")


def publish_brief_cards(brief: dict) -> int:
    """Given a brief row, fan out one or more dashboard cards."""
    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable: %s", e)
        return 0

    section_for_kind = {
        "daily_market_brief": "daily_market_brief",
        "trading_angle": "trading_angle_generator",
        "podcast_outline": "podcast_prep_queue",
        "weekly_recap": "daily_market_brief",
    }
    section = section_for_kind.get(brief.get("kind"), "daily_market_brief")

    card = {
        "section": section,
        "title": brief.get("headline") or brief.get("kind"),
        "body_markdown": brief.get("body_markdown"),
        "body_json": brief.get("body_json"),
        "brief_id": brief.get("id"),
        "project_tags": _projects_from_json(brief.get("body_json") or {}),
        "sort_order": 0,
        "visible": True,
    }
    sb.table("dashboard_brief_cards").insert(card).execute()
    return 1


def publish_intake_card(content_item: dict, section: str = "video_intake_queue") -> None:
    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable: %s", e)
        return
    card = {
        "section": section,
        "title": content_item.get("title") or content_item.get("source_url"),
        "body_markdown": None,
        "body_json": {
            "url": content_item.get("citation_url"),
            "source_name": content_item.get("source_name"),
            "transcript_status": content_item.get("transcript_status"),
            "permission_status": content_item.get("permission_status"),
        },
        "content_item_id": content_item.get("id"),
        "project_tags": content_item.get("project_tags") or [],
        "sort_order": 0,
        "visible": True,
    }
    sb.table("dashboard_brief_cards").insert(card).execute()


def record_source_health(
    source_id: str,
    *,
    status: str,
    latency_ms: int | None = None,
    items_found: int | None = None,
    http_status: int | None = None,
    last_error: str | None = None,
) -> None:
    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable: %s", e)
        return
    sb.table("source_health_checks").insert(
        {
            "source_id": source_id,
            "status": status,
            "latency_ms": latency_ms,
            "items_found": items_found,
            "http_status": http_status,
            "last_error": last_error,
        }
    ).execute()


def _projects_from_json(body_json: dict) -> list[str]:
    angles = body_json.get("trading_angles") or []
    pods = body_json.get("podcast_angles") or []
    return list({a.get("project") for a in angles + pods if a.get("project")})
