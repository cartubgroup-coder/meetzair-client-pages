# FounderBrain — Content Intelligence (in this repo)

This folder is the **synced copy** of `C:\FounderBrain\` on the Lingo PC, scoped
to the Content Intelligence skill. The shape mirrors the local path exactly so
you can `robocopy` (or rsync) this folder onto the Lingo PC without renaming.

## Layout

```
FounderBrain/
├── 03_Agent_Skills/
│   └── Content_Intelligence/        ← the skill: SKILL.md, runbook, templates, policy
├── app_modules/                     ← python pipeline modules
├── supabase/migrations/             ← schema (apply once)
├── config/                          ← .env.example, sources, controlled vocab
└── tests/                           ← offline unit suite + live verification report
```

## Start here

1. Read **`03_Agent_Skills/Content_Intelligence/SKILL.md`** — that's the spec.
2. Follow **`03_Agent_Skills/Content_Intelligence/content-intake-runbook.md`**
   for setup, daily flow, manual flows, and failure recovery.
3. Run **`python -m pytest tests/test_unit.py -q`** to confirm the offline
   suite is green before doing anything on the Lingo PC.
4. The founder dashboard lives at **`/content-intelligence`** (see
   `../content-intelligence/index.html`).

## Compliance

`youtube-intake-policy.md` is binding. Default is **metadata only**. Anything
else needs an explicit `permission_status` upgrade and a row in
`permission_notes`. The four allowed full-media statuses are `owner_content`,
`creative_commons`, `licensed`, and `manual_review_required` (after founder
approval).

## Status

See `03_Agent_Skills/Content_Intelligence/session-tracker.md` for the live
task list, blockers, and next actions.
