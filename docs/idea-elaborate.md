# `idea-elaborate` flow

텔레그램에 던진 단편적 아이디어/할 일 메모를, Gemini가 brainstorming 스킬을 컨텍스트로 활용해 구체화하고 GitHub Issue로 적재한다.

## 트리거

| 입력 형태 | 예시 | 라우팅 |
|-----------|------|--------|
| `/idea <본문>` | `/idea 회의록 요약 봇 만들어보기` | idea flow |
| `/todo <본문>` | `/todo 분기별 KPI 정리` | idea flow (동의어) |
| 명령어 없는 평문 | `회의록 요약 봇 만들어보기` | dispatch 하지 않고 `/idea <본문>` 안내 회신 |
| 등록되지 않은 명령어 | `/foo ...` | 도움말 회신 |

repository_dispatch event_type: **`idea-submitted`**.

## 흐름

```
[Telegram User]
  │ /idea <메시지>
  ▼
[Cloudflare Worker]
  │ secret + 화이트리스트 검증
  │ event_type: idea-submitted, payload: { chat_id, message_id, text, submitted_at }
  ▼
[GitHub Action: idea-elaborate.yml]
  │ ① actions/checkout, setup-node
  │ ② pip install yt-dlp trafilatura youtube-transcript-api (URL 추출용)
  │ ③ Gemini OAuth credentials 복원 (~/.gemini/oauth_creds.json)
  │ ④ npm install -g @google/gemini-cli
  │ ⑤ scripts/idea-elaborate.sh 실행
  ▼
scripts/idea-elaborate.sh
  │ ① 본문에서 URL 감지 → fetch-url-content.py (실패해도 계속 진행)
  │ ② prompts/idea-elaborate.md + skills/product-brainstorming.SKILL.md
  │      + 사용자 원문 + (있으면) fetched content 합성
  │ ③ gemini --yolo -m <GEMINI_MODEL> -p "<합성 프롬프트>" (실패 시 1회 재시도)
  │ ④ 출력에서 JSON 추출 (python re, fenced/bare 양쪽 지원)
  │ ⑤ jq로 마크다운 본문 생성
  │ ⑥ gh issue create --label idea[,needs-clarification]
  │ ⑦ Telegram sendMessage로 issue URL 회신
  ▼
[GitHub Issue: 요약/문제/목표/접근/리스크/Open Questions/Next Actions]
```

## 관련 파일

| 경로 | 역할 |
|------|------|
| [.github/workflows/idea-elaborate.yml](../.github/workflows/idea-elaborate.yml) | repository_dispatch + workflow_dispatch 트리거. Gemini OAuth 부트스트랩 + `idea-elaborate.sh` 호출 |
| [scripts/idea-elaborate.sh](../scripts/idea-elaborate.sh) | 본 처리 스크립트 |
| [scripts/prompts/idea-elaborate.md](../scripts/prompts/idea-elaborate.md) | Gemini 시스템 프롬프트 + 출력 JSON 스키마 |
| [scripts/fetch-url-content.py](../scripts/fetch-url-content.py) | 본문 속 URL 내용 추출 (yt-dlp / trafilatura / youtube-transcript-api) |
| [skills/product-brainstorming.SKILL.md](../skills/product-brainstorming.SKILL.md) | brainstorming 컨텍스트 (anthropics/knowledge-work-plugins 출처). `SKILL_FILE` env 로 교체 가능 |
| [worker/src/flows.ts](../worker/src/flows.ts) | `commands: ["idea","todo"]` → `eventType: "idea-submitted"` 매핑 (flow manifest) |

## 환경변수 / 시크릿

### GitHub Secrets (Action에서 사용)

| Secret | 필수 | 용도 |
|--------|------|------|
| `GEMINI_OAUTH_CREDS` | ✅ | `~/.gemini/oauth_creds.json`을 base64 인코딩한 문자열. `base64 -i ~/.gemini/oauth_creds.json` |
| `GEMINI_GOOGLE_EMAIL` | ✅ | Gemini OAuth 계정 이메일 |
| `TG_BOT_TOKEN` | ✅ (회신용) | 없으면 Issue는 생성되나 텔레그램 두 번째 회신(링크) 생략 |

`culcom-routines`에서 동일 OAuth를 이미 쓰고 있다면 같은 값 재사용 가능.

### GitHub Variables (선택)

