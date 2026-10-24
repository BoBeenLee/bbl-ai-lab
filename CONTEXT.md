# bbl-ai-lab Context

## Language

**Hub**:
이 저장소의 주된 제품 형태. 운영 repo, 프로젝트 repo, 상류 도구 repo 를 `ops/repos.md` manifest 로 묶어 한 곳에서 클론하고 찾아가게 한다. hub 자신은 manifest, 공용 agent skill, friction 기록 도구, 지식 번들만 가진다.
_Avoid_: monorepo, 자동화 허브

**Operator workspace repo**:
hub 와 분리된 별도 운영 도구 repo. 예: `hermes-workspace`는 remote Hermes 운영 runbook, scripts, artifacts의 owner이며, 이 hub repo는 `ops/repos.md` manifest에 URL과 브랜치만 등록하고 `ops/repo-sync.sh`가 지정된 path에 클론한다. 체크아웃 내용은 hub가 추적하지 않는다.
_Avoid_: git submodule, gitlink 포인터 커밋

**Project repo**:
`projects/` 아래에 매니페스트로 설치되는 별도 repo. operator workspace repo와 설치 방식은 같지만 소유 대상이 다르다 — operator repo는 원격 호스트의 운영을 소유하고, project repo는 한 카테고리의 작업 덩어리를 소유한다. 예: `projects/games`는 게임 관련 에이전트 스킬을, `projects/travel`은 여행 계획을, `projects/finance`는 재테크 지식 베이스를, `projects/music`은 AI 음악 제작 지식을, `projects/shopping`은 실구매 판단 워크플로를, `projects/hiking`은 등산 지식과 산행 기록을, `projects/cad`는 CAD 지식과 설계 기록을, `projects/voice-agent`는 음성 에이전트 지식과 에이전트별 기록을, `projects/promo-agent`는 홍보 채널 지식과 캠페인별 기록을, `projects/kakao-agent`는 Mac 에서 카톡 메시지로 로컬 에이전트 CLI 를 구동하는 봇을, `projects/blender`는 Blender 지식과 작업별 기록을, `projects/car`는 차에 관한 지식과 작업별 기록을, `projects/meeting-agent`는 Mac 에서 회의를 듣다가 나에게만 조언하는 에이전트를 소유한다. 열셋 다 private다 — 앞의 셋은 개인 데이터(계정 로스터, 여행 일정, 재무 프로필)를 담고 있고, `music`은 생성곡·가사·취향이, `shopping`은 구매 이력·예산·사이즈가, `hiking`은 GPS 경로·체력 수치·장비 이력이, `cad`는 집 실측 치수·제작 이력이, `voice-agent`는 통화 녹음·전사·목소리가, `promo-agent`는 커뮤니티에서 수집한 제3자의 글·닉네임·동네가, `kakao-agent`는 주인·봇 계정 id 와 방 id 가, `blender`는 참고 사진·집 장면·렌더가, `car`는 차량 식별 정보·차 사진·원본 그림이, `meeting-agent`는 업무 회의 맥락과 측정 결과가 쌓이면 개인 데이터가 되기 때문이다(회의 음성과 전사 자체는 커밋하지 않는다). operator repo와 달리 매니페스트 등록은 손이 아니라 `repo-sync.sh`가 한다.
_Avoid_: operator workspace repo와 동일 취급, `ops/` 아래 배치, `projects/` 항목을 손으로 매니페스트에 적기

**Upstream tool repo**:
매니페스트로 설치되지만 내가 소유하지 않는 서드파티 도구 repo. operator workspace repo(원격 호스트의 운영을 소유)도 project repo(작업 덩어리를 소유)도 아니며, 소유자가 상류라는 점에서 갈린다. 결과로 세 가지가 달라진다. 로컬 수정은 커밋해도 푸시할 곳이 없고, 라이선스는 hub와 무관하게 상류 것을 따르며(`ops/openmontage`는 AGPL-3.0), `repo-sync.sh`는 클론만 하고 의존성 설치는 그 repo 자신의 절차(`make setup`)가 한다. 예: `ops/openmontage`는 영상 제작 파이프라인 도구이고 `assets` 단계에서 `ops/remote-comfyui`의 DGX ComfyUI를 프로바이더로 호출한다.
_Avoid_: operator workspace repo와 동일 취급, git submodule, hub가 상류 라이선스를 상속한다고 보기, `repo-sync.sh`가 설치까지 한다고 보기

**Operator repo manifest**:
`ops/repos.md`의 YAML frontmatter. operator workspace repo, project repo, upstream tool repo의 `name`, `url`, `path`, `branch`를 모아둔 단일 진실원이며 `ops/repo-sync.sh`가 유일한 소비자이자 `projects/` 항목의 유일한 필자다.
_Avoid_: README에 URL 중복 기재, .gitmodules, `projects/` 항목 수기 편집

**Knowledge bundle**:
`knowledge/` 아래에 있는 Open Knowledge Format 문서 묶음. 사람용 운영 문서(`README.md`, `docs/`)를 대체하지 않고, 에이전트가 프로젝트 개념과 그 관계를 안정적으로 순회하도록 돕는 agent-consumable 지식 계층이다.
_Avoid_: README 사본, docs 전체 복제본

**Concept**:
Knowledge bundle 안의 단일 지식 단위. 하나의 Markdown 파일로 표현되며 YAML frontmatter의 `type`으로 종류를 밝히고, 본문에서 관련 source 문서로 연결한다.
_Avoid_: 임의 문서 조각, 섹션 하나

**Friction**:
에이전트가 일하다 repo 쪽 문제(낡은 문서나 규칙, 깨지거나 느린 스크립트, 빠진 도구) 때문에 우회한 불편. 그 repo 에 `friction` 라벨 이슈로 남긴다(`ops/friction.sh`). 고칠지는 사람이 정한다. 외부 서비스 탓이라 repo 에서 못 고치는 것은 friction 이 아니다.
_Avoid_: 버그 리포트와 동일 취급, 기억 파일에만 적기, `gh issue create` 로 직접 남기기
