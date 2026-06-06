export interface FlowAdapterPaths {
  workflow: string;
  script: string;
  prompt: string;
  docs: string;
}

export interface FlatFlowDef extends FlowAdapterPaths {
  /** Telegram commands without the leading slash. First command is canonical. */
  commands: string[];
  /** GitHub repository_dispatch event_type. */
  eventType: string;
  /** Reply sent when the command has no body. */
  usageHint: string;
  /** Reply sent after repository_dispatch succeeds. */
  ackText: string;
  /** Allows pre-registry event names that intentionally do not match the file prefix. */
  legacyEventType?: true;
}

export interface FlowSubcommandDef extends FlowAdapterPaths {
  /** Subcommand token after the top-level command. */
  name: string;
  /** Optional aliases for the subcommand token. */
  aliases?: string[];
  eventType: string;
  usageHint: string;
  ackText: string;
  legacyEventType?: true;
}

export interface SubcommandFlowDef {
  /** Telegram commands without the leading slash. First command is canonical. */
  commands: string[];
  /** Help shown when the top-level command is used without a subcommand. */
  usageHint: string;
  subcommands: FlowSubcommandDef[];
}

export type FlowDef = FlatFlowDef | SubcommandFlowDef;

export interface DispatchFlow extends FlowAdapterPaths {
  command: string;
  subcommand?: string;
  eventType: string;
  usageHint: string;
  ackText: string;
  legacyEventType?: true;
}

export type RouteResult =
  | { kind: "matched"; flow: DispatchFlow; body: string }
  | { kind: "missing_body"; usageHint: string }
  | { kind: "unknown_command"; command: string }
  | { kind: "missing_prefix" };

export const FLOWS = [
  {
    commands: ["idea", "todo"],
    eventType: "idea-submitted",
    legacyEventType: true,
    usageHint: "예: /idea 텔레그램 봇으로 메모를 받아 GH Issue로 자동 정리",
    ackText: "아이디어 접수 완료. 1~2분 내에 Issue 링크를 회신합니다.",
    workflow: ".github/workflows/idea-elaborate.yml",
    script: "scripts/idea-elaborate.sh",
    prompt: "scripts/prompts/idea-elaborate.md",
    docs: "docs/idea-elaborate.md",
  },
] satisfies FlowDef[];

export function routeCommand(text: string, flows: readonly FlowDef[] = FLOWS): RouteResult {
  const m = text.match(/^\/(\w+)(?:@[\w_]+)?(?:\s+([\s\S]*))?$/);
  if (!m) {
    return { kind: "missing_prefix" };
  }

  const cmd = m[1].toLowerCase();
  const rest = (m[2] ?? "").trim();
  const flow = findFlow(cmd, flows);
  if (!flow) {
    return { kind: "unknown_command", command: cmd };
  }

  if (!hasSubcommands(flow)) {
    if (!rest) {
      return { kind: "missing_body", usageHint: flow.usageHint };
    }
    return {
      kind: "matched",
      flow: {
        command: cmd,
        eventType: flow.eventType,
        usageHint: flow.usageHint,
        ackText: flow.ackText,
        legacyEventType: flow.legacyEventType,
        workflow: flow.workflow,
        script: flow.script,
        prompt: flow.prompt,
        docs: flow.docs,
      },
      body: rest,
    };
  }

  const [subcommandToken, body] = splitSubcommand(rest);
  if (!subcommandToken) {
    return { kind: "missing_body", usageHint: flow.usageHint };
  }

  const subcommand = findSubcommand(subcommandToken, flow);
  if (!subcommand) {
    return { kind: "unknown_command", command: `${cmd} ${subcommandToken}` };
  }
  if (!body) {
    return { kind: "missing_body", usageHint: subcommand.usageHint };
  }

  return {
    kind: "matched",
    flow: {
      command: cmd,
      subcommand: subcommand.name,
      eventType: subcommand.eventType,
      usageHint: subcommand.usageHint,
      ackText: subcommand.ackText,
      legacyEventType: subcommand.legacyEventType,
      workflow: subcommand.workflow,
      script: subcommand.script,
      prompt: subcommand.prompt,
      docs: subcommand.docs,
    },
    body,
  };
}

export function renderHelp(prefix: string, flows: readonly FlowDef[] = FLOWS): string {
  const lines = flows.flatMap((flow) => {
    const command = flow.commands[0];
    if (!hasSubcommands(flow)) {
      return [`  /${command} — ${flow.usageHint}`];
    }
    return flow.subcommands.map((subcommand) => (
      `  /${command} ${subcommand.name} — ${subcommand.usageHint}`
    ));
  });
  return `${prefix}\n사용 가능한 명령어:\n${lines.join("\n")}`;
}

export function flattenFlows(flows: readonly FlowDef[] = FLOWS): DispatchFlow[] {
  return flows.flatMap((flow) => {
    const command = flow.commands[0];
    if (!hasSubcommands(flow)) {
      return [{
        command,
        eventType: flow.eventType,
        usageHint: flow.usageHint,
        ackText: flow.ackText,
        legacyEventType: flow.legacyEventType,
        workflow: flow.workflow,
        script: flow.script,
        prompt: flow.prompt,
        docs: flow.docs,
      }];
    }
    return flow.subcommands.map((subcommand) => ({
      command,
      subcommand: subcommand.name,
      eventType: subcommand.eventType,
      usageHint: subcommand.usageHint,
      ackText: subcommand.ackText,
      legacyEventType: subcommand.legacyEventType,
      workflow: subcommand.workflow,
      script: subcommand.script,
      prompt: subcommand.prompt,
      docs: subcommand.docs,
    }));
  });
}

function findFlow(command: string, flows: readonly FlowDef[]): FlowDef | undefined {
  return flows.find((flow) => flow.commands.some((candidate) => candidate.toLowerCase() === command));
}

function findSubcommand(token: string, flow: SubcommandFlowDef): FlowSubcommandDef | undefined {
  const lowered = token.toLowerCase();
  return flow.subcommands.find((subcommand) => (
    subcommand.name.toLowerCase() === lowered ||
    (subcommand.aliases ?? []).some((alias) => alias.toLowerCase() === lowered)
  ));
}

function hasSubcommands(flow: FlowDef): flow is SubcommandFlowDef {
  return "subcommands" in flow;
}

function splitSubcommand(text: string): [string, string] | ["", ""] {
  if (!text) return ["", ""];
  const match = text.match(/^(\S+)(?:\s+([\s\S]*))?$/);
  if (!match) return ["", ""];
  return [match[1], (match[2] ?? "").trim()];
}
