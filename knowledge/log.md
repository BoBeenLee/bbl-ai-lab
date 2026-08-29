---
type: Knowledge Bundle Log
title: bbl-ai-lab Knowledge Bundle Log
description: Chronological update history for the OKF bundle.
resource: ./index.md
tags: [okf, changelog]
timestamp: 2026-06-27T00:00:00+09:00
---

# Log

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
