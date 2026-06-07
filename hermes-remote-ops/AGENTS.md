# Hermes Remote Ops Agent Guide

SSH-first toolkit for operating the remote Hermes Agent on the Hermes MacBook. Read this before changing files here or operating the remote Mac.

## Source Context

The operating model comes from:

- `CONTEXT.md`
- `docs/workspace-lifecycle.md`
- `docs/research-workflow.md`
- `docs/discord-thread-triage.md`
- migrated historical plans under `docs/plans/` when they are present after repo promotion

Important terms:

- **Control MacBook**: the local Mac where Codex/Desktop automation runs.
- **Hermes MacBook**: the remote Mac that runs NousResearch `hermes-agent`.
- **Hermes agent**: the per-user Hermes install at `~/.hermes/hermes-agent`, with config/data/logs under `~/.hermes` and command wrapper at `~/.local/bin/hermes`.
- **Remote access path**: SSH key access from Control MacBook to Hermes MacBook. Tailscale/LAN aliases are access paths, not application state.
- **Workspace Lifecycle module**: the interface every Hermes task follows before it is reported as `done` or `review-required`.
- **Research Analysis module**: the interface for market research and analysis work, including brief, source ledger, notes, and report artifacts.

## Current Default Target

Defaults live in `config/example.env`; local overrides live in ignored `.env`.

- SSH alias: `bobeen`
- Remote user: `bobeenlee`
- observed Tailscale IP: `100.89.89.70`
- Remote Hermes command: `/Users/bobeenlee/.local/bin/hermes`
- Remote CuaDriver command: `/Users/bobeenlee/.local/bin/cua-driver`
- Remote Hermes config: `/Users/bobeenlee/.hermes/config.yaml`
- Canonical remote workspace: `/Users/bobeenlee/Workspaces/hermes-remote-ops`

Do not commit `.env`.

## Safety Rules

- Never commit SSH private keys, provider API keys, OAuth tokens, Discord tokens, `.env` files, or remote Hermes secrets.
- Treat `~/.hermes/.env`, `~/.hermes/auth.json`, and provider config output as sensitive. Summarize status without copying secrets.
- Prefer `bin/hermes-remote` commands over ad hoc SSH because the script captures the expected paths and backup behavior.
- Before editing remote `~/.hermes/config.yaml`, create or rely on a timestamped backup.
- Use user-level Hermes/launchd commands. Do not introduce root/system-level daemons unless a user explicitly asks.
- Do not remove remote access keys or stop the gateway unless the user asks or the rollback task requires it.
- macOS `computer_use` permissions cannot be fully automated. `grant-computer-use` opens the flow; the user may need to approve CuaDriver in System Settings.
- Never mark script, remote config, gateway, key/auth, or recurring automation changes as fully done without human review. Use `review-required`.
- For research-based tasks, keep a source ledger and do not present current market, product, pricing, legal, or policy claims without web verification.

## Core Workflow

Start every remote operations session with:

```bash
cd /Users/mac_al03241161/Documents/mygit/bbl-ai-lab/hermes-remote-ops
bin/hermes-remote check-ssh
bin/hermes-remote status
```

Start every Hermes repo task with `docs/workspace-lifecycle.md`: choose task type, use canonical workspace, isolate branch/worktree, produce required outputs, run checks, finish `done` or `review-required`.

If SSH fails:

- Check Tailscale status from the Control MacBook.
- Try the configured SSH alias before changing config.
- Remember that VNC/Screen Sharing can be reachable while SSH is temporarily slow or unavailable.

## Computer Use Workflow

Use `docs/workspace-lifecycle.md` plus this command path when Hermes needs macOS desktop control.

```bash
bin/hermes-remote setup-computer-use
bin/hermes-remote grant-computer-use
bin/hermes-remote verify-computer-use
bin/hermes-remote gateway-restart
```

Success: Hermes finds `cua-driver`, permissions show Accessibility + Screen Recording from `driver-daemon`, MCP test discovers tools, screen/window commands return data. Known gotcha: non-interactive SSH may miss `~/.local/bin`; toolkit patches wrapper PATH.

## Kanban Workflow

Use when Hermes needs durable tasks.

```bash
bin/hermes-remote setup-kanban
bin/hermes-remote status
```

Success: `~/.hermes/kanban.db` exists, board list shows current board, stats work, config has `kanban.dispatch_in_gateway: true`, gateway logs show `kanban dispatcher: embedded in gateway`.

## Discord Thread Triage

Detailed workflow: `docs/discord-thread-triage.md`. Wake Hermes from the user's Discord account by mentioning `@Bob Hermes`; do not use bot/webhook activation. For Discord URLs, use the final ID as thread/chat ID unless logs prove otherwise.

```bash
bin/hermes-remote is-working <thread_id>
bin/hermes-remote tail-thread <thread_id>
```

Interpret state using `docs/discord-thread-triage.md`: recent inbound/live worker/Kanban running means working; sent response/no worker/running 0 means done; errors in logs mean failed or incomplete.

## Market Research and Analysis

Follow `docs/research-workflow.md` for market/product/competitor/pricing/legal/policy/trend work. Current claims require web verification and a source ledger. Report-only work can be `done`; scripts, recurring automation, or remote config changes are `review-required`.

## Antigravity Delegation

Follow `docs/antigravity-delegation.md`. Hermes supervises, Antigravity implements in an isolated worktree through manual tmux or `antigravity-worker`, and completion stays `review-required`.

## Gateway Operations

After config changes:

```bash
bin/hermes-remote gateway-restart
bin/hermes-remote status
```

Expected gateway service:

- user-level launchd
- label `ai.hermes.gateway`
- logs under `~/.hermes/logs/gateway.log` and `~/.hermes/logs/gateway.error.log`

## Dashboard Operations

The dashboard is not required for gateway operation.

```bash
bin/hermes-remote dashboard-status
bin/hermes-remote dashboard-start
```

It binds to `127.0.0.1:9119` on the remote Mac by default. Do not use insecure external binding unless explicitly requested.

## Verification Before Finishing

For script edits:

```bash
bash -n bin/hermes-remote
bin/hermes-remote check-ssh
bin/hermes-remote status
```

For docs-only edits, at least inspect changed files and run:

```bash
rg -n "Workspace Lifecycle|Research Analysis|review-required|source ledger" .
git diff -- .
```

## Commit Hygiene

- Keep `.env` untracked.
- Stage only intentional files under `hermes-remote-ops/` unless the user asked for broader changes.
- Existing untracked files elsewhere in the repo may belong to the user; do not remove or stage them accidentally.
