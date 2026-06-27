---
type: Automation Flow
title: idea-elaborate
description: Converts short Telegram idea or todo messages into elaborated GitHub Issues using Gemini.
resource: ../../docs/idea-elaborate.md
tags: [idea, telegram, github-actions, gemini]
timestamp: 2026-06-27T00:00:00+09:00
---

# idea-elaborate

`idea-elaborate` turns a short Telegram `/idea` or `/todo` message into a structured GitHub Issue.

# Trigger

| Input | Routing |
|-------|---------|
| `/idea <body>` | Dispatches the idea flow |
| `/todo <body>` | Alias for the idea flow |

The current repository dispatch event type is `idea-submitted`, which is an allowed legacy event type.

# Data Flow

```text
Telegram message
  -> Cloudflare Worker
  -> worker/src/flows.ts route
  -> GitHub repository_dispatch
  -> .github/workflows/idea-elaborate.yml
  -> scripts/idea-elaborate.sh
  -> scripts/prompts/idea-elaborate.md + skills/product-brainstorming.SKILL.md
  -> GitHub Issue
  -> Telegram reply
```

# Adapter Files

| Role | Path |
|------|------|
| Workflow | `.github/workflows/idea-elaborate.yml` |
| Runtime script | `scripts/idea-elaborate.sh` |
| Prompt | `scripts/prompts/idea-elaborate.md` |
| Operator docs | `docs/idea-elaborate.md` |
| Registry entry | `worker/src/flows.ts` |

# Verification

- Run `cd worker && npm run typecheck` after registry or adapter path changes.
- Run `bash -n scripts/idea-elaborate.sh` after shell script changes.
- Use the GitHub Actions manual dispatch or Telegram E2E path for runtime verification.
