// Cloudflare Worker: Telegram webhook -> GitHub repository_dispatch (multi-flow router)
//
// 새 자동화 flow 추가하려면:
//   1) src/flows.ts manifest에 한 항목 추가
//   2) manifest가 가리키는 workflow/script/prompt/docs 파일 추가
//   3) `npm run typecheck`로 repository_dispatch.types와 파일 존재 여부를 검증
//
// 매칭 규칙:
//   - 메시지가 "/<command> ..." 로 시작하면 해당 flow로 라우팅
//   - subcommand flow는 "/<command> <subcommand> ..." 로 라우팅
//   - 명령어가 없는 평문은 dispatch 하지 않고 prefix 사용 안내만 회신
//   - 등록되지 않은 명령어는 도움말 회신

import { renderHelp, routeCommand } from "./flows";

interface Env {
  // secrets
  TG_BOT_TOKEN: string;
  TG_WEBHOOK_SECRET: string;
  GH_DISPATCH_TOKEN: string;

  // vars
  GH_REPO: string;
  ALLOWED_CHAT_IDS: string;
}

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

    if (routed.kind === "missing_body") {
      await sendTelegramReply(env, chatId, msg.message_id, routed.usageHint);
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
