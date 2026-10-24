# bbl-ai-lab

운영 repo 와 프로젝트 repo 를 한 곳에서 클론하고 찾아가는 **허브**. hub 자신은 manifest(`ops/repos.md`), 공용 agent skill, friction 기록 도구, 지식 번들만 가진다. 실작업은 각 repo 가 소유한다.

에이전트가 이 저장소를 수정할 때는 [AGENTS.md](AGENTS.md)를 먼저 읽는다.

## 문서 레이어

같은 사실을 세 군데 두지 않는다. 대상 독자로 나뉜다.

| 위치 | 독자 | 내용 |
|------|------|------|
| `README.md`, `docs/` | 사람 | 운영 모델, 셋업, 조사 기록 |
| [CONTEXT.md](CONTEXT.md) | 사람 + 에이전트 | 프로젝트 고유 용어집. 동의어는 `_Avoid_`로 컷 |
| [AGENTS.md](AGENTS.md) | 에이전트 | repo manifest / 문서 / 안전 규칙과 검증 명령 |
| [knowledge/](knowledge/) | 에이전트 | Open Knowledge Format 번들. YAML frontmatter + concept 간 링크 |

## 스킬

| 위치 | 소유 | 용도 |
|------|------|------|
| `.agents/skills/` + [skills-lock.json](skills-lock.json) | 외부 installer | 설치된 agent skill (`baoyu-youtube-transcript`, `unlazy`). 손으로 고치지 않는다. `dgx-comfyui-ops` 는 `ops/remote-comfyui` 클론을 가리키는 symlink |
| `.claude/skills/` | 혼합 | `.agents/skills/` 로의 symlink 와, 이 repo 가 소유하는 `file-friction` |

## friction 기록

세션이 일하다 repo 쪽 문제로 우회하면 `file-friction` skill 기준으로 `ops/friction.sh` 를 불러 그 repo 에 `friction` 라벨 이슈를 남긴다. 고칠지는 사람이 정한다. 자세한 것은 [knowledge/concepts/friction-log.md](knowledge/concepts/friction-log.md).

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

카테고리별로 **지식을 축적하고 그 지식으로 결과물을 만드는** repo. 설치 방식은 운영 repo와 같고(`ops/repos.md` manifest + `repo-sync.sh`) 소유 대상만 다르다 — 운영 repo는 원격 호스트의 운영을, 프로젝트 repo는 한 카테고리의 축적물을 소유한다.

