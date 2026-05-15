# Content Intelligence — Test Report

Run this checklist after every change to a module or migration. Save results
here with the timestamp and the `content_item_id` so we can audit any regression.

---

## Offline unit suite (always green before push)

| # | Test | Result | Notes |
|---|------|--------|-------|
| U1 | `tests/test_unit.py::test_normalize_url_strips_trackers` | ✅ pass | offline |
| U2 | `tests/test_unit.py::test_normalize_url_lowercases_host_and_forces_https` | ✅ pass | offline |
| U3 | `tests/test_unit.py::test_classify_url_youtube_video` | ✅ pass | offline |
| U4 | `tests/test_unit.py::test_classify_url_youtu_be_shortlink` | ✅ pass | offline |
| U5 | `tests/test_unit.py::test_classify_url_fed_rss` | ✅ pass | offline |
| U6 | `tests/test_unit.py::test_classify_url_sec` | ✅ pass | offline |
| U7 | `tests/test_unit.py::test_youtube_video_id_watch` | ✅ pass | offline |
| U8 | `tests/test_unit.py::test_youtube_video_id_shortlink` | ✅ pass | offline |
| U9 | `tests/test_unit.py::test_youtube_video_id_none_for_unrelated` | ✅ pass | offline |
| U10 | `tests/test_unit.py::test_chunker_returns_chunks` | ✅ pass | offline |
| U11 | `tests/test_unit.py::test_chunker_empty` | ✅ pass | offline |

Latest offline run: `2026-05-15` — **11 / 11 passed** on `python 3.11.15`.

---

## Live verification (SKILL.md §11)

These require the Supabase project, API keys, and the cron scheduler.
Record each `content_item_id` so we can re-read it from the dashboard.

| # | Test | Expected | Status | content_item_id | Notes |
|---|------|---------|--------|-----------------|-------|
| L1 | YouTube URL **with captions** | `transcript_status = extracted`; brief card created | ⬜ pending | | |
| L2 | YouTube URL **without captions** | `transcript_status = unavailable`; no download attempted | ⬜ pending | | |
| L3 | One Fed RSS item | item created with `citation_url` pointing at federalreserve.gov | ⬜ pending | | |
| L4 | One SEC RSS item | item created with `citation_url` pointing at sec.gov | ⬜ pending | | |
| L5 | One GDELT query | ≥1 item with `source_type = gdelt_query` | ⬜ pending | | |
| L6 | Dashboard cards | cards visible in correct sections | ⬜ pending | n/a | |
| L7 | Supabase rows | rows in `content_items`, `content_briefs`, `dashboard_brief_cards` | ⬜ pending | n/a | |
| L8 | Source down test | `source_health_checks` row written; pipeline keeps going | ⬜ pending | n/a | |
| L9 | Forced transcript failure | item still created; appears under Founder Action Queue | ⬜ pending | | |

---

## How to run

```
# Offline (always)
python -m pytest FounderBrain/tests/test_unit.py -q

# Single-URL live test
python -m content_ingestor.run --url "<youtube url with captions>"

# Watchlist scan
python -m content_ingestor.run --watchlist

# Daily brief
python -m brief_generator.run --kind daily_market_brief
```

After each live test, fill in the row above, commit the file, and link the
`content_item_id` to the dashboard in the PR description.
