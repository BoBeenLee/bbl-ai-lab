# bbl-ai-lab

텔레그램 메시지를 입구로, Cloudflare Worker가 명령어별로 라우팅해 GitHub Actions를 트리거하고, 그 안에서 Gemini CLI가 산출물(Issue, 요약, 보고서 등)을 만들어 회신하는 **여러 자동화 flow를 prefix 단위로 쌓는 hub**.

## 등록된 flow

| 명령어 | flow | 결과 | 상세 |
|--------|------|------|------|
| `/idea`, `/todo` | `idea` | 아이디어를 구체화한 GitHub Issue 생성 | [docs/idea-elaborate.md](docs/idea-elaborate.md) |

> 새 flow를 추가하면 이 표에 한 줄, 그리고 `docs/<flow>-<action>.md`에 상세 문서를 더한다.

에이전트가 이 저장소를 수정할 때는 [AGENTS.md](AGENTS.md)의 flow registry 규칙을 먼저 따른다.

## OKF 지식 번들 (`knowledge/`)

[knowledge/](knowledge/)는 이 저장소의 Open Knowledge Format 지식 번들이다. `README.md`와 `docs/`는 사람용 운영 문서로 유지하고, `knowledge/`는 에이전트가 개념과 flow 관계를 안정적으로 순회할 수 있는 Markdown + YAML frontmatter 계층으로 관리한다.

새 flow나 load-bearing 개념을 추가하면 기존 운영 문서와 함께 다음도 갱신한다:

- `knowledge/flows/<flow>-<action>.md` — flow concept 문서
- `knowledge/concepts/<concept>.md` — 새 프로젝트 개념이 생긴 경우
- `knowledge/log.md` — OKF bundle의 의미 있는 변경 이력

## 운영 workspace submodule

Hermes 원격 운영 runbook, host 진단/설치 스크립트, Discord/Camofox helper, 운영 artifact는 이 hub repo가 아니라 [hermes-workspace](hermes-workspace/) submodule에서 관리한다. 이 저장소는 Telegram → Worker → GitHub Actions automation flow를 owner로 유지하고, Hermes 관련 실작업은 `hermes-workspace` repo에서 변경한다.

## 계획 관리 (`docs/plans/`)

idea 이슈가 만들어진 다음 단계인 **계획 명세화**는 클로드 데스크탑/로컬에서 사람이 직접 진행한다. 산출물은 `docs/plans/<issue#>-<slug>.md` 로 PR 적재되고, 보강이 필요하면 같은 파일에 새 PR (revision) 을 올린다. `.github/workflows/plan-link-back.yml` 가 PR open/merge 시 연결 이슈에 자동 코멘트와 `has-plan` 라벨을 부착하고, `status: shipped` 면 이슈를 close 한다.

```
/idea → idea 이슈 생성 → (수동) 클로드 데스크탑에서 plan draft → docs/plans/ PR
                                                       │
                       ┌───────────── plan-link-back (자동) ─────────────┐
                       ▼                                                  ▼
                이슈 코멘트                                       has-plan 라벨 / close
```

자세한 운영 가이드와 template, status 전환 규칙은 [docs/plans/README.md](docs/plans/README.md) 참고.

## 공통 아키텍처

```
[Telegram User]
  │ /<command> <본문>
  ▼
[Cloudflare Worker (tg-automation-bridge)]
  │ secret 검증, chat_id 화이트리스트
  │ worker/src/flows.ts manifest에서 명령어 → eventType 매핑
  │ GitHub repository_dispatch (event_type: <flow>-<action>)
  ▼
[GitHub Action: <flow>-<action>.yml]
  │ Gemini OAuth 복원 → gemini-cli 설치
  │ skills/*.SKILL.md 컨텍스트로 호출
  │ 산출물 생성 (Issue 등) → Telegram 회신
```

## 디렉토리 구조

```
.
├── .github/workflows/
│   └── <flow>-<action>.yml          ← flow별 워크플로우
├── scripts/
│   ├── <flow>-<action>.sh           ← 본 처리 스크립트
│   └── prompts/
│       └── <flow>-<action>.md       ← Gemini 시스템 프롬프트
├── skills/
│   └── *.SKILL.md                   ← Gemini에 attach할 skill 컨텍스트
├── knowledge/                       ← OKF 지식 번들 (agent-consumable concepts)
├── hermes-workspace/                ← Hermes 운영 repo submodule
├── worker/                          ← Cloudflare Worker (멀티 flow 라우터)
│   ├── src/flows.ts                 ←   flow manifest가 단일 진실원
│   ├── src/index.ts                 ←   manifest를 읽어 Telegram webhook 라우팅
│   ├── scripts/check-flows.mjs      ←   manifest ↔ adapter 파일/dispatch type 검증
│   └── wrangler.toml
└── docs/
    └── <flow>-<action>.md           ← flow별 상세 문서
```

## 명명 규칙 (prefix)

새 자동화를 추가할 때 모든 산출물이 같은 `<flow>` prefix를 공유하도록 한다. 예: `idea-elaborate`, `meeting-summarize`, `pr-review`.

| 위치 | 패턴 | 예시 |
|------|------|------|
| GitHub Actions workflow | `.github/workflows/<flow>-<action>.yml` | `idea-elaborate.yml` |
| 실행 스크립트 | `scripts/<flow>-<action>.sh` | `idea-elaborate.sh` |
| Gemini 프롬프트 | `scripts/prompts/<flow>-<action>.md` | `idea-elaborate.md` |
| repository_dispatch event_type | `<flow>-<action>` | `idea-submitted` (legacy) / 신규는 `<flow>-<action>` |
| Worker 명령어 등록 | `worker/src/flows.ts` manifest | `commands: ["idea","todo"]` |
| 상세 문서 | `docs/<flow>-<action>.md` | `docs/idea-elaborate.md` |

