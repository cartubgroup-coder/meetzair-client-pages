# YouTube Intake Policy

This policy is **binding** on every module in this skill. If a module cannot
satisfy it, the module must mark the item `permission_status = blocked` and
push it to the **Founder Action Queue** instead of proceeding.

---

## 1. What we may store, by default

For any YouTube URL the founder ingests, default storage is **metadata only**:

- video ID, channel ID, channel name
- title, description, published_at
- duration, view_count, like_count (snapshot)
- thumbnail URL (link, not file)
- the source URL itself

That's it. No video file, no audio file, no extracted MP3.

---

## 2. Transcripts

We use the **`youtube-transcript-api`** library (or equivalent) to pull
captions when, and only when, captions are publicly available on the video.

Rules:

1. If captions are **available**, store the transcript text in
   `content_transcripts.transcript_text` with `transcript_status = extracted`.
2. If captions are **unavailable, disabled, or behind an age/region wall**,
   set `transcript_status = unavailable`. Do **not** attempt to generate
   captions by downloading audio + running ASR.
3. If extraction errors out for any other reason, set
   `transcript_status = failed`, capture the error in `transcript_error`, and
   continue the pipeline.

We never circumvent caption restrictions, account walls, or paid content.

---

## 3. Full media — when allowed

A full video or audio download is only allowed when **all** of the following
are true:

- The item's `permission_status` is one of:
  `owner_content`, `creative_commons`, `licensed`, `manual_review_required`
  (the last requires explicit founder approval logged in `permission_notes`).
- The source's `trust_tier` is consistent with that status (e.g.
  `owner_content` requires that the channel is the founder's own).
- The founder has acknowledged a one-time "I confirm I have rights" prompt
  for this `source_id` (recorded in `content_sources.permission_ack_at`).

If any of those is false, the request to download is **denied**, the item
is marked `blocked`, and a row is added to `content_tasks` with
`kind = permission_review`.

---

## 4. Discovery vs. ingestion

| Action | Allowed via |
|--------|-------------|
| Find new videos on a channel | YouTube channel RSS first; Data API only if RSS missing fields |
| Fetch a video's metadata | YouTube Data API `videos.list` |
| Fetch captions | `youtube-transcript-api` |
| Search YouTube broadly | YouTube Data API `search.list` (counts against quota) |
| Download media | **Not allowed by default.** See §3. |

---

## 5. Quota and rate limits

- Default Data API quota is 10,000 units/day. Discovery via RSS keeps us under
  ~200 units/day.
- Cache `videos.list` responses for 24h. Re-fetch only when an item enters the
  brief or the founder explicitly refreshes it.
- On a 403 quota error, the module switches to RSS-only mode and posts a
  one-line note to **Source Health**. Reset is at 00:00 PT.

---

## 6. Attribution

Every dashboard card, brief bullet, or generated clip idea that draws from a
YouTube source must include:

- Channel name
- Video title
- Link back to the canonical YouTube URL
- For transcript-derived claims: timestamp range, e.g. `[12:03–12:48]`

If we can't attribute, we don't publish.

---

## 7. Removal requests

If a channel owner asks for removal:

1. Set `enabled = false` on their `content_sources` row.
2. Set `dashboard_status = archived` on all related `content_items`.
3. Hard-delete any stored transcript and chunks within 7 days
   (`content_transcripts`, `content_chunks`, `content_embeddings`).
4. Log the request in `content_tasks` with `kind = takedown_request`.

---

## 8. Things we explicitly will not do

- We will not download Spotify, Apple Podcasts, or paywalled audio.
- We will not bypass age gates, region locks, or paid memberships.
- We will not re-host or republish the source media.
- We will not use ASR on third-party audio we don't have rights to.
- We will not scrape comments at scale (one-off founder reads are fine).
