---
type: Project Concept
title: Automation flow
description: An end-to-end path from a user command to GitHub Actions execution and a produced artifact.
resource: ../../CONTEXT.md
tags: [automation-flow, telegram, github-actions]
timestamp: 2026-06-27T00:00:00+09:00
---

# Automation Flow

An automation flow is one user intent or recurring job handled end to end.

In this repository, a flow usually starts with a Telegram command, passes through the Cloudflare Worker, dispatches a GitHub Actions workflow, and runs scripts or prompts that create an issue, report, document, or other output.

# Relationships

- Registered in the [flow registry](flow-registry.md).
- Implemented by [flow adapter files](flow-adapter-files.md).
- Documented for operators in `docs/<flow>-<action>.md`.

# Examples

- [idea-elaborate](../flows/idea-elaborate.md)
