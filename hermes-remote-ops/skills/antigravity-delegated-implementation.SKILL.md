# Antigravity Delegated Implementation

Use this skill when the user asks Hermes to delegate implementation to Antigravity, mentions Antigravity as a worker, or gives a repo-local coding task that is large enough to benefit from a separate implementation worker.

## Role Split

- Hermes is the supervisor and verifier.
- Antigravity CLI is the implementation worker.
- Completion mode is always `review-required`.

## When To Delegate

Delegate to `antigravity-worker` for:

- multi-file implementation tasks
- repo-local coding tasks with tests or checks
- implementation spikes where a separate worktree is useful
- explicit requests such as "ask Antigravity", "delegate to Antigravity", or "use Antigravity as a worker"

Do not delegate:

- secret, auth, key, or `.env` handling
- gateway restart, launchd changes, or remote config changes
- deploys, merges, commits, or destructive cleanup
- research-only tasks

## Required Flow

1. Create a short task brief for Antigravity.
2. Call `antigravity_start_task` with the brief.
3. Poll `antigravity_status` until the worker is ready for review, blocked, or should be stopped.
4. Call `antigravity_collect`.
5. Re-run the relevant checks yourself from the returned worktree path.
6. Report the session id, branch, worktree, artifact path, changed files, checks, and `review-required`.

If the worker is stuck, call `antigravity_stop`, then `antigravity_collect`.

## Safety Rules

- Keep Antigravity inside the isolated worktree returned by the tool.
- Never ask Antigravity to read or print `.env`, SSH keys, `~/.hermes/auth.json`, provider tokens, or copied secret files.
- Never let Antigravity stage, commit, merge, push, deploy, restart the gateway, or change remote auth/config as part of this flow.
- Treat Antigravity output as evidence to inspect, not as proof of correctness.

## Completion Note

The final response must include:

- task type: `delegated-implementation`
- Antigravity session id
- branch and worktree path
- artifact path
- changed files or report path
- tests/checks Hermes re-ran
- completion mode: `review-required`
