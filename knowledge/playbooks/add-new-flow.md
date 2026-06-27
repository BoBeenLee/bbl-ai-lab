---
type: Playbook
title: Add a new automation flow
description: Steps for adding a new Telegram to GitHub Actions automation flow while keeping docs and OKF concepts aligned.
resource: ../../README.md
tags: [playbook, automation-flow, okf]
timestamp: 2026-06-27T00:00:00+09:00
---

# Add a New Flow

Use this playbook when adding a new [automation flow](../concepts/automation-flow.md).

# Steps

1. Register the flow in `worker/src/flows.ts`.
2. Add the adapter files named by the registry entry:
   - `.github/workflows/<flow>-<action>.yml`
   - `scripts/<flow>-<action>.sh`
   - `scripts/prompts/<flow>-<action>.md`
   - `docs/<flow>-<action>.md`
3. Add `knowledge/flows/<flow>-<action>.md` with OKF frontmatter.
4. Update the registered flow table in `README.md`.
5. Add or update project language in `CONTEXT.md` if the flow introduces a load-bearing term.
6. Run the required verification:
   - `cd worker && npm run typecheck`
   - `bash -n scripts/<flow>-<action>.sh`

# OKF Requirements

Every `knowledge/**/*.md` concept document must start with YAML frontmatter and include `type`.

Recommended fields are `title`, `description`, `resource`, `tags`, and `timestamp`.
