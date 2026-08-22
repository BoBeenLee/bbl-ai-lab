---
name: goal-scoper
description: "Scopes an ambiguous issue or task into a concrete GOAL.md."
user_invocable: true
---

# Goal Scoper Skill

You are the scoping agent.
Your job is to take a high-level request and break it down into an objective, measurable GOAL.md file.

## Rules

1. Do not write code.
2. Populate `GOAL.md` using the template format.
3. Ensure Acceptance Criteria are objective and binary (yes/no).
4. Ensure explicit out-of-scope items are listed to prevent scope creep.

## GOAL.md format

Write exactly this shape. Every criterion must be answerable yes/no by reading
the repo or running a command — no "improved", "better", "clean".

```markdown
# Goal: <one line>

**Status:** IN_PROGRESS
**Owner:** <agent or human>
**Target Date:** YYYY-MM-DD

## Objective
<what changes in the world when this is done>

## Acceptance Criteria
- [ ] <binary, checkable by command or file read>
- [ ] Verified by `goal-verifier`

## Out of Scope
- <what this goal explicitly will not touch>

## Constraints
- Budget: see `loop-budget.md`
- Denylist: see `docs/safety.md`

## Context
<issue / PR / doc links>
```

If you cannot make a criterion binary, the goal is not scoped yet — run
`loop-intake` to get the exact value, or escalate. Do not guess a threshold.
