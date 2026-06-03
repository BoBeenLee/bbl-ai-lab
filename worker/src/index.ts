// Cloudflare Worker: Telegram webhook -> GitHub repository_dispatch (multi-flow router)
//
// 새 자동화 flow 추가하려면:
//   1) 아래 FLOWS 테이블에 한 줄 추가
//   2) 같은 prefix로 GitHub Actions workflow 추가:
//        .github/workflows/<flow>-<action>.yml
//        scripts/<flow>-<action>.sh
//        scripts/prompts/<flow>-<action>.md
//   3) workflow의 트리거를 `repository_dispatch.types: [<event_type>]` 로 맞춘다.
//
// 매칭 규칙:
//   - 메시지가 "/<command> ..." 로 시작하면 해당 flow로 라우팅 (잘라낸 본문만 dispatch)
//   - 명령어가 없는 평문은 dispatch 하지 않고 prefix 사용 안내만 회신
//   - 등록되지 않은 명령어는 도움말 회신

interface Env {
  // secrets
  TG_BOT_TOKEN: string;
  TG_WEBHOOK_SECRET: string;
  GH_DISPATCH_TOKEN: string;

  // vars
  GH_REPO: string;
  ALLOWED_CHAT_IDS: string;
}

interface FlowDef {
  /** 텔레그램 명령어 (앞의 / 제외, 소문자). 동의어 허용 */
  commands: string[];
  /** GitHub repository_dispatch event_type. workflow의 types와 정확히 일치해야 함 */
  eventType: string;
  /** 사용자에게 보낼 안내 (명령어만 입력하고 본문 비었을 때) */
  usageHint: string;
  /** 접수 직후 텔레그램 회신 텍스트 */
  ackText: string;
}

const FLOWS: FlowDef[] = [
  {
    commands: ["idea", "todo"],
    eventType: "idea-submitted",
    usageHint: "예: /idea 텔레그램 봇으로 메모를 받아 GH Issue로 자동 정리",
    ackText: "아이디어 접수 완료. 1~2분 내에 Issue 링크를 회신합니다.",
  },
  // 새 flow 추가 예시:
  // {
  //   commands: ["meeting"],
  //   eventType: "meeting-summarize",
  //   usageHint: "예: /meeting <회의록 raw 텍스트>",
  //   ackText: "회의록 요약 시작. 잠시 후 결과를 회신합니다.",
  // },
];

const COMMAND_INDEX: Record<string, FlowDef> = Object.fromEntries(
  FLOWS.flatMap((f) => f.commands.map((c) => [c.toLowerCase(), f] as const)),
);

interface TelegramUpdate {
  message?: {
    message_id: number;
    date: number;
    text?: string;
    caption?: string;
    chat: { id: number };
    from?: { id: number; username?: string };
  };
  edited_message?: TelegramUpdate["message"];
}

