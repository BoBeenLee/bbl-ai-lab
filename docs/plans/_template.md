---
issue: 0
issue_url: https://github.com/BoBeenLee/bbl-ai-lab/issues/0
title: <plan title>
status: draft  # draft | active | blocked | shipped | abandoned
owner: <github-handle>
created: YYYY-MM-DD
updated: YYYY-MM-DD
revisions:
  - { date: YYYY-MM-DD, pr: 0, note: "initial draft" }
---

# <title>

## Context

이 plan이 왜 필요한가. 연결 이슈의 핵심 문제·목표를 자기 언어로 1~2문단. 이슈 본문 복붙 금지 — 이슈는 "무엇·왜"의 진실원, 여기는 "어떻게·언제·누가"의 진실원이다.

## Approach

권장 접근 1개. 대안은 [Alternatives considered](#alternatives-considered) 섹션으로 분리.

## Critical files

| 경로 | 역할 | 신규/수정 |
|------|------|-----------|
|      |      |           |

## Verification

| 단계 | 액션 | 기대 |
|------|------|------|
|      |      |      |

## Open questions

- [ ] ...

## Domain language updates

이 plan 으로 인해 `CONTEXT.md` 에 추가/수정/충돌 해소되는 도메인 용어. 연결 이슈의 "글로사리 후보" 섹션에서 시작해 이 plan 단계에서 결정화. 변경 없으면 명시적으로 "변경 없음" 한 줄.

| 용어 | 정의 (1~2문장) | 액션 | 비고 |
|------|----------------|------|------|
|      |                | add / update / resolve-conflict |  |

`CONTEXT.md` 가 아직 레포에 없다면 이 plan 의 첫 항목으로 lazy 생성한다. 포맷은 `docs/plans/README.md` 의 "CONTEXT.md 포맷 (1쪽)" 참고.

## ADR proposals

이 plan 으로 같은 PR 에 추가되는 `docs/adr/000N-<slug>.md` 항목. 연결 이슈의 "ADR 후보" 섹션에서 시작해, ADR 3조건을 모두 충족하는 것만 옮긴다. 변경 없으면 명시적으로 "변경 없음" 한 줄.

| ADR 번호 | 제목 | 3조건 자기검증 |
|----------|------|----------------|
|  000N    |      | [ ] hard-to-reverse [ ] surprising [ ] real trade-off |

`docs/adr/` 가 아직 레포에 없다면 이 plan 의 첫 ADR 로 lazy 생성한다. 번호는 `docs/adr/` 의 최대값 + 1.

## Alternatives considered

잠깐 본 다른 길과 탈락 사유.

## Revisions

- YYYY-MM-DD (#<PR>): initial draft
