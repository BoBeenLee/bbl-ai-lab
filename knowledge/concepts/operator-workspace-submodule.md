---
type: Project Concept
title: Operator workspace submodule
description: A separate operational tooling repository mounted as a submodule rather than owned by the flow hub.
resource: ../../hermes-workspace/
tags: [submodule, operator-workspace, hermes]
timestamp: 2026-06-27T00:00:00+09:00
---

# Operator Workspace Submodule

An operator workspace submodule is an operational tooling repository mounted inside this hub repository.

`hermes-workspace/` owns remote Hermes runbooks, host scripts, helper tools, and operational artifacts. The hub repository owns Telegram to Worker to GitHub Actions automation flows.

# Boundary

- Flow adapter scripts belong in the hub repository's top-level `scripts/`.
- Operator host scripts and runbooks belong in the relevant submodule.
- Hub-level docs may link to the submodule, but implementation changes should happen in the owning workspace.
