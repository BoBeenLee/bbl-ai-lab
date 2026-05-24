---
issue: 24
issue_url: https://github.com/BoBeenLee/bbl-ai-lab/issues/24
title: mattpocock/skills 기반 Grilling 플로우 도입
status: draft
owner: BoBeenLee
created: 2026-05-24
updated: 2026-05-24
revisions:
  - { date: 2026-05-24, pr: 0, note: "initial draft — 비동기 코멘트 grilling + CONTEXT.md/ADR 후보 누적" }
---

# Grilling 플로우 도입: 단발성 elaborate → 비동기 grilling 라운드

## Context

현재 `scripts/idea-elaborate.sh` 는 사용자의 짧은 텔레그램 메모를 Gemini에 한 번 던지고 그 결과를 그대로 GitHub Issue로 만든다. 프롬프트(`scripts/prompts/idea-elaborate.md` 36행)는 "원문이 모호해도 추측해서 채우되 추측한 부분은 open_questions 로 검증을 요청"하라고 지시한다 — 즉 모호함을 "그래도 한 번에 통과"시키는 쪽으로 편향되어 있다. 결과적으로 PRD 수준의 깊이가 부족하고, 도메인 언어가 글로 굳기 전에 plan 단계로 넘어가서 plan PR 단계에서 같은 질문을 다시 하게 된다.

mattpocock/skills 의 `grill-me` / `grill-with-docs` / `to-prd` 는 (1) 의사결정 트리의 각 가지를 끝까지 따라가는 1문항씩 질문, (2) CONTEXT.md / ADR 로 공유 언어를 즉시 결정화, (3) 그 결과를 PRD/이슈로 결정화 하는 패턴을 가지고 있다. 이 이슈는 이 철학을 우리 단발 GHA 아키텍처에 맞게 **비동기 이슈 코멘트 라운드**로 이식하는 것을 목표로 한다.

## Approach

세 갈래로 변경한다. (1) 1차 elaborate 프롬프트를 sparring partner 페르소나로 개편하고 JSON 스키마를 확장한다. (2) 이슈 코멘트를 트리거로 도는 **followup grilling 워크플로**를 신설해 다중 라운드를 지원한다. (3) grilling 과정에서 결정화되는 도메인 용어/하드-투-리버스 결정은 이슈 본문에 "글로사리 후보 / ADR 후보" 섹션으로 누적되며, plan PR 작성자가 같은 PR 안에서 `CONTEXT.md` 와 `docs/adr/000N-*.md` 를 같이 만든다.

핵심 설계 원칙:

