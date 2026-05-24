# `docs/plans/` — 계획 도큐먼트 운영

idea 이슈가 "무엇·왜"의 단일 진실원이라면, `docs/plans/<issue#>-<slug>.md`는 그 이슈를 어떻게·언제·누가 실행할지에 대한 살아 있는 단일 진실원이다. 모든 보강은 PR로 들어와 git history가 곧 revision log가 된다.

## 라이프사이클

```
1. /idea ... (Telegram)
     │
     ▼
2. [idea-elaborate flow]
     │  GitHub Issue 생성 (label: idea)
     │  Next Actions 마지막 항목: "계획 명세화: 이 이슈 링크로 클로드 데스크탑에서 plan draft 작성 후 docs/plans/ PR 제출"
     ▼
3. (수동) 클로드 데스크탑에서 이슈 URL 전달
     │  _template.md 를 기반으로 docs/plans/<issue#>-<slug>.md 작성
     │  branch: plan/<issue#>-<slug>
     │  PR title: "plan(#<issue>): <짧은 요지> — initial draft"
     │  PR label: plan
     ▼
4. plan-link-back workflow (자동)
     │  PR opened → 이슈에 "Plan PR opened: <pr_url>" 코멘트
     │  PR merged → 이슈에 "Plan merged (revision N): <doc_url>" 코멘트 + has-plan 라벨
     │  status: shipped 면 이슈 close
     ▼
5. 보강 (반복)
     │  같은 plan 파일을 새 branch + PR로 수정
     │  PR title: "plan(#<issue>): revise N — <요지>"
     │  frontmatter의 updated / revisions 갱신
     ▼
6. 구현 단계
     │  코드 PR 본문에 "Implements docs/plans/<#>-<slug>.md" 명시
     │  최종 머지 시 plan doc의 status frontmatter 를 shipped 로 마지막 revision PR
```

## 명명 규칙

- 경로: `docs/plans/<issue-number>-<kebab-slug>.md`
  - 예: `docs/plans/16-recruit-market-data-collection.md`
- slug: issue title 기반, 60자 이내 소문자 kebab-case (`a-z0-9-` 만)
- 이슈 1개 ↔ plan doc 1개 (1:1). 동일 이슈 보강은 같은 파일 수정 PR.

## Frontmatter 스키마

`_template.md` 참고. 필수 키:

| 키 | 형식 | 비고 |
|----|------|------|
| `issue` | integer | 연결 GitHub Issue 번호 |
| `issue_url` | URL | 전체 URL (link-back workflow가 파싱) |
| `title` | string | plan title |
| `status` | enum | `draft` \| `active` \| `blocked` \| `shipped` \| `abandoned` |
| `owner` | github-handle | plan 책임자 |
| `created` | YYYY-MM-DD | 최초 작성일 |
| `updated` | YYYY-MM-DD | 마지막 PR merge일 |
| `revisions` | list | `{ date, pr, note }` 항목 누적 |

## Status 전환

| status | 진입 조건 |
|--------|----------|
| `draft` | 첫 PR이 머지된 직후 |
| `active` | 구현 PR이 plan doc 을 참조하기 시작 (revision PR 로 변경) |
| `blocked` | Open questions 미해소 또는 외부 의존 (revision PR 로 변경) |
| `shipped` | 구현 완료. 마지막 revision PR 에서 변경하며 워크플로우가 이슈 close |
| `abandoned` | 추진 중단. frontmatter 에 사유 메모 후 이슈도 close |

## PR 규칙

- branch: `plan/<issue#>-<slug>`
- label: `plan` (없으면 link-back workflow 가 자동 생성)
- PR title: `plan(#<issue>): <요지>`. 초안 = `initial draft`, 개정 = `revise N — <요지>`
- PR 본문 첫 줄: `Closes-with #<issue> (plan only — issue stays open until shipped)`
  - 실제 issue close 는 status=shipped 시 link-back workflow 가 담당
  - `Closes #<issue>` 처럼 GitHub 표준 키워드는 사용하지 말 것
- PR 본문에 frontmatter `revisions` 마지막 항목과 같은 한 줄 포함

PR template: `.github/PULL_REQUEST_TEMPLATE/plan.md` 사용 (URL 쿼리: `?template=plan.md`).

## 자동 link-back

`.github/workflows/plan-link-back.yml` 가 다음을 수행한다:

1. `docs/plans/**` 가 변경된 PR 의 frontmatter `issue` 파싱
2. PR opened/reopened → 해당 이슈에 PR URL 코멘트
3. PR merged → 이슈에 "Plan merged (revision N)" 코멘트 + `has-plan` 라벨 부착
4. frontmatter `status: shipped` 면 추가로 이슈 close

권한: `contents: read`, `issues: write`, `pull-requests: read`. 시크릿은 `GITHUB_TOKEN` 한 개.

## 작성 가이드 (클로드 데스크탑 세션용)

이슈 URL 만 받았을 때 클로드가 해야 할 절차:

1. `gh issue view <#>` 로 이슈 본문/라벨 확인
2. `docs/plans/_template.md` 복사 → `docs/plans/<#>-<slug>.md` 생성
3. frontmatter 의 모든 필수 키 채움 (`status: draft`, `created`/`updated` 오늘, `revisions` 1개)
4. Context / Approach / Critical files / Verification 채움. 대안이 있으면 Alternatives considered
5. `plan/<#>-<slug>` branch 생성, PR 제출 (label: `plan`, body 첫 줄 `Closes-with #<#>...`)

보강 세션:

1. 기존 `docs/plans/<#>-<slug>.md` 읽기
2. 필요한 섹션만 수정
3. frontmatter `updated` 오늘 날짜, `revisions` 에 새 한 줄 추가
4. PR title `revise N — <요지>`

## 비범위

- LLM 이 GHA 안에서 plan doc 을 자동 작성하지 않는다. 작성·보강은 전부 클로드 데스크탑.
- 텔레그램에 `/plan` 명령어 추가하지 않는다. Worker FLOWS 무변경.
- plan doc 을 PR 없이 main 에 직접 push 하는 경로 없음.
- 다중 이슈 ↔ 1 plan 매핑 미지원 (1:1 만).
