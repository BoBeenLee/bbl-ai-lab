# bbl-ai-lab Context

## Language

**Automation flow hub**:
이 저장소의 주된 제품 형태. Telegram command를 Cloudflare Worker가 받아 GitHub repository_dispatch로 넘기고, GitHub Actions가 script/prompt/skill context를 실행해 Issue, 보고서, 문서 같은 산출물을 만드는 여러 automation flow의 집합이다.
_Avoid_: 단순 Worker, 봇 하나

**Automation flow**:
하나의 사용자 의도 또는 반복 작업을 처리하는 end-to-end 경로. command 또는 subcommand, repository_dispatch event type, workflow, script, prompt, docs가 함께 움직인다. 예: `idea-elaborate`.
_Avoid_: workflow만, script만

**Flow registry**:
`worker/src/flows.ts`에 있는 automation flow manifest와 routing helper. Telegram command/subcommand, event type, usage/ack text, adapter file path를 한 interface에 모아 drift를 검증 가능하게 만든다.
_Avoid_: FLOWS 테이블, 라우팅 배열

**Flow adapter files**:
Flow registry entry가 가리키는 concrete files. 현재는 GitHub Actions workflow, runtime script, Gemini prompt, flow docs를 뜻한다.
_Avoid_: 관련 파일들

**Legacy event type**:
Flow registry 도입 전부터 운영되어 `<flow>-<action>` naming rule을 따르지 않는 repository_dispatch event type. 현재 허용된 값은 `idea-submitted`뿐이다.
_Avoid_: 예외 이벤트

**Subcommand flow**:
하나의 top-level Telegram command 아래 여러 action을 두는 automation flow. 형식은 `/command subcommand body`이며, 각 subcommand가 별도 event type과 flow adapter files를 가진다. 예: 예정된 `/recruit collect`.
_Avoid_: nested command, 하위 명령

**Operator workspace submodule**:
이 저장소의 Telegram/GitHub Actions automation flow와 분리된 운영 도구 repo를 가리키는 git submodule. 예: `hermes-workspace`는 remote Hermes 운영 runbook, scripts, artifacts의 owner이며, 이 hub repo는 submodule pointer와 얇은 안내만 관리한다.
_Avoid_: flow adapter script와 운영 host script를 같은 `scripts/` owner로 취급하기

**Knowledge bundle**:
`knowledge/` 아래에 있는 Open Knowledge Format 문서 묶음. 사람용 운영 문서(`README.md`, `docs/`)를 대체하지 않고, 에이전트가 프로젝트 개념과 flow 관계를 안정적으로 순회하도록 돕는 agent-consumable 지식 계층이다.
_Avoid_: README 사본, docs 전체 복제본

**Concept**:
Knowledge bundle 안의 단일 지식 단위. 하나의 Markdown 파일로 표현되며 YAML frontmatter의 `type`으로 종류를 밝히고, 본문에서 관련 source 문서나 flow로 연결한다.
_Avoid_: 임의 문서 조각, 섹션 하나
