# Daily Brief Template

Output format the `brief_generator` produces every morning at **06:30
America/New_York**. The template is also used (with different inputs) for
on-demand trading angles and podcast outlines.

The brief is written to `content_briefs` and rendered on
`/content-intelligence` → **Daily Market Brief**.

---

## 1. Markdown template

```markdown
# FounderBrain Daily Brief — {{date_long}}

> Window: last 24h. Sources: {{n_official}} official, {{n_trusted}} trusted,
> {{n_community}} community. Items reviewed: {{n_items}}.

## Top of the day

**{{headline}}**

{{one_paragraph_context_with_inline_citations}}

## Five things that moved

1. {{bullet_1}} [{{ref_1}}]
2. {{bullet_2}} [{{ref_2}}]
3. {{bullet_3}} [{{ref_3}}]
4. {{bullet_4}} [{{ref_4}}]
5. {{bullet_5}} [{{ref_5}}]

## Trading angles

### TradeDonor
- **Angle:** {{td_angle}}
- **Why now:** {{td_why_now}} [{{td_ref}}]
- **Risk:** {{td_risk}}

### SilicaBASE
- **Angle:** {{sb_angle}}
- **Why now:** {{sb_why_now}} [{{sb_ref}}]
- **Risk:** {{sb_risk}}

## Podcast angles

### MeetZair
- **Hook:** {{mz_hook}}
- **Guest pitch:** {{mz_guest}}
- **Source:** [{{mz_ref}}]

### 34Resets
- **Hook:** {{rs_hook}}
- **Reset frame:** {{rs_frame}}
- **Source:** [{{rs_ref}}]

## Founder action queue
- {{action_1}}
- {{action_2}}
- {{action_3}}

## Sources
[1] {{source_1_title}} — {{source_1_url}}
[2] {{source_2_title}} — {{source_2_url}}
...
```

Every bracketed `[n]` token in the body **must** resolve to a row in the
**Sources** block, which **must** have a working URL.

---

## 2. JSON shape (stored alongside the Markdown)

```json
{
  "brief_id": "uuid",
  "kind": "daily_market_brief",
  "date": "2026-05-15",
  "timezone": "America/New_York",
  "headline": "string",
  "summary": "one-paragraph string",
  "bullets": [
    { "text": "...", "source_id": "uuid", "citation_url": "https://..." }
  ],
  "trading_angles": [
    {
      "project": "tradedonor",
      "angle": "...",
      "why_now": "...",
      "risk": "...",
      "citations": ["https://...", "..."]
    }
  ],
  "podcast_angles": [
    {
      "project": "meetzair",
      "hook": "...",
      "guest_pitch": "...",
      "citations": ["https://..."]
    }
  ],
  "actions": [
    { "text": "...", "owner": "founder", "due": "today" }
  ],
  "sources": [
    {
      "ref": 1,
      "content_item_id": "uuid",
      "title": "...",
      "url": "https://...",
      "trust_tier": "official"
    }
  ],
  "stats": {
    "items_reviewed": 0,
    "official": 0,
    "trusted": 0,
    "community": 0,
    "skipped_blocked": 0,
    "skipped_no_transcript": 0
  }
}
```

---

## 3. Generation rules

1. **Recency filter.** Only items with `published_at` within the last 24h,
   unless the founder pinned an older item.
2. **Trust weighting.** Each bullet must include at least one `official` or
   `trusted` source. `community` items can support but not be the sole source.
3. **Project coverage.** Try for at least one angle per project. If a project
   has no relevant items, leave its section out rather than fabricate.
4. **Citation discipline.** No claim without a citation. If you can't cite
   it, drop it.
5. **Length.** The Markdown body should be under ~600 words. Brevity is the
   point.
6. **Failure mode.** If the generator has fewer than 3 usable items, it still
   publishes a brief that says so — and lists the missing sources under
   **Source Health** on the dashboard.

---

## 4. Variants

| Kind | Trigger | Input scope |
|------|---------|------------|
| `daily_market_brief` | Cron 06:30 ET | Last 24h, all enabled sources |
| `trading_angle` | Founder asks a topic question | Official + trusted only |
| `podcast_outline` | Founder selects N library items | Selected items only |
| `weekly_recap` | Cron Sat 09:00 ET | Last 7 days, top items by usage |

All variants share the **same JSON shape** with `kind` set accordingly. This
keeps the dashboard renderer simple.
