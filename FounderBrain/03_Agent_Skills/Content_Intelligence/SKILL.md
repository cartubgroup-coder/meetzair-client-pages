# FounderBrain Skill: Content Intelligence

> Reusable founder skill for collecting YouTube videos, podcast feeds, web articles,
> official market sources, and trading news into a searchable resource library, and
> for producing daily briefs and project-specific content angles for **TradeDonor**,
> **34Resets**, **MeetZair**, and **SilicaBASE**.

---

## 1. Purpose

Give the founder a single, compliant pipeline that turns daily incoming content
(videos, podcasts, articles, market data, news) into:

1. A searchable **Research Library** in Supabase.
2. A **Daily Market Brief** delivered at **06:30 America/New_York**.
3. **Project-tagged content angles** for each of the four ventures.
4. **Podcast prep packets** and **clip ideas** the founder can use the same day.
5. A **Founder Action Queue** of things only the founder can decide.

This skill is invoked when the founder says any of:

- "ingest this link"
- "add this channel to the watchlist"
- "give me today's brief"
- "build a podcast outline from these sources"
- "what's the trading angle on \<topic\>?"
- "summarize this video / article / feed"
- "/content-intelligence" (dashboard)

---

## 2. Hard rules (read before every run)

1. **Never download copyrighted YouTube video or audio by default.**
2. Use **YouTube RSS** and the **YouTube Data API** for discovery and metadata only.
3. Use **`youtube-transcript-api`** only when captions/transcripts are available.
   Failures must be logged, not retried into a download.
4. Store **links, metadata, summaries, citations, excerpts, generated notes, and
   embeddings** — not raw media — unless permission_status allows it.
5. Full media download is allowed **only when** `permission_status` is one of:
   - `owner_content`
   - `creative_commons`
   - `licensed`
   - `manual_review_required` after the founder explicitly approves
6. All files live under `C:\FounderBrain\`. Never write to Desktop or user home.
7. Every generated artifact must include a **citation_url** back to the source.

If any of these can't be satisfied, mark the item `blocked` and surface it on
the dashboard in **Founder Action Queue** with a one-line reason.

---

## 3. Inputs

| Input | Where it comes from |
|-------|--------------------|
| Manual URL  | Dashboard intake form, founder voice memo, paste-in |
| Watchlist   | `content_sources` rows where `auto_scan = true` |
| Schedule    | Cron at 06:25 ET (scan) and 06:30 ET (publish brief) |
| Search call | Tavily / Exa / GDELT query from a founder question |

---

## 4. Outputs

| Output | Destination |
|--------|-------------|
| Normalized content item | `content_items` row |
| Transcript (if available) | `content_transcripts` row |
| Chunks + embeddings | `content_chunks`, `content_embeddings` |
| Daily brief (Markdown + JSON) | `content_briefs` + `dashboard_brief_cards` |
| Founder action items | `content_tasks` (status = `awaiting_founder`) |
| Source health record | `source_health_checks` |
| Dashboard page | FounderDash `/content-intelligence` |

---

## 5. Source list (default, free or low cost first)

**Discovery / search**

- YouTube Data API v3 (channel and video metadata)
- YouTube channel RSS (`https://www.youtube.com/feeds/videos.xml?channel_id=...`)
- `youtube-transcript-api` (only when captions exist)
- Firecrawl free tier (web scrape + clean text)
- Tavily free tier (search)
- Exa free tier (semantic search)
- GDELT 2.0 DOC API (news + global events)

**Official / trusted feeds**

- Federal Reserve RSS (`https://www.federalreserve.gov/feeds/press_all.xml`)
- SEC RSS (filings, press, litigation)
- FRED API (macro time series)
- BLS API (labor + inflation)
- BEA API (GDP + national accounts)
- Podcast RSS feeds (per show)
- Listen Notes free plan **or** PodcastIndex (whichever has the show)

Every source must be registered in `content_sources` with a `permission_status`
and a `trust_tier` (`official`, `trusted`, `community`, `unknown`).

---

## 6. Pipeline (end to end)

```
URL or feed item
   │
   ▼
content_ingestor  ────►  source_normalizer
   │                          │
   │                          ▼
   │                    permission check (rules in §2)
   │                          │
   │                          ▼
   ├─► youtube_metadata_fetcher  (if YouTube)
   ├─► youtube_transcript_fetcher (if captions)
   ├─► rss_feed_ingestor          (if RSS)
   ├─► market_news_ingestor       (if Fed/SEC/GDELT/FRED/BLS/BEA)
   │
   ▼
content_chunker  ────►  embedding_writer
   │
   ▼
brief_generator (daily + on demand)
   │
   ▼
dashboard_publisher  ────►  /content-intelligence
```

Each stage writes a row, updates a status column, and emits a log line tagged
with the `content_item_id`. The dashboard reads status columns directly so the
founder can see exactly where each item is.

---

## 7. Status fields on every content item

