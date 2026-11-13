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
- The same manifest also covers project repos, which live under `projects/` rather than `ops/`. `path` is resolved from the hub root, so it need not start with `ops/`. An operator repo owns operations for a remote host; a project repo owns one category's body of work. What each repo owns is the `description` of its entry in `ops/repos.md`, the only place that says it: read it there to pick a repo, then start from that repo's `CLAUDE.md`, else `AGENTS.md`, else `README.md`. All install the same way and none is tracked by the hub. Project repos register themselves: `repo-sync.sh` scans `projects/*/`, and any clone missing from the manifest is appended from its own `origin` URL and default branch, so `.gitignore` (a `/projects/*/` glob) is never edited and the entry is never written by hand. A directory with no `origin` is warned about and skipped. The one hand edit is the new entry's `description`, which the sync cannot know and warns about until it is there.
- A third kind of manifest entry is an upstream tool repo, owned by its upstream author rather than by me. `ops/openmontage` is the only one: an AGPL-3.0 video production pipeline that calls `ops/remote-comfyui`'s DGX ComfyUI as one provider inside its `assets` stage. Its `.gitignore` line is added by hand like an operator repo's, `repo-sync.sh` clones but does not install (`make setup` inside the repo does), and local edits have nowhere to push until it is forked. See `knowledge/concepts/operator-workspace-repo.md`.
- A manifest repo may be private; most project repos are. Which ones and why are under "private repo" in `ops/repos.md`. Private entries need a `gh auth` session or `GIT_TOKEN=<pat>` to clone.
- Every session shares one checkout of each child repo, and a hub worktree isolates only the hub. Before editing a child repo, run `git -C <path> worktree list` to see what others hold, then add a worktree on a new branch and edit only there. From a hub worktree session, put it under that session's folder (`git -C projects/<name> worktree add <session worktree>/projects/<name>-<slug> -b claude/<slug>`, ignored by the `/projects/*/` glob); an edit hook blocks paths outside the session folder.
- The `kakao-agent` bot reads this hub too. Its host keeps a clone at `~/bbl-ai-lab` with every manifest repo, pulled by hand, except that a PR the bot merges itself is pulled into that clone in the same turn (its `hub_pull` tool), and the bot's rules send any question about my projects there: it picks a repo from `ops/repos.md` by each entry's `description` (its rules still say "what each owns is in AGENTS.md", so the pointer above must stay), then follows that repo's `CLAUDE.md` or `README.md`. A project's entry doc is therefore also what the bot answers from, so keep it pointing at the repo's skills and data. When I ask it to in a mention, it also edits: one git worktree per change on a `kakao/<name>` branch, pushed and opened as a PR, never a push to `main`. It merges that PR itself only when my mention says to, and only with `gh pr merge <url> --merge` on an open `kakao/*` branch; otherwise I merge. `hermes-workspace`, `projects/kakao-agent`, and `ops/openmontage` stay read-only to it. Expect `kakao/*` PRs whose commits end with `Assisted-by: kakao-agent (<brain>)`, and follow the repo's own rules when reviewing them. The DGX `[jarvis]` bot (hermes-workspace `plugins/kakao`) reads the hub the same way from its own `~/bbl-ai-lab` once that clone is installed there, and only in the owner's own turns.
- Shared agent skills live in `.agents/skills/` (installer-owned, pinned in `skills-lock.json`) and are exposed to Claude Code through `.claude/skills/` symlinks. `file-friction` is the only skill this repo owns directly. It is used in every repo, so the user-level `~/.agents/skills/file-friction` is a symlink to this repo's copy; edit it here, never in the user folder, or the two drift.
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
