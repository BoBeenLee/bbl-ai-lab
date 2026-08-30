# bbl-ai-lab Agent Guide

This repository is an automation flow hub. Telegram commands enter through the Cloudflare Worker, the Worker dispatches GitHub Actions, and the Actions run scripts/prompts that create issues, reports, or other outputs.

Read this guide before changing repository-level automation, Worker routing, docs, or flow files.

## Source Context

Use these files as the source of truth:

- `CONTEXT.md` for project language.
- `README.md` for the public operating model and setup.
- `docs/plans/README.md` for plan document workflow.
- `worker/src/flows.ts` for automation flow registration.
- `LOOP.md` for which autonomous loops run, and `docs/safety.md` for their denylist.

## Flow Registry Rules

- Start every new automation flow in `worker/src/flows.ts`.
- Treat `worker/src/flows.ts` as the single manifest for Telegram commands, subcommands, `repository_dispatch` event types, and adapter file paths.
- Do not add a workflow, script, prompt, or flow doc without also adding or updating the manifest entry.
- Keep new `eventType` values equal to `<flow>-<action>` unless preserving an explicit legacy event. The only current legacy event allowed by the checker is `idea-submitted`.
- For subcommand flows, use the shape `/command subcommand body`; put action-specific workflow/script/prompt/docs paths inside `subcommands`.
- After flow changes, run:

```bash
cd worker
npm run typecheck
```

This runs TypeScript checking and verifies manifest drift against workflow `repository_dispatch.types` plus workflow/script/prompt/docs file existence.

## Current Flow Layout

- Worker runtime: `worker/src/index.ts`
- Flow manifest and routing helpers: `worker/src/flows.ts`
- Flow consistency checker: `worker/scripts/check-flows.mjs`
- GitHub Actions workflows: `.github/workflows/<flow>-<action>.yml`
- Runtime scripts: `scripts/<flow>-<action>.sh`
- Gemini prompts: `scripts/prompts/<flow>-<action>.md`
- Flow docs: `docs/<flow>-<action>.md`
- Skill context attached by Actions: `skills/*.SKILL.md`
- Operator tooling that is not a Telegram/GitHub Actions flow belongs in the relevant operator repo, such as `hermes-workspace/` or `ops/remote-comfyui/`, not in this repo's top-level `scripts/`.
- Operator repos are cloned, not submodules. `ops/repos.md` is the single manifest for their URL, branch, and install path; `ops/repo-sync.sh` reads it. Adding or moving an operator repo means editing the manifest and `.gitignore` together.
- The same manifest also covers project repos, which live under `projects/` rather than `ops/`. `path` is resolved from the hub root, so it need not start with `ops/`. An operator repo owns operations for a remote host; a project repo owns a body of work that is not a Telegram/Actions flow — `projects/games` owns game-related agent skills, `projects/travel` owns trip planning, `projects/finance` owns a personal-finance knowledge base, and `projects/music` owns AI music production knowledge. All install the same way and none is tracked by the hub. Project repos register themselves: `repo-sync.sh` scans `projects/*/`, and any clone missing from the manifest is appended from its own `origin` URL and default branch, so neither `ops/repos.md` nor `.gitignore` (a `/projects/*/` glob) is edited by hand. A directory with no `origin` is warned about and skipped. Do not hand-edit `ops/repos.md` for a `projects/` entry — add the remote and run the sync.
- A manifest repo may be private. `games`, `travel`, `finance`, `music`, and `shopping` are. The first three hold personal data outright; `music` is private because generated songs, lyrics, and taste become personal data as they accumulate. Private entries need a `gh auth` session or `GIT_TOKEN=<pat>` to clone.

## Loop Rules

Autonomous loops are scheduled, not Telegram-triggered, so they take no
`worker/src/flows.ts` entry. See `knowledge/concepts/autonomous-loop.md`.

- Treat `LOOP.md` as the single manifest for which loops run, at what cadence, and at what readiness level.
- `docs/safety.md` is the binding denylist. A loop that would touch a listed path escalates instead of editing.
- A loop reads `STATE.md` at the start of every run and writes outcomes there at the end. Escalation means a `needs-human` item under High Priority, not a new issue.
- The implementer never marks its own work done. `goal-verifier` or the `loop-verifier` agent decides.
- Do not raise a loop above L1 while `loop-run-log.md` has no clean run history.
- Loop skills live as real directories in `.claude/skills/`, not as `.agents/skills/` symlinks, because `skills-lock.json` only tracks skills the external installer placed.

## Documentation Rules

- Update `README.md` when the repository operating model, setup flow, or user-facing flow list changes.
- Update `CONTEXT.md` when a new project term becomes load-bearing for future plans or code reviews.
- Update `docs/<flow>-<action>.md` when a specific flow's trigger, environment, output, or verification changes.
- Update `knowledge/flows/<flow>-<action>.md` when an automation flow is added or its relationships change.
- Update `knowledge/concepts/` when a load-bearing project concept is added or materially redefined.
- Keep every `knowledge/**/*.md` file in Open Knowledge Format style: YAML frontmatter at the top with `type` required; prefer `title`, `description`, `resource`, `tags`, and `timestamp` when available.
- Update `docs/plans/README.md` only when the plan document workflow changes.

## Safety Rules

- Never commit secrets, OAuth credentials, Telegram bot tokens, GitHub tokens, SSH keys, `.env` files, or remote operator workspace secrets.
- Keep `worker/wrangler.toml` free of secrets; use `wrangler secret put` for sensitive values.
- Do not remove generated or local worktree directories unless the user explicitly asks.
- Existing untracked files may belong to the user. Stage only intentional files when asked to commit.

## Verification Before Finishing

For Worker or flow registry changes:

```bash
cd worker
npm run typecheck
```

For shell script changes:

```bash
bash -n scripts/<changed-script>.sh
```

For operator repo manifest changes:

```bash
bash ops/repo-sync.sh --list
bash ops/repo-sync.test.sh
```

`--list` registers any unregistered `projects/` clone, then parses `ops/repos.md` and fails if an entry is missing a name, url, path, or branch. `repo-sync.test.sh` exercises that registration in a temp directory and touches no real repo.

For docs-only changes, inspect the diff and make sure links/paths still match the manifest.

For loop scaffolding changes:

```bash
npx @cobusgreyling/loop audit .
```

For OKF knowledge bundle changes:

```bash
rg -n "^type:" knowledge
find knowledge -name "*.md" | sort
```
