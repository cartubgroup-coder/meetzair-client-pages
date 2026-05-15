"""YouTube transcript fetcher.

Uses `youtube-transcript-api` and ONLY public captions. If no captions exist
this module returns `unavailable` — it does not attempt to generate captions
from audio. See `03_Agent_Skills/Content_Intelligence/youtube-intake-policy.md`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from _shared import TranscriptStatus, get_logger
from source_normalizer.module import youtube_video_id

log = get_logger("youtube_transcript_fetcher")


@dataclass
class TranscriptResult:
    status: TranscriptStatus
    text: Optional[str] = None
    language: Optional[str] = None
    error: Optional[str] = None
    segments: Optional[list[dict]] = None  # raw [{text,start,duration}, ...]


def fetch_transcript(url_or_id: str, *, languages: tuple[str, ...] = ("en",)) -> TranscriptResult:
    video_id = url_or_id if len(url_or_id) == 11 else youtube_video_id(url_or_id)
    if not video_id:
        return TranscriptResult(
            status=TranscriptStatus.FAILED, error="could not parse video id"
        )

    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        from youtube_transcript_api._errors import (  # type: ignore
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )
    except ImportError:
        return TranscriptResult(
            status=TranscriptStatus.FAILED,
            error="youtube-transcript-api not installed",
        )

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=list(languages))
    except TranscriptsDisabled:
        return TranscriptResult(status=TranscriptStatus.UNAVAILABLE, error="captions disabled")
    except NoTranscriptFound:
        return TranscriptResult(status=TranscriptStatus.UNAVAILABLE, error="no transcript found")
    except VideoUnavailable:
        return TranscriptResult(status=TranscriptStatus.UNAVAILABLE, error="video unavailable")
    except Exception as e:  # network, region block, etc.
        log.warning("transcript fetch failed for %s: %s", video_id, e)
        return TranscriptResult(status=TranscriptStatus.FAILED, error=str(e))

    text = "\n".join(seg.get("text", "") for seg in transcript).strip()
    if not text:
        return TranscriptResult(status=TranscriptStatus.UNAVAILABLE, error="empty transcript")

    return TranscriptResult(
        status=TranscriptStatus.EXTRACTED,
        text=text,
        language=languages[0] if languages else None,
        segments=transcript,
    )
