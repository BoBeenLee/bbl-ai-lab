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

**Operator workspace repo**:
이 저장소의 Telegram/GitHub Actions automation flow와 분리된 별도 운영 도구 repo. 예: `hermes-workspace`는 remote Hermes 운영 runbook, scripts, artifacts의 owner이며, 이 hub repo는 `ops/repos.md` manifest에 URL과 브랜치만 등록하고 `ops/repo-sync.sh`가 지정된 path에 클론한다. 체크아웃 내용은 hub가 추적하지 않는다.
_Avoid_: git submodule, gitlink 포인터 커밋, flow adapter script와 운영 host script를 같은 `scripts/` owner로 취급하기

**Project repo**:
`projects/` 아래에 매니페스트로 설치되는 별도 repo. operator workspace repo와 설치 방식은 같지만 소유 대상이 다르다 — operator repo는 원격 호스트의 운영을 소유하고, project repo는 Telegram/Actions flow가 아닌 작업 덩어리를 소유한다. 예: `projects/games`는 게임 관련 에이전트 스킬을, `projects/travel`은 여행 계획을, `projects/finance`는 재테크 지식 베이스를, `projects/music`은 AI 음악 제작 지식을, `projects/shopping`은 실구매 판단 워크플로를, `projects/hiking`은 등산 지식과 산행 기록을 소유한다. 여섯 다 private다 — 앞의 셋은 개인 데이터(계정 로스터, 여행 일정, 재무 프로필)를 담고 있고, `music`은 생성곡·가사·취향이, `shopping`은 구매 이력·예산·사이즈가, `hiking`은 GPS 경로·체력 수치·장비 이력이 쌓이면 개인 데이터가 되기 때문이다. operator repo와 달리 매니페스트 등록은 손이 아니라 `repo-sync.sh`가 한다.
_Avoid_: operator workspace repo와 동일 취급, hub의 flow로 취급, `ops/` 아래 배치, `projects/` 항목을 손으로 매니페스트에 적기

**Operator repo manifest**:
`ops/repos.md`의 YAML frontmatter. operator workspace repo와 project repo의 `name`, `url`, `path`, `branch`를 모아둔 단일 진실원이며 `ops/repo-sync.sh`가 유일한 소비자이자 `projects/` 항목의 유일한 필자다.
_Avoid_: README에 URL 중복 기재, .gitmodules, `projects/` 항목 수기 편집

**Knowledge bundle**:
`knowledge/` 아래에 있는 Open Knowledge Format 문서 묶음. 사람용 운영 문서(`README.md`, `docs/`)를 대체하지 않고, 에이전트가 프로젝트 개념과 flow 관계를 안정적으로 순회하도록 돕는 agent-consumable 지식 계층이다.
_Avoid_: README 사본, docs 전체 복제본

**Concept**:
Knowledge bundle 안의 단일 지식 단위. 하나의 Markdown 파일로 표현되며 YAML frontmatter의 `type`으로 종류를 밝히고, 본문에서 관련 source 문서나 flow로 연결한다.
_Avoid_: 임의 문서 조각, 섹션 하나

**Autonomous loop**:
사람이 매 턴 프롬프트를 넣지 않고, 정해진 주기마다 스스로 관측·판단·기록하는 에이전트 실행 단위. 이 저장소에서는 Claude Code의 `/loop`이 엔진이고 `LOOP.md`가 어떤 루프가 어떤 주기로 도는지의 단일 진실원이다. Telegram command로 시작하는 automation flow와 달리 트리거가 사람이 아니라 스케줄이다.
_Avoid_: 크론잡, 자동화 스크립트, automation flow와 동일 취급

**Loop state spine**:
`STATE.md`. 루프가 매 실행 시작에 읽고 끝에 쓰는 유일한 상태 파일. High Priority, Watch List, Recent Noise 세 구획과 마지막 실행 시각을 가진다. 대화 로그를 읽지 않고도 루프가 지금 무엇을 들고 있는지 사람이 확인하는 지점이다.
_Avoid_: 채팅 히스토리, 실행 로그(`loop-run-log.md`)와 혼용

**Loop readiness level**:
루프에 허용된 자율성 등급. L1은 보고만 하고 아무것도 고치지 않으며, L2는 검증자 승인 하에 작은 수정을 하고, L3은 명시적 gate를 두고 넓게 행동한다. 현재 이 저장소의 daily triage 루프는 L1이다.
_Avoid_: 신뢰도, 단계
