# Loop Safety — bbl-ai-lab

Denylist and scope rules for autonomous loops in this repository.
`loop-constraints` reads `loop-constraints.md`; this file is the reference it and
`LOOP.md` point at. Rules here are binding on every loop run.

## Never edit without human approval

These paths break the hub or leak credentials when an agent guesses:

| Path | Why |
|------|-----|
| `.env`, `.env.*`, `.dev.vars` | Secrets. Never read, edit, or echo. |
| `worker/wrangler.toml` | Must stay secret-free; secrets go through `wrangler secret put`. |
| `worker/src/flows.ts` | Single flow manifest. A wrong edit silently breaks Telegram routing. |
| `.github/workflows/**` | Dispatch surface. A loop editing its own trigger is a runaway. |
| `ops/repos.md`, `.gitignore` | Operator repo manifest pair; must change together. `projects/` entries are written by `ops/repo-sync.sh`, not by hand. |
| `skills-lock.json`, `.agents/skills/**` | Managed by the external skills installer, not by hand. |
| `hermes-workspace/`, `ops/remote-comfyui/`, `ops/openhuman-altalt-proxy/` | Untracked operator repo clones. Owned by their own repos. |
| `.claude/worktrees/**` | Other sessions' worktrees. Never delete. |

## Never do

- Push to `main`, or auto-merge any PR. Draft PR first, human marks ready.
- Squash or rebase merge. This repo uses regular merge only.
- Close an issue or PR.
- Commit untracked files the loop did not create. Stage intentionally.
- Disable or skip a test to make CI green.

## Auto-merge allowlist

Empty. No path is auto-mergeable at L1. Revisit only after the daily triage loop
has run report-only for two weeks with a clean `loop-run-log.md`.

## MCP and tool scope

L1 daily triage is read-only: it needs repo reads and `gh` reads. It does not
need write scopes, and it does not need the ComfyUI, Notion, Jira, Confluence, or
Works connectors. Grant write scopes per loop, never globally.

## Verification a loop must run before proposing a change

```bash
cd worker && npm run typecheck
```

```bash
bash -n scripts/<changed-script>.sh
```

```bash
bash ops/repo-sync.sh --list
```

## Escalation

Stop and hand back to a human when any of these is true:

- A work item is not specific enough to verify "done" after one `loop-intake` pass.
- Three fix attempts on one item have failed.
- A change would touch any denylist path above.
- Token spend hit 80% of the daily cap in `loop-budget.md`.

Escalate by writing the item under **High Priority** in `STATE.md` and marking it
`needs-human`. Do not act on a guess.
