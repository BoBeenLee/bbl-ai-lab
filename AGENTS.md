# bbl-ai-lab Agent Guide

This repository is a hub. It holds the manifest (`ops/repos.md`) that installs operator, project, and upstream tool repos, the shared agent skills, the friction tooling, and an OKF knowledge bundle. Real work happens in the repos it installs.

Read this guide before changing the manifest, shared skills, friction tooling, or docs.

## Source Context

Use these files as the source of truth:

- `CONTEXT.md` for project language.
- `README.md` for the public operating model and setup.
- `ops/repos.md` for which repos the hub installs.

## Repo Layout

- Operator tooling belongs in the relevant operator repo, such as `hermes-workspace/` or `ops/remote-comfyui/`, not in this hub.
- Operator repos are cloned, not submodules. `ops/repos.md` is the single manifest for their URL, branch, and install path; `ops/repo-sync.sh` reads it. Adding or moving an operator repo means editing the manifest and `.gitignore` together.
- The same manifest also covers project repos, which live under `projects/` rather than `ops/`. `path` is resolved from the hub root, so it need not start with `ops/`. An operator repo owns operations for a remote host; a project repo owns one category's body of work:
  - `projects/games`: game agent skills (party, gear builds).
  - `projects/travel`: trip planning.
  - `projects/finance`: personal-finance knowledge base.
  - `projects/music`: AI music production knowledge.
  - `projects/shopping`: real-purchase decision workflows.
  - `projects/hiking`: hiking knowledge and per-outing records.
  - `projects/cad`: FreeCAD knowledge and per-design records (3D-printable parts, furniture and interior layouts).
  - `projects/voice-agent`: voice-agent knowledge and per-agent records, gated on staying free.
  - `projects/promo-agent`: promotion-channel knowledge and per-campaign records.
  - `projects/kakao-agent`: the Mac KakaoTalk bot that runs a local agent CLI per turn through Iris, next to the DGX bot.
  - `projects/blender`: Blender scenes, renders, animation, GLB and STL exports (dimension-driven parts go to `cad`).
  - `projects/car`: car knowledge and custom wrap images (3D scenes go to `blender`).
  - `projects/stock-agent`: stock analysis on TradingAgents (KOSPI, KOSDAQ first); orders only through a kakao-agent tool after my approval.
  - `projects/app-analysis` (formerly `reverse-engineering`): analysis notes on installed apps and web services (REA, Ghidra, clean-room study), never the binaries or captures.
  - `projects/meeting-agent`: a meeting companion that listens locally, watches my screen, and advises only me; its skill edition is installed by the repo's `scripts/setup-mac.sh`.

  All install the same way and none is tracked by the hub. Project repos register themselves: `repo-sync.sh` scans `projects/*/`, and any clone missing from the manifest is appended from its own `origin` URL and default branch, so neither `ops/repos.md` nor `.gitignore` (a `/projects/*/` glob) is edited by hand. A directory with no `origin` is warned about and skipped. Do not hand-edit `ops/repos.md` for a `projects/` entry — add the remote and run the sync.
- A third kind of manifest entry is an upstream tool repo, owned by its upstream author rather than by me. `ops/openmontage` is the only one: an AGPL-3.0 video production pipeline that calls `ops/remote-comfyui`'s DGX ComfyUI as one provider inside its `assets` stage. Its `.gitignore` line is added by hand like an operator repo's, `repo-sync.sh` clones but does not install (`make setup` inside the repo does), and local edits have nowhere to push until it is forked. See `knowledge/concepts/operator-workspace-repo.md`.
- Every `projects/*` repo is private: each holds personal data or accumulates it (purchase history, GPS tracks, account ids, holdings, decompiled third-party code). `README.md` says why per repo. Meeting audio, transcripts, and screen captures from `meeting-agent` are never committed at all. Private entries need a `gh auth` session or `GIT_TOKEN=<pat>` to clone.
- The `kakao-agent` bot reads this hub too. Its host keeps a clone at `~/bbl-ai-lab` with every manifest repo, pulled by hand, except that a PR the bot merges itself is pulled into that clone in the same turn (its `hub_pull` tool), and the bot's rules send any question about my projects there: it picks a repo from `ops/repos.md` and the descriptions above, then follows that repo's `CLAUDE.md` or `README.md`. A project's entry doc is therefore also what the bot answers from, so keep it pointing at the repo's skills and data. When I ask it to in a mention, it also edits: one git worktree per change on a `kakao/<name>` branch, pushed and opened as a PR, never a push to `main`. It merges that PR itself only when my mention says to, and only with `gh pr merge <url> --merge` on an open `kakao/*` branch; otherwise I merge. `hermes-workspace`, `projects/kakao-agent`, and `ops/openmontage` stay read-only to it. Expect `kakao/*` PRs whose commits end with `Assisted-by: kakao-agent (<brain>)`, and follow the repo's own rules when reviewing them. The DGX `[jarvis]` bot (hermes-workspace `plugins/kakao`) reads the hub the same way from its own `~/bbl-ai-lab` once that clone is installed there, and only in the owner's own turns.
- Shared agent skills live in `.agents/skills/` (installer-owned, pinned in `skills-lock.json`) and are exposed to Claude Code through `.claude/skills/` symlinks. `file-friction` is the only skill this repo owns directly.
- Sessions file repo papercuts they worked around as `friction` issues in the owning repo through `ops/friction.sh`, guided by the `file-friction` skill. See `knowledge/concepts/friction-log.md`. Never call `gh issue create` for friction directly, and never file friction into this public hub with personal data.

## Documentation Rules

- Update `README.md` when the hub's operating model, setup flow, or repo list changes.
- Update `CONTEXT.md` when a new project term becomes load-bearing for future plans or code reviews.
- Update `knowledge/concepts/` when a load-bearing project concept is added or materially redefined, and add an entry to `knowledge/log.md`.
- Keep every `knowledge/**/*.md` file in Open Knowledge Format style: YAML frontmatter at the top with `type` required; prefer `title`, `description`, `resource`, `tags`, and `timestamp` when available.

## Safety Rules

- Never commit secrets, OAuth credentials, bot tokens, GitHub tokens, SSH keys, `.env` files, or remote operator workspace secrets.
- Do not remove generated or local worktree directories unless the user explicitly asks.
- Existing untracked files may belong to the user. Stage only intentional files when asked to commit.

## Verification Before Finishing

For shell script changes:

```bash
bash -n ops/<changed-script>.sh
```

For operator repo manifest changes:

```bash
bash ops/repo-sync.sh --list
bash ops/repo-sync.test.sh
```

`--list` registers any unregistered `projects/` clone, then parses `ops/repos.md` and fails if an entry is missing a name, url, path, or branch. `repo-sync.test.sh` exercises that registration in a temp directory and touches no real repo.

For friction tooling changes:

```bash
bash ops/friction.test.sh
```

For docs-only changes, inspect the diff and make sure links/paths still match the manifest.

For OKF knowledge bundle changes:

```bash
rg -n "^type:" knowledge
find knowledge -name "*.md" | sort
```
