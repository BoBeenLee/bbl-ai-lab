---
type: Project Concept
title: Flow registry
description: The single manifest for Telegram commands, repository dispatch event types, and flow adapter paths.
resource: ../../worker/src/flows.ts
tags: [flow-registry, worker, manifest]
timestamp: 2026-06-27T00:00:00+09:00
---

# Flow Registry

The flow registry is `worker/src/flows.ts`.

It is the single manifest for Telegram commands, subcommands, `repository_dispatch` event types, usage and acknowledgement text, and the adapter files that implement each automation flow.

# Rules

- Start every new [automation flow](automation-flow.md) in the registry.
- Keep new `eventType` values equal to `<flow>-<action>` unless preserving an explicit legacy event.
- Keep adapter file paths in the registry aligned with files on disk.
- Run `cd worker && npm run typecheck` after registry changes.

# Consumers

- `worker/src/index.ts` uses the registry to route Telegram webhook messages.
- `worker/scripts/check-flows.mjs` verifies manifest drift against workflow triggers and file existence.
