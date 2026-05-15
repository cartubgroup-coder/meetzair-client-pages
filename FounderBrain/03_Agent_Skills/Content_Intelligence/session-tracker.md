# Live Session Tracker

| Status | Task | Files touched | Blockers | Next |
|--------|------|---------------|----------|------|
| ✅ done | Author SKILL.md | `FounderBrain/03_Agent_Skills/Content_Intelligence/SKILL.md` | — | — |
| ✅ done | Author runbook | `…/content-intake-runbook.md` | — | — |
| ✅ done | Author source registry template | `…/source-registry-template.md` | — | — |
| ✅ done | Author YouTube policy | `…/youtube-intake-policy.md` | — | — |
| ✅ done | Author daily brief template | `…/daily-brief-template.md` | — | — |
| ✅ done | Author founder action checklist | `…/founder-action-checklist.md` | — | — |
| ✅ done | Supabase migration | `FounderBrain/supabase/migrations/20260515_content_intelligence.sql` | — | apply on Lingo PC's Supabase project |
| ✅ done | App module: shared types + supabase client + logging | `FounderBrain/app_modules/_shared/*` | — | — |
| ✅ done | App module: source_normalizer | `FounderBrain/app_modules/source_normalizer/*` | — | — |
| ✅ done | App module: youtube_metadata_fetcher | `FounderBrain/app_modules/youtube_metadata_fetcher/*` | — | — |
| ✅ done | App module: youtube_transcript_fetcher | `FounderBrain/app_modules/youtube_transcript_fetcher/*` | — | — |
| ✅ done | App module: rss_feed_ingestor | `FounderBrain/app_modules/rss_feed_ingestor/*` | — | — |
| ✅ done | App module: market_news_ingestor | `FounderBrain/app_modules/market_news_ingestor/*` | — | — |
| ✅ done | App module: content_chunker | `FounderBrain/app_modules/content_chunker/*` | — | — |
| ✅ done | App module: embedding_writer | `FounderBrain/app_modules/embedding_writer/*` | — | — |
| ✅ done | App module: brief_generator | `FounderBrain/app_modules/brief_generator/*` | — | — |
| ✅ done | App module: dashboard_publisher | `FounderBrain/app_modules/dashboard_publisher/*` | — | — |
| ✅ done | App module: content_ingestor (orchestrator + CLI) | `FounderBrain/app_modules/content_ingestor/*` | — | — |
| ✅ done | Config: `.env.example`, `content_tags.yml`, `sources.starter.yml` | `FounderBrain/config/*` | — | — |
| ✅ done | Offline unit suite passing (11/11) | `FounderBrain/tests/test_unit.py` | — | — |
| ✅ done | Test report scaffold + live checklist | `FounderBrain/tests/test-report.md` | — | run live tests on Lingo PC |
| ✅ done | Dashboard page `/content-intelligence` | `content-intelligence/index.html` | — | wire `SUPABASE_URL`/`SUPABASE_ANON` on FounderDash deploy |
| ⬜ todo | Run live verification tests L1–L9 | — | needs Supabase project + API keys on the Lingo PC | follow SKILL.md §11 |
| ⬜ todo | Schedule cron at 06:25 / 06:30 ET | — | needs scheduler on Lingo PC | use Windows Task Scheduler or n8n |
| ⬜ todo | Wire Supabase edge functions for `ingest_url` + `generate_trading_angle` | — | needs Supabase project | mirrors the Python CLIs |

**Blockers right now:** none on the offline side. The remaining items all
depend on the founder's Lingo PC environment (Supabase project, API keys,
scheduler) — they're not blockers on this repo.

**Next actions on Lingo PC:**

1. Copy `FounderBrain/` from this repo to `C:\FounderBrain\`.
2. Apply `supabase/migrations/20260515_content_intelligence.sql`.
3. Fill `config/.env` from `.env.example`.
4. `pip install -r FounderBrain/app_modules/requirements.txt`.
5. `python -m content_ingestor.run --watchlist` to validate L3–L5.
6. `python -m brief_generator.run --kind daily_market_brief` to validate L6–L7.
7. Update `tests/test-report.md` with results and `content_item_id`s.
