---
type: Project Concept
title: Autonomous loop
description: A scheduled agent execution unit configured by LOOP.md, distinct from the Telegram-triggered automation flows this hub owns.
resource: ../../LOOP.md
tags: [loop, state-spine, readiness-level, daily-triage]
timestamp: 2026-08-22T00:00:00+09:00
---

# Autonomous Loop

An autonomous loop runs on a schedule instead of on a human turn. An automation
flow starts when someone sends a Telegram command; a loop starts because its
cadence came due. Both produce artifacts, but only the loop decides on its own
that now is the time.

The engine is Claude Code's `/loop`. This repository adds only the parts `/loop`
does not carry: what the loop is allowed to do, what it remembers, and when it
must stop.

# Files

| File | Role |
|------|------|
| `LOOP.md` | Single manifest of which loops run, at what cadence, at what readiness level |
| `STATE.md` | Loop state spine — read at the start of every run, written at the end |
| `loop-constraints.md` | Binding rules, read by the `loop-constraints` skill before any action |
| `docs/safety.md` | Denylist paths, auto-merge allowlist, MCP scope, escalation triggers |
| `loop-budget.md` | Daily run and token caps, kill switch |
| `loop-run-log.md` | Append-only run history |

# Skills

`loop-intake` sharpens a vague work item into a verifiable goal before anything
acts on it. `goal-scoper` turns a request into a `GOAL.md` with binary acceptance
criteria. `loop-triage` produces the findings report. `goal-verifier` and the
`loop-verifier` agent decide whether a goal is done — the implementer never marks
its own work complete. `loop-budget` checks spend at both ends of a run.

# Readiness

The daily triage loop is L1: report-only, zero sub-agent spawns, no auto-merge
path. Raising it to L2 means the verifier gates every change and implementers run
in `isolation: worktree`. Do not raise the level while `loop-run-log.md` is empty.

# Boundary

- A loop never edits its own trigger (`.github/workflows/**`) or the flow manifest (`worker/src/flows.ts`).
- A loop escalates by writing to `STATE.md` High Priority, not by opening an issue.
- Loop scaffolding lives at the repo root and in `.claude/`; it is not an automation flow and takes no `worker/src/flows.ts` entry.
