# FounderBrain app modules

Python modules that implement the Content Intelligence pipeline. Each module
is a small, single-responsibility package with the same shape:

```
app_modules/<module_name>/
├── __init__.py        # public API
├── module.py          # implementation
└── README.md          # what it does and how to invoke it
```

Modules are intentionally thin. They are orchestrated by `content_ingestor`,
which is the only module that talks to the dashboard and the cron scheduler.

## Module map

| Module | Responsibility |
|--------|----------------|
| `content_ingestor` | Entry point. Resolves URLs, dispatches to fetchers, writes `content_items`. |
| `youtube_metadata_fetcher` | YouTube Data API + channel RSS. Metadata only. |
| `youtube_transcript_fetcher` | `youtube-transcript-api`. Captions only, no ASR. |
| `rss_feed_ingestor` | Generic RSS / Atom feed reader. |
| `market_news_ingestor` | Fed, SEC, GDELT, FRED, BLS, BEA. |
| `source_normalizer` | URL canonicalization, dedupe, source registry lookup. |
| `content_chunker` | Splits transcripts/articles into ~500-token chunks. |
| `embedding_writer` | Batches chunks and writes to `content_embeddings`. |
| `brief_generator` | Daily brief + on-demand trading/podcast outputs. |
| `dashboard_publisher` | Writes `dashboard_brief_cards`, surfaces tasks. |

## Required env

See `FounderBrain\config\.env`. Modules must fail soft when keys are missing
and write a `source_health_checks` row marking themselves degraded.

## Running locally

```bash
python -m content_ingestor.run --url "https://www.youtube.com/watch?v=..."
python -m brief_generator.run --kind daily_market_brief
```

## Tests

See `FounderBrain/tests/`. The verification checklist in `SKILL.md` §11 is
the contract.