- **단발 호출은 유지**한다. 라운드 사이의 상태는 GitHub Issue 본문/코멘트가 유일한 진실원이다 (Worker 에 상태 없음).
- **강도는 프롬프트 휴리스틱으로 자동**. 입력 길이·URL 유무·구체성 신호를 보고 LLM이 `grill_level ∈ {light, standard, deep}` 을 스스로 결정.
- **CONTEXT.md / ADR 자동 commit 안 함**. 후보를 이슈 본문에 누적시켜 plan PR 작성자가 검토/병합한다. 자동 PR 생성은 추후 별도 plan.
- **bot 폭주 차단**. followup 워크플로는 actor가 bot/Actions이거나 코멘트에 `[skip-grill]` 토큰이 있으면 즉시 종료. ALLOWED 화이트리스트 재사용.
- **`worker/src/index.ts` 미변경** (이슈 #24 본문의 "텔레그램에 /plan 명령어 추가하지 않는다" 비범위 정신 그대로).

### 1차 elaborate 프롬프트 개편 (`scripts/prompts/idea-elaborate.md`)

- 페르소나: "단편적 메모를 그대로 받아쓰는 어시스턴트" → **"기획의 구멍을 찾아내 끝까지 물고 늘어지는 적극적 스파링 파트너"**.
- "모호해도 추측해서 채우라" 규칙 삭제. 대신 **"추측이 필요한 핵심 결정은 채우지 말고 `open_questions`로 강제하라"**.
- 휴리스틱 가이드: 입력 < 200자 또는 동사/대상 사용자/성공 기준 중 하나라도 결락 → `grill_level: "deep"`, 5+ open_questions 필수. URL fetched content가 풍부하고 의도가 명확 → `light`, 1~3 questions.
- JSON 스키마에 추가 필드:
  - `grill_level: "light" | "standard" | "deep"`
  - `glossary_candidates: [{ term, proposed_definition, conflicts_with }]` — 사용된 도메인 용어 중 정의가 필요한 것
  - `adr_candidates: [{ title, why, alternatives }]` — 본문에서 발견된 hard-to-reverse 결정 (grill-with-docs ADR 3조건 충족 시만)
  - `next_grill_focus: string` — 다음 라운드에서 집중해야 할 영역 (예: "성공 지표 정의", "엣지 케이스")
- 도메인 언어 체크리스트를 system prompt에 명시 (오버로드된 용어 의심, 동의어 충돌, 약어, 함의된 actor).

### Followup grilling 스크립트/프롬프트 (`scripts/idea-grill.sh`, `scripts/prompts/idea-grill.md`)

- 입력: 이슈 번호, 새 코멘트 본문(또는 코멘트 ID).
- 동작: `gh issue view <#> --json body,comments` 로 전체 맥락 적재 → grill 프롬프트에 주입 → Gemini 호출 → JSON 반환.
- 출력 JSON 스키마:
  - `resolved_questions: [원래질문문자열]` — 이번 라운드에서 답이 들어온 것
  - `remaining_questions: [string]` — 여전히 미해소
  - `new_questions: [string]` — 답변을 따라가다 새로 떠오른 것
  - `glossary_diff: [{ term, before?, after, source_comment }]`
  - `adr_diff: [{ title, status: "proposed" | "accepted", body }]`
  - `updated_sections: { problem?, goal?, approach?, non_goals?, risks? }` — 답변으로 정제된 본문 섹션 (변경 있을 때만)
  - `round: integer` — 라운드 카운터 (`gh issue` 본문에서 파싱)
  - `needs_clarification: boolean` — 모든 가지가 정리되면 false
  - `round_summary: string` — 사용자에게 보낼 짧은 진행 요약
- 이슈 본문 갱신 로직 (스크립트가 `gh issue edit --body`):
  - "## 🔥 Grilling Rounds" 섹션 누적. 각 라운드는 `<details><summary>Round N (date) — needs_clarification: …</summary>` 안에 resolved/remaining/new + delta 섹션.
  - 본문 상단의 정식 섹션(요약/문제/목표/접근/리스크/Open Questions)은 `updated_sections` 와 `resolved/remaining` 으로 in-place 갱신.
  - "## 글로사리 후보 (CONTEXT.md 반영 예정)" / "## ADR 후보 (docs/adr/ 반영 예정)" 섹션 누적.
  - `needs_clarification == false` 면 `needs-clarification` 라벨 제거 + `grilled` 라벨 부여 + 본문 하단에 "✅ Grilling complete. 다음 단계: plan PR" 배너.
- Telegram 회신: 1차 elaborate와 동일하게 `TG_BOT_TOKEN`+`CHAT_ID` 있으면 `round_summary` + issue URL 발송. CHAT_ID 는 followup 단계에서는 알 수 없으므로 1차 이슈 생성 시 `<!-- chat_id: ... -->` 형태 HTML 코멘트로 본문에 박아두고 followup 스크립트가 파싱한다.

### Followup 워크플로 (`.github/workflows/idea-grill-followup.yml`)

- 트리거: `issue_comment` (types: `[created]`).
- Guard: 다음 중 하나면 즉시 종료
  - `github.event.issue.labels` 에 `idea` 또는 `needs-clarification` 없음
  - `github.event.comment.user.type == 'Bot'` 또는 actor 가 `github-actions[bot]`
  - 코멘트 본문에 `[skip-grill]` 토큰
  - actor 가 ALLOWED 화이트리스트 밖 (`secrets.ALLOWED_GITHUB_LOGINS` 신설, 콤마구분 — 비어있으면 issue author 만 허용)
- 단계: 기존 idea-elaborate.yml과 동일한 setup (Gemini OAuth 복원, Python deps, gemini CLI 설치) 후 `scripts/idea-grill.sh` 호출.
- 권한: `contents: read`, `issues: write` (본문/라벨/코멘트).

### 도메인 문서 통합 (CONTEXT.md, docs/adr/)

- 이슈 본문에 누적되는 "글로사리 후보" / "ADR 후보" 는 **자동으로 main에 반영되지 않는다**. plan PR 작성자가 같은 PR 안에서 수동으로 옮긴다.
- `docs/plans/_template.md` 에 두 섹션 신규:
  - `## Domain language updates` — 이 plan으로 인해 CONTEXT.md 에 추가/수정/충돌 해소되는 용어 표. 변경 없으면 명시적으로 "변경 없음".
  - `## ADR proposals` — 같이 PR 에 추가되는 `docs/adr/000N-<slug>.md` 항목 리스트 + 각 ADR의 3조건(hard-to-reverse / surprising / real trade-off) 자기검증 체크박스.
- `CONTEXT.md` 와 `docs/adr/` 디렉터리는 **이번 PR에서 생성하지 않음** (lazy). 첫 번째 plan PR이 첫 글로사리 항목/ADR을 추가하는 순간 생성. `docs/plans/README.md` 에 이 방침 한 줄 추가.
- `CONTEXT.md` 와 ADR 포맷은 mattpocock 의 `CONTEXT-FORMAT.md` / `ADR-FORMAT.md` 를 참고하되 한국어 작성. `docs/plans/README.md` 끝에 두 포맷의 핵심만 1쪽 가이드로 인라인.

### 1차 elaborate.sh 의 본문 렌더링 변경 (`scripts/idea-elaborate.sh`)

- JSON 새 필드(`grill_level`, `glossary_candidates`, `adr_candidates`, `next_grill_focus`)를 본문 머리/꼬리에 렌더링.
- 이슈 본문 최상단에 `<!-- bbl-grill-meta: round=1 chat_id=… msg_id=… grill_level=… -->` HTML 코멘트 박아 followup 이 파싱하게 함.
- "## Open Questions" 헤더 바로 위에 `> 🔥 Grilling round 1 — 이 질문들에 이슈 코멘트로 답하면 자동으로 다음 라운드가 돕니다. 라운드를 멈추려면 코멘트에 \`[skip-grill]\` 포함.` 안내.
- `needs_clarification == true` 일 때 라벨은 그대로 `needs-clarification` 유지(기존 동작과 호환).

## Critical files

| 경로 | 역할 | 신규/수정 |
|------|------|-----------|
| `scripts/prompts/idea-elaborate.md` | 1차 sparring 페르소나 + 확장 JSON 스키마 + 휴리스틱 가이드 | 수정 |
| `scripts/prompts/idea-grill.md` | followup 라운드 system prompt (이슈 본문 + 새 코멘트 → diff JSON) | 신규 |
| `scripts/idea-elaborate.sh` | 새 JSON 필드 렌더링, grill-meta HTML 코멘트 삽입 | 수정 |
| `scripts/idea-grill.sh` | followup 오케스트레이션 (이슈/코멘트 read → Gemini → 본문 갱신 → telegram 회신) | 신규 |
| `.github/workflows/idea-grill-followup.yml` | `issue_comment` 트리거 + guard + scripts/idea-grill.sh 실행 | 신규 |
| `docs/plans/_template.md` | Domain language updates / ADR proposals 섹션 | 수정 |
| `docs/plans/README.md` | grilling 라운드 → plan PR 핸드오프 설명, CONTEXT.md/ADR 작성 가이드 1쪽 | 수정 |
| `worker/src/index.ts` | — (변경 없음, 명시적으로 비범위) | — |
| `CONTEXT.md`, `docs/adr/` | 첫 plan PR이 lazy 생성 (이 PR에서는 안 만듦) | — |

기존 재사용 자산: `scripts/idea-elaborate.sh` 의 Gemini 호출/재시도/JSON 추출 블록(81~125행), `gh label create … || true` 패턴(178~181행), Telegram payload 조립(206~222행) — followup 스크립트도 동일 패턴 복붙 대신 공용 helper로 빼는 건 v2 과제로 둔다.

## Verification

| 단계 | 액션 | 기대 |
|------|------|------|
| 단위 | `IDEA_TEXT="텔레그램으로 잡 알람 받기"` 등 짧은 입력으로 `bash scripts/idea-elaborate.sh` 로컬 실행 | `grill_level: "deep"`, open_questions ≥ 5, glossary_candidates 1개 이상, needs-clarification 라벨 |
| 단위 | URL이 포함되고 의도 명확한 입력으로 동일 실행 | `grill_level: "light"`, open_questions ≤ 3 |
| 통합 | 실제 dispatch: `gh workflow run idea-elaborate.yml -f text="<vague>"` → 이슈 생성됨 확인 | grill-meta HTML 코멘트, Grilling round 1 배너, 글로사리/ADR 후보 섹션 모두 렌더 |
| 통합 | 생성된 이슈에 owner 계정으로 답변 코멘트 작성 | followup 워크플로 1회 트리거 → round 2 details 추가, 본문 정식 섹션 in-place 갱신 |
| 통합 | 동일 이슈에 `[skip-grill]` 포함 코멘트 작성 | followup 즉시 종료 (workflow run 은 success, no edits) |
| 통합 | bot 계정 코멘트 또는 화이트리스트 밖 user 코멘트 | guard에서 skip |
| 통합 | grilling이 충분히 진행되어 `needs_clarification: false` 출력 | `needs-clarification` 제거, `grilled` 라벨 부여, ✅ 배너 추가 |
| 회귀 | 기존 plan-link-back.yml 동작 (PR open/merge → 이슈 코멘트/라벨) | 변경 없이 그대로 작동 (`docs/plans/**` 경로 가드만 본다) |
| 텔레그램 | `/idea <짧은 메모>` → 이슈 생성 회신 수신 → 이슈에 답글 작성 후 round 2 진행 시 텔레그램 회신 도착 | grill-meta의 chat_id 파싱이 정상 작동 |

## Open questions

- [ ] `ALLOWED_GITHUB_LOGINS` 시크릿을 새로 둘지, 아니면 기존 `ALLOWED_CHAT_IDS` 패턴처럼 vars로 둘지. (지금은 secret 가정.)
- [ ] grilling 라운드 상한 (예: round 5 도달 시 자동 stop + "휴먼 개입 필요" 라벨) — v1 에서는 무제한, 그러나 라운드별 본문 길이 폭증 위험.
- [ ] `glossary_candidates` 가 0건이고 이미 이슈 본문에 같은 용어가 있을 때 중복 누적 방지 (LLM에 기존 후보 리스트 주입 필요).
- [ ] 비공개 ADR 후보(예: 외부 벤더명 포함)를 grilling 중 노출하지 말아야 하는지 — 현재 레포는 public이라 `[skip-grill]` 이외 마스킹 메커니즘 없음.

## Alternatives considered

- **Telegram 실시간 핑퐁** (worker가 KV/D1 세션 관리). UX는 더 매끄럽지만 worker가 처음으로 stateful 해지고 timeout/reset/concurrent session 처리 비용이 큼. AskUserQuestion 결과 비채택.
- **프롬프트만 단발 강화** (아키텍처 무변경). 가장 작지만 grill-me 의 "지문 트리를 끝까지" 정신을 단발 호출로는 흉내내기 어렵고, 1차 답변 이후 후속 grilling이 불가능. 채택 안 함.
- **CONTEXT.md / ADR 자동 PR 생성** (스크립트가 직접 branch + PR). grill-with-docs의 "inline 업데이트" 정신에는 더 가깝지만, 자동 commit이 main path에 처음 들어가는 변경이라 리스크가 크고 plan PR 의 책임 경계가 흐려짐. v2 별도 plan으로 분리.
- **`/grill` 슬래시 명령어로 명시적 강도 조절**. 사용자가 한 번 더 외워야 하는 부담이 크고, 휴리스틱이 잘 작동하면 불필요. AskUserQuestion 결과 비채택.

## Revisions

- 2026-05-24 (#TBD): initial draft — 비동기 코멘트 grilling + CONTEXT.md/ADR 후보 누적
