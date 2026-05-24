---
issue: 0
issue_url: https://github.com/BoBeenLee/bbl-ai-lab/issues/0
title: idea 이슈 → docs/plans/ PR 운영 체계
status: draft
owner: BoBeenLee
created: 2026-05-24
updated: 2026-05-24
revisions:
  - { date: 2026-05-24, pr: 0, note: "initial draft — convention + workflow scaffold" }
---

# idea 이슈 → `docs/plans/` PR 운영 체계

> 이 plan doc 은 `docs/plans/` 운영 체계 자체를 dogfooding 한다. 첫 번째 plan 으로 머지되면 link-back workflow 와 컨벤션이 셀프 검증된다.
>
> `issue: 0` 은 placeholder. meta-issue 생성 후 frontmatter 와 `issue_url` 을 갱신하는 revision PR 을 올린다.

## Context

[`idea-elaborate` flow](../idea-elaborate.md) 는 텔레그램 메시지를 GitHub Issue 로 자동 구체화한다. 그러나 "이슈가 만들어진 다음 단계" — 즉 "이 아이디어를 어떻게 실행할 것인가" 의 계획 명세화 — 는 비어 있었다. 사용자는 그 단계를 **클로드 데스크탑에서 이슈 링크를 던져 직접 진행** 하는 워크플로우를 선호한다. 따라서 자동 LLM flow 를 더 추가하는 대신, **컨벤션 + 템플릿 + PR 워크플로** 로 산출물을 표준화한다. 이슈는 "무엇·왜" 의 진실원, plan doc 은 "어떻게·언제·누가" 의 진실원으로 분리한다.

## Approach

`docs/plans/<issue#>-<slug>.md` 단일 파일 1:1 매핑 + frontmatter 기반 상태머신 + 모든 보강을 PR 로. `.github/workflows/plan-link-back.yml` 가 PR open/merge 이벤트를 받아 연결 이슈와 자동 동기화한다. LLM 자동 작성은 명시적 비범위.

세부 규칙·라이프사이클 다이어그램·status 전환표는 [docs/plans/README.md](README.md) 가 단일 진실원. 이 plan doc 은 변경 요지만 추적한다.

## Critical files

| 경로 | 역할 | 신규/수정 |
|------|------|-----------|
| [docs/plans/_template.md](_template.md) | plan doc 표준 템플릿 | 신규 |
| [docs/plans/README.md](README.md) | 운영 가이드 (명명, frontmatter, status, PR 규칙) | 신규 |
| [.github/PULL_REQUEST_TEMPLATE/plan.md](../../.github/PULL_REQUEST_TEMPLATE/plan.md) | plan PR 본문 표준 | 신규 |
| [.github/workflows/plan-link-back.yml](../../.github/workflows/plan-link-back.yml) | PR open/merge → 이슈 코멘트/라벨/close | 신규 |
| [scripts/idea-elaborate.sh](../../scripts/idea-elaborate.sh) | jq 단계에서 Next Actions 마지막에 "계획 명세화: docs/plans/ PR" 한 줄 자동 첨부 | 수정 |
| [scripts/prompts/idea-elaborate.md](../../scripts/prompts/idea-elaborate.md) | 위 자동 첨부 규칙 명시 (LLM 이 중복 생성하지 않도록) | 수정 |
| [README.md](../../README.md) | "## 계획 관리 (`docs/plans/`)" 섹션 추가 | 수정 |

## Verification

| 단계 | 액션 | 기대 |
|------|------|------|
| 템플릿 일관성 | `_template.md` 와 `0-meta.md` frontmatter 키 비교 | 100% 일치 |
| README 진입성 | repo `README.md` 에서 `docs/plans/README.md` 링크 클릭 | OK |
| idea Next Actions 첨부 | `gh workflow run idea-elaborate.yml -f text="테스트"` → 생성 이슈 Next Actions 마지막 줄 | "계획 명세화: ... docs/plans/ PR 제출" 포함 |
| link-back (opened) | 이 PR open | 연결 issue 에 "Plan PR opened: <pr_url>" 코멘트 |
| link-back (merged) | 이 PR merge | 이슈에 "Plan merged (revision 1)" 코멘트 + `has-plan` 라벨 |
| link-back (revision) | 0-meta 의 frontmatter `updated`/`revisions` 갱신 2번째 PR | 이슈에 "Plan merged (revision 2)" 코멘트 |
| link-back (shipped) | 마지막 PR 이 `status: shipped` 로 변경 | workflow 가 이슈 close (reason: completed) |
| 템플릿 제외 | `_template.md` 만 수정한 PR | link-back 동작 없음 (grep 으로 제외) |

## Open questions

- [ ] meta-issue 를 별도로 만들고 `0-meta.md` 의 `issue` / `issue_url` 을 갱신하는 첫 revision PR 을 언제 올릴지 (이 PR merge 직후 권장)
- [ ] `plan-link-back.yml` 의 `pull_request_target` 사용에 대해 추가 보안 검토 필요 여부 (현재는 PR 코드를 실행하지 않고 frontmatter 데이터만 파싱하므로 안전 판단)

## Alternatives considered

- **자동 LLM 으로 plan doc 생성** (GHA + Gemini): 첫 초안 품질이 클로드 데스크탑보다 떨어지고, 사용자가 "이슈 링크 던져서 직접 작성" 흐름을 선호 → 비채택.
- **이슈 본문에 plan 직접 작성**: 이슈가 "무엇·왜" 와 "어떻게" 가 섞여 비대해지고, revision history 가 GH 이슈 edit history 라 diff 가 약함 → 비채택.
- **별도 저장소 (e.g. wiki)**: 같은 PR 흐름과 라이프사이클 자동화가 어려움 → 비채택.

## Revisions

- 2026-05-24 (#TBD): initial draft — convention + workflow scaffold
