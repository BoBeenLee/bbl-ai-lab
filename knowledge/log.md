---
type: Knowledge Bundle Log
title: bbl-ai-lab Knowledge Bundle Log
description: Chronological update history for the OKF bundle.
resource: ./index.md
tags: [okf, changelog]
timestamp: 2026-06-27T00:00:00+09:00
---

# Log

## 2026-09-05

- `projects/cad`가 `projects/hiking`의 조사 프로토콜을 다시 이식했다 — 이식의 두 번째 사례이자 첫 두 홉
  이식이다. 게이트 → 공식 1차 출처 → 영상 전수조사 → stale 게이트 → 라우팅 → 결정 큐 순서와
  `survey.py`·`check_links.py`(`hike.py`는 첫 설계 건까지 보류)다. 실패 기록은 두 홉을 건너 왔고, 도메인
  차이는 다시 갈렸다: 게이트는 계절이 아니라 버전·플랫폼, `classify` 버킷은 들머리가 아니라 도구·대상,
  조사 언어는 ko 만이 아니라 ko+en. `hiking`이 접어 넣은 stale 게이트 단계는 `travel`의 `plan-trip`에서
  직접 가져왔다 — 버전 경계에서 썩는 사실이 두꺼운 도메인이라서다. 첫 조사: 쿼리 28개 → 고유 1,029편 →
  한국어 FreeCAD 68편(검색 제목 기준 145편 — 절반이 영어 채널의 자동 번역 제목), 자막 86%, 수동 자막 26%로
  `hiking`의 0%와 반대. 한국어 조회수 상위 10 중 9편이 FreeCAD 1.0(2024-11) 이전 화면이다.

- `projects/cad` private repo 추가. FreeCAD 지식(축적층 `knowledge/`)과 설계 한 건(산출층
  `designs/<날짜>-<slug>/`)을 디렉터리로 가르는 규율만 먼저 세우고 내용은 비워 두었다. 도구는
  FreeCAD 하나다 — 1.0 에서 Assembly 가 내장되고 Arch 가 BIM 으로 합쳐져 3D 프린팅 부품·Python
  생성·가구·인테리어 세 하위 도메인이 한 도구에 들어왔고, `knowledge/` 는 도메인이 아니라 질문
  단위로 가른다. 매니페스트 등록은 `bash ops/repo-sync.sh` 자동 등록으로 했다. private 인 이유는
  `hiking` 과 같은 축이다: 집 실측 치수·평면도·제작 이력이 쌓이면 개인 데이터가 된다.

## 2026-08-30

- `projects/hiking`이 `projects/travel`의 조사 프로토콜을 이식했다. 계절 게이트 → 공식
  1차 출처 → 영상 전수조사 → stale 게이트 → 3곳 라우팅 → 결정 큐 순서와 `survey.py`·
  `check_links.py`·`trip.py`(→`hike.py`) 세 스크립트다. hub가 공용 프레임워크를 갖는
  대신 **repo 사이 이식**을 택했다 — 실패 기록이 방법과 같이 오기 때문이다. 실제로
  travel 이 적어 둔 "표본 30편으로 결론의 강도가 표본을 넘었다"가 hiking 에서 그대로
  재현될 뻔한 것을 막았다. 도메인 차이는 이식하면서 갈린다: 여행은 계절이, 등산은
  들머리가 강한 신호라 `classify` 에 들머리 버킷이 추가됐다. 포크가 아니라 이식이므로
  원본과 동기화되지 않는다.

- `projects/hiking` private repo 추가. 등산 지식(축적층 `knowledge/`)과 산행 한 건(산출층
  `hikes/<날짜>-<산>/`)을 디렉터리로 가르는 규율만 먼저 세우고 내용은 비워 두었다. 매니페스트
  등록은 손으로 하지 않았다 — origin 을 붙이고 `bash ops/repo-sync.sh` 를 한 번 돌려
  자동 등록 경로가 실제로 동작하는지 같이 확인했다. `hiking` 이 private 인 이유는 `music`·
  `shopping` 과 같은 축이다: 처음부터 개인 데이터를 담아서가 아니라 GPS 경로·체력 수치·장비
  이력이 쌓이면서 개인 데이터가 되기 때문이다.

- `projects/` 아래 repo의 매니페스트 등록을 `ops/repo-sync.sh`가 하도록 바꿨다. 스크립트가
  `projects/*/` 를 훑어 매니페스트에 없는 클론의 `origin` URL과 기본 브랜치를 읽어 frontmatter에
  넣고, `.gitignore`는 개별 경로 대신 `/projects/*/` glob 하나로 덮는다. 사람이 잊는 쪽은
  클론이 아니라 등록이고, 그 망각은 repo를 *만든* 머신에서 일어나므로 등록이 클론과 같은 명령에
  묶여 있어야 잡힌다 — 실제로 `projects/shopping`이 그렇게 누락된 채로 있었다.
  `ops/repo-sync.test.sh`가 등록·중복 방지·origin 없는 디렉터리 경고를 임시 디렉터리에서 검증한다.

## 2026-08-29

- `projects/music` private repo를 `ops/repos.md` 매니페스트에 등록. AI 음악 제작 지식을 소유하며,
  첫 산출물은 로컬 오픈 모델과 상용 서비스를 라이선스·비용·하드웨어 제약으로 비교한 조사 문서다.
  hub 의 `docs/`는 flow 문서 자리이고 `knowledge/`는 hub 자신의 개념 번들이라 외부 토픽을
  담지 않는다는 것이 별도 repo 로 뺀 이유다. 허브는 URL 과 브랜치만 소유한다.

## 2026-08-23

- `projects/finance` private repo를 `ops/repos.md` 매니페스트에 등록. 재테크 지식 베이스를 소유하며,
  값의 휘발성을 세 등급(구조 / 제도값 / 시세)으로 갈라 저장 위치로 staleness를 강제하는 것이 그 repo의
  설계 축이다. 허브는 URL과 브랜치만 소유한다.

## 2026-08-22

- `projects/games` private repo를 `ops/repos.md` 매니페스트에 등록. 매니페스트가 `ops/` 밖 경로와 private repo도 담는다는 사실을 AGENTS.md·CONTEXT.md에 반영하고 project repo 용어를 추가했다.
- Installed loop engineering scaffolding from `cobusgreyling/loop-engineering`: `LOOP.md`, `STATE.md`, `loop-constraints.md`, `loop-budget.md`, `loop-run-log.md`, `docs/safety.md`, and six `.claude/skills/` entries.
- Added the [Autonomous loop](concepts/autonomous-loop.md) concept to separate scheduled loops from Telegram-triggered automation flows.
- Replaced the three operator submodules with manifest-driven clones: `ops/repos.md` plus `ops/repo-sync.sh`.
- Renamed the `Operator workspace submodule` concept to [Operator workspace repo](concepts/operator-workspace-repo.md).

## 2026-06-27

- Created the initial OKF knowledge bundle.
- Added core project concepts, the `idea-elaborate` flow concept, and the new-flow playbook.
