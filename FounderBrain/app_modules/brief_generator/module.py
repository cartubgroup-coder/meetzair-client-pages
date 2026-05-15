"""Brief generator: daily market brief, trading angles, podcast outlines.

The LLM call is isolated to `_llm_complete`. If no LLM provider is configured,
the generator falls back to a structured, citation-only brief that lists items
without paraphrase — never invents content.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Iterable

from _shared import get_logger, get_supabase

log = get_logger("brief_generator")

DEFAULT_TIMEZONE = os.environ.get("BRIEF_TIMEZONE", "America/New_York")


def _llm_complete(prompt: str, *, system: str = "", max_tokens: int = 800) -> str | None:
    """Call Anthropic Messages API. Returns None if no key is set."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    body = {
        "model": os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        "max_tokens": max_tokens,
        "system": system or "You are FounderBrain's content brief writer. Cite every claim.",
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log.warning("LLM call failed: %s", e)
        return None
    blocks = payload.get("content") or []
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text") or None


def _recent_items(hours: int = 24, limit: int = 50) -> list[dict]:
    sb = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    return (
        sb.table("content_items")
        .select("id,title,citation_url,source_name,platform,project_tags,published_at,description,permission_status")
        .gte("published_at", cutoff)
        .neq("permission_status", "blocked")
        .order("published_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )


def _format_sources_block(items: list[dict]) -> tuple[str, list[dict]]:
    sources = []
    lines = []
    for i, it in enumerate(items, start=1):
        sources.append(
            {
                "ref": i,
                "content_item_id": it["id"],
                "title": it["title"],
                "url": it["citation_url"],
            }
        )
        lines.append(f"[{i}] {it['title']} — {it['citation_url']}")
    return "\n".join(lines), sources


def generate_daily_brief() -> dict:
    """Produce a daily_market_brief row and return it."""
    items = _recent_items(hours=24, limit=50)
    sources_block, sources = _format_sources_block(items)
    n_items = len(items)
    today = datetime.now(timezone.utc).astimezone().strftime("%A, %B %-d, %Y")

    if not items:
        markdown = (
            f"# FounderBrain Daily Brief — {today}\n\n"
            "No new items in the last 24h.\n\n"
            "## Sources\n(none)\n"
        )
        body_json = {
            "kind": "daily_market_brief",
            "headline": "No new items in the last 24h",
            "bullets": [],
            "trading_angles": [],
            "podcast_angles": [],
            "sources": [],
            "stats": {"items_reviewed": 0},
        }
        return _write_brief("daily_market_brief", markdown, body_json, source_count=0)

    item_lines = "\n".join(
        f"- [{i+1}] {it['title']} ({it['source_name']}, {it.get('published_at','?')}) {it['citation_url']}"
        for i, it in enumerate(items)
    )
    prompt = (
        "You are writing the FounderBrain Daily Market Brief.\n"
        "Produce concise Markdown following this exact structure:\n"
        "1) headline (one line),\n"
        "2) one short context paragraph,\n"
        "3) five bullets, each citing one or more source numbers like [1],\n"
        "4) up to two trading angles (TradeDonor, SilicaBASE) with why-now and risk,\n"
        "5) up to two podcast angles (MeetZair, 34Resets),\n"
        "6) a 'Founder action queue' with at most 3 items,\n"
        "7) a 'Sources' block re-listing every [n] used.\n\n"
        "Strict rules: every bullet must cite at least one [n]; do not invent facts; "
        "if you can't cite something, drop it. Keep total under 600 words.\n\n"
        f"Today: {today}\n"
        f"Sources available ({n_items}):\n{item_lines}\n"
    )
    text = _llm_complete(prompt) or _fallback_markdown(today, items, sources_block)

    body_json = {
        "kind": "daily_market_brief",
        "headline": _first_heading(text) or "Daily Market Brief",
        "summary": None,
        "bullets": [],
        "trading_angles": [],
        "podcast_angles": [],
        "sources": sources,
        "stats": {"items_reviewed": n_items},
    }
    return _write_brief("daily_market_brief", text, body_json, source_count=n_items)


def generate_trading_angle(topic: str) -> dict:
    sb = get_supabase()
    items = (
        sb.table("content_items")
        .select("id,title,citation_url,source_name,project_tags")
        .or_("title.ilike.%" + topic + "%,description.ilike.%" + topic + "%")
        .limit(20)
        .execute()
        .data
        or []
    )
    sources_block, sources = _format_sources_block(items)
    prompt = (
        f"Topic: {topic}\n"
        "Write a trading angle for FounderBrain. Required sections: Angle, Why now, "
        "Risk, Confidence, Sources. Cite every claim with [n]. If the available "
        "sources are insufficient, say so plainly.\n\n"
        f"Sources:\n{sources_block}\n"
    )
    text = _llm_complete(prompt, max_tokens=600) or (
        f"# Trading angle — {topic}\n\nInsufficient sources to write a grounded angle.\n\n"
        f"## Sources\n{sources_block or '(none)'}\n"
    )
    body_json = {
        "kind": "trading_angle",
        "headline": f"Trading angle: {topic}",
        "sources": sources,
        "stats": {"items_reviewed": len(items)},
    }
    return _write_brief("trading_angle", text, body_json, source_count=len(items))


def generate_podcast_outline(content_item_ids: list[str]) -> dict:
    sb = get_supabase()
    if not content_item_ids:
        return {"error": "no items selected"}
    items = (
        sb.table("content_items")
        .select("id,title,citation_url,source_name,project_tags")
        .in_("id", content_item_ids)
        .execute()
        .data
        or []
    )
    sources_block, sources = _format_sources_block(items)
    prompt = (
        "Write a podcast outline. Structure: Hook, Three segments (each with talking "
        "points and citations), Guest pitch (if applicable), Closing CTA. Cite every "
        "claim with [n] back to the Sources block.\n\n"
        f"Sources:\n{sources_block}\n"
    )
    text = _llm_complete(prompt, max_tokens=900) or (
        f"# Podcast outline\n\nLLM unavailable. Selected sources:\n{sources_block}\n"
    )
    body_json = {
        "kind": "podcast_outline",
        "headline": "Podcast outline",
        "sources": sources,
        "stats": {"items_reviewed": len(items)},
    }
    return _write_brief("podcast_outline", text, body_json, source_count=len(items))


def _fallback_markdown(today: str, items: list[dict], sources_block: str) -> str:
    bullets = "\n".join(
        f"- {it['title']} [{i+1}]" for i, it in enumerate(items[:5])
    )
    return (
        f"# FounderBrain Daily Brief — {today}\n\n"
        f"> LLM unavailable. Citation-only listing of {len(items)} items.\n\n"
        f"## Items in window\n{bullets}\n\n"
        f"## Sources\n{sources_block}\n"
    )


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    return None


def _write_brief(kind: str, markdown: str, body_json: dict, *, source_count: int) -> dict:
    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable, returning brief without persistence: %s", e)
        return {"kind": kind, "body_markdown": markdown, "body_json": body_json}

    row = {
        "kind": kind,
        "headline": body_json.get("headline"),
        "summary": body_json.get("summary"),
        "body_markdown": markdown,
        "body_json": body_json,
        "source_count": source_count,
    }
    inserted = sb.table("content_briefs").insert(row).execute()
    return inserted.data[0] if inserted.data else row
