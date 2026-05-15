# Founder Action Checklist

Daily, weekly, and ad-hoc decisions only the founder can make. The dashboard
surfaces these in **Founder Action Queue**; this file is the canonical list
of what the founder is expected to review and how long it should take.

---

## Daily (≤ 10 minutes, after the 06:30 brief)

- [ ] Open `/content-intelligence` → **Daily Market Brief**.
- [ ] Skim the 5 bullets. Pin any you want carried into tomorrow's brief.
- [ ] Open **Trading Angles**. Mark each:
  - **Use** → moves to TradeDonor / SilicaBASE working doc.
  - **Park** → keeps it in library, not in brief tomorrow.
  - **Kill** → archives the item, won't surface again.
- [ ] Open **Podcast Prep Queue**. If recording today, click
      **Generate podcast outline** for selected items.
- [ ] Open **Founder Action Queue**. Resolve each row:
  - Permission asks (approve / deny `permission_status` upgrades).
  - Tagging conflicts (auto-tag vs. founder pin).
  - Blocked items (decide: license, drop, or leave blocked).
- [ ] Glance at **Source Health**. If any source is unhealthy > 24h, click
      **Investigate** or **Disable**.

---

## Weekly (≤ 20 minutes, Saturday morning)

- [ ] Read the `weekly_recap` brief.
- [ ] Open **Source Watchlist**. For each `community` source:
  - Promote to `trusted` if consistently strong.
  - Disable if noisy.
- [ ] Review API cost card under Source Health. If projected monthly spend
      is above $25, decide what to throttle.
- [ ] Spot-check 3 random Research Library items: do the citations resolve?
      Is the transcript text accurate? File any defects to `content_tasks`.

---

## Ad-hoc

- [ ] **New source request.** Add via Source Watchlist → Add source. Fill
      `permission_status` honestly. If unsure, default to `metadata_only`.
- [ ] **Take-down request.** Set `enabled = false`, archive related items,
      schedule transcript deletion (handled by the policy).
- [ ] **Owner content upload.** Mark `permission_status = owner_content`
      and acknowledge the rights confirmation. Only then is full media
      stored.
- [ ] **Public clip.** Never publish without a final founder review. The
      dashboard's "Publish clip" button requires a confirm dialog by design.

---

## Things that should never reach this queue

If any of these show up, treat it as a bug and file it:

- Items without a citation URL.
- Auto-promoted permission upgrades (only the founder can promote).
- A scheduled brief that ran but didn't publish a card.
- A source flagged `unhealthy` with no `last_error` text.

---

## How long this should take

Daily: target 7 minutes, ceiling 10. If you're spending more than 10 minutes
on the queue most days, the auto-tagger or trust tiers need adjustment —
file a task with `kind = skill_tuning` and link the offending items.
