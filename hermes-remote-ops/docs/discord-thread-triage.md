# Discord Thread Triage

## Activation Rule

When asking Hermes to start work from Discord, post from the user's Discord account and mention `@Bob Hermes`. Do not use a bot account or webhook for this activation path, because Hermes is expected to react to the user-account mention.

Use this when a Discord message link looks like:

```text
https://discord.com/channels/<guild_id>/<channel_id>/<message_or_thread_id>
```

For Hermes gateway logs, the useful value is usually the thread/chat id. In Hermes logs it appears like:

```text
chat=<thread_id>
agent:main:discord:thread:<thread_id>:<thread_id>
```

Commands:

```bash
bin/hermes-remote is-working <thread_id>
bin/hermes-remote tail-thread <thread_id>
```

Signs it is still working:

- a recent `inbound message` line without a later `response ready`
- a live `hermes` worker process beyond the gateway process
- a Kanban task in `running`

Signs it is done:

- `response ready` followed by `Sending response`
- no extra worker process
- Kanban counts show `running 0`