```
source_type           e.g. youtube_video, podcast_episode, web_article, fed_rss, sec_rss, gdelt
source_name           Human readable channel/feed name
source_url            Canonical URL
original_author       Best-effort attribution
platform              youtube, web, podcast, fed, sec, gdelt, fred, bls, bea, etc.
title                 Item title
published_at          ISO 8601 from source
fetched_at            ISO 8601 from us
project_tags          subset of {tradedonor, 34resets, meetzair, silicabase}
content_tags          free-form, plus controlled vocab in config/content_tags.yml
permission_status     metadata_only | transcript_available | owner_content
                      | creative_commons | licensed | manual_review_required | blocked
transcript_status     none | unavailable | extracted | failed
summary_status        pending | generated | failed
dashboard_status      hidden | queued | published | archived
citation_url          Source URL used in any output
storage_path          Only set when full media is permitted; else NULL
embedding_status      pending | written | failed
```

---

## 8. Daily Market Brief (06:30 ET)

- Trigger: cron `25 6 * * *` (scan) then `30 6 * * *` (publish), tz `America/New_York`.
- Inputs (last 24h): Fed RSS, SEC RSS, GDELT topic queries, FRED releases,
  trusted YouTube/podcast watchlist items with transcripts, manual founder pins.
- Output:
  - `content_briefs` row with: headline, 5 bullets, 3 trading angles, 3 podcast
    angles, sources block (`[1]…[n]` with citation URLs).
  - One **dashboard_brief_cards** row per section.
- Format: see `daily-brief-template.md`.
- Failure mode: brief never blocks. If a source is down, list it under
  "Source Health" and continue.

---

## 9. Project tagging

When tagging a content item, prefer **explicit founder pins** over auto-tag.

Default heuristics:

- `tradedonor` — markets, charity, donor flows, philanthropy + finance overlap
- `34resets` — habits, performance reset frameworks, productivity science
- `meetzair` — networking, social discovery, founder/operator interviews
- `silicabase` — semiconductors, fabs, supply chain, materials, US re-shoring

Heuristic matches go in `project_tags` with a `tag_confidence` of `auto`.
Founder pins set `tag_confidence = founder` and override.

---

## 10. Dashboard (FounderDash → `/content-intelligence`)

Sections, in display order:

1. **Daily Market Brief** — today's brief + last 7 days.
2. **Podcast Prep Queue** — items tagged for an upcoming recording.
3. **Video Intake Queue** — YouTube items awaiting review.
4. **Source Watchlist** — channels/feeds with last-scan and health.
5. **Research Library** — searchable table: keyword, tag, source, date, project.
6. **Clip Ideas** — short outputs ready to post; each ties to a transcript span.
7. **Trading Angle Generator** — on-demand prompt; saves to `content_briefs`.
8. **Founder Action Queue** — items needing founder decision (permission,
   tagging conflicts, blocked downloads).
9. **Source Health** — per-source last_success_at, last_error, scan_latency.

See `source-registry-template.md` for the watchlist schema the founder fills in.

---

## 11. Verification (run before declaring "ready")

| # | Test | Expected |
|---|------|----------|
| 1 | Ingest a YouTube URL **with captions** | `transcript_status = extracted`, summary generated, dashboard card published |
| 2 | Ingest a YouTube URL **without captions** | `transcript_status = unavailable`, item still appears with metadata, no download attempted |
| 3 | Ingest a Fed RSS item | Item created, `permission_status = metadata_only`, trading angle generated |
| 4 | Ingest a SEC RSS item | Item created, citation_url points at SEC, item is searchable |
| 5 | Run a GDELT query | At least one item created with `source_type = gdelt` |
| 6 | Check dashboard | Cards appear in correct section, links resolve |
| 7 | Check Supabase | Rows in `content_items`, `content_briefs`, `dashboard_brief_cards` |
| 8 | Source down test | Disable a feed; pipeline continues; `source_health_checks` records the failure |
| 9 | Transcript failure | Force a transcript error; intake completes, item is `summary_status = failed`, dashboard shows it under Founder Action Queue |

Record results in `tests/test-report.md`.

---

## 12. When to ask the founder

Always ask before:

- Marking anything `licensed` or `owner_content` that wasn't already tagged that way.
- Posting a clip publicly.
- Adding a new auto-scan source.
- Spending against a paid tier of any API (Tavily, Exa, Listen Notes, etc.).

Use the **Founder Action Queue** for asks. Don't email, don't DM — queue it.

---

## 13. Companion files

- `content-intake-runbook.md` — step-by-step operational runbook
- `source-registry-template.md` — watchlist schema + starter rows
- `youtube-intake-policy.md` — captions / metadata / no-download policy
- `daily-brief-template.md` — output format for the 06:30 ET brief
- `founder-action-checklist.md` — what the founder reviews each day

---

## 14. Setup at a glance

See `content-intake-runbook.md` §1 for the full setup. Short version:

1. Copy this folder to `C:\FounderBrain\03_Agent_Skills\Content_Intelligence\`.
2. Copy `FounderBrain/app_modules/` to `C:\FounderBrain\app_modules\`.
3. Run the Supabase migration in `FounderBrain/supabase/migrations/`.
4. Fill `C:\FounderBrain\config\.env` with the API keys listed in the runbook.
5. Register starter sources via `source-registry-template.md`.
6. Run the verification checklist in §11.
7. Open the dashboard at `/content-intelligence`.