| path | repo | 축적층 (남는 것) | 산출층 (건별로 소멸) | 작업 규칙 |
| --- | --- | --- | --- | --- |
| `projects/games/` | [BoBeenLee/games](https://github.com/BoBeenLee/games) | `skills/party-guide/references/`, `roster.md`, `builds.md` | `guide.md`, `party-candidates.md` | `skills/party-guide/SKILL.md` |
| `projects/travel/` | [BoBeenLee/travel](https://github.com/BoBeenLee/travel) | `knowledge/` | `trips/<여행>/` | `CLAUDE.md` |
| `projects/finance/` | [BoBeenLee/finance](https://github.com/BoBeenLee/finance) | `knowledge/` (숫자는 `rules.yaml` 한 곳) | `guides/` | `CLAUDE.md` |
| `projects/music/` | [BoBeenLee/music](https://github.com/BoBeenLee/music) | `research/`, `craft/` | `runs/<날짜>-<slug>/` | `AGENTS.md` |
| `projects/shopping/` | [BoBeenLee/shopping](https://github.com/BoBeenLee/shopping) | `skills/smart-shopping/` | 건별 구매 판단 | `skills/smart-shopping/SKILL.md` |
| `projects/hiking/` | [BoBeenLee/hiking](https://github.com/BoBeenLee/hiking) | `knowledge/` | `hikes/<날짜>-<산>/` | `CLAUDE.md` |
| `projects/cad/` | [BoBeenLee/cad](https://github.com/BoBeenLee/cad) | `knowledge/` | `designs/<날짜>-<slug>/` | `CLAUDE.md` |
| `projects/voice-agent/` | [BoBeenLee/voice-agent](https://github.com/BoBeenLee/voice-agent) | `knowledge/` | `agents/<날짜>-<slug>/` | `CLAUDE.md` |
| `projects/promo-agent/` | [BoBeenLee/promo-agent](https://github.com/BoBeenLee/promo-agent) | `knowledge/`, `research/` | `campaigns/<날짜>-<slug>/` | `CLAUDE.md` |
| `projects/kakao-agent/` | [BoBeenLee/kakao-agent](https://github.com/BoBeenLee/kakao-agent) | `knowledge/` | 없음 (대화·세션은 호스트의 `~/kakao-agent/` 에만) | `CLAUDE.md` |
| `projects/blender/` | [BoBeenLee/blender](https://github.com/BoBeenLee/blender) | `knowledge/` | `works/<날짜>-<slug>/` | `CLAUDE.md` |
| `projects/car/` | [BoBeenLee/car](https://github.com/BoBeenLee/car) | `knowledge/` | `wraps/<날짜>-<slug>/` | `CLAUDE.md` |
| `projects/meeting-agent/` | [BoBeenLee/meeting-agent](https://github.com/BoBeenLee/meeting-agent) | `knowledge/`, `research/` | 없음 (회의 음성·전사는 `private/` 에만, 커밋 안 함) | `CLAUDE.md` |

두 층을 **디렉터리로 가른다.** 축적층은 카테고리가 살아 있는 한 남고, 산출층은 건이 끝나면 참조 기록으로만 남는다. 섞으면 다음 건이 빈 화면에서 시작하거나, 지난 건의 상황 판단이 지식으로 승격돼 버린다.

열셋 다 **private**다. `games`/`travel`/`finance`는 계정 로스터·여행 일정·재무 프로필 같은 개인 데이터를 이미 담고 있고, `music`은 생성곡·가사·취향이, `shopping`은 구매 이력·예산·사이즈가, `hiking`은 GPS 경로·체력 수치·장비 이력이, `cad`는 집 실측 치수·제작 이력이, `voice-agent`는 통화 녹음·전사·목소리가, `promo-agent`는 커뮤니티에서 수집한 제3자의 글·닉네임·동네가, `kakao-agent`는 주인·봇 계정 id 와 방 id 가, `blender`는 참고 사진·집 장면·렌더가, `car`는 차량 식별 정보·차 사진·원본 그림이, `meeting-agent`는 업무 회의 맥락과 측정 결과가 쌓이면 개인 데이터가 된다(회의 음성과 전사 자체는 커밋하지 않는다). 클론에 `gh auth` 세션이나 `GIT_TOKEN=<pat>`이 필요하다.

각 repo가 자기 구조·규율·검증 명령의 단일 진실원이다. hub는 URL과 브랜치만 소유하고 내용은 추적하지 않는다.

### 조사 방법은 repo 사이에서 이식한다

hub가 공용 조사 프레임워크를 소유하지 않는다. 방법이 필요한 repo가 **이미 방법을 가진 repo에서 가져다 자기 도메인에 맞게 고친다.** `hiking`이 `travel`의 조사 프로토콜(계절 게이트 → 공식 1차 출처 → 영상 전수조사 → stale 게이트 → 3곳 라우팅 → 결정 큐)과 스크립트 3종을 이식한 것이 첫 사례다.

`cad`가 `hiking`의 이식본을 다시 이식한 것이 두 번째 사례이자 첫 두 홉 이식이다. 두 홉을 건너도 실패 기록(표본 30편, 조회수 정렬, 자동 자막 오인식, 무성 영상)이 같이 왔고, 도메인 차이는 다시 갈렸다 — 계절·들머리 대신 도구·버전이 버킷이고, 게이트는 날짜가 아니라 버전·플랫폼이다. `hiking`이 접어 넣었던 stale 게이트 단계는 `travel`의 `plan-trip`에서 다시 펴 왔다. 버전 경계에서 썩는 사실(UI·워크벤치·API)이 두꺼운 도메인이라서다. 이식본이 원본에 없던 것을 찾기도 한다 — `cad`는 검색 결과의 한글 제목이 영어 채널의 자동 번역이라는 것을 잡았는데, `hiking`은 한국어 영상만 다뤄 부딪히지 않았다.

`voice-agent`가 `cad`에서 가져간 것이 세 번째 사례이고, 여기서 처음으로 **이식 대상 자체가 갈렸다.** 앞의 두 번은 조사 프로토콜과 스크립트를 통째로 가져갔지만 `voice-agent`는 `check_links.py`와 값/지식 분리 규율만 가져가고 `survey.py`(영상 전수조사)는 **의도적으로 두고 왔다.** 앞의 셋은 등산로·여행 동선·FreeCAD 워크플로처럼 공식 문서가 얇고 실전 지식이 영상에 있는 도메인이었는데, 음성 에이전트는 1차 출처가 요금 페이지와 약관 페이지고 그 둘은 fetch가 되고 날짜가 찍힌다. 그래서 이식이 "무엇을 가져올까"가 아니라 **"무엇을 두고 올까"를 정하는 일**이 됐다. 안 쓸 스크립트를 가져오면 빈 인프라가 남는다.

`promo-agent`가 `voice-agent`에서 가져간 것이 네 번째 사례이고, 여기서 처음으로 **이식본이 원본에 없던 규율을 더했다.** 가져온 것은 값/지식 3등급 분리와 결정 로그 형식이고 영상 전수조사는 또 두고 왔는데, 거기에 **표면 실측**을 새로 세웠다 — 플랫폼 UI 위에 자동화를 설계하기 전에 DOM을 직접 열어 확인한다는 규칙이다. `voice-agent`의 1차 출처가 요금·약관 페이지였다면 홍보 도메인의 1차 출처는 **실제 화면**이다. 당근 이용약관까지 읽어 자동화 게시 금지 조항을 찾아 놓고도 정작 그 앞의 질문을 안 해서 계획을 한 번 버렸다 — 웹에 쓰기 UI 자체가 없었다. 약관이 허용하는지와 버튼이 존재하는지는 다른 질문이고 후자가 먼저다.

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
├── AGENTS.md                        ← 에이전트 규칙 (repo manifest / 문서 / 안전)
├── CONTEXT.md                       ← 프로젝트 용어집
├── skills-lock.json                 ← 설치된 agent skill lockfile (외부 installer 소유)
├── .github/ISSUE_TEMPLATE/friction.yml
├── .agents/skills/                  ← 외부 installer가 설치한 agent skill
├── .claude/skills/                  ← file-friction(실물) + .agents/skills symlink
├── knowledge/                       ← OKF 지식 번들 (concepts / log)
├── docs/research/                   ← 조사 기록
├── ops/
│   ├── repos.md                     ← 운영·프로젝트 repo manifest (단일 진실원)
│   ├── repo-sync.sh                 ←   미등록 projects/* 자동 등록 후 미설치 repo만 클론
│   ├── repo-sync.test.sh            ←   자동 등록 self-check (임시 디렉터리)
│   ├── friction.sh                  ←   friction 이슈 생성/코멘트
│   ├── friction.test.sh
│   ├── remote-comfyui/              ←   clone, git 미추적
│   └── openmontage/                 ←   clone, git 미추적
├── projects/                        ← 카테고리별 지식·산출 repo (clone, git 미추적)
└── hermes-workspace/                ← clone, git 미추적
```
