# bbl-ai-lab

텔레그램으로 던진 아이디어/할 일 메모를, Cloudflare Worker → GitHub Actions → Gemini CLI 파이프라인을 거쳐 자동으로 구체화된 GitHub Issue로 적재한다.

## 전체 흐름

```
[Telegram User]
  │ 텍스트 또는 /idea ...
  ▼
[Cloudflare Worker]      ← webhook
  │ secret 검증, chat_id 화이트리스트
  │ GitHub repository_dispatch 호출
  ▼
[GitHub Action: idea-elaborate.yml]
  │ Gemini OAuth 복원 → gemini-cli 설치
  │ skills/office-hours.SKILL.md 컨텍스트로 호출
  │ JSON 출력 파싱 → gh issue create
  │ Telegram 회신 (issue 링크)
  ▼
[GitHub Issue: 요약 / 문제 / 목표 / 접근 / 리스크 / Open Questions / Next Actions]
```

## 디렉토리

| 경로 | 설명 |
|------|------|
| `.github/workflows/idea-elaborate.yml` | repository_dispatch 트리거. workflow_dispatch로도 수동 실행 가능. |
| `scripts/elaborate.sh` | Gemini 호출 → JSON 파싱 → `gh issue create` → Telegram 회신 |
| `scripts/prompts/elaborate.md` | Gemini 시스템 프롬프트 + 출력 JSON 스키마 |
| `skills/office-hours.SKILL.md` | Brainstorming 스킬 (gstack/office-hours 출처). Gemini에 컨텍스트로 첨부 |
| `worker/` | Cloudflare Worker (텔레그램 webhook 수신) |

## 설치 / 운영 가이드

### 1. Telegram 봇 발급

1. `@BotFather`에서 `/newbot` → 봇 토큰 확보 (`TG_BOT_TOKEN`)
2. `@userinfobot`에 메시지 보내 본인 chat_id 확인 (`ALLOWED_CHAT_IDS`에 들어갈 값)
3. (선택) BotFather에서 `/setcommands`로 커맨드 등록:
   ```
   idea - 아이디어를 GitHub Issue로 정리
   ```

### 2. GitHub Secrets / Variables

레포 Settings → Secrets and variables → Actions:

**Secrets**

| 이름 | 값 |
|------|-----|
| `GEMINI_OAUTH_CREDS` | `~/.gemini/oauth_creds.json`을 base64 인코딩한 문자열 (`base64 -i ~/.gemini/oauth_creds.json`) |
| `GEMINI_GOOGLE_EMAIL` | Gemini OAuth가 연결된 구글 계정 이메일 |
| `TG_BOT_TOKEN` | 텔레그램 봇 토큰 (회신용) |

**Variables (선택)**

| 이름 | 기본값 | 비고 |
|------|--------|------|
| `GEMINI_MODEL` | `gemini-2.5-pro` | 다른 모델로 바꿀 때만 |

> `culcom-routines`에서 이미 같은 OAuth를 사용 중이라면 동일 secret을 재사용하면 된다.

### 3. GitHub Personal Access Token (Cloudflare Worker용)

레포에 `repository_dispatch`만 호출할 fine-grained PAT를 만든다:

- Repository access: 이 레포 1개만
- Permissions → Repository → **Contents: Read-only**, **Metadata: Read-only**
- (`repository_dispatch`는 Contents: Read 권한이면 충분)

PAT 값을 `GH_DISPATCH_TOKEN`으로 Cloudflare에 저장 (다음 단계).

### 4. Cloudflare Worker 배포

```bash
cd worker
npm install
npx wrangler login
# 시크릿 주입
npx wrangler secret put TG_BOT_TOKEN
npx wrangler secret put TG_WEBHOOK_SECRET     # openssl rand -hex 32 같은 임의 문자열
npx wrangler secret put GH_DISPATCH_TOKEN     # 위에서 만든 PAT
# wrangler.toml 의 GH_REPO, ALLOWED_CHAT_IDS 값 본인 것으로 수정
npx wrangler deploy
```

배포 후 Worker URL 확보 (`https://tg-idea-bridge.<account>.workers.dev`).

### 5. Telegram setWebhook

```bash
curl -X POST "https://api.telegram.org/bot<TG_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://tg-idea-bridge.<account>.workers.dev/tg-webhook",
    "secret_token": "<TG_WEBHOOK_SECRET 와 동일한 값>",
    "allowed_updates": ["message"]
  }'
```

확인: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`

### 6. E2E 검증

| 단계 | 명령 / 액션 | 기대 결과 |
|------|------------|-----------|
| Action 단독 | GitHub Actions UI → Idea Elaborate → Run workflow → text 입력 | Issue 생성됨 |
| Worker 단독 | `curl -X POST $WORKER_URL/tg-webhook -H "X-Telegram-Bot-Api-Secret-Token: $SECRET" -H 'Content-Type: application/json' -d '{"message":{"chat":{"id":<YOUR_ID>},"from":{"id":<YOUR_ID>},"text":"테스트","message_id":1,"date":'$(date +%s)'}}'` | repository_dispatch 트리거되고 Action 실행 |
| 화이트리스트 | 다른 chat_id로 같은 요청 | Action 미트리거, 200 무응답 |
| Telegram E2E | 봇에 "아이디어 …" 전송 | "접수 완료" 회신 → 1~2분 내 Issue 링크 회신 |

## 보안 메모

- `TG_WEBHOOK_SECRET`은 Worker와 setWebhook 양쪽에 같은 값을 넣어야 한다.
- `ALLOWED_CHAT_IDS`가 비어 있으면 모든 발신자가 통과하므로, 운영 시 반드시 본인 chat_id로 채울 것.
- `GH_DISPATCH_TOKEN`은 fine-grained PAT, 단일 레포 + 최소 권한.
- Worker에 들어오는 모든 요청은 401/200 둘 중 하나만 반환 (재시도 폭주 방지).

## 향후 확장

- 보강 루프 워크플로우 (`needs-clarification` 라벨 + 코멘트 → 본문 자동 업데이트)
- 채택된 Issue를 markdown 파일로 git 아카이빙
- 음성 메시지 → Whisper 변환 → 동일 파이프라인
- 다중 brainstorm 스킬 자동 라우팅 (스킬 인덱스로 1차 호출 → 선택된 스킬로 2차 호출)
