---
type: Project Concept
title: Flow adapter files
description: The concrete workflow, script, prompt, and operator documentation files that implement a registered flow.
resource: ../../README.md
tags: [automation-flow, github-actions, scripts, prompts, docs]
timestamp: 2026-06-27T00:00:00+09:00
---

# Flow Adapter Files

Flow adapter files are the concrete files named by a [flow registry](flow-registry.md) entry.

For a normal flow, the adapter set is:

| Role | Pattern |
|------|---------|
| Workflow | `.github/workflows/<flow>-<action>.yml` |
| Runtime script | `scripts/<flow>-<action>.sh` |
| Prompt | `scripts/prompts/<flow>-<action>.md` |
| Flow docs | `docs/<flow>-<action>.md` |
| OKF flow concept | `knowledge/flows/<flow>-<action>.md` |

# Verification

The Worker typecheck verifies the registry against workflow dispatch types and the existence of workflow, script, prompt, and docs paths. The OKF concept file is maintained by documentation rules rather than the Worker checker.
