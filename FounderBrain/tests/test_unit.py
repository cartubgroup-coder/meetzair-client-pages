"""Offline unit tests that exercise pure-Python behavior (no network, no DB).

Run with:  python -m pytest FounderBrain/tests/test_unit.py -q

These tests are intentionally small. The full verification checklist (SKILL.md
§11) requires a live environment and is recorded in test-report.md.
"""
from __future__ import annotations

import sys
import os

# Make the app_modules importable when this file is run directly
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "app_modules")
)

from source_normalizer.module import normalize_url, classify_url, youtube_video_id
from _shared.types import SourceType, Platform


def test_normalize_url_strips_trackers():
    raw = "https://example.com/foo/?utm_source=twitter&id=42&utm_medium=cpc"
    assert normalize_url(raw) == "https://example.com/foo?id=42"


def test_normalize_url_lowercases_host_and_forces_https():
    raw = "http://YouTube.com/watch?v=abc"
    assert normalize_url(raw) == "https://youtube.com/watch?v=abc"


def test_classify_url_youtube_video():
    st, plat = classify_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert st == SourceType.YOUTUBE_VIDEO
    assert plat == Platform.YOUTUBE


def test_classify_url_youtu_be_shortlink():
    st, plat = classify_url("https://youtu.be/dQw4w9WgXcQ")
    assert st == SourceType.YOUTUBE_VIDEO
    assert plat == Platform.YOUTUBE


def test_classify_url_fed_rss():
    st, plat = classify_url("https://www.federalreserve.gov/feeds/press_all.xml")
    assert st == SourceType.FED_RSS
    assert plat == Platform.FED


def test_classify_url_sec():
    st, plat = classify_url(
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&output=atom"
    )
    assert st == SourceType.SEC_RSS
    assert plat == Platform.SEC


def test_youtube_video_id_watch():
    assert youtube_video_id("https://www.youtube.com/watch?v=abc12345678") == "abc12345678"


def test_youtube_video_id_shortlink():
    assert youtube_video_id("https://youtu.be/abc12345678") == "abc12345678"


def test_youtube_video_id_none_for_unrelated():
    assert youtube_video_id("https://example.com/page") is None


def test_chunker_returns_chunks():
    from content_chunker.module import chunk_text
    text = "para one.\n\npara two.\n\n" + ("word " * 1200)
    chunks = chunk_text(text, target_tokens=200, overlap_tokens=20)
    assert len(chunks) >= 2
    assert all(c.token_count > 0 for c in chunks)


def test_chunker_empty():
    from content_chunker.module import chunk_text
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []
