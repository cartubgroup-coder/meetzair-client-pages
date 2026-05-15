"""Content chunker.

Targets ~500-token chunks with ~50-token overlap. The token counter uses a
naive whitespace heuristic when `tiktoken` is unavailable — good enough for
chunking, and the embedding provider is the canonical token count anyway.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from _shared import get_logger

log = get_logger("content_chunker")

DEFAULT_TARGET_TOKENS = 500
DEFAULT_OVERLAP_TOKENS = 50


@dataclass
class Chunk:
    text: str
    token_count: int
    start_seconds: int | None = None
    end_seconds: int | None = None


def _count_tokens(text: str) -> int:
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # whitespace-based fallback
        return max(1, len(text.split()))


def chunk_text(
    text: str,
    *,
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Split a plain text body into roughly token-sized chunks at paragraph boundaries when possible."""
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_tokens = 0

    for p in paragraphs:
        p_tokens = _count_tokens(p)
        if buf and buf_tokens + p_tokens > target_tokens:
            joined = "\n\n".join(buf)
            chunks.append(Chunk(text=joined, token_count=buf_tokens))
            # apply overlap by keeping the tail of the buffer
            if overlap_tokens > 0 and chunks[-1].token_count > overlap_tokens:
                tail = _tail(joined, overlap_tokens)
                buf = [tail]
                buf_tokens = _count_tokens(tail)
            else:
                buf = []
                buf_tokens = 0
        buf.append(p)
        buf_tokens += p_tokens

    if buf:
        joined = "\n\n".join(buf)
        chunks.append(Chunk(text=joined, token_count=buf_tokens))

    log.debug("chunk_text produced %d chunks", len(chunks))
    return chunks


def chunk_transcript_segments(
    segments: list[dict],
    *,
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Chunk youtube-transcript-api segments, preserving start/end timestamps."""
    chunks: list[Chunk] = []
    buf_text: list[str] = []
    buf_start: float | None = None
    buf_end: float = 0.0
    buf_tokens = 0

    for seg in segments:
        s_text = (seg.get("text") or "").strip()
        if not s_text:
            continue
        s_start = float(seg.get("start", 0.0))
        s_dur = float(seg.get("duration", 0.0))
        s_end = s_start + s_dur
        s_tokens = _count_tokens(s_text)

        if buf_text and buf_tokens + s_tokens > target_tokens:
            chunks.append(
                Chunk(
                    text=" ".join(buf_text),
                    token_count=buf_tokens,
                    start_seconds=int(buf_start) if buf_start is not None else None,
                    end_seconds=int(buf_end),
                )
            )
            if overlap_tokens > 0 and buf_tokens > overlap_tokens:
                tail = _tail(" ".join(buf_text), overlap_tokens)
                buf_text = [tail]
                buf_tokens = _count_tokens(tail)
                buf_start = buf_end
            else:
                buf_text = []
                buf_tokens = 0
                buf_start = None

        if not buf_text:
            buf_start = s_start
        buf_text.append(s_text)
        buf_tokens += s_tokens
        buf_end = s_end

    if buf_text:
        chunks.append(
            Chunk(
                text=" ".join(buf_text),
                token_count=buf_tokens,
                start_seconds=int(buf_start) if buf_start is not None else None,
                end_seconds=int(buf_end),
            )
        )
    log.debug("chunk_transcript_segments produced %d chunks", len(chunks))
    return chunks


def _tail(text: str, approx_tokens: int) -> str:
    """Return the last ~approx_tokens worth of text."""
    words = text.split()
    return " ".join(words[-approx_tokens:])
