// Cloudflare Worker: Telegram webhook -> GitHub repository_dispatch
//
// 동작:
//   1) POST /tg-webhook (Telegram이 호출)
//   2) X-Telegram-Bot-Api-Secret-Token 헤더로 진위 검증
//   3) message.from.id 가 ALLOWED_CHAT_IDS 에 포함되는지 확인
//   4) repository_dispatch 호출 (event_type=idea-submitted)
//   5) 사용자에게 즉시 "처리 중" 회신 전송

interface Env {
  // secrets
  TG_BOT_TOKEN: string;
  TG_WEBHOOK_SECRET: string;
  GH_DISPATCH_TOKEN: string;

  // vars
  GH_REPO: string;
  ALLOWED_CHAT_IDS: string;
  DISPATCH_EVENT_TYPE: string;
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
      // 우리가 처리하지 않는 update 종류 (channel_post 등). 200으로 ack.
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
        // 조용히 무시 (응답은 200으로 — 텔레그램이 재시도하지 않게)
        return new Response("ok", { status: 200 });
      }
    }

    const text = (msg.text ?? msg.caption ?? "").trim();
    if (!text) {
      await sendTelegramReply(env, chatId, msg.message_id, "텍스트 메시지를 보내 주세요.");
      return new Response("ok", { status: 200 });
    }

    // /idea 접두사가 있으면 잘라낸다
    const ideaText = stripCommandPrefix(text);
    if (!ideaText) {
      await sendTelegramReply(env, chatId, msg.message_id, "예: /idea 텔레그램 봇으로 메모를 받아 GH Issue로 자동 정리");
      return new Response("ok", { status: 200 });
    }

    // 3) GitHub repository_dispatch 호출
    const dispatchResp = await dispatchToGitHub(env, {
      chat_id: chatId,
      message_id: msg.message_id,
      text: ideaText,
      submitted_at: new Date(msg.date * 1000).toISOString(),
    });

    if (!dispatchResp.ok) {
      const detail = await safeText(dispatchResp);
      console.error("dispatch failed", dispatchResp.status, detail);
      await sendTelegramReply(
        env,
        chatId,
        msg.message_id,
        `GitHub 트리거 실패 (${dispatchResp.status}). 잠시 후 다시 시도해 주세요.`,
      );
      return new Response("ok", { status: 200 });
    }

    // 4) 사용자에게 처리 중 안내
    await sendTelegramReply(
      env,
      chatId,
      msg.message_id,
      "아이디어 접수 완료. 1~2분 내에 Issue 링크를 회신합니다.",
    );

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

function stripCommandPrefix(text: string): string {
  // "/idea ...", "/idea@botname ..." 형태 처리
  const m = text.match(/^\/(?:idea|todo)(?:@[\w_]+)?(?:\s+|$)/i);
  if (!m) return text;
  return text.slice(m[0].length).trim();
}

async function dispatchToGitHub(
  env: Env,
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
      "User-Agent": "tg-idea-bridge",
    },
    body: JSON.stringify({
      event_type: env.DISPATCH_EVENT_TYPE || "idea-submitted",
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
