---
type: Project Concept
title: Operator workspace repo
description: A separate operational tooling repository installed by manifest-driven clone rather than tracked as a submodule.
resource: ../../ops/repos.md
tags: [operator-repo, manifest, hermes, openmontage]
timestamp: 2026-08-31T00:00:00+09:00
---

# Operator Workspace Repo

An operator workspace repo is an operational tooling repository that lives beside this hub repository but is owned by itself.

`hermes-workspace/` owns remote Hermes runbooks, host scripts, helper tools, and operational artifacts. `ops/remote-comfyui/` and `ops/openhuman-altalt-proxy/` own their own ComfyUI and proxy operations. The hub repository owns Telegram to Worker to GitHub Actions automation flows.

# Installation

These repos are not git submodules. `ops/repos.md` holds only their `name`, `url`, `path`, and `branch`; `ops/repo-sync.sh` reads that manifest and clones any path that is not present yet. Every install path is listed in `.gitignore`, so the hub never records a commit pointer for them.

```bash
bash ops/repo-sync.sh
```

# Project repos

The same manifest installs project repos, which live under `projects/` instead of
`ops/`. `repo-sync.sh` resolves `path` from the hub root, so the prefix is free.

The distinction is ownership, not mechanism. An operator repo owns operations for
a remote host. A project repo owns a body of work that is not a Telegram to
Actions flow. `projects/games` owns game-related agent skills and is private
because it holds account data; private entries need a `gh auth` session or
`GIT_TOKEN`.

Project repos register themselves. `repo-sync.sh` scans `projects/*/` and appends
any clone missing from the manifest, reading the `name` from the directory and the
`url` and `branch` from the clone's own `origin`. `.gitignore` covers the whole
tree with a `/projects/*/` glob. So adding one is `git remote add origin` plus one
sync run, and neither file is edited by hand. A directory with no `origin` is
warned about and skipped, because a manifest entry without a URL cannot be cloned.

The reason registration is bundled into the sync command rather than left as a
documented step: the forgettable half is registration, not cloning, and it is
forgotten on the machine where the repo was *created* — a machine that never needs
to clone. Only a command run there can catch it.

# Upstream tool repos

The manifest also installs upstream tool repos: third-party tools that are not
mine at all. `ops/openmontage` is the only one today.

Again the distinction is ownership. An operator repo owns operations for a remote
host, a project repo owns a body of work, and an upstream tool repo is owned by
its upstream author. Three things follow. Local edits can be committed but have
nowhere to push, so a fork is deferred until a push is actually needed. The
license is the upstream's and does not reach the hub (`ops/openmontage` is
AGPL-3.0, the hub is not). And `repo-sync.sh` only clones. Dependency install is
the repo's own procedure, `make setup` in this case, which builds its venv, npm
tree, and `.env`.

`.gitignore` is edited by hand for these, exactly as for an operator repo. The
self-registration in `repo-sync.sh` covers `projects/*/` only.

The boundary against `ops/remote-comfyui`: OpenMontage owns the production
pipeline around generation, and `remote-comfyui` owns DGX host operations. The
former calls the latter as one provider inside its `assets` stage. Batch queueing
stays with `remote-comfyui`, because OpenMontage's ComfyUI tool does not free
memory between jobs.

# Boundary

- Flow adapter scripts belong in the hub repository's top-level `scripts/`.
- Operator host scripts and runbooks belong in the owning operator repo.
- Hub-level docs may link to an operator repo path, but implementation changes happen in the owning repo and never produce a hub commit.
- Adding or moving an operator repo means editing `ops/repos.md` and `.gitignore` together. A project repo under `projects/` is instead registered by `repo-sync.sh`; hand-editing the manifest for one is drift waiting to happen.