| Variable | 기본값 | 비고 |
|----------|--------|------|
| `GEMINI_MODEL` | `gemini-3-pro-preview` | 아래 [Gemini 모델 옵션](#gemini-모델-옵션) 참고 |

### Worker 측 (참고)

flow에 직접 영향은 없지만 Worker가 dispatch를 못 하면 이 flow도 시작 안 됨. 자세한 셋업은 [공통 인프라](../README.md#공통-인프라-셋업) 참고.

## Gemini 모델 옵션

`GEMINI_MODEL` GitHub Variable로 모델을 바꿀 수 있다. gemini-cli `-m` 플래그가 받는 canonical 식별자 (출처: [geminicli.com/docs/cli/model](https://geminicli.com/docs/cli/model)):

| 식별자 | 세대 | 용도 |
|--------|------|------|
| `gemini-3-pro-preview` | Gemini 3 (preview) | 최고 추론 품질, 1M 토큰 컨텍스트 / **현재 본 flow 기본값** |
| `gemini-3-flash-preview` | Gemini 3 (preview) | 빠르고 저렴, 동일 컨텍스트 한도 |
| `gemini-2.5-pro` | Gemini 2.5 (GA) | 안정성 우선 시 fallback |
| `gemini-2.5-flash` | Gemini 2.5 (GA) | 빠르고 저렴, 단순 요약/추출에 적합 |
| `auto` | 메타 | 작업 복잡도에 따라 Gemini 3 라인업 중 자동 선택 (공식 권장 / preview 식별자 갱신에 자동 대응) |
| `auto-2.5` | 메타 | Gemini 2.5 라인업 중 자동 선택 |

OAuth Personal(무료) 한도는 계정 합산 분당 60req / 일 1,000req (gemini-cli README 기준, 모델 합산). 본 flow는 전체 SKILL.md를 컨텍스트로 attach 하기 때문에 (~110KB) Pro 계열이 안전하지만, Open Questions까지만 뽑는 단순 케이스는 Flash로도 충분할 수 있다.

추천:
- **품질 우선 / 현재 default** → `gemini-3-pro-preview`
- preview 식별자 갱신에 자동 대응 → `auto`
- GA 안정성 우선 시 fallback → `gemini-2.5-pro`
- 아이디어 폭발기에 quota 절약 → `gemini-2.5-flash`

> ⚠️ `gemini-3-pro-preview`는 preview 라인업이므로 GA 전환 시 식별자가 `gemini-3-pro` 등으로 변경될 수 있다. 워크플로우가 fail하면 `auto`로 옮기거나 GA 식별자로 바꿀 것. preview 특유의 일시적 502/429는 [scripts/idea-elaborate.sh](../scripts/idea-elaborate.sh)의 1회 재시도 로직이 흡수한다.

설정 변경:
```bash
gh variable set GEMINI_MODEL --repo BoBeenLee/bbl-ai-lab --body "gemini-3-pro-preview"
# 되돌리기
gh variable delete GEMINI_MODEL --repo BoBeenLee/bbl-ai-lab
```

## Gemini 출력 스키마

[scripts/prompts/idea-elaborate.md](../scripts/prompts/idea-elaborate.md)가 강제하는 형식:

```json
{
  "title": "string (60자 이내)",
  "summary": "string (한 문장)",
  "problem": "string",
  "goal": "string",
  "non_goals": ["string", "..."],
  "approach": "string",
  "risks": ["string", "..."],
  "open_questions": ["string", "..."],
  "next_actions": ["string", "..."],
  "needs_clarification": true | false
}
```

스크립트는 ```json``` 펜스 + 베어 JSON 둘 다 받아내며, 위 키들로 마크다운 Issue 본문을 렌더링한다. `needs_clarification: true`면 `needs-clarification` 라벨이 자동 부착된다.

## 검증

| 단계 | 명령 | 기대 결과 |
|------|------|-----------|
| Action 단독 | GitHub Actions UI → Idea Elaborate → Run workflow → text 입력 | Issue 생성 |
| Action CLI | `gh workflow run idea-elaborate.yml --repo BoBeenLee/bbl-ai-lab -f text="테스트"` | 동일 |
| 명령어 라우팅 | `/idea ...`, `/todo ...`만 idea flow / 평문과 `/unknown ...`은 도움말 | Worker 로그(`wrangler tail`)로 확인 |
| Telegram E2E | 봇에 `/idea 첫 테스트` 전송 | 즉시 ack → 1~2분 내 Issue 링크 회신 |
| 출력 스키마 위반 | gemini가 JSON 외 텍스트만 반환한 경우 | 스크립트가 stderr에 raw output 출력 후 exit 1 (Action fail) |

## 향후 확장

- 보강 루프 워크플로우 (`needs-clarification` 라벨 + Issue 코멘트 → Gemini가 본문 자동 업데이트, 모든 Open Questions이 답변되면 라벨 제거)
- 채택된 Issue를 markdown으로 git 아카이빙 (`docs/ideas/<slug>.md`)
- 다중 brainstorm 스킬 자동 라우팅 (skills 인덱스로 1차 호출 → 선택된 스킬로 2차 호출)
- 음성 메시지 → Whisper 변환 → 동일 파이프라인 진입
- Gemini 출력 스키마 위반 시 자동 재시도 (1회) 또는 fallback 모델로 재호출
