"""Embedding writer.

Batches `content_chunks` for a single content_item and writes results to
`content_embeddings`. Supports OpenAI and Voyage. Provider is chosen by the
first non-empty key in `config/.env`.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Iterable

from _shared import EmbeddingStatus, get_logger, get_supabase

log = get_logger("embedding_writer")


def _provider() -> tuple[str, str] | None:
    if os.environ.get("OPENAI_API_KEY"):
        return ("openai", os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small"))
    if os.environ.get("VOYAGE_API_KEY"):
        return ("voyage", os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3"))
    return None


def _embed_openai(texts: list[str], model: str) -> list[list[float]]:
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps({"input": texts, "model": model}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return [d["embedding"] for d in payload.get("data", [])]


def _embed_voyage(texts: list[str], model: str) -> list[list[float]]:
    req = urllib.request.Request(
        "https://api.voyageai.com/v1/embeddings",
        data=json.dumps({"input": texts, "model": model}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return [d["embedding"] for d in payload.get("data", [])]


def write_embeddings_for_item(content_item_id: str, *, batch_size: int = 32) -> EmbeddingStatus:
    prov = _provider()
    if not prov:
        log.warning("no embedding provider configured; skipping %s", content_item_id)
        return EmbeddingStatus.SKIPPED
    provider, model = prov

    try:
        sb = get_supabase()
    except RuntimeError as e:
        log.warning("supabase unavailable: %s", e)
        return EmbeddingStatus.FAILED

    chunks = (
        sb.table("content_chunks")
        .select("id, chunk_text")
        .eq("content_item_id", content_item_id)
        .order("chunk_index")
        .execute()
        .data
        or []
    )
    if not chunks:
        return EmbeddingStatus.SKIPPED

    # find already-embedded chunk ids to avoid duplicate writes
    chunk_ids = [c["id"] for c in chunks]
    existing = (
        sb.table("content_embeddings")
        .select("content_chunk_id")
        .in_("content_chunk_id", chunk_ids)
        .eq("provider", provider)
        .eq("model", model)
        .execute()
        .data
        or []
    )
    done = {row["content_chunk_id"] for row in existing}
    pending = [c for c in chunks if c["id"] not in done]
    if not pending:
        return EmbeddingStatus.WRITTEN

    rows_to_insert: list[dict] = []
    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        texts = [c["chunk_text"] for c in batch]
        try:
            if provider == "openai":
                vectors = _embed_openai(texts, model)
            else:
                vectors = _embed_voyage(texts, model)
        except Exception as e:
            log.warning("embedding batch failed for %s: %s", content_item_id, e)
            return EmbeddingStatus.FAILED

        for chunk, vec in zip(batch, vectors):
            rows_to_insert.append(
                {
                    "content_chunk_id": chunk["id"],
                    "embedding": vec,
                    "provider": provider,
                    "model": model,
                }
            )

    if rows_to_insert:
        sb.table("content_embeddings").insert(rows_to_insert).execute()
    return EmbeddingStatus.WRITTEN
