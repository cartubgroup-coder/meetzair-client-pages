# Content Intake Runbook

Operational runbook for the Content Intelligence skill. The audience is the
founder and any operator following this skill on the Lingo PC.

All paths assume **`C:\FounderBrain\`** as the root.

---

## 1. One-time setup

### 1.1 Directory layout

```
C:\FounderBrain\
├── 03_Agent_Skills\
│   └── Content_Intelligence\         ← this skill
├── app_modules\
│   ├── content_ingestor\
│   ├── youtube_metadata_fetcher\
│   ├── youtube_transcript_fetcher\
│   ├── rss_feed_ingestor\
│   ├── market_news_ingestor\
│   ├── source_normalizer\
│   ├── content_chunker\
│   ├── embedding_writer\
│   ├── brief_generator\
│   └── dashboard_publisher\
├── supabase\
│   └── migrations\
│       └── 2026xxxx_content_intelligence.sql
├── config\
│   ├── .env                          ← never commit
│   ├── sources.starter.yml
│   └── content_tags.yml
├── logs\
└── tests\
    └── test-report.md
```

### 1.2 Required API keys (write into `config\.env`)

```
# YouTube
YOUTUBE_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# Embeddings (choose one provider per environment)
OPENAI_API_KEY=
# or
VOYAGE_API_KEY=

# Search / scrape
TAVILY_API_KEY=
EXA_API_KEY=
FIRECRAWL_API_KEY=

# Market / macro
FRED_API_KEY=
BLS_API_KEY=
BEA_API_KEY=

# Podcasts (optional, pick what you actually use)
LISTEN_NOTES_API_KEY=
PODCAST_INDEX_KEY=
PODCAST_INDEX_SECRET=

# News
GDELT_BASE_URL=https://api.gdeltproject.org/api/v2/doc/doc

# Briefs
BRIEF_TIMEZONE=America/New_York
BRIEF_PUBLISH_LOCAL_TIME=06:30
```

Keys not in use can stay blank — modules must no-op gracefully when their key
is missing and report it under **Source Health**.

### 1.3 Supabase migration

Run `FounderBrain\supabase\migrations\2026xxxx_content_intelligence.sql` against
the FounderDash Supabase project. Verify with:

```
select count(*) from content_sources;
select count(*) from content_items;
```

### 1.4 Seed sources

Edit `config\sources.starter.yml` (or use the dashboard intake form) to load
the starter watchlist:

- Federal Reserve press RSS
- SEC press / filings RSS
- 2–3 YouTube channels per project
- 2–3 podcast feeds per project
- 1 GDELT macro query
- 1 FRED indicator (e.g. `DGS10`)

See `source-registry-template.md` for the exact fields.

---

## 2. Daily flow (automated)

| Time (ET) | What runs | Module |
|-----------|-----------|--------|
| 06:25 | Watchlist scan | `rss_feed_ingestor`, `market_news_ingestor`, `youtube_metadata_fetcher` |
| 06:26 | Transcript pass | `youtube_transcript_fetcher` |
| 06:27 | Chunk + embed | `content_chunker`, `embedding_writer` |
| 06:28 | Generate brief | `brief_generator` |
| 06:30 | Publish to dashboard | `dashboard_publisher` |
| Hourly | Source health | `source_normalizer` heartbeat |

A run is **successful** if at least one item is ingested or every source is
recorded in `source_health_checks`. A run that finds nothing new is fine —
the brief still publishes with "No new items in the last 24h" and the previous
day's pinned highlights.

---

## 3. Manual flows

### 3.1 Single URL intake (from dashboard)

1. Founder pastes a URL into **Video Intake Queue** or **Research Library → Add**.
2. Frontend POSTs to `dashboard_publisher` which writes to `content_tasks`
   with `kind = manual_intake`.
3. `content_ingestor` picks up the task, resolves the URL via
   `source_normalizer`, dispatches to the right fetcher.
4. Founder sees the item appear with `dashboard_status = queued`; once
   chunked + embedded it flips to `published`.

### 3.2 Add a channel/feed to the watchlist

1. Founder fills `source-registry-template.md` fields in the dashboard form.
2. Row is inserted into `content_sources` with `auto_scan = true` and a
   `trust_tier`.
3. Next 06:25 scan picks it up.

### 3.3 Build a podcast outline

1. Founder selects N library items, clicks **Generate podcast outline**.
2. `brief_generator` runs in `podcast_outline` mode against the selected
   `content_chunks`, returns a structured outline + citations.
3. Output saved to `content_briefs` with `kind = podcast_outline`.

### 3.4 Trading angle on demand

1. Founder types a topic in **Trading Angle Generator**.
2. `brief_generator` runs `trading_angle` mode, pulling from official + trusted
   sources only (`trust_tier in ('official','trusted')`).
3. Output cites every claim. No claim without a citation.

---

## 4. Failure modes and how to recover

| Symptom | Likely cause | Action |
|--------|--------------|--------|
| Transcript pass empty | Captions disabled on the video | Item stays at `transcript_status = unavailable`; no retry, no download |
| YouTube API 403 | Quota exhausted | Modules switch to RSS-only mode; reset at 00:00 PT |
| Fed/SEC RSS 5xx | Upstream outage | Source marked `unhealthy`; retried next hour |
| Supabase write fails | Network / RLS | Item written to `logs\dead_letter\` as JSON for replay |
| Embedding provider 429 | Rate limit | Chunks remain `embedding_status = pending`; next run retries |

The pipeline is designed so **no single failure stops intake**. If you see the
whole pipeline halt, check `logs\fatal.log` — it's almost always a bad
`config\.env`.

---

## 5. Verification checklist (run after setup and after any module change)

Use the table in `SKILL.md` §11. Save results to `tests\test-report.md` with
timestamps and the `content_item_id` for each test. The skill is not "ready"
until tests 1–9 pass.

---

## 6. Cost control

- Tavily, Exa, Firecrawl, Listen Notes — start on free tiers.
- Embeddings — batch chunks (recommend ≥ 32 per request).
- Brief generation — one LLM call per brief, not per source.
- YouTube Data API — discovery via RSS first, hit the API only for metadata
  on items we actually keep.

If projected monthly spend crosses **$25**, the dashboard surfaces a card in
**Founder Action Queue** asking for an explicit approval to continue.

---

## 7. Compliance reminders

Re-read `youtube-intake-policy.md` whenever you add a new source type.
Default is **metadata only**. Anything else needs a row in `content_sources`
with `permission_status` set to one of the allowed values and a note in
`permission_notes` explaining why.
