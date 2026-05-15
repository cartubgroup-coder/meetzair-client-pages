# Source Registry Template

This is the schema and starter set for the **Source Watchlist**. Every source
the system scans automatically must appear in `content_sources` with the
fields below. Use this file as the canonical template — the dashboard form
mirrors the same fields.

---

## Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source_type` | enum | yes | `youtube_channel`, `youtube_playlist`, `podcast_feed`, `rss`, `fed_rss`, `sec_rss`, `gdelt_query`, `fred_series`, `bls_series`, `bea_series`, `web_search`, `manual` |
| `source_name` | text | yes | Human readable name |
| `source_url` | text | yes | Canonical URL or feed URL |
| `source_external_id` | text | when applicable | YouTube channel ID, FRED series ID, etc. |
| `platform` | enum | yes | `youtube`, `web`, `podcast`, `fed`, `sec`, `gdelt`, `fred`, `bls`, `bea`, `other` |
| `original_author` | text | optional | Owner / host name |
| `trust_tier` | enum | yes | `official`, `trusted`, `community`, `unknown` |
| `permission_status` | enum | yes | `metadata_only`, `transcript_available`, `owner_content`, `creative_commons`, `licensed`, `manual_review_required`, `blocked` |
| `permission_notes` | text | when non-default | Why this status, who approved |
| `project_tags` | text[] | yes | Subset of `{tradedonor, 34resets, meetzair, silicabase}` |
| `content_tags` | text[] | optional | Free-form, plus controlled vocab in `config/content_tags.yml` |
| `auto_scan` | boolean | yes | `true` to include in the 06:25 ET scan |
| `scan_interval_minutes` | int | yes | Default `60` for RSS, `360` for YouTube channels |
| `enabled` | boolean | yes | Soft disable without deleting |

---

## Starter rows

The below are suggested defaults. Edit project_tags as needed.

### Official / market

```yaml
- source_type: fed_rss
  source_name: Federal Reserve — All Press Releases
  source_url: https://www.federalreserve.gov/feeds/press_all.xml
  platform: fed
  trust_tier: official
  permission_status: metadata_only
  project_tags: [tradedonor]
  auto_scan: true
  scan_interval_minutes: 60
  enabled: true

- source_type: sec_rss
  source_name: SEC — Press Releases
  source_url: https://www.sec.gov/news/pressreleases.rss
  platform: sec
  trust_tier: official
  permission_status: metadata_only
  project_tags: [tradedonor]
  auto_scan: true
  scan_interval_minutes: 60
  enabled: true

- source_type: sec_rss
  source_name: SEC — Latest Filings (8-K)
  source_url: https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&output=atom
  platform: sec
  trust_tier: official
  permission_status: metadata_only
  project_tags: [tradedonor]
  auto_scan: true
  scan_interval_minutes: 60
  enabled: true

- source_type: fred_series
  source_name: 10-Year Treasury Constant Maturity Rate
  source_url: https://api.stlouisfed.org/fred/series/observations?series_id=DGS10
  source_external_id: DGS10
  platform: fred
  trust_tier: official
  permission_status: metadata_only
  project_tags: [tradedonor]
  auto_scan: true
  scan_interval_minutes: 360
  enabled: true

- source_type: gdelt_query
  source_name: GDELT — Global macro (last 24h)
  source_url: https://api.gdeltproject.org/api/v2/doc/doc?query=(monetary%20OR%20inflation%20OR%20yield%20OR%20FOMC)&mode=ArtList&timespan=24h&format=json
  platform: gdelt
  trust_tier: trusted
  permission_status: metadata_only
  project_tags: [tradedonor]
  auto_scan: true
  scan_interval_minutes: 180
  enabled: true
```

### YouTube (RSS-first; replace placeholders with real channel IDs)

```yaml
- source_type: youtube_channel
  source_name: <fill in trader channel>
  source_url: https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>
  source_external_id: <CHANNEL_ID>
  platform: youtube
  trust_tier: community
  permission_status: metadata_only
  project_tags: [tradedonor]
  auto_scan: true
  scan_interval_minutes: 360
  enabled: true

- source_type: youtube_channel
  source_name: <fill in habits / productivity channel>
  source_url: https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>
  source_external_id: <CHANNEL_ID>
  platform: youtube
  trust_tier: community
  permission_status: metadata_only
  project_tags: [34resets]
  auto_scan: true
  scan_interval_minutes: 360
  enabled: true

- source_type: youtube_channel
  source_name: <fill in founders / networking channel>
  source_url: https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>
  source_external_id: <CHANNEL_ID>
  platform: youtube
  trust_tier: community
  permission_status: metadata_only
  project_tags: [meetzair]
  auto_scan: true
  scan_interval_minutes: 360
  enabled: true

- source_type: youtube_channel
  source_name: <fill in semis / fabs channel>
  source_url: https://www.youtube.com/feeds/videos.xml?channel_id=<CHANNEL_ID>
  source_external_id: <CHANNEL_ID>
  platform: youtube
  trust_tier: community
  permission_status: metadata_only
  project_tags: [silicabase]
  auto_scan: true
  scan_interval_minutes: 360
  enabled: true
```

### Podcasts (RSS only; do not store audio unless permission allows)

```yaml
- source_type: podcast_feed
  source_name: <show name>
  source_url: <podcast RSS URL>
  platform: podcast
  trust_tier: community
  permission_status: metadata_only
  project_tags: [meetzair]
  auto_scan: true
  scan_interval_minutes: 360
  enabled: true
```

---

## How to add a source

1. Open `/content-intelligence` → **Source Watchlist** → **Add source**.
2. Fill the form (mirrors the fields above).
3. Submit. The row is written to `content_sources`.
4. Wait until the next scan (or click **Scan now** on that row).
5. Confirm an item appears in **Video Intake Queue** or **Research Library**.

---

## How to disable a source

Set `enabled = false`. The source stays in the table (and your history stays
intact) but no future scan touches it. To re-enable, flip it back to `true`.

---

## How to re-tier a source

If a source publishes consistently strong primary information, raise its
`trust_tier` from `community` → `trusted`. Briefs weight `trusted` and
`official` more heavily, so this directly changes what makes it to the 06:30
brief.