const TELEGRAM_SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return new Response("ok", { status: 200 });
    }

    if (request.method !== "POST" || url.pathname !== "/tg-webhook") {
      return new Response("not found", { status: 404 });
    }

    // 1) Telegram secret 검증
    const provided = request.headers.get(TELEGRAM_SECRET_HEADER);
    if (!provided || provided !== env.TG_WEBHOOK_SECRET) {
      return new Response("unauthorized", { status: 401 });
    }

    let update: TelegramUpdate;
    try {
      update = await request.json();
    } catch {
      return new Response("bad request", { status: 400 });
    }

    const msg = update.message ?? update.edited_message;
    if (!msg) {
      return new Response("ok", { status: 200 });
    }

    // 2) 화이트리스트 검증
    const allowed = parseAllowedIds(env.ALLOWED_CHAT_IDS);
    const fromId = msg.from?.id;
    const chatId = msg.chat.id;

    if (allowed.size > 0) {
      const passes =
        (fromId !== undefined && allowed.has(fromId)) || allowed.has(chatId);
      if (!passes) {
        return new Response("ok", { status: 200 });
      }
    }

    const text = (msg.text ?? msg.caption ?? "").trim();
    if (!text) {
      await sendTelegramReply(env, chatId, msg.message_id, "텍스트 메시지를 보내 주세요.");
      return new Response("ok", { status: 200 });
    }

    // 3) 명령어 → flow 라우팅
    const routed = routeCommand(text);

    if (routed.kind === "unknown_command") {
      await sendTelegramReply(
        env,
        chatId,
        msg.message_id,
        renderHelp(`알 수 없는 명령어: /${routed.command}`),
      );
      return new Response("ok", { status: 200 });
    }

    if (routed.kind === "missing_prefix") {
      await sendTelegramReply(
        env,
        chatId,
        msg.message_id,
        renderHelp("명령어 prefix가 필요합니다. /idea 또는 /todo 로 시작해 주세요."),
      );
      return new Response("ok", { status: 200 });
    }

    if (!routed.body) {
      await sendTelegramReply(env, chatId, msg.message_id, routed.flow.usageHint);
      return new Response("ok", { status: 200 });
    }

    // 4) GitHub repository_dispatch
    const dispatchResp = await dispatchToGitHub(env, routed.flow.eventType, {
      chat_id: chatId,
      message_id: msg.message_id,
      text: routed.body,
      submitted_at: new Date(msg.date * 1000).toISOString(),
    });

    if (!dispatchResp.ok) {
      const detail = await safeText(dispatchResp);
      console.error("dispatch failed", routed.flow.eventType, dispatchResp.status, detail);
      await sendTelegramReply(
        env,
        chatId,
        msg.message_id,
        `GitHub 트리거 실패 (${dispatchResp.status}). 잠시 후 다시 시도해 주세요.`,
      );
      return new Response("ok", { status: 200 });
    }

    // 5) 즉시 ack
    await sendTelegramReply(env, chatId, msg.message_id, routed.flow.ackText);
    return new Response("ok", { status: 200 });
  },
};

type RouteResult =
  | { kind: "matched"; flow: FlowDef; body: string }
  | { kind: "unknown_command"; command: string }
  | { kind: "missing_prefix" };

function routeCommand(text: string): RouteResult {
  const m = text.match(/^\/(\w+)(?:@[\w_]+)?(?:\s+([\s\S]*))?$/);
  if (!m) {
    return { kind: "missing_prefix" };
  }
  const cmd = m[1].toLowerCase();
  const body = (m[2] ?? "").trim();
  const flow = COMMAND_INDEX[cmd];
  if (!flow) {
    return { kind: "unknown_command", command: cmd };
  }
  return { kind: "matched", flow, body };
}

function renderHelp(prefix: string): string {
  const lines = FLOWS.map((f) => `  /${f.commands[0]} — ${f.usageHint}`);
  return `${prefix}\n사용 가능한 명령어:\n${lines.join("\n")}`;
}

function parseAllowedIds(raw: string | undefined): Set<number> {
  if (!raw) return new Set();
  return new Set(
    raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) => Number(s))
      .filter((n) => Number.isFinite(n)),
  );
}

async function dispatchToGitHub(
  env: Env,
  eventType: string,
  payload: Record<string, unknown>,
): Promise<Response> {
  const url = `https://api.github.com/repos/${env.GH_REPO}/dispatches`;
  return fetch(url, {
    method: "POST",
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": `Bearer ${env.GH_DISPATCH_TOKEN}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
      "User-Agent": "tg-automation-bridge",
    },
    body: JSON.stringify({
      event_type: eventType,
      client_payload: payload,
    }),
  });
}

async function sendTelegramReply(
  env: Env,
  chatId: number,
  replyToMessageId: number,
  text: string,
): Promise<void> {
  try {
    await fetch(
      `https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text,
          reply_to_message_id: replyToMessageId,
          disable_web_page_preview: true,
        }),
      },
    );
  } catch (err) {
    console.error("telegram reply failed", err);
  }
}

async function safeText(resp: Response): Promise<string> {
  try {
    return await resp.text();
  } catch {
    return "<no body>";
  }
}