## 새 flow 추가 가이드

1. **Flow manifest 등록**: `worker/src/flows.ts`에 한 항목 추가.
   ```ts
   {
     commands: ["meeting"],
     eventType: "meeting-summarize",
     usageHint: "예: /meeting <회의록 raw 텍스트>",
     ackText: "회의록 요약 시작.",
     workflow: ".github/workflows/meeting-summarize.yml",
     script: "scripts/meeting-summarize.sh",
     prompt: "scripts/prompts/meeting-summarize.md",
     docs: "docs/meeting-summarize.md",
   }
   ```
   subcommand flow는 `subcommands` 안에 action별 adapter 경로를 둔다. 예: `/recruit collect` → `eventType: "recruit-collect"`.
2. **Workflow 추가**: manifest의 `workflow` 경로에 파일을 만들고, 트리거를 `repository_dispatch.types: [meeting-summarize]`로 지정.
3. **스크립트 / 프롬프트 추가**: `scripts/meeting-summarize.sh`, `scripts/prompts/meeting-summarize.md`.
4. **(선택) skill 컨텍스트 추가**: `skills/<name>.SKILL.md`.
5. **상세 문서 작성**: `docs/meeting-summarize.md` (flow 개요, 트리거, 환경변수, 출력, 검증). 위 [등록된 flow](#등록된-flow) 표에 한 줄 추가.
6. **OKF concept 작성**: `knowledge/flows/meeting-summarize.md`에 `type: Automation Flow` frontmatter와 adapter 링크를 추가.
7. **검증**: `cd worker && npm run typecheck`. 이 명령은 TypeScript와 함께 manifest가 가리키는 workflow/script/prompt/docs 파일 존재 여부, workflow `repository_dispatch.types`, legacy event type 예외를 검사한다.
8. **Worker 재배포**: `cd worker && npx wrangler deploy`.
9. **(선택) BotFather `/setcommands`** 에 새 명령어 등록.

## 공통 인프라 셋업

flow에 무관하게 한 번만 하면 되는 셋업입니다. flow별 추가 셋업은 각 `docs/<flow>-<action>.md`를 참고하세요.

### 1. Telegram 봇 발급

1. `@BotFather`에서 `/newbot` → 봇 토큰 확보 (`TG_BOT_TOKEN`)
2. `@userinfobot`에 메시지 보내 본인 chat_id 확인
3. (선택) BotFather에서 `/setcommands` 또는 [setMyCommands API](https://core.telegram.org/bots/api#setmycommands)로 명령어 등록

### 2. GitHub PAT (Cloudflare Worker용)

`repository_dispatch`만 호출할 fine-grained PAT를 만들어 Cloudflare에 `GH_DISPATCH_TOKEN`으로 등록.

- Repository access: 이 레포 1개만
- Permissions → Repository → **Contents: Read-only**, **Metadata: Read-only**

### 3. Cloudflare Worker 배포

```bash
cd worker
npm install
npx wrangler login
# 시크릿 주입
npx wrangler secret put TG_BOT_TOKEN          # 텔레그램 봇 토큰
npx wrangler secret put TG_WEBHOOK_SECRET     # openssl rand -hex 32 같은 임의 문자열
npx wrangler secret put GH_DISPATCH_TOKEN     # 위에서 만든 PAT
# wrangler.toml 의 GH_REPO, ALLOWED_CHAT_IDS 본인 값으로 수정
npx wrangler deploy
```

배포 후 Worker URL 확인 (`https://tg-automation-bridge.<account>.workers.dev`).

### 4. Telegram setWebhook

```bash
TOKEN="<TG_BOT_TOKEN>"
WORKER_URL="https://tg-automation-bridge.<account>.workers.dev"
SECRET="<TG_WEBHOOK_SECRET 와 동일 값>"

curl -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg url "${WORKER_URL}/tg-webhook" \
    --arg secret "$SECRET" \
    '{ url: $url, secret_token: $secret, allowed_updates: ["message"], drop_pending_updates: true }')"
```

확인:
```bash
curl -s "https://api.telegram.org/bot${TOKEN}/getWebhookInfo" | jq
```

### 5. flow별 GitHub Secrets

각 flow가 요구하는 secret 목록은 `docs/<flow>-<action>.md`의 "환경변수 / 시크릿" 섹션을 참고. 모든 flow가 공통으로 필요로 하는 것:

| Secret | 용도 |
|--------|------|
| `TG_BOT_TOKEN` | Action에서 텔레그램 회신 시 사용 |

flow별 추가 secret(예: `GEMINI_OAUTH_CREDS`)은 해당 flow 문서 참고.

## 보안 메모

- `TG_WEBHOOK_SECRET`은 Worker와 setWebhook 양쪽에 같은 값을 넣어야 한다.
- `ALLOWED_CHAT_IDS`가 비어 있으면 모든 발신자가 통과하므로, 운영 시 반드시 본인 chat_id로 채울 것.
- `GH_DISPATCH_TOKEN`은 fine-grained PAT, 단일 레포 + 최소 권한.
- Worker에 들어오는 모든 요청은 401/200 둘 중 하나만 반환 (재시도 폭주 방지).
- 새 flow 추가 시 trigger 가능한 사용자 범위(default = 화이트리스트)와 GitHub Action이 작성/수정하는 자원 범위를 한 번 더 점검할 것.
