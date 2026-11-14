---
repositories:
  - name: hermes-workspace
    url: https://github.com/BoBeenLee/hermes-workspace.git
    path: hermes-workspace
    branch: main
    description: "원격 Hermes 호스트(기본 원격 Mac, DGX Spark) 운영. SSH, Tailscale, 원격 데스크톱, 로컬 LLM, Mac Hermes 브리지. DGX [jarvis] 카톡 봇은 2026-10-16 부터 꺼져 있다. 운영 repo"
  - name: remote-comfyui
    url: https://github.com/BoBeenLee/remote-comfyui.git
    path: ops/remote-comfyui
    branch: main
    description: "DGX ComfyUI 서비스 운영, 워크플로, 모델 권고와 실행 산출물. 운영 repo"
  - name: openmontage
    url: https://github.com/calesthio/OpenMontage.git
    path: ops/openmontage
    branch: main
    description: "영상 제작 파이프라인(편집, 조립, 후반). remote-comfyui 를 assets 단계 공급자로 부른다. 업스트림 도구 repo, AGPL-3.0"
  - name: games
    url: https://github.com/BoBeenLee/games.git
    path: projects/games
    branch: main
    description: "게임 에이전트 스킬. 원신, 젠레스 존 제로, 이환의 보유 캐릭터로 파티와 장비를 짠다(party-guide)"
  - name: travel
    url: https://github.com/BoBeenLee/travel.git
    path: projects/travel
    branch: main
    description: "여행 계획. 조사 지식과 여행별 일정"
  - name: finance
    url: https://github.com/BoBeenLee/finance.git
    path: projects/finance
    branch: main
    description: "개인 재테크 지식 베이스. 숫자는 rules.yaml 한 곳"
  - name: music
    url: https://github.com/BoBeenLee/music.git
    path: projects/music
    branch: main
    description: "AI 음악 제작 지식(모델별 라이선스, 연출)과 생성 기록"
  - name: shopping
    url: https://github.com/BoBeenLee/shopping.git
    path: projects/shopping
    branch: main
    description: "실구매 판단 흐름(smart-shopping). 요구조건, 재고 실검증, 구매 채널"
  - name: hiking
    url: https://github.com/BoBeenLee/hiking.git
    path: projects/hiking
    branch: main
    description: "등산 지식과 산행별 기록"
  - name: cad
    url: https://github.com/BoBeenLee/cad.git
    path: projects/cad
    branch: main
    description: "FreeCAD 지식과 설계별 기록. 3D 프린팅 부품, 파이썬 생성 모델, 가구와 실내 배치"
  - name: voice-agent
    url: https://github.com/BoBeenLee/voice-agent.git
    path: projects/voice-agent
    branch: main
    description: "음성 에이전트 지식과 에이전트별 기록. 무료로 돌아가는 것만"
  - name: promo-agent
    url: https://github.com/BoBeenLee/promo-agent.git
    path: projects/promo-agent
    branch: main
    description: "홍보 채널 지식과 캠페인별 기록. 자동화 전에 플랫폼 화면을 실측한다"
  - name: kakao-agent
    url: https://github.com/BoBeenLee/kakao-agent.git
    path: projects/kakao-agent
    branch: main
    description: "Mac 카톡 봇. Iris(안드로이드 에뮬레이터) 위에서 턴마다 고른 에이전트 CLI(Claude Code, Codex, opencode)를 돌린다"
  - name: blender
    url: https://github.com/BoBeenLee/blender.git
    path: projects/blender
    branch: main
    description: "Blender 지식과 작업별 기록(헤드리스 장면, 렌더, 애니메이션, GLB, STL). 치수 중심 부품은 cad"
  - name: car
    url: https://github.com/BoBeenLee/car.git
    path: projects/car
    branch: main
    description: "자동차 지식과 작업별 기록(화면용 랩 이미지 먼저). 3D 장면과 렌더는 blender"
  - name: meeting-agent
    url: https://github.com/BoBeenLee/meeting-agent.git
    path: projects/meeting-agent
    branch: main
    description: "회의 동석 에이전트. Mac 에서 로컬로 듣고 내 화면을 보며 나에게만 조언한다. 스킬판만 설치, 회의 음성, 전사, 캡처는 커밋 안 함"
  - name: app-analysis
    url: https://github.com/BoBeenLee/app-analysis.git
    path: projects/app-analysis
    branch: main
    description: "설치된 앱과 웹 서비스 분석 노트(REA, Ghidra, craft-anything). 바이너리와 캡처 원본은 두지 않는다"
  - name: stock-agent
    url: https://github.com/BoBeenLee/stock-agent.git
    path: projects/stock-agent
    branch: main
    description: "TradingAgents 기반 주식 분석(국내 KOSPI, KOSDAQ 먼저). 주문은 나중에 kakao-agent 워커 도구로, 내 승인 뒤에만"
  - name: hermes-dgx-off
    url: https://github.com/BoBeenLee/hermes-workspace.git
    path: projects/hermes-dgx-off
    branch: main
