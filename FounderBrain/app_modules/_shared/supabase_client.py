"""Thin Supabase client wrapper.

The actual `supabase` Python SDK is an optional dependency. This module
isolates the import so the rest of the pipeline can be unit-tested without it.
"""
from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_supabase():
    """Return a configured supabase-py client.

    Raises a clear error if env vars are missing; modules should catch and
    record a `degraded` health check rather than crash the run.
    """
    try:
        from supabase import create_client  # type: ignore
    except ImportError as e:  # pragma: no cover - import-time guard
        raise RuntimeError(
            "supabase-py is not installed. Add 'supabase' to requirements."
        ) from e

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in config/.env"
        )
    return create_client(url, key)
