"""Shared enums and dataclasses mirroring the Supabase schema.

Kept deliberately small. The DB is the source of truth; these types exist so
the Python pipeline can talk to itself without stringly-typed status fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    YOUTUBE_CHANNEL = "youtube_channel"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    YOUTUBE_VIDEO = "youtube_video"
    PODCAST_FEED = "podcast_feed"
    PODCAST_EPISODE = "podcast_episode"
    RSS = "rss"
    WEB_ARTICLE = "web_article"
    FED_RSS = "fed_rss"
    SEC_RSS = "sec_rss"
    GDELT_QUERY = "gdelt_query"
    FRED_SERIES = "fred_series"
    BLS_SERIES = "bls_series"
    BEA_SERIES = "bea_series"
    WEB_SEARCH = "web_search"
    MANUAL = "manual"


class Platform(str, Enum):
    YOUTUBE = "youtube"
    WEB = "web"
    PODCAST = "podcast"
    FED = "fed"
    SEC = "sec"
    GDELT = "gdelt"
    FRED = "fred"
    BLS = "bls"
    BEA = "bea"
    OTHER = "other"


class TrustTier(str, Enum):
    OFFICIAL = "official"
    TRUSTED = "trusted"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class PermissionStatus(str, Enum):
    METADATA_ONLY = "metadata_only"
    TRANSCRIPT_AVAILABLE = "transcript_available"
    OWNER_CONTENT = "owner_content"
    CREATIVE_COMMONS = "creative_commons"
    LICENSED = "licensed"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    BLOCKED = "blocked"


class TranscriptStatus(str, Enum):
    NONE = "none"
    UNAVAILABLE = "unavailable"
    EXTRACTED = "extracted"
    FAILED = "failed"


class SummaryStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"


class DashboardStatus(str, Enum):
    HIDDEN = "hidden"
    QUEUED = "queued"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EmbeddingStatus(str, Enum):
    PENDING = "pending"
    WRITTEN = "written"
    FAILED = "failed"
    SKIPPED = "skipped"


PROJECTS = ("tradedonor", "34resets", "meetzair", "silicabase")


# permission values that allow storing the full media file
DOWNLOAD_ALLOWED = frozenset(
    {
        PermissionStatus.OWNER_CONTENT,
        PermissionStatus.CREATIVE_COMMONS,
        PermissionStatus.LICENSED,
    }
)


@dataclass
class SourceRecord:
    id: Optional[str]
    source_type: SourceType
    source_name: str
    source_url: str
    platform: Platform
    trust_tier: TrustTier = TrustTier.UNKNOWN
    permission_status: PermissionStatus = PermissionStatus.METADATA_ONLY
    project_tags: list[str] = field(default_factory=list)
    auto_scan: bool = False
    scan_interval_minutes: int = 60
    enabled: bool = True


@dataclass
class ContentItem:
    source_type: SourceType
    source_name: str
    source_url: str
    platform: Platform
    title: str
    citation_url: str
    source_id: Optional[str] = None
    description: Optional[str] = None
    original_author: Optional[str] = None
    published_at: Optional[datetime] = None
    project_tags: list[str] = field(default_factory=list)
    content_tags: list[str] = field(default_factory=list)
    permission_status: PermissionStatus = PermissionStatus.METADATA_ONLY
    transcript_status: TranscriptStatus = TranscriptStatus.NONE
    summary_status: SummaryStatus = SummaryStatus.PENDING
    dashboard_status: DashboardStatus = DashboardStatus.QUEUED
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING
    external_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    storage_path: Optional[str] = None
    raw_payload: Optional[dict] = None
