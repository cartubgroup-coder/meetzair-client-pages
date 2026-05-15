-- Content Intelligence schema for FounderBrain
-- Apply against the FounderDash Supabase project.
-- All tables are idempotent (IF NOT EXISTS) so re-running is safe.

-- ---------- extensions ----------
create extension if not exists "pgcrypto";
create extension if not exists "vector";

-- ---------- enums ----------
do $$ begin
  create type source_type_t as enum (
    'youtube_channel','youtube_playlist','youtube_video',
    'podcast_feed','podcast_episode',
    'rss','web_article',
    'fed_rss','sec_rss','gdelt_query',
    'fred_series','bls_series','bea_series',
    'web_search','manual'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type platform_t as enum (
    'youtube','web','podcast','fed','sec','gdelt','fred','bls','bea','other'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type trust_tier_t as enum ('official','trusted','community','unknown');
exception when duplicate_object then null; end $$;

do $$ begin
  create type permission_status_t as enum (
    'metadata_only','transcript_available','owner_content',
    'creative_commons','licensed','manual_review_required','blocked'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type transcript_status_t as enum ('none','unavailable','extracted','failed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type summary_status_t as enum ('pending','generated','failed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type dashboard_status_t as enum ('hidden','queued','published','archived');
exception when duplicate_object then null; end $$;

do $$ begin
  create type embedding_status_t as enum ('pending','written','failed','skipped');
exception when duplicate_object then null; end $$;

do $$ begin
  create type brief_kind_t as enum (
    'daily_market_brief','trading_angle','podcast_outline','weekly_recap'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type task_kind_t as enum (
    'manual_intake','permission_review','tagging_conflict',
    'takedown_request','skill_tuning','cost_alert'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type task_status_t as enum (
    'awaiting_founder','in_progress','done','cancelled'
  );
exception when duplicate_object then null; end $$;

do $$ begin
  create type source_health_t as enum ('healthy','degraded','unhealthy','disabled');
exception when duplicate_object then null; end $$;

-- ---------- tables ----------

create table if not exists content_sources (
  id                     uuid primary key default gen_random_uuid(),
  source_type            source_type_t not null,
  source_name            text not null,
  source_url             text not null,
  source_external_id     text,
  platform               platform_t not null,
  original_author        text,
  trust_tier             trust_tier_t not null default 'unknown',
  permission_status      permission_status_t not null default 'metadata_only',
  permission_notes       text,
  permission_ack_at      timestamptz,
  project_tags           text[] not null default '{}',
  content_tags           text[] not null default '{}',
  auto_scan              boolean not null default false,
  scan_interval_minutes  int not null default 60,
  enabled                boolean not null default true,
  last_scanned_at        timestamptz,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

create unique index if not exists content_sources_url_uniq
  on content_sources (source_url);

create table if not exists content_items (
  id                  uuid primary key default gen_random_uuid(),
  source_id           uuid references content_sources(id) on delete set null,
  source_type         source_type_t not null,
  source_name         text not null,
  source_url          text not null,
  original_author     text,
  platform            platform_t not null,
  title               text not null,
  description         text,
  published_at        timestamptz,
  fetched_at          timestamptz not null default now(),
  project_tags        text[] not null default '{}',
  content_tags        text[] not null default '{}',
  tag_confidence      text not null default 'auto',
  permission_status   permission_status_t not null default 'metadata_only',
  transcript_status   transcript_status_t not null default 'none',
  summary_status      summary_status_t not null default 'pending',
  dashboard_status    dashboard_status_t not null default 'queued',
  citation_url        text not null,
  storage_path        text,
  embedding_status    embedding_status_t not null default 'pending',
  external_id         text,
  duration_seconds    int,
  thumbnail_url       text,
  raw_payload         jsonb,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create unique index if not exists content_items_source_url_uniq
  on content_items (source_url);
create index if not exists content_items_published_at_idx
  on content_items (published_at desc);
create index if not exists content_items_project_tags_idx
  on content_items using gin (project_tags);
create index if not exists content_items_content_tags_idx
  on content_items using gin (content_tags);

create table if not exists content_transcripts (
  id                 uuid primary key default gen_random_uuid(),
  content_item_id    uuid not null references content_items(id) on delete cascade,
  transcript_status  transcript_status_t not null default 'extracted',
  transcript_text    text,
  transcript_error   text,
  language           text,
  source_kind        text,            -- 'youtube_captions' | 'podcast_show_notes' | etc.
  duration_seconds   int,
  created_at         timestamptz not null default now()
);

create index if not exists content_transcripts_item_idx
  on content_transcripts (content_item_id);

create table if not exists content_chunks (
  id                 uuid primary key default gen_random_uuid(),
  content_item_id    uuid not null references content_items(id) on delete cascade,
  chunk_index        int not null,
  chunk_text         text not null,
  start_seconds      int,
  end_seconds        int,
  token_count        int,
  created_at         timestamptz not null default now(),
  unique (content_item_id, chunk_index)
);

create index if not exists content_chunks_item_idx
  on content_chunks (content_item_id);

create table if not exists content_embeddings (
  id                 uuid primary key default gen_random_uuid(),
  content_chunk_id   uuid not null references content_chunks(id) on delete cascade,
  embedding          vector(1536),
  provider           text not null,
  model              text not null,
  created_at         timestamptz not null default now(),
  unique (content_chunk_id, provider, model)
);

-- ivfflat index; tune lists to ~sqrt(rowcount). Start at 100.
create index if not exists content_embeddings_vec_idx
  on content_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create table if not exists content_briefs (
  id              uuid primary key default gen_random_uuid(),
  kind            brief_kind_t not null,
  brief_date      date not null default (now() at time zone 'America/New_York')::date,
  timezone        text not null default 'America/New_York',
  headline        text,
  summary         text,
  body_markdown   text,
  body_json       jsonb not null,
  source_count    int not null default 0,
  created_at      timestamptz not null default now()
);

create index if not exists content_briefs_kind_date_idx
  on content_briefs (kind, brief_date desc);

create table if not exists content_tasks (
  id                uuid primary key default gen_random_uuid(),
  kind              task_kind_t not null,
  status            task_status_t not null default 'awaiting_founder',
  content_item_id   uuid references content_items(id) on delete set null,
  source_id         uuid references content_sources(id) on delete set null,
  title             text not null,
  detail            text,
  payload           jsonb,
  created_at        timestamptz not null default now(),
  resolved_at       timestamptz,
  resolution_note   text
);

create index if not exists content_tasks_status_idx
  on content_tasks (status, created_at desc);

create table if not exists source_health_checks (
  id              uuid primary key default gen_random_uuid(),
  source_id       uuid not null references content_sources(id) on delete cascade,
  checked_at      timestamptz not null default now(),
  status          source_health_t not null,
  latency_ms      int,
  items_found     int,
  http_status     int,
  last_error      text
);

create index if not exists source_health_source_idx
  on source_health_checks (source_id, checked_at desc);

create table if not exists dashboard_brief_cards (
  id              uuid primary key default gen_random_uuid(),
  section         text not null,        -- 'daily_market_brief', 'podcast_prep_queue', etc.
  title           text not null,
  body_markdown   text,
  body_json       jsonb,
  brief_id        uuid references content_briefs(id) on delete cascade,
  content_item_id uuid references content_items(id) on delete set null,
  project_tags    text[] not null default '{}',
  sort_order      int not null default 0,
  visible         boolean not null default true,
  created_at      timestamptz not null default now()
);

create index if not exists dashboard_brief_cards_section_idx
  on dashboard_brief_cards (section, sort_order);

-- ---------- updated_at triggers ----------
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists trg_content_sources_updated_at on content_sources;
create trigger trg_content_sources_updated_at
  before update on content_sources
  for each row execute function set_updated_at();

drop trigger if exists trg_content_items_updated_at on content_items;
create trigger trg_content_items_updated_at
  before update on content_items
  for each row execute function set_updated_at();

-- ---------- RLS scaffolding ----------
-- Enable RLS but leave policies to the FounderDash app layer to define;
-- the service role used by the ingestor bypasses RLS.
alter table content_sources         enable row level security;
alter table content_items           enable row level security;
alter table content_transcripts     enable row level security;
alter table content_chunks          enable row level security;
alter table content_embeddings      enable row level security;
alter table content_briefs          enable row level security;
alter table content_tasks           enable row level security;
alter table source_health_checks    enable row level security;
alter table dashboard_brief_cards   enable row level security;
