# bbl-ai-lab

아이디어 한 줄을 던지면 GitHub Issue → grilling 라운드 → plan 문서까지 굴러가는 **자동화 허브**.
트리거 표면은 세 가지(Telegram 메시지, 이슈 코멘트, PR)이고, 실행은 전부 GitHub Actions 안에서 Gemini CLI가 맡는다.
여기에 사람이 프롬프트를 넣지 않아도 도는 **자율 루프(autonomous loop)** 레이어가 얹혀 있다.

에이전트가 이 저장소를 수정할 때는 [AGENTS.md](AGENTS.md)를 먼저 읽는다.

## 등록된 자동화

| 트리거 | 자동화 | 결과 | 상세 |
|--------|--------|------|------|
| Telegram `/idea`, `/todo` | `idea-elaborate` | 아이디어를 구체화한 GitHub Issue 생성 (`idea` 라벨) | [docs/idea-elaborate.md](docs/idea-elaborate.md) |
| 이슈 코멘트 `/grill [focus]` | `idea-grill-followup` | 이슈 본문 in-place 정제 + Open Questions 축소, 완료 시 `grilled` 라벨 | [docs/plans/README.md](docs/plans/README.md#라이프사이클) |
| `docs/plans/**` 변경 PR | `plan-link-back` | 연결 이슈에 코멘트 + `has-plan` 라벨, `status: shipped`면 close | [docs/plans/README.md](docs/plans/README.md#자동-link-back) |
| 스케줄 (`/loop`) | Daily Triage | `STATE.md`에 findings 기록 (L1 report-only) | [LOOP.md](LOOP.md) |

Telegram 명령어만 [worker/src/flows.ts](worker/src/flows.ts) manifest에 등록된다. 이슈/PR 트리거는 워크플로우 자신이 `on:` 으로 선언하고, 스케줄 루프는 [LOOP.md](LOOP.md)가 manifest다.

> 새 Telegram flow를 추가하면 이 표에 한 줄, `docs/<flow>-<action>.md`에 상세 문서, `knowledge/flows/<flow>-<action>.md`에 OKF concept를 더한다.

## 아키텍처

```
[Telegram]  /idea <본문>
   │
   ▼
[Cloudflare Worker: tg-automation-bridge]
   │  X-Telegram-Bot-Api-Secret-Token 검증 → ALLOWED_CHAT_IDS 화이트리스트
   │  worker/src/flows.ts manifest에서 command → eventType 매핑
   │  POST /repos/<owner>/<repo>/dispatches
   │
   ├──────────────┐
   ▼              │            [이슈 코멘트 /grill]      [PR: docs/plans/**]
[idea-elaborate]  │                     │                        │
   │              │                     ▼                        ▼
   │              │            [idea-grill-followup]      [plan-link-back]
   │              │                     │                        │
   │  Gemini OAuth 복원 → gemini-cli 설치 → prompt + skill 컨텍스트 합성
   │  gemini --yolo -m $GEMINI_MODEL → JSON 추출 → gh issue create/edit
   ▼              ▼                     ▼                        ▼
[GitHub Issue]  [Telegram 회신]   [Issue 본문 갱신]        [Issue 코멘트/라벨/close]
```

Worker는 들어오는 모든 요청에 401 또는 200만 반환한다 (텔레그램 재시도 폭주 방지). 헬스체크는 `GET /health`.

## 자율 루프 (`LOOP.md`)

Telegram flow와 달리 트리거가 사람이 아니라 스케줄인 실행 단위. Claude Code의 `/loop`이 엔진이고, `worker/src/flows.ts`에 항목을 만들지 않는다.

| 파일 | 역할 |
|------|------|
| [LOOP.md](LOOP.md) | 어떤 루프가 어떤 주기·readiness level로 도는지의 단일 진실원 |
| [STATE.md](STATE.md) | 루프 state spine. 매 실행 시작에 읽고 끝에 쓴다 (High Priority / Watch List / Recent Noise) |
| [loop-constraints.md](loop-constraints.md) | 매 실행마다 읽는 **binding** 규칙 |
| [docs/safety.md](docs/safety.md) | 경로 denylist. 여기 걸리면 편집 대신 escalate |
| [loop-budget.md](loop-budget.md) | 일일 실행/토큰/서브에이전트 상한과 kill switch |
| [loop-run-log.md](loop-run-log.md) | 실행 1건당 1 entry. 30일 지난 항목은 prune |

현재 등록된 루프는 Daily Triage 하나이고 **L1 (report-only)** — 관측하고 `STATE.md`에 쓸 뿐 아무것도 고치지 않는다. 구현자는 자기 작업을 done으로 표시하지 않고, `goal-verifier` 또는 `.claude/agents/loop-verifier.md`가 판정한다.

```bash
npx @cobusgreyling/loop audit .
```

루프 skill은 `.claude/skills/`에 실제 디렉터리로 산다 (`loop-constraints`, `loop-budget`, `loop-intake`, `loop-triage`, `goal-scoper`, `goal-verifier`). `.agents/skills/` symlink가 아닌 이유는 `skills-lock.json`이 외부 installer가 설치한 skill만 추적하기 때문이다.

## 계획 관리 (`docs/plans/`)

idea 이슈가 "무엇·왜"라면 `docs/plans/<issue#>-<slug>.md`는 "어떻게·언제·누가"다. plan 작성은 GHA가 아니라 사람이 클로드 데스크탑에서 한다.

```
/idea → [idea-elaborate] → Issue
              │
              ├── 코멘트 /grill → [idea-grill-followup] → 본문 정제 (반복 가능)
              │                    needs_clarification=false 도달 시 grilled 라벨
              ▼
   (수동) docs/plans/<#>-<slug>.md 작성 → plan/<#>-<slug> branch → PR
              │
              ▼
   [plan-link-back] → 이슈 코멘트 + has-plan 라벨 + (shipped면) close
```

frontmatter 스키마, status 전환 규칙, PR 규칙, CONTEXT.md/ADR 핸드오프는 [docs/plans/README.md](docs/plans/README.md) 참고. PR 템플릿은 `.github/PULL_REQUEST_TEMPLATE/plan.md` (`?template=plan.md`).

## 문서 레이어

같은 사실을 세 군데 두지 않는다. 대상 독자로 나뉜다.

| 위치 | 독자 | 내용 |
|------|------|------|
| `README.md`, `docs/` | 사람 | 운영 모델, 셋업, flow별 상세 |
| [CONTEXT.md](CONTEXT.md) | 사람 + 에이전트 | 프로젝트 고유 용어집. 동의어는 `_Avoid_`로 컷 |
| [AGENTS.md](AGENTS.md) | 에이전트 | flow registry / loop / 문서 / 안전 규칙과 검증 명령 |
| [knowledge/](knowledge/) | 에이전트 | Open Knowledge Format 번들. YAML frontmatter + concept 간 링크 |

`knowledge/`는 README 사본이 아니라 에이전트가 개념과 flow 관계를 순회하는 계층이다. 새 flow나 load-bearing 개념이 생기면 `knowledge/flows/`, `knowledge/concepts/`, `knowledge/log.md`를 함께 갱신한다.

## 스킬

두 종류가 섞여 있다. 소유자가 다르니 구분한다.

| 위치 | 소유 | 용도 |
|------|------|------|
| [skills/](skills/) | 이 repo | GitHub Action 안에서 Gemini CLI에 attach하는 컨텍스트 파일 (`*.SKILL.md`). 현재 `product-brainstorming.SKILL.md` 하나 |
| `.agents/skills/` + [skills-lock.json](skills-lock.json) | 외부 installer | 설치된 agent skill 74개 (marketingskills 40, baoyu-skills 19, mattpocock/skills 14, huashu-design 1). 손으로 고치지 않는다 |
| `.claude/skills/` | 혼합 | 대부분 `.agents/skills/`로의 symlink. 루프 skill 6개만 실제 디렉터리 |

## 운영 repo

Hermes 원격 운영 runbook, ComfyUI 서비스 운영, host 스크립트 같은 실작업은 이 hub가 아니라 별도 운영 repo가 소유한다. submodule이 아니라 **manifest + 로컬 클론**이다. 하위 repo에 커밋이 생겨도 hub에 포인터 커밋을 만들 필요가 없다.

```bash
bash ops/repo-sync.sh          # 미설치 경로만 클론
bash ops/repo-sync.sh --list   # manifest 검증 (name/url/path/branch 누락 시 fail)
```

| path | repo |
| --- | --- |
| `hermes-workspace/` | [BoBeenLee/hermes-workspace](https://github.com/BoBeenLee/hermes-workspace) |
| `ops/remote-comfyui/` | [BoBeenLee/remote-comfyui](https://github.com/BoBeenLee/remote-comfyui) |
| `ops/openhuman-altalt-proxy/` | [BoBeenLee/openhuman-altalt-proxy](https://github.com/BoBeenLee/openhuman-altalt-proxy) |
| `ops/openmontage/` | [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) (업스트림, AGPL-3.0) |

URL과 브랜치의 단일 진실원은 [ops/repos.md](ops/repos.md) frontmatter다. 운영 repo를 추가하면 이 파일과 `.gitignore`를 **함께** 고친다. `projects/` 아래는 손으로 고치지 않는다 — 아래 참조.

`ops/openmontage/` 만 내 소유가 아닌 업스트림 도구다. `repo-sync.sh` 는 클론까지만 하므로, 그 repo 안에서 `make setup` 을 한 번 더 돌려야 쓸 수 있다.

DGX Spark 작업은 종류에 상관없이 `hermes-workspace/knowledge/runbooks/dgx-spark-remote-access.md`의 DGX Doc Map에서 시작한다.

| 대상 | owner |
| --- | --- |
| 호스트/OS, SSH·Tailscale, 원격 데스크톱, 종료, DGX Dashboard, 로컬 LLM 서비스 | `hermes-workspace` → `knowledge/runbooks/dgx-spark-remote-access.md` |
| ComfyUI 서비스 내부, 모델 디렉터리, `comfyops` 계정, ops CLI | `ops/remote-comfyui` → `references/dgx-comfyui.md` |
| ComfyUI 워크플로, 모델 권고, 실행 산출물 | `ops/remote-comfyui` → `docs/`, `knowledge/` |

## 프로젝트 repo

카테고리별로 **지식을 축적하고 그 지식으로 결과물을 만드는** repo. 설치 방식은 운영 repo와 같고(`ops/repos.md` manifest + `repo-sync.sh`) 소유 대상만 다르다 — 운영 repo는 원격 호스트의 운영을, 프로젝트 repo는 한 카테고리의 축적물을 소유한다. Telegram/Actions flow가 아니므로 `worker/src/flows.ts`에는 등록하지 않는다.

| path | repo | 축적층 (남는 것) | 산출층 (건별로 소멸) | 작업 규칙 |
| --- | --- | --- | --- | --- |
| `projects/games/` | [BoBeenLee/games](https://github.com/BoBeenLee/games) | `skills/party-guide/references/`, `roster.md`, `builds.md` | `guide.md`, `party-candidates.md` | `skills/party-guide/SKILL.md` |
| `projects/travel/` | [BoBeenLee/travel](https://github.com/BoBeenLee/travel) | `knowledge/` | `trips/<여행>/` | `CLAUDE.md` |
| `projects/finance/` | [BoBeenLee/finance](https://github.com/BoBeenLee/finance) | `knowledge/` (숫자는 `rules.yaml` 한 곳) | `guides/` | `CLAUDE.md` |
| `projects/music/` | [BoBeenLee/music](https://github.com/BoBeenLee/music) | `research/`, `craft/` | `runs/<날짜>-<slug>/` | `AGENTS.md` |
| `projects/shopping/` | [BoBeenLee/shopping](https://github.com/BoBeenLee/shopping) | `skills/smart-shopping/` | 건별 구매 판단 | `skills/smart-shopping/SKILL.md` |
| `projects/hiking/` | [BoBeenLee/hiking](https://github.com/BoBeenLee/hiking) | `knowledge/` | `hikes/<날짜>-<산>/` | `CLAUDE.md` |

두 층을 **디렉터리로 가른다.** 축적층은 카테고리가 살아 있는 한 남고, 산출층은 건이 끝나면 참조 기록으로만 남는다. 섞으면 다음 건이 빈 화면에서 시작하거나, 지난 건의 상황 판단이 지식으로 승격돼 버린다.

여섯 다 **private**다. `games`/`travel`/`finance`는 계정 로스터·여행 일정·재무 프로필 같은 개인 데이터를 이미 담고 있고, `music`은 생성곡·가사·취향이, `shopping`은 구매 이력·예산·사이즈가, `hiking`은 GPS 경로·체력 수치·장비 이력이 쌓이면 개인 데이터가 된다. 클론에 `gh auth` 세션이나 `GIT_TOKEN=<pat>`이 필요하다.

각 repo가 자기 구조·규율·검증 명령의 단일 진실원이다. hub는 URL과 브랜치만 소유하고 내용은 추적하지 않는다.

### 조사 방법은 repo 사이에서 이식한다

hub가 공용 조사 프레임워크를 소유하지 않는다. 방법이 필요한 repo가 **이미 방법을 가진 repo에서 가져다 자기 도메인에 맞게 고친다.** `hiking`이 `travel`의 조사 프로토콜(계절 게이트 → 공식 1차 출처 → 영상 전수조사 → stale 게이트 → 3곳 라우팅 → 결정 큐)과 스크립트 3종을 이식한 것이 첫 사례다.

이식이 복사보다 나은 이유는 **실패 기록이 같이 온다**는 점이다. `travel`이 "표본 30편으로 결론의 강도가 표본을 넘었다"고 적어 둔 덕분에 `hiking`이 같은 실패를 반복하지 않았다. 대신 도메인 차이는 이식하면서 갈린다 — 여행은 계절이, 등산은 들머리가 강한 신호다.

포크가 아니라 이식이므로 **원본과 동기화되지 않는다.** 이식본이 개선되어도 원본은 모른다. 그 대가로 각 repo가 자기 도메인에 맞게 자유롭게 갈라질 수 있다.

### 프로젝트 repo 추가 (자동 등록)

`projects/` 아래는 manifest도 `.gitignore`도 손으로 고치지 않는다. repo를 만들고 origin을 붙인 뒤 sync를 한 번 돌리면 끝이다.

```bash
git -C projects/<name> remote add origin https://github.com/BoBeenLee/<name>.git
bash ops/repo-sync.sh
```

`repo-sync.sh`가 `projects/*/` 를 훑어 manifest에 없는 클론을 찾고, 그 repo의 origin URL과 기본 브랜치를 읽어 [ops/repos.md](ops/repos.md) frontmatter에 등록한다. 이미 등록된 건 건드리지 않고, origin이 없는 디렉터리는 경고만 하고 넘어간다. `.gitignore`는 `/projects/*/` glob이라 이미 덮고 있다.

이 자동 등록을 넣은 이유: 사람이 잊는 쪽은 클론이 아니라 등록이다. 새 머신에서 클론이 빠지는 사고는 manifest를 못 고친 데서 시작하는데, 그 순간은 repo를 **만든** 머신에서 일어나므로 등록이 클론과 같은 명령에 묶여 있어야 한다.

## 디렉토리 구조

```
.
├── AGENTS.md                        ← 에이전트 규칙 (flow registry / loop / 안전)
├── CONTEXT.md                       ← 프로젝트 용어집
├── LOOP.md  STATE.md                ← 루프 manifest / 루프 상태
├── loop-constraints.md              ← 루프 binding 규칙
├── loop-budget.md  loop-run-log.md  ← 루프 예산 / 실행 로그
├── skills-lock.json                 ← 설치된 agent skill lockfile (외부 installer 소유)
├── .github/
│   ├── workflows/
│   │   ├── idea-elaborate.yml       ←   repository_dispatch: idea-submitted
│   │   ├── idea-grill-followup.yml  ←   issue_comment: /grill
│   │   └── plan-link-back.yml       ←   pull_request_target: docs/plans/**
│   └── PULL_REQUEST_TEMPLATE/plan.md
├── worker/                          ← Cloudflare Worker (Telegram 라우터)
│   ├── src/flows.ts                 ←   flow manifest가 단일 진실원
│   ├── src/index.ts                 ←   manifest를 읽어 webhook 라우팅
│   ├── scripts/check-flows.mjs      ←   manifest ↔ adapter 파일/dispatch type 검증
│   └── wrangler.toml
├── scripts/
│   ├── idea-elaborate.sh            ← Gemini 호출 → gh issue create
│   ├── idea-grill.sh                ← 코멘트 수집 → Gemini → 본문 갱신
│   ├── _idea_grill_body.py          ←   grill 본문 마크다운 조작 (idea-grill.sh 전용)
│   ├── fetch-url-content.py         ←   본문 속 URL 내용 추출 (yt-dlp / trafilatura)
│   └── prompts/<flow>-<action>.md   ← Gemini 시스템 프롬프트
├── skills/*.SKILL.md                ← Gemini에 attach할 skill 컨텍스트
├── .agents/skills/                  ← 외부 installer가 설치한 agent skill
├── .claude/
│   ├── agents/loop-verifier.md      ← 루프 결과 판정 에이전트
│   └── skills/                      ← 루프 skill(실물) + .agents/skills symlink
├── knowledge/                       ← OKF 지식 번들 (concepts / flows / playbooks)
├── docs/
│   ├── <flow>-<action>.md           ← flow별 상세 문서
│   ├── safety.md                    ← 루프 denylist
│   └── plans/<issue#>-<slug>.md     ← 계획 문서
├── ops/
│   ├── repos.md                     ← 운영·프로젝트 repo manifest (단일 진실원)
│   ├── repo-sync.sh                 ←   미등록 projects/* 자동 등록 후 미설치 repo만 클론
│   ├── repo-sync.test.sh            ←   자동 등록 self-check (임시 디렉터리)
│   ├── remote-comfyui/              ←   clone, git 미추적
│   └── openhuman-altalt-proxy/      ←   clone, git 미추적
├── projects/                        ← 카테고리별 지식·산출 repo (clone, git 미추적)
│   ├── games/    travel/    shopping/
│   └── finance/  music/    hiking/
└── hermes-workspace/                ← clone, git 미추적
```

## 명명 규칙 (prefix)

새 Telegram 자동화를 추가할 때 모든 산출물이 같은 `<flow>` prefix를 공유하도록 한다. 예: `idea-elaborate`, `meeting-summarize`, `pr-review`.

| 위치 | 패턴 | 예시 |
|------|------|------|
| GitHub Actions workflow | `.github/workflows/<flow>-<action>.yml` | `idea-elaborate.yml` |
| 실행 스크립트 | `scripts/<flow>-<action>.sh` | `idea-elaborate.sh` |
| Gemini 프롬프트 | `scripts/prompts/<flow>-<action>.md` | `idea-elaborate.md` |
| repository_dispatch event_type | `<flow>-<action>` | 신규는 `<flow>-<action>` / `idea-submitted`는 유일하게 허용된 legacy |
| Worker 명령어 등록 | `worker/src/flows.ts` manifest | `commands: ["idea","todo"]` |
| 상세 문서 | `docs/<flow>-<action>.md` | `docs/idea-elaborate.md` |
| OKF concept | `knowledge/flows/<flow>-<action>.md` | `knowledge/flows/idea-elaborate.md` |

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
5. **상세 문서 작성**: `docs/meeting-summarize.md` (flow 개요, 트리거, 환경변수, 출력, 검증). 위 [등록된 자동화](#등록된-자동화) 표에 한 줄 추가.
6. **OKF concept 작성**: `knowledge/flows/meeting-summarize.md`에 `type: Automation Flow` frontmatter와 adapter 링크를 추가.
7. **검증**:
   ```bash
   cd worker && npm run typecheck
   ```
   TypeScript와 함께 manifest가 가리키는 workflow/script/prompt/docs 파일 존재 여부, workflow `repository_dispatch.types`, legacy event type 예외를 검사한다.
8. **Worker 재배포**: `cd worker && npx wrangler deploy`.
9. **(선택) BotFather `/setcommands`** 에 새 명령어 등록.

스케줄로 도는 자율 루프는 flow가 아니다. `worker/src/flows.ts`에 넣지 말고 `LOOP.md`에 등록한다.

## 공통 인프라 셋업

flow에 무관하게 한 번만 하면 되는 셋업. flow별 추가 셋업은 각 `docs/<flow>-<action>.md` 참고.

### 1. Telegram 봇 발급

1. `@BotFather`에서 `/newbot` → 봇 토큰 확보 (`TG_BOT_TOKEN`)
2. `@userinfobot`에 메시지 보내 본인 chat_id 확인
3. (선택) BotFather에서 `/setcommands` 또는 [setMyCommands API](https://core.telegram.org/bots/api#setmycommands)로 명령어 등록

### 2. GitHub PAT (Cloudflare Worker용)

`repository_dispatch`만 호출할 fine-grained PAT를 만들어 Cloudflare에 `GH_DISPATCH_TOKEN`으로 등록.

- Repository access: 이 레포 1개만
- Permissions → Repository → **Contents: Read and write**, **Metadata: Read-only**

> `POST /repos/{owner}/{repo}/dispatches`는 fine-grained PAT에서 Contents **write** 를 요구한다 ([GitHub 문서](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens#repository-permissions-for-contents)). read-only로 만들면 Worker가 403을 받고 텔레그램에 "GitHub 트리거 실패 (403)"으로 회신한다.

### 3. Cloudflare Worker 배포

```bash
cd worker
npm install
npx wrangler login
```

```bash
cd worker && npx wrangler secret put TG_BOT_TOKEN
```

```bash
cd worker && npx wrangler secret put TG_WEBHOOK_SECRET
```

```bash
cd worker && npx wrangler secret put GH_DISPATCH_TOKEN
```

`TG_WEBHOOK_SECRET`은 `openssl rand -hex 32` 같은 임의 문자열. `wrangler.toml`의 `GH_REPO`, `ALLOWED_CHAT_IDS`를 본인 값으로 고친 뒤 배포한다.

```bash
cd worker && npx wrangler deploy
```

배포 후 Worker URL 확인 (`https://tg-automation-bridge.<account>.workers.dev`).

### 4. Telegram setWebhook

```bash
TOKEN="<TG_BOT_TOKEN>"; WORKER_URL="https://tg-automation-bridge.<account>.workers.dev"; SECRET="<TG_WEBHOOK_SECRET 와 동일 값>"; curl -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" -H "Content-Type: application/json" -d "$(jq -n --arg url "${WORKER_URL}/tg-webhook" --arg secret "$SECRET" '{ url: $url, secret_token: $secret, allowed_updates: ["message"], drop_pending_updates: true }')"
```

확인:

```bash
curl -s "https://api.telegram.org/bot<TG_BOT_TOKEN>/getWebhookInfo" | jq
```

### 5. GitHub Secrets / Variables

| 이름 | 종류 | 필수 | 사용처 |
|------|------|------|--------|
| `GEMINI_OAUTH_CREDS` | secret | ✅ | `~/.gemini/oauth_creds.json`을 base64 인코딩한 값. `idea-elaborate`, `idea-grill-followup` |
| `GEMINI_GOOGLE_EMAIL` | secret | ✅ | Gemini OAuth 계정 이메일 |
| `TG_BOT_TOKEN` | secret | ✅ | Action에서 텔레그램 회신 |
| `ALLOWED_GITHUB_LOGINS` | secret | 선택 | `/grill` 트리거 화이트리스트. 비우면 repo write 권한 보유자로 폴백 |
| `GEMINI_MODEL` | variable | 선택 | 기본 `gemini-3-pro-preview`. 옵션은 [docs/idea-elaborate.md](docs/idea-elaborate.md#gemini-모델-옵션) |

`GITHUB_TOKEN`은 Actions가 자동 주입하므로 등록하지 않는다.

## 보안 메모

- `TG_WEBHOOK_SECRET`은 Worker와 setWebhook 양쪽에 같은 값을 넣어야 한다.
- `ALLOWED_CHAT_IDS`가 비어 있으면 모든 발신자가 통과하므로, 운영 시 반드시 본인 chat_id로 채울 것.
- `GH_DISPATCH_TOKEN`은 fine-grained PAT, 단일 레포 + 최소 권한 (Contents write / Metadata read).
- `/grill`은 opt-in 트리거다. 매치 안 되는 코멘트는 비용 0으로 컷하고, 실제 실행은 `idea` 라벨 + 비봇 + 첫 줄 정규식 + actor 화이트리스트를 모두 통과해야 한다.
- `plan-link-back`은 `pull_request_target`을 쓴다. PR head 코드를 실행하지 않고 frontmatter만 파싱하는 현재 형태를 유지할 것.
- 자율 루프가 건드리면 안 되는 경로는 [docs/safety.md](docs/safety.md)가 binding denylist다. 루프는 denylist에 걸리면 편집 대신 `STATE.md`에 `needs-human`으로 escalate 한다.
- `worker/wrangler.toml`에는 시크릿을 넣지 않는다. `wrangler secret put`만 사용.
- 새 flow 추가 시 trigger 가능한 사용자 범위(default = 화이트리스트)와 GitHub Action이 작성/수정하는 자원 범위를 한 번 더 점검할 것.
