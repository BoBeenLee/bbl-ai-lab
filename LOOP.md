# Loop Configuration — Minimal Triage (Claude Code)

## Active Loops

| Pattern | Cadence | Status | Command |
|---------|---------|--------|---------|
| Daily Triage | 1d | L1 report-only | `/loop 1d Run $loop-triage` |

## Skills

Run order within one loop pass:

| Order | Skill | Role |
|-------|-------|------|
| 1 | `loop-constraints` | Read `loop-constraints.md`; rules are binding |
| 2 | `loop-budget` | Check spend against `loop-budget.md`; exit early if over |
| 3 | `loop-intake` | Only if the item is too vague to verify "done" |
| 4 | `loop-triage` | Produce findings; write to `STATE.md` |
| 5 | `loop-budget` | Record spend at end of run |

Goal-shaped work (a single objective rather than a queue) uses `goal-scoper` to
write `GOAL.md`, then `goal-verifier` or the `loop-verifier` agent to decide done.
The implementer never marks its own work complete.

## Human Gates

- No auto-fix until L2 checklist complete
- All high-risk paths: human review required (see [docs/safety.md](docs/safety.md) denylist)

## Worktrees

- Use `isolation: worktree` when spawning implementer sub-agents (L2+).
- One worktree per fix attempt; discard after verifier REJECT.

## Connectors (MCP)

- MCP optional for L1 report-only loops.
- For L2+: GitHub MCP to read CI/issues; scope connectors to read + comment only until trusted.

## Budget

- Max sub-agent spawns per run: 0 (L1)
- Review STATE.md daily

## Links

- Pattern: [daily-triage](https://github.com/cobusgreyling/loop-engineering/blob/main/patterns/daily-triage.md)
- Checklist: [loop-design-checklist](https://github.com/cobusgreyling/loop-engineering/blob/main/docs/loop-design-checklist.md)