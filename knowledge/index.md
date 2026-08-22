---
type: Knowledge Bundle Index
title: bbl-ai-lab Knowledge Bundle
description: OKF bundle for the automation flow hub, optimized for agent traversal and cross-document linking.
resource: ../README.md
tags: [okf, automation-flow-hub, agents]
timestamp: 2026-06-27T00:00:00+09:00
---

# bbl-ai-lab Knowledge Bundle

This directory is the Open Knowledge Format bundle for `bbl-ai-lab`.

`README.md` remains the human-facing operating guide. This bundle is the agent-friendly knowledge layer: each concept is a Markdown file with YAML frontmatter, stable links, and concise relationships to source files.

# Core Concepts

- [Automation flow](concepts/automation-flow.md)
- [Flow registry](concepts/flow-registry.md)
- [Flow adapter files](concepts/flow-adapter-files.md)
- [Operator workspace repo](concepts/operator-workspace-repo.md)

# Flows

- [idea-elaborate](flows/idea-elaborate.md)

# Playbooks

- [Add a new flow](playbooks/add-new-flow.md)

# Source Documents

- [Repository README](../README.md)
- [Project context](../CONTEXT.md)
- [Agent guide](../AGENTS.md)
- [Plan workflow guide](../docs/plans/README.md)
- [Flow manifest](../worker/src/flows.ts)
