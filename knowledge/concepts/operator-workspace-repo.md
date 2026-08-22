---
type: Project Concept
title: Operator workspace repo
description: A separate operational tooling repository installed by manifest-driven clone rather than tracked as a submodule.
resource: ../../ops/repos.md
tags: [operator-repo, manifest, hermes]
timestamp: 2026-08-22T00:00:00+09:00
---

# Operator Workspace Repo

An operator workspace repo is an operational tooling repository that lives beside this hub repository but is owned by itself.

`hermes-workspace/` owns remote Hermes runbooks, host scripts, helper tools, and operational artifacts. `ops/remote-comfyui/` and `ops/openhuman-altalt-proxy/` own their own ComfyUI and proxy operations. The hub repository owns Telegram to Worker to GitHub Actions automation flows.

# Installation

These repos are not git submodules. `ops/repos.md` holds only their `name`, `url`, `path`, and `branch`; `ops/repo-sync.sh` reads that manifest and clones any path that is not present yet. Every install path is listed in `.gitignore`, so the hub never records a commit pointer for them.

```bash
bash ops/repo-sync.sh
```

# Boundary

- Flow adapter scripts belong in the hub repository's top-level `scripts/`.
- Operator host scripts and runbooks belong in the owning operator repo.
- Hub-level docs may link to an operator repo path, but implementation changes happen in the owning repo and never produce a hub commit.
- Adding or moving an operator repo means editing `ops/repos.md` and `.gitignore` together.