---

# 운영 repo 목록

`ops/repo-sync.sh` 전용 참조 파일이자 운영 repo 목록의 단일 진실원. 이 hub는 URL과 브랜치만 소유하고, repo 내용은 각 repo가 소유한다. submodule gitlink가 아니므로 하위 repo에 커밋이 생겨도 hub에 포인터 커밋을 만들 필요가 없다.

## 설치

```bash
bash ops/repo-sync.sh
```

이미 클론된 경로는 스킵한다. `GIT_TOKEN=<pat>` 를 주면 https URL에 토큰을 끼워 클론한다.

## repo 추가

`path`는 `ops/` 아래일 필요가 없다 — `repo-sync.sh`가 hub 루트 기준 임의 경로를 클론한다.

**`projects/` 아래는 항목을 손으로 만들지 않는다.** repo를 만들고 origin만 붙인 뒤 `bash ops/repo-sync.sh`를
한 번 돌리면 `repo-sync.sh`가 origin URL과 기본 브랜치를 읽어 이 frontmatter에 등록한다. 손으로 적는 것은 그 뒤의
`description` 한 줄뿐이다(아래).
`.gitignore`는 `/projects/*/` glob이라 이미 덮고 있다. origin이 없는 디렉터리는 경고만 하고 건너뛴다.

```bash
git -C projects/<name> remote add origin https://github.com/BoBeenLee/<name>.git
bash ops/repo-sync.sh
```

`projects/` 밖(운영 repo)은 여전히 이 파일의 frontmatter와 `.gitignore` 두 곳을 함께 고친다.
`branch`를 생략하면 `main`으로 클론한다.

`description`은 그 repo가 맡은 일 한 줄이다. 에이전트와 봇이 질문을 받으면 이 줄을 보고 repo를 고르므로, repo가 맡은 일의
단일 진실원은 여기다(AGENTS.md, README에 다시 적지 않는다). 자동 등록은 이 줄을 채우지 못하므로 등록된 뒤 손으로 적는다.
빠지면 `repo-sync.sh`가 경고한다. `: `가 들어갈 수 있으니 큰따옴표로 감싼다.

repo를 고른 뒤에는 그 repo의 `CLAUDE.md`, 없으면 `AGENTS.md`, 없으면 `README.md`부터 읽는다.

## private repo

`games`, `travel`, `finance`, `music`, `shopping`, `hiking`, `cad`, `voice-agent`, `promo-agent`, `kakao-agent`,
`blender`, `car`, `meeting-agent`, `stock-agent`, `app-analysis`는 private다. 앞의 셋은 계정 로스터, 여행 일정, 재무 프로필 같은 개인 데이터를 이미 담고 있고, `music`은
생성곡·가사·취향이, `shopping`은 구매 이력·예산·사이즈가, `hiking`은 GPS 경로·체력 수치·장비 이력이, `cad`는
집 실측 치수·제작 이력이, `voice-agent`는 통화 녹음·전사·목소리가, `promo-agent`는 커뮤니티에서 수집한 제3자의
글·닉네임·동네가, `kakao-agent`는 주인·봇 계정 id 와 방 id 가, `blender`는 참고 사진·집 장면·렌더가, `car`는
차량 식별 정보·차 사진·원본 그림이, `meeting-agent`는 업무 회의 맥락과 측정 결과가, `stock-agent`는 보유 종목·주문·계좌 결과가 쌓이면 개인 데이터가 되기 때문이다
(회의 음성과 전사 자체는 커밋하지 않는다).
`app-analysis`는 개인 데이터가 아니라 상용 앱의 디컴파일 발췌와 남의 서비스 캡처를 담기 때문에 private다.
나중에 공개에서 비공개로 돌리는 것보다 처음부터 private인 쪽이 싸다.
private repo는 `gh auth` 세션이나 `GIT_TOKEN=<pat>` 없이는 클론되지 않는다.

## 외부 도구 repo

`openmontage` 만 내 소유가 아니다. 업스트림은 [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage),
라이선스는 AGPL-3.0 이다. `repo-sync.sh` 는 클론만 하고 의존성은 설치하지 않는다. venv, npm, `.env` 는
그 repo 자신의 `make setup` 이 만든다.

로컬 수정은 푸시 대상이 없으므로 로컬 커밋으로만 남는다. 푸시가 필요해지면 그때 포크하고 이 항목의 `url` 을 바꾼다.
